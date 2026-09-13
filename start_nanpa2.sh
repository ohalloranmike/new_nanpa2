#!/usr/bin/env bash
# Start nanpa2 from the project directory (same role as start_nanpa2.bat on Windows).
# Usage: ./start_nanpa2.sh
#    or: bash ~/PycharmProjects/new_nanpa2/start_nanpa2.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

PYTHON="${ROOT}/.venv/bin/python"

if [[ ! -x "$PYTHON" ]]; then
  echo "Virtual environment not found at ${PYTHON}" >&2
  echo "Run setup first:" >&2
  echo "  cd ${ROOT}" >&2
  echo "  python3 -m venv .venv" >&2
  echo "  .venv/bin/python -m pip install -r requirements.txt" >&2
  exit 1
fi

# Same defaults as app.config.Config / start_nanpa2.bat (127.0.0.1:8002)
export NANPA_HOST="${NANPA_HOST:-127.0.0.1}"
export NANPA_PORT="${NANPA_PORT:-8002}"
NANPA_BIND="${NANPA_HOST}:${NANPA_PORT}"

echo "Stopping any process listening on port ${NANPA_PORT}..."
if command -v fuser >/dev/null 2>&1; then
  fuser -k "${NANPA_PORT}/tcp" 2>/dev/null || true
elif command -v lsof >/dev/null 2>&1; then
  mapfile -t pids < <(lsof -ti ":${NANPA_PORT}" 2>/dev/null || true)
  if ((${#pids[@]} > 0)); then
    kill -9 "${pids[@]}" 2>/dev/null || true
  fi
else
  echo "  (fuser/lsof not found; skip port cleanup)" >&2
fi
sleep 1

echo
echo "Starting NANPA2..."
echo "Open: http://${NANPA_BIND}"
echo "Press Ctrl+C to stop the server."
echo

set +e
"$PYTHON" run.py
status=$?
set -e

if [[ $status -ne 0 ]]; then
  echo
  echo "The server exited with an error (code ${status})." >&2
  echo "If the port is in use, try: NANPA_PORT=8003 ./start_nanpa2.sh" >&2
  exit "$status"
fi
