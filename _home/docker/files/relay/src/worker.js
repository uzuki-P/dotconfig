// Public relay for gokapi-android: checks a per-device credential, allows only
// the API routes the app calls, and forwards the request to Gokapi through a
// Workers VPC service binding (a Cloudflare Tunnel with no public hostname).
// See ../../docs/relay.md.

// Gokapi file IDs are letters and digits. The narrow character class keeps
// percent-encoded slashes and dots out of the forwarded path.
const FILE_ID = "[A-Za-z0-9_-]{1,128}";

// Every route GokapiClient.kt in gokapi-android calls. Anything else is 404.
// Keep this list, the tests, and the app in step.
export const API_ROUTES = [
	["GET", new RegExp("^/api/info/(version|config)$")],
	["GET", new RegExp("^/api/files/list$")],
	["GET", new RegExp(`^/api/files/list/${FILE_ID}$`)],
	["GET", new RegExp(`^/api/files/download/${FILE_ID}$`)],
	["DELETE", new RegExp("^/api/files/delete$")],
	["POST", new RegExp("^/api/chunk/(add|complete)$")],
];

// Previews from gokapi-thumbs (../../thumbs), a separate service behind its
// own VPC binding. Only `size=s` or `size=l` may follow.
const THUMBNAIL_ROUTE = new RegExp(`^/api/thumbnail/${FILE_ID}$`);
const THUMBNAIL_QUERY = /^(\?size=[sl])?$/;

// Only the Host header and TLS SNI come from these URLs; the VPC service
// configuration decides where the request goes.
const DEFAULT_UPSTREAM_ORIGIN = "http://127.0.0.1:53842";
const DEFAULT_THUMBS_ORIGIN = "http://127.0.0.1:53845";

const DEVICE_ID = /^[a-z0-9][a-z0-9-]{0,63}$/;
const MAX_SECRET_LENGTH = 256;
// KV caches a device record at the edge this long, so a revoked device can
// keep working for up to a minute.
const DEVICE_CACHE_TTL = 60;

const HOP_BY_HOP = new Set([
	"connection",
	"keep-alive",
	"proxy-authenticate",
	"proxy-authorization",
	"proxy-connection",
	"te",
	"trailer",
	"transfer-encoding",
	"upgrade",
]);
// Headers the relay owns or that would mislead Gokapi. cookie is dropped so a
// browser session can never ride along; the app authenticates with apikey.
const DROPPED = new Set(["host", "content-length", "cookie", "forwarded", "x-real-ip", "true-client-ip"]);

export function isAllowedRoute(method, pathname) {
	return API_ROUTES.some(([allowed, pattern]) => allowed === method && pattern.test(pathname));
}

function relayError(status, code, message) {
	return new Response(`${message}\n`, {
		status,
		headers: {
			"content-type": "text/plain; charset=utf-8",
			"cache-control": "no-store",
			"x-relay-error": code,
		},
	});
}

async function sha256(text) {
	return new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text)));
}

function hexToBytes(hex) {
	if (typeof hex !== "string" || !/^[0-9a-f]{64}$/i.test(hex)) return null;
	const bytes = new Uint8Array(32);
	for (let i = 0; i < 32; i++) bytes[i] = parseInt(hex.slice(i * 2, i * 2 + 2), 16);
	return bytes;
}

// Both inputs are 32-byte digests, so their length leaks nothing.
export function timingSafeEqual(a, b) {
	if (a.length !== b.length) return false;
	if (typeof crypto.subtle.timingSafeEqual === "function") return crypto.subtle.timingSafeEqual(a, b);
	let diff = 0;
	for (let i = 0; i < a.length; i++) diff |= a[i] ^ b[i];
	return diff === 0;
}

