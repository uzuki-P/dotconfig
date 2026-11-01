import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { beforeEach, describe, test } from "node:test";

import worker, { isAllowedRoute } from "../src/worker.js";

const RELAY = "https://relay.example.com";
const DEVICE_ID = "pixel-9-0a1b2c3d";
const SECRET = "c2VjcmV0LXNlY3JldC1zZWNyZXQtc2VjcmV0LXNlY3JldA";

function hash(secret) {
	return createHash("sha256").update(secret).digest("hex");
}

class FakeKv {
	constructor(entries = {}) {
		this.entries = new Map(Object.entries(entries));
		this.reads = 0;
	}
	async get(key, options) {
		this.reads++;
		assert.equal(options?.type, "json");
		const value = this.entries.get(key);
		return value === undefined ? null : JSON.parse(value);
	}
}

class FakeLimiter {
	constructor() {
		this.blocked = new Set();
		this.keys = [];
	}
	async limit({ key }) {
		this.keys.push(key);
		return { success: !this.blocked.has(key) };
	}
}

class FakeVpc {
	constructor() {
		this.calls = [];
		this.respond = async () => new Response('{"Result":"OK"}', { headers: { "content-type": "application/json" } });
	}
	async fetch(url, init) {
		const headers = new Headers(init.headers);
		const body = init.body ? Buffer.from(await new Response(init.body).arrayBuffer()).toString() : null;
		this.calls.push({ url, method: init.method, headers, body, init });
		return this.respond(url, init);
	}
}

let env;

beforeEach(() => {
	env = {
		DEVICES: new FakeKv({
			[`device:${DEVICE_ID}`]: JSON.stringify({ name: "pixel-9", hash: hash(SECRET), created: "2026-10-31T00:00:00Z" }),
		}),
		GOKAPI: new FakeVpc(),
		IP_LIMITER: new FakeLimiter(),
		DEVICE_LIMITER: new FakeLimiter(),
	};
});

function request(path, { method = "GET", headers = {}, body, auth = true } = {}) {
	const all = {
		"cf-connecting-ip": "203.0.113.7",
		...(auth ? { "x-relay-id": DEVICE_ID, "x-relay-secret": SECRET } : {}),
		...headers,
	};
	return new Request(RELAY + path, { method, headers: all, body, ...(body ? { duplex: "half" } : {}) });
}

async function send(...args) {
	return worker.fetch(request(...args), env);
}

describe("allowed routes", () => {
	const allowed = [
		["GET", "/api/info/version"],
		["GET", "/api/info/config"],
		["GET", "/api/files/list"],
		["GET", "/api/files/list/abcDEF123"],
		["GET", "/api/files/download/abcDEF123"],
		["DELETE", "/api/files/delete"],
		["POST", "/api/chunk/add"],
		["POST", "/api/chunk/complete"],
	];

	for (const [method, path] of allowed) {
		test(`${method} ${path} forwards with apikey and without relay headers`, async () => {
			const response = await send(path, {
				method,
				headers: { apikey: "gokapi-key", cookie: "session=x", "x-forwarded-for": "6.6.6.6", "cf-ray": "abc" },
			});
			assert.equal(response.status, 200);
			assert.equal(response.headers.get("cache-control"), "no-store");
			assert.equal(env.GOKAPI.calls.length, 1);
			const call = env.GOKAPI.calls[0];
			assert.equal(call.method, method);
			assert.equal(call.url, `http://127.0.0.1:53842${path}`);
			assert.equal(call.init.redirect, "manual");
			assert.equal(call.headers.get("apikey"), "gokapi-key");
			assert.equal(call.headers.get("x-forwarded-for"), "203.0.113.7");
			for (const name of ["x-relay-id", "x-relay-secret", "cookie", "cf-ray", "cf-connecting-ip", "host"]) {
				assert.equal(call.headers.has(name), false, name);
			}
		});
	}

	test("query string is preserved", async () => {
		await send("/api/files/list?foo=bar&x=%2F");
		assert.equal(env.GOKAPI.calls[0].url, "http://127.0.0.1:53842/api/files/list?foo=bar&x=%2F");
	});

	test("request body streams through", async () => {
		const chunks = ["--boundary\r\n", "chunk-data-".repeat(1000), "\r\n--boundary--\r\n"];
		const stream = new ReadableStream({
			start(controller) {
				for (const chunk of chunks) controller.enqueue(new TextEncoder().encode(chunk));
				controller.close();
			},
		});
		const response = await send("/api/chunk/add", {
			method: "POST",
			body: stream,
			headers: { "content-type": "multipart/form-data; boundary=boundary", apikey: "k" },
		});
		assert.equal(response.status, 200);
		const call = env.GOKAPI.calls[0];
		assert.equal(call.body, chunks.join(""));
		assert.equal(call.headers.get("content-type"), "multipart/form-data; boundary=boundary");
		assert.equal(call.init.duplex, "half");
	});

	test("response body, status, and headers stream back", async () => {
		const payload = "x".repeat(100_000);
		env.GOKAPI.respond = async () =>
			new Response(
				new ReadableStream({
					start(controller) {
						controller.enqueue(new TextEncoder().encode(payload));
						controller.close();
					},
				}),
				{ status: 206, headers: { "content-type": "application/octet-stream", "set-cookie": "a=b", "cache-control": "public" } },
			);
		const response = await send("/api/files/download/abc");
		assert.equal(response.status, 206);
		assert.equal(await response.text(), payload);
		assert.equal(response.headers.get("content-type"), "application/octet-stream");
		assert.equal(response.headers.get("cache-control"), "no-store");
		assert.equal(response.headers.has("set-cookie"), false);
	});

	test("Gokapi redirects are returned, not followed", async () => {
		env.GOKAPI.respond = async () => new Response(null, { status: 302, headers: { location: "/admin" } });
		const response = await send("/api/info/version");
		assert.equal(response.status, 302);
		assert.equal(response.headers.get("location"), "/admin");
	});

	test("Gokapi's own 401 passes through", async () => {
		env.GOKAPI.respond = async () => new Response('{"Result":"error"}', { status: 401, headers: { "content-type": "application/json" } });
		const response = await send("/api/info/version");
		assert.equal(response.status, 401);
		assert.equal(response.headers.has("x-relay-error"), false);
	});

	test("unreachable tunnel is 502", async () => {
		env.GOKAPI.respond = async () => {
			throw new Error("no tunnel");
		};
		const response = await send("/api/info/version");
		assert.equal(response.status, 502);
		assert.equal(response.headers.get("x-relay-error"), "upstream-unreachable");
	});
});

