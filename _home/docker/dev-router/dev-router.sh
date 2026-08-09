#!/usr/bin/env bash

set -euo pipefail

readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly ROUTE_CLI="${SCRIPT_DIR}/../../.local/bin/dev-route"
readonly CADDY_ENV="${SCRIPT_DIR}/../caddy/.env"

usage() {
	cat <<'EOF'
Usage: ./dev-router.sh <command>

Commands:
  setup      Initialize routes from Caddy's environment and apply them
  validate   Validate the registry and generated Caddy fragment
  apply      Reapply persistent routes to the running Caddy instance
  status     Show currently published routes
  help       Show this help
EOF
}

case "${1:-help}" in
	setup)
		if [[ -f "${CADDY_ENV}" ]]; then
			"${ROUTE_CLI}" init --from-env-file "${CADDY_ENV}"
		else
			"${ROUTE_CLI}" init
		fi
		;;
	validate)
		"${ROUTE_CLI}" validate
		;;
	apply)
		"${ROUTE_CLI}" apply
		;;
	status)
		"${ROUTE_CLI}" list
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
