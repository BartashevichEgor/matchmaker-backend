#!/usr/bin/env sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 /absolute/path/backup.dump" >&2
  exit 2
fi

backup=$1
case "$backup" in
  /*) ;;
  *) echo "Backup path must be absolute" >&2; exit 2 ;;
esac
if [ ! -f "$backup" ] || [ ! -r "$backup" ]; then
  echo "Backup must be an existing readable file" >&2
  exit 2
fi
if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required for an isolated restore check" >&2
  exit 2
fi

# The restore runs in a disposable, network-isolated PostgreSQL container. The
# backup is streamed over stdin; the data directory lives only in tmpfs.
container="matchmaker-restore-check-$$"
started=0
cleanup() {
  if [ "$started" -eq 1 ]; then
    docker rm -f "$container" >/dev/null 2>&1 || true
  fi
}
trap cleanup 0
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

docker run --detach \
  --name "$container" \
  --network none \
  --tmpfs /var/lib/postgresql/data:rw,nosuid,size=1g \
  --env POSTGRES_DB=restore_check \
  --env POSTGRES_USER=restore_check \
  --env PGUSER=restore_check \
  --env POSTGRES_HOST_AUTH_METHOD=trust \
  postgres:16 >/dev/null
started=1

attempt=0
until docker exec "$container" pg_isready -U restore_check -d restore_check >/dev/null 2>&1; do
  attempt=$((attempt + 1))
  if [ "$attempt" -ge 60 ]; then
    echo "Temporary PostgreSQL did not become ready" >&2
    exit 1
  fi
  sleep 1
done

docker exec -i "$container" pg_restore \
  --exit-on-error \
  --no-owner \
  --no-acl \
  --dbname=restore_check < "$backup"

revision=$(docker exec "$container" psql --no-psqlrc --tuples-only --no-align \
  --set=ON_ERROR_STOP=1 --dbname=restore_check \
  --command="SELECT version_num FROM alembic_version LIMIT 1")
table_count=$(docker exec "$container" psql --no-psqlrc --tuples-only --no-align \
  --set=ON_ERROR_STOP=1 --dbname=restore_check \
  --command="SELECT count(*) FROM information_schema.tables WHERE table_schema = current_schema()")
if [ -z "$revision" ] || [ "$table_count" -lt 2 ]; then
  echo "Restored database is missing its migration version or application tables" >&2
  exit 1
fi
echo "Restore verified: migration=$revision, tables=$table_count"