describe("authentication", () => {
	const cases = {
		"no headers": { auth: false },
		"wrong secret": { auth: false, headers: { "x-relay-id": DEVICE_ID, "x-relay-secret": "nope" } },
		"unknown device": { auth: false, headers: { "x-relay-id": "other-00000000", "x-relay-secret": SECRET } },
		"id only": { auth: false, headers: { "x-relay-id": DEVICE_ID } },
		"bad id": { auth: false, headers: { "x-relay-id": "../device", "x-relay-secret": SECRET } },
	};
	for (const [name, options] of Object.entries(cases)) {
		for (const path of ["/api/info/version", "/admin", "/api/auth/create", "/"]) {
			test(`${name} on ${path} is 401`, async () => {
				const response = await send(path, options);
				assert.equal(response.status, 401);
				assert.equal(response.headers.get("x-relay-error"), "unauthorized");
				assert.equal(env.GOKAPI.calls.length, 0);
			});
		}
	}

	test("malformed stored hash is rejected", async () => {
		env.DEVICES.entries.set(`device:${DEVICE_ID}`, JSON.stringify({ name: "x", hash: "zz" }));
		assert.equal((await send("/api/info/version")).status, 401);
	});
});

describe("disallowed routes with valid credentials", () => {
	const blocked = [
		["GET", "/admin"],
		["GET", "/"],
		["GET", "/d?id=abc"],
		["GET", "/h/abc.png"],
		["GET", "/setup"],
		["GET", "/apidocumentation"],
		["POST", "/api/auth/create"],
		["PUT", "/api/auth/modify"],
		["GET", "/api/user/list"],
		["GET", "/api/logs/delete"],
		["POST", "/api/files/list"],
		["GET", "/api/files/delete"],
		["GET", "/api/chunk/add"],
		["GET", "/api/files/list/abc/def"],
		["GET", "/api/files/download/..%2F..%2Fadmin"],
		["GET", "/api/files/list/../../admin"],
		["GET", "/api/info/version/"],
		["HEAD", "/api/info/version"],
	];
	for (const [method, path] of blocked) {
		test(`${method} ${path} is 404`, async () => {
			const response = await send(path, { method });
			assert.equal(response.status, 404);
			assert.equal(response.headers.get("x-relay-error"), "not-allowed");
			assert.equal(env.GOKAPI.calls.length, 0);
		});
	}

	test("isAllowedRoute is method-aware", () => {
		assert.equal(isAllowedRoute("GET", "/api/files/list"), true);
		assert.equal(isAllowedRoute("DELETE", "/api/files/list"), false);
	});
});

describe("rate limits", () => {
	test("per-IP limit applies before authentication", async () => {
		env.IP_LIMITER.blocked.add("ip:203.0.113.7");
		const response = await send("/api/info/version", { auth: false });
		assert.equal(response.status, 429);
		assert.equal(response.headers.get("x-relay-error"), "rate-limited");
		assert.equal(env.DEVICES.reads, 0);
	});

	test("per-device limit applies after authentication", async () => {
		env.DEVICE_LIMITER.blocked.add(`device:${DEVICE_ID}`);
		const response = await send("/api/info/version");
		assert.equal(response.status, 429);
		assert.equal(response.headers.get("x-relay-error"), "rate-limited");
		assert.equal(env.GOKAPI.calls.length, 0);
		assert.deepEqual(env.DEVICE_LIMITER.keys, [`device:${DEVICE_ID}`]);
	});
});
