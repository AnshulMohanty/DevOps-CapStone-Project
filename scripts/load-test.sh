#!/bin/sh
# Generate enough traffic on the FoundIt backend to push CPU past the HPA target,
# mixed with a few writes so the business metrics panels move too.
#
# Run it *inside* the cluster (no port-forward bottleneck):
#   kubectl run load -n foundit --rm -i --restart=Never --image=curlimages/curl:8.11.1 \
#     --env REQUESTS=6000 --command -- sh -c "$(cat scripts/load-test.sh)"
#
# Kept deliberately light (8 parallel clients): on a single small minikube node a heavier test
# starves the API server itself. A cloud node group would add nodes instead.
set -eu
export BASE="${BASE:-http://foundit-backend.foundit:8000}"
REQUESTS="${REQUESTS:-6000}"
CONCURRENCY="${CONCURRENCY:-8}"

echo "Load test: $REQUESTS requests, $CONCURRENCY in parallel, against $BASE"

# Every 40th request reports an item, every 100th marks the oldest open one as returned;
# everything else is a filtered list query (DB query + JSON serialisation = real CPU).
seq 1 "$REQUESTS" | xargs -P "$CONCURRENCY" -n 1 sh -c '
  i=$1
  if [ $((i % 100)) -eq 0 ]; then
    id=$(curl -s "$BASE/api/items?status=OPEN" | grep -o "\"id\":[0-9]*" | tail -1 | cut -d: -f2)
    [ -n "$id" ] && curl -s -o /dev/null -X POST "$BASE/api/items/$id/resolve"
  elif [ $((i % 40)) -eq 0 ]; then
    if [ $((i % 80)) -eq 0 ]; then t=FOUND; else t=LOST; fi
    curl -s -o /dev/null -X POST "$BASE/api/items" -H "Content-Type: application/json" \
      -d "{\"title\":\"Load-test item $i\",\"type\":\"$t\",\"category\":\"OTHER\",\"location\":\"Load generator\",\"reported_by\":\"load-test\"}"
  else
    curl -s -o /dev/null "$BASE/api/items?q=e"
  fi
' _

echo "Load test finished: $REQUESTS requests sent to $BASE"