// authenticate returns the device record or null. It hashes the secret even
// when the ID is unknown, so both failures take about the same time.
export async function authenticate(request, env) {
	const id = request.headers.get("x-relay-id") ?? "";
	const secret = request.headers.get("x-relay-secret") ?? "";
	if (!DEVICE_ID.test(id) || secret.length === 0 || secret.length > MAX_SECRET_LENGTH) return null;
	const record = await env.DEVICES.get(`device:${id}`, { type: "json", cacheTtl: DEVICE_CACHE_TTL });
	const actual = await sha256(secret);
	const expected = hexToBytes(record?.hash) ?? new Uint8Array(32);
	const match = timingSafeEqual(actual, expected);
	return record && hexToBytes(record.hash) && match ? { id, name: record.name } : null;
}

export function forwardHeaders(incoming) {
	const listed = (incoming.get("connection") ?? "")
		.split(",")
		.map((name) => name.trim().toLowerCase())
		.filter(Boolean);
	const headers = new Headers();
	for (const [name, value] of incoming) {
		if (
			HOP_BY_HOP.has(name) ||
			DROPPED.has(name) ||
			listed.includes(name) ||
			name.startsWith("x-relay-") ||
			name.startsWith("cf-") ||
			name.startsWith("x-forwarded-")
		) {
			continue;
		}
		headers.append(name, value);
	}
	// Gokapi trusts X-Forwarded-For only from 127.0.0.1 (GOKAPI_TRUSTED_PROXIES),
	// which is where the tunnel connects from, so it logs the real client
	// instead of the tunnel.
	const client = incoming.get("cf-connecting-ip");
	if (client) headers.set("x-forwarded-for", client);
	return headers;
}

async function proxyApi(request, env, url, service = env.GOKAPI, origin = env.UPSTREAM_ORIGIN || DEFAULT_UPSTREAM_ORIGIN) {
	const upstream = new URL(url.pathname + url.search, origin);
	const hasBody = request.body !== null && request.method !== "GET" && request.method !== "HEAD";
	let response;
	try {
		response = await service.fetch(upstream.toString(), {
			method: request.method,
			headers: forwardHeaders(request.headers),
			body: hasBody ? request.body : undefined,
			// Required by Node's fetch for a streamed body; the Workers runtime ignores it.
			...(hasBody ? { duplex: "half" } : {}),
			redirect: "manual",
		});
	} catch {
		return relayError(502, "upstream-unreachable", "files server unreachable");
	}
	const headers = new Headers(response.headers);
	headers.set("cache-control", "no-store");
	headers.delete("set-cookie");
	return new Response(response.body, { status: response.status, statusText: response.statusText, headers });
}

export async function handleRequest(request, env) {
	const url = new URL(request.url);
	const ip = request.headers.get("cf-connecting-ip") ?? "unknown";

	// Per-IP limit first, so guessing device credentials is slow.
	if (!(await env.IP_LIMITER.limit({ key: `ip:${ip}` })).success) {
		return relayError(429, "rate-limited", "too many requests");
	}

	// Authenticate before looking at the path, so unauthenticated probes
	// cannot tell allowed routes from the rest.
	const device = await authenticate(request, env);
	if (!device) return relayError(401, "unauthorized", "unauthorized");

	if (!(await env.DEVICE_LIMITER.limit({ key: `device:${device.id}` })).success) {
		return relayError(429, "rate-limited", "too many requests");
	}

	// A future login page or other routes would be dispatched here, before
	// the API allowlist.
	if (request.method === "GET" && THUMBNAIL_ROUTE.test(url.pathname) && THUMBNAIL_QUERY.test(url.search) && env.THUMBS) {
		return proxyApi(request, env, url, env.THUMBS, env.THUMBS_ORIGIN || DEFAULT_THUMBS_ORIGIN);
	}
	if (url.pathname.startsWith("/api/") && isAllowedRoute(request.method, url.pathname)) {
		return proxyApi(request, env, url);
	}
	return relayError(404, "not-allowed", "not found");
}

export default {
	async fetch(request, env) {
		try {
			return await handleRequest(request, env);
		} catch (error) {
			console.error("relay error", error);
			return relayError(500, "internal", "relay error");
		}
	},
};
