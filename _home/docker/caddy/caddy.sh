#!/usr/bin/env bash

set -euo pipefail

readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly COMPOSE_FILE="${SCRIPT_DIR}/compose.yaml"
readonly CONTAINER_NAME="caddy"

podman_rootful() {
	if (( EUID == 0 )); then
		podman "$@"
	else
		sudo podman "$@"
	fi
}

compose() {
	podman_rootful compose --file "${COMPOSE_FILE}" "$@"
}

validate() {
	podman_rootful exec "${CONTAINER_NAME}" \
		caddy validate --config /etc/caddy/Caddyfile
}

usage() {
	cat <<'EOF'
Usage: ./caddy.sh <command>

Commands:
  setup      Build the image and start or update the Caddy container
  validate   Validate the Caddyfile inside the running container
  reload     Validate, then activate the current Caddyfile
  status     Show the Caddy container status
  logs       Follow the Caddy container logs
  help       Show this help
EOF
}

case "${1:-help}" in
	setup)
		compose up --detach --build
		validate
		;;
	validate)
		validate
		;;
	reload)
		validate
		podman_rootful exec "${CONTAINER_NAME}" \
			caddy reload --config /etc/caddy/Caddyfile
		;;
	status)
		podman_rootful ps --filter "name=^${CONTAINER_NAME}$"
		;;
	logs)
		podman_rootful logs --follow --tail 100 "${CONTAINER_NAME}"
		;;
	help|-h|--help)
		usage
		;;
	*)
		echo "Unknown command: $1" >&2
		usage >&2
		exit 2
		;;
esac
