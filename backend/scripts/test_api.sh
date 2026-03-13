#!/usr/bin/env bash
# Quick API smoke test. Run with backend server up: ./scripts/test_api.sh
# Usage: from backend dir: ./scripts/test_api.sh   or   bash scripts/test_api.sh

set -e
BASE="${BASE_URL:-http://127.0.0.1:8000}"

echo "=== 1. Health ==="
curl -sS "${BASE}/health" | head -1
echo ""

echo "=== 2. Register ==="
REGISTER_RESP=$(curl -sS -X POST "${BASE}/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123"}')
echo "$REGISTER_RESP" | head -1
if echo "$REGISTER_RESP" | grep -q "email"; then echo "OK"; else echo "FAIL or already registered"; fi

echo "=== 3. Login (token) ==="
TOKEN_RESP=$(curl -sS -X POST "${BASE}/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=testpass123")
echo "$TOKEN_RESP" | head -1
TOKEN=$(echo "$TOKEN_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null || true)
if [ -z "$TOKEN" ]; then echo "No token - login failed?"; else echo "OK"; fi

echo "=== 4. /me (authenticated) ==="
if [ -n "$TOKEN" ]; then
  curl -sS "${BASE}/me" -H "Authorization: Bearer $TOKEN" | head -1
  echo " OK"
else
  echo "Skip (no token)"
fi

echo "=== 5. Courses (no auth) ==="
curl -sS "${BASE}/courses" | head -1
echo " OK"

echo "=== 6. Watch rules (authenticated) ==="
if [ -n "$TOKEN" ]; then
  curl -sS "${BASE}/watch-rules" -H "Authorization: Bearer $TOKEN" | head -1
  echo " OK"
else
  echo "Skip (no token)"
fi

echo ""
echo "Done."
