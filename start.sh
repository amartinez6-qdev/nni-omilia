#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/nni-backend"
FRONTEND_DIR="$ROOT_DIR/nni-frontend"
export UV_CACHE_DIR="${UV_CACHE_DIR:-${TMPDIR:-/tmp}/nni-omilia-uv-cache}"

find_free_port() {
  python3 - "$1" <<'PY'
import socket
import sys

start = int(sys.argv[1])
for port in range(start, start + 20):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind(("127.0.0.1", port))
        except OSError:
            continue
        print(port)
        break
else:
    raise SystemExit(f"No free port found in range {start}-{start + 19}")
PY
}

BACKEND_PORT="${BACKEND_PORT:-$(find_free_port 8000)}"
FRONTEND_PORT="${FRONTEND_PORT:-$(find_free_port 5173)}"

if ! command -v uv >/dev/null 2>&1; then
  echo "Error: uv is required. Install it from https://docs.astral.sh/uv/" >&2
  exit 1
fi
if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
  echo "Error: Node.js and npm are required." >&2
  exit 1
fi

echo "Preparing backend environment..."
uv sync --project "$BACKEND_DIR"

if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
  echo "Installing frontend dependencies..."
  npm ci --prefix "$FRONTEND_DIR"
fi

BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  trap - INT TERM EXIT
  [ -z "$BACKEND_PID" ] || kill "$BACKEND_PID" 2>/dev/null || true
  [ -z "$FRONTEND_PID" ] || kill "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup INT TERM EXIT

echo "Starting backend at http://127.0.0.1:$BACKEND_PORT"
uv run --project "$BACKEND_DIR" uvicorn nni_backend.api:app --host 127.0.0.1 --port "$BACKEND_PORT" &
BACKEND_PID=$!

sleep 1
if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
  echo "Error: backend failed to start on port $BACKEND_PORT." >&2
  exit 1
fi

echo "Starting frontend at http://localhost:$FRONTEND_PORT"
VITE_BACKEND_URL="http://127.0.0.1:$BACKEND_PORT" npm --prefix "$FRONTEND_DIR" run dev -- --host 127.0.0.1 --port "$FRONTEND_PORT" &
FRONTEND_PID=$!

sleep 1
if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
  echo "Error: frontend failed to start on port $FRONTEND_PORT." >&2
  exit 1
fi

echo "Application ready: http://localhost:$FRONTEND_PORT"
wait "$BACKEND_PID" "$FRONTEND_PID"
