#!/bin/sh
# One load run against a running stack: users, spawn rate, duration, host. Prints Locust's summary, writes CSVs.
#   sh loadtest/run.sh [USERS=20] [RATE=5] [TIME=2m] [HOST=http://127.0.0.1:8000] [OUT=loadtest/out/run]
set -eu
here="$(cd "$(dirname "$0")" && pwd)"
USERS="${1:-20}"; RATE="${2:-5}"; TIME="${3:-2m}"; HOST="${4:-http://127.0.0.1:8000}"; OUT="${5:-$here/out/run}"
mkdir -p "$(dirname "$OUT")"
UV="$(command -v uv || echo "$HOME/.local/bin/uv")"
exec "$UV" tool run --from locust locust -f "$here/locustfile.py" --headless -u "$USERS" -r "$RATE" -t "$TIME" \
  --host "$HOST" --csv "$OUT" --only-summary
