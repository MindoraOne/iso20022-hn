#!/usr/bin/env bash
# iso20022-hn — manual rate limit probe.
#
# Fires N requests with curl against POST {API_PREFIX}/local/hn/generate
# (JSON: template + data — main contract, service-to-service) and counts
# how many return 200 and how many return 429.
# Requires the service to already be up (make dev / make run / docker compose up).
#
# To test the multipart endpoint (manual CSV upload), use instead:
#   POST {API_PREFIX}/local/hn/generate/csv
#
# Usage:
#   scripts/load-test.sh [N]
#   PORT=8000 scripts/load-test.sh 50

set -euo pipefail

N="${1:-40}"
PORT="${PORT:-8000}"
HOST="${LOAD_TEST_HOST:-localhost}"
URL="http://${HOST}:${PORT}/api/v1/local/hn/generate"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JSON_PAYLOAD="${SCRIPT_DIR}/fixtures/generate-ach-payload.json"

if [ ! -f "$JSON_PAYLOAD" ]; then
  echo "ERROR: no se encontro el fixture JSON en $JSON_PAYLOAD" >&2
  exit 1
fi

echo "Disparando $N requests contra $URL ..."

count_200=0
count_429=0
count_other=0

for i in $(seq 1 "$N"); do
  status=$(curl -s -o /dev/null -w '%{http_code}' \
    -X POST "$URL" \
    -H "Content-Type: application/json" \
    --data-binary "@${JSON_PAYLOAD}")

  case "$status" in
    200) count_200=$((count_200 + 1)) ;;
    429) count_429=$((count_429 + 1)) ;;
    *) count_other=$((count_other + 1)); echo "  request $i -> status inesperado: $status" ;;
  esac
done

echo ""
echo "Resumen:"
echo "  200 OK              : $count_200"
echo "  429 rate_limit       : $count_429"
echo "  otros                : $count_other"
echo "  total                : $N"
