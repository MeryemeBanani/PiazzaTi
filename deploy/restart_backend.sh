#!/usr/bin/env bash
set -euo pipefail

# restart_backend.sh
# Safely stop any uvicorn processes that have DB_HOST=postgres (typical docker/dev env),
# ensure psycopg2-binary is installed in the venv, and start a single uvicorn using
# the project's .env and venv.
#
# Usage (on the server):
#   sudo bash /opt/piazzati/backend/deploy/restart_backend.sh

PROJECT_DIR="/opt/piazzati/backend"
VENV_CANDIDATES=("/root/.venv" "${PROJECT_DIR}/.venv" )
VENV=""
ENVFILE="$PROJECT_DIR/.env"
LOGDIR="/var/log/piazzati"
LOGFILE="$LOGDIR/uvicorn.log"

echo "Project dir: $PROJECT_DIR"

if [ ! -f "$ENVFILE" ]; then
  echo "ERROR: env file not found at $ENVFILE" >&2
  exit 1
fi

# find a usable venv
for c in "${VENV_CANDIDATES[@]}"; do
  if [ -x "$c/bin/python" ]; then
    VENV="$c"
    break
  fi
done

if [ -z "$VENV" ]; then
  echo "ERROR: no virtualenv found in candidates: ${VENV_CANDIDATES[*]}" >&2
  exit 1
fi

echo "Using venv: $VENV"

# Stop uvicorn processes whose environment has DB_HOST=postgres
echo "Scanning for uvicorn processes with DB_HOST=postgres..."
for pid in $(pgrep -f uvicorn || true); do
  if [ -r "/proc/$pid/environ" ]; then
    if tr '\0' '\n' < /proc/$pid/environ | grep -q '^DB_HOST=postgres$'; then
      echo "Stopping PID $pid (DB_HOST=postgres)"
      kill "$pid" 2>/dev/null || true
      sleep 2
      if kill -0 "$pid" 2>/dev/null; then
        echo "PID $pid still alive; sending SIGKILL"
        kill -9 "$pid" 2>/dev/null || true
      fi
    fi
  fi
done

echo "Ensuring no uvicorn still listens on :8000"
if ss -ltnp '( sport = :8000 )' 2>/dev/null | grep -q ':8000'; then
  echo "Warning: something is still listening on :8000" >&2
  ss -ltnp '( sport = :8000 )' || true
fi

# Activate venv and install psycopg2-binary if missing
echo "Activating venv and checking psycopg2..."
source "$VENV/bin/activate"
if ! python -c "import importlib.util;print(bool(importlib.util.find_spec('psycopg2')) )" | grep -q True; then
  echo "psycopg2 not found in venv — installing psycopg2-binary..."
  pip install --upgrade pip
  pip install "psycopg2-binary>=2.7.3.1"
else
  echo "psycopg2 already present in venv"
fi

# Prepare log dir
mkdir -p "$LOGDIR"
chown root:root "$LOGDIR" || true

echo "Starting uvicorn from $PROJECT_DIR (logs -> $LOGFILE)"
cd "$PROJECT_DIR"

# load env and start in background via nohup
set -o allexport
source "$ENVFILE"
set +o allexport

# start uvicorn in background; adjust user/group in production (systemd recommended)
nohup "$VENV/bin/uvicorn" app.main:app --host 127.0.0.1 --port 8000 > "$LOGFILE" 2>&1 &
UV_PID=$!
echo "uvicorn started with PID $UV_PID (logs: $LOGFILE)"

exit 0
