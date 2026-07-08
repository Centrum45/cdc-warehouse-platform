#!/bin/bash
# DS bootstrap: login and submit workflow via curl
# DS must be running on localhost:12345

DS_URL="http://localhost:12345/dolphinscheduler"
ADMIN="admin"
PASS="dolphinscheduler123"
PROJECT="cdc_warehouse"

echo "=== Login ==="
QUERY=$(python3 -c 'import sys, urllib.parse; print(urllib.parse.urlencode({"userName": sys.argv[1], "userPassword": sys.argv[2]}))' "$ADMIN" "$PASS")
RESP=$(curl -s -X POST "${DS_URL}/login?${QUERY}")
TOKEN=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['sessionId'])")
echo "Token: ${TOKEN:0:20}..."

echo "=== Create project ==="
curl -s -X POST "${DS_URL}/v2/projects" \
  -H "Cookie: sessionId=$TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"projectName":"'"$PROJECT"'","description":"CDC warehouse demo"}'
echo ""

echo "=== Project list ==="
curl -s "${DS_URL}/projects/list?pageNo=1&pageSize=10" \
  -H "Cookie: sessionId=$TOKEN"
echo ""

echo ""
echo "DS API ready at: $DS_URL"
echo "Web UI: http://localhost:12345/dolphinscheduler/ui/"
echo ""
echo "To create workflow — open Web UI, go to Project 'cdc_warehouse',"
echo "import the workflow definition from:"
echo "  warehouse/scheduler/dolphinscheduler/warehouse_daily_process.json"
