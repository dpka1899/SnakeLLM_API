#!/bin/bash
set -euo pipefail

BASE="http://localhost:8000"
API_KEY="demo-key-change-me"   # <- must match your .env API_KEY

echo "== 1) HEALTH =="
curl -s "$BASE/health" | python3 -m json.tool
echo

echo "== 2) GENERATE JOB =="
RESP=$(curl -s -X POST "$BASE/generate" \
  -H "Content-Type: application/json" \
  -H "x-api-key: $API_KEY" \
  -d '{"prompt":"Run RNA-seq differential expression using DESeq2"}')

echo "$RESP" | python3 -m json.tool

JOB_ID=$(python3 - <<PY
import json
print(json.loads('''$RESP''')["job_id"])
PY
)
echo "JOB_ID=$JOB_ID"
echo

echo "== 3) POLL STATUS (up to 60s) =="
FINAL=""
for i in {1..60}; do
  S=$(curl -s -H "x-api-key: $API_KEY" "$BASE/status/$JOB_ID")
  echo "$S"
  FINAL=$(python3 - <<PY
import json
s=json.loads('''$S''')
print(s.get("status",""))
PY
)
  if [[ "$FINAL" == "DONE" || "$FINAL" == "FAILED" ]]; then
    break
  fi
  sleep 1
done

echo
echo "FINAL_STATUS=$FINAL"
echo

echo "== 4) RESULT =="
curl -s -H "x-api-key: $API_KEY" "$BASE/result/$JOB_ID" | python3 -m json.tool
echo

echo "== 5) DOWNLOAD (expected to fail if FAILED) =="
set +e
curl -s -i -H "x-api-key: $API_KEY" -OJ "$BASE/download/$JOB_ID?wait=2"
echo
echo "Download attempted (expected 500 if job failed)."