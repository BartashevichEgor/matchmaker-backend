#!/usr/bin/env sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "Usage: PGHOST=... PGUSER=... PGDATABASE=... PGPASSFILE=... $0 /absolute/path/backup.dump" >&2
  exit 2
fi

target=$1
case "$target" in
  /*) ;;
  *) echo "Backup target must be an absolute path" >&2; exit 2 ;;
esac

if [ -e "$target" ] || [ -L "$target" ]; then
  echo "Backup target already exists" >&2
  exit 2
fi

target_dir=$(dirname "$target")
if [ ! -d "$target_dir" ]; then
  echo "Backup target directory does not exist" >&2
  exit 2
fi

if [ -z "${PGHOST:-}" ] || [ -z "${PGUSER:-}" ] || [ -z "${PGDATABASE:-}" ] || [ -z "${PGPASSFILE:-}" ]; then
  echo "PGHOST, PGUSER, PGDATABASE and PGPASSFILE must be set" >&2
  exit 2
fi
if [ ! -r "$PGPASSFILE" ]; then
  echo "PGPASSFILE must name a readable PostgreSQL password file" >&2
  exit 2
fi
if ! command -v pg_dump >/dev/null 2>&1; then
  echo "pg_dump is required" >&2
  exit 2
fi

umask 077
temporary=$(mktemp "$target.tmp.XXXXXX")
cleanup() {
  rm -f "$temporary"
}
trap cleanup 0
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

PGCONNECT_TIMEOUT=${PGCONNECT_TIMEOUT:-10} pg_dump \
  --format=custom \
  --no-owner \
  --no-acl \
  --file="$temporary"

# Link creation is atomic and fails if another process created the target meanwhile.
ln "$temporary" "$target"
rm -f "$temporary"
trap - 0 HUP INT TERM
echo "Backup written: $target"
