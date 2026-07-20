#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
backup_dir="${project_dir}/backups"
timestamp="$(date +%Y%m%d-%H%M%S)"

set -a
# shellcheck disable=SC1091
source "${project_dir}/.env"
set +a

mkdir -p "${backup_dir}"
cd "${project_dir}"

podman compose exec -T postgres pg_dumpall \
  --username "${POSTGRES_USER:-developer}" \
  > "${backup_dir}/postgres-${timestamp}.sql"
podman compose exec -T redis redis-cli \
  -a "${REDIS_PASSWORD:-development_only_change_me}" \
  --no-auth-warning BGSAVE >/dev/null

echo "PostgreSQL backup: ${backup_dir}/postgres-${timestamp}.sql"
echo "Redis persisted to: ${project_dir}/data/redis/dump.rdb"
