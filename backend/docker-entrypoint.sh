#!/bin/sh
set -eu

if [ ! -f /app/hoferland.db ]; then
  echo "hoferland.db fehlt im Image." >&2
  exit 1
fi

mkdir -p /data
cp -f /app/hoferland.db /data/hoferland.db
exec "$@"
