# Development databases

Local PostgreSQL and Redis for host applications and other Podman containers.
The ports bind only to `127.0.0.1`; container-to-container traffic uses the
`dev-databases` network.

## Start and stop

```bash
cd /home/uzuki_p/dotconfig/_home/docker/database
just setup
just status
just stop
```

`down` removes containers but preserves everything in `data/`. To remove the
database contents, stop the stack and explicitly delete the relevant data
directory contents.

## Connect from the host

- PostgreSQL: `postgresql://developer:development_only_change_me@127.0.0.1:5432/development`
- Redis: `redis://:development_only_change_me@127.0.0.1:6379/0`

Change the development credentials and optional host ports in `.env` before
starting PostgreSQL for the first time. Per the official image behavior,
`POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB` only apply while
initializing an empty `data/postgres/` directory. Later `.env` changes do not
modify the persisted cluster.

## Connect from another container

Join the shared network, then use service container names and internal ports:

```bash
podman run --rm --network dev-databases docker.io/library/postgres:17-alpine \
  psql postgresql://developer:development_only_change_me@dev-postgres:5432/development

podman run --rm --network dev-databases docker.io/library/redis:8-alpine \
  redis-cli -h dev-redis -a development_only_change_me ping
```

For another Compose project, declare the network as external:

```yaml
networks:
  databases:
    external: true
    name: dev-databases
```

Attach the consuming service to `databases`, then connect to `dev-postgres:5432`
or `dev-redis:6379`. A Podman pod can likewise be created with
`podman pod create --network dev-databases ...`.

## Layout

```text
database/
├── compose.yaml
├── .env
├── config/redis/redis.conf
├── data/postgres/
├── data/redis/
├── backups/
└── scripts/backup.sh
```

Run `just backup` while the services are running to dump PostgreSQL and request
a Redis snapshot. Run `just` to list all available operations.
