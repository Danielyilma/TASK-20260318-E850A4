#!/usr/bin/env bash

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

backend_status=0
frontend_status=0

echo "=== Running backend tests ==="
if [ -d "$SCRIPT_DIR/backend" ]; then
  (
    cd "$SCRIPT_DIR/backend" || exit 1
    pytest
  ) || backend_status=$?
else
  echo "Backend directory not found: $SCRIPT_DIR/backend"
  backend_status=1
fi

echo
echo "=== Running frontend tests ==="
if [ -d "$SCRIPT_DIR/frontend" ]; then
  (
    cd "$SCRIPT_DIR/frontend" || exit 1
    npm run test:unit
  ) || frontend_status=$?
else
  echo "Frontend directory not found: $SCRIPT_DIR/frontend"
  frontend_status=1
fi

echo
if [ "$backend_status" -eq 0 ] && [ "$frontend_status" -eq 0 ]; then
  echo "All tests passed."
  exit 0
fi

echo "Some tests failed."
echo "Backend status: $backend_status"
echo "Frontend status: $frontend_status"
exit 1
