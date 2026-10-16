#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/nni-backend"
FRONTEND_DIR="$ROOT_DIR/nni-frontend"
export UV_CACHE_DIR="${UV_CACHE_DIR:-${TMPDIR:-/tmp}/nni-omilia-uv-cache}"
RESTART_DELAY_SECONDS="${RESTART_DELAY_SECONDS:-1}"

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

run_service() {
  local service_name="$1"
  shift

  local service_pid=""
  local stopping=0
  local exit_code=0

  stop_service() {
    stopping=1
    if [ -n "$service_pid" ] && kill -0 "$service_pid" 2>/dev/null; then
      kill "$service_pid" 2>/dev/null || true
      wait "$service_pid" 2>/dev/null || true
    fi
    exit 143
  }
  trap stop_service INT TERM

  while [ "$stopping" -eq 0 ]; do
    echo "Starting $service_name"
    "$@" &
    service_pid=$!

    if wait "$service_pid"; then
      exit_code=0
    else
      exit_code=$?
    fi
    service_pid=""

    if [ "$stopping" -eq 1 ]; then
      break
    fi

    echo "$service_name stopped with exit code $exit_code; restarting in ${RESTART_DELAY_SECONDS}s..." >&2
    sleep "$RESTART_DELAY_SECONDS"
  done
}

cleanup() {
  trap - INT TERM EXIT
  for service_pid in "$BACKEND_PID" "$FRONTEND_PID"; do
    [ -z "$service_pid" ] || kill "$service_pid" 2>/dev/null || true
  done
}
trap cleanup INT TERM EXIT

run_service "backend at http://127.0.0.1:$BACKEND_PORT" \
  uv run --project "$BACKEND_DIR" uvicorn src.api:app --host 127.0.0.1 --port "$BACKEND_PORT" &
BACKEND_PID=$!

sleep 1
if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
  echo "Error: backend failed to start on port $BACKEND_PORT." >&2
  exit 1
fi

run_service "frontend at http://localhost:$FRONTEND_PORT" \
  env VITE_BACKEND_URL="http://127.0.0.1:$BACKEND_PORT" \
  npm --prefix "$FRONTEND_DIR" run dev -- --host 127.0.0.1 --port "$FRONTEND_PORT" &
FRONTEND_PID=$!

sleep 1
if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
  echo "Error: frontend failed to start on port $FRONTEND_PORT." >&2
  exit 1
fi

echo "Application ready: http://localhost:$FRONTEND_PORT"
wait "$BACKEND_PID" "$FRONTEND_PID"
