#!/bin/bash
set -euo pipefail
# Usage: MODEL_NAME="llama3.2:3b" REPO_DIR="/opt/piazzati" ./scripts/setup-server.sh

MODEL_NAME=${MODEL_NAME:-llama3.2:3b}
REPO_DIR=${REPO_DIR:-/opt/piazzati}
MARKER_DIR=${MARKER_DIR:-/var/lib/piazzati}
MARKER_FILE="${MARKER_DIR}/.ollama_setup_done"

echo "================================================================================"
echo "STEP 1: Installing system dependencies & Ollama setup"
echo "================================================================================"

mkdir -p "${MARKER_DIR}"

echo "[setup-server] Installing system packages (tesseract, poppler, curl)"
# Wait for apt/dpkg locks to be free to avoid races with other package processes.
wait_for_apt() {
  local max_retries=24
  local retry_interval=5
  local i=0
  while true; do
    # check for common lock files
    if [ ! -e /var/lib/dpkg/lock ] && [ ! -e /var/lib/dpkg/lock-frontend ] && [ ! -e /var/lib/apt/lists/lock ]; then
      break
    fi
    # also check for apt/dpkg processes
    if ! pgrep -x apt >/dev/null 2>&1 && ! pgrep -x apt-get >/dev/null 2>&1 && ! pgrep -x dpkg >/dev/null 2>&1; then
      break
    fi
    i=$((i+1))
    if [ ${i} -ge ${max_retries} ]; then
      echo "[setup-server] Timeout waiting for apt/dpkg locks after $((max_retries * retry_interval))s"
      break
    fi
    echo "[setup-server] apt/dpkg lock present — waiting ${retry_interval}s (${i}/${max_retries})"
    sleep ${retry_interval}
  done
}

wait_for_apt

apt-get update -qq
apt-get install -y tesseract-ocr tesseract-ocr-eng tesseract-ocr-ita poppler-utils curl

echo "\n[setup-server] Verifying Tesseract installation"
if command -v tesseract >/dev/null 2>&1; then
  tesseract --version || true
  tesseract --list-langs || true
else
  echo "[setup-server] ERROR: tesseract not found after install" >&2
fi

# Install Ollama if missing
if ! command -v ollama >/dev/null 2>&1; then
  echo "[setup-server] Installing Ollama..."
  curl -fsSL https://ollama.com/install.sh | sh
else
  echo "[setup-server] Ollama already installed"
fi

# Determine path to ollama binary
OLLAMA_BIN=$(command -v ollama || echo "/usr/local/bin/ollama")

# Create or restart systemd service to run ollama serve
if [ ! -f /etc/systemd/system/ollama.service ]; then
  echo "[setup-server] Creating systemd service for Ollama"
  cat >/etc/systemd/system/ollama.service <<'EOF'
[Unit]
Description=Ollama server
After=network.target

[Service]
ExecStart=%OLLAMA_BIN% serve
Restart=always
User=root
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF
  # Substitute actual path
  sed -i "s|%OLLAMA_BIN%|${OLLAMA_BIN}|g" /etc/systemd/system/ollama.service
  systemctl daemon-reload
  systemctl enable --now ollama.service || true
else
  echo "[setup-server] Ollama systemd service already present"
  systemctl restart ollama.service || true
fi

echo "[setup-server] Waiting for Ollama API to become responsive"
# Wait up to 60 seconds for Ollama to answer
MAX_RETRIES=12
RETRY_INTERVAL=5
COUNT=0
until curl -fsS http://localhost:11434/api/tags >/dev/null 2>&1; do
  COUNT=$((COUNT+1))
  if [ ${COUNT} -ge ${MAX_RETRIES} ]; then
    echo "[setup-server] Warning: Ollama API not responding after $((MAX_RETRIES * RETRY_INTERVAL))s"
    break
  fi
  echo "[setup-server] Ollama not ready yet; retrying in ${RETRY_INTERVAL}s... (${COUNT}/${MAX_RETRIES})"
  sleep ${RETRY_INTERVAL}
done

# Marker logic: if we've already pulled the same model, skip re-pulling
SKIP_PULL=0
if [ -f "${MARKER_FILE}" ]; then
  MARKER_MODEL=$(cat "${MARKER_FILE}" 2>/dev/null || echo "")
  if [ "${MARKER_MODEL}" = "${MODEL_NAME}" ]; then
    echo "[setup-server] Marker found for model ${MODEL_NAME} — skipping model pull"
    SKIP_PULL=1
  fi
fi

if [ ${SKIP_PULL} -eq 0 ]; then
  # Pull model if not present
  if ! ${OLLAMA_BIN} list | grep -q "${MODEL_NAME}"; then
    echo "[setup-server] Pulling model ${MODEL_NAME} (this may take several minutes)"
    ${OLLAMA_BIN} pull "${MODEL_NAME}"
  else
    echo "[setup-server] Model ${MODEL_NAME} already present"
  fi
  # Record the successfully-pulled model in the marker file
  echo "${MODEL_NAME}" > "${MARKER_FILE}"
  chmod 644 "${MARKER_FILE}" || true
else
  echo "[setup-server] Skipping model pull per marker"
fi

# Install Python requirements if file exists in repo (use a venv to avoid system-wide installs)
if [ -f "${REPO_DIR}/backend/requirements.txt" ]; then
  echo "[setup-server] Installing Python requirements into a virtualenv"

  # Ensure python3 and venv support exist
  if ! python3 -c "import venv" >/dev/null 2>&1; then
    echo "[setup-server] python3-venv missing; installing via apt"
    apt-get update -qq || true
    apt-get install -y python3-venv python3-pip || true
  fi

  VENV_DIR="${REPO_DIR}/.venv"
  if [ ! -d "${VENV_DIR}" ]; then
    echo "[setup-server] Creating virtualenv at ${VENV_DIR}"
    python3 -m venv "${VENV_DIR}"
  else
    echo "[setup-server] Reusing existing virtualenv at ${VENV_DIR}"
  fi

  # If the venv is present but seems broken (missing python binary), recreate it
  if [ ! -x "${VENV_DIR}/bin/python" ]; then
    echo "[setup-server] Existing virtualenv is broken or incomplete; recreating ${VENV_DIR}"
    rm -rf "${VENV_DIR}" || true
    python3 -m venv "${VENV_DIR}"
  fi

  PIP_BIN="${VENV_DIR}/bin/pip"
  PY_BIN="${VENV_DIR}/bin/python"

  echo "[setup-server] Upgrading pip in venv"
  "${PY_BIN}" -m pip install --upgrade pip setuptools wheel || true

  echo "[setup-server] Installing requirements from ${REPO_DIR}/backend/requirements.txt"
  "${PIP_BIN}" install --no-cache-dir -r "${REPO_DIR}/backend/requirements.txt" || {
    echo "[setup-server] Warning: pip install exited with non-zero status" >&2
  }
else
  echo "[setup-server] No requirements.txt found at ${REPO_DIR}/backend/requirements.txt"
fi

echo "================================================================================"
echo "SYSTEM SETUP COMPLETE"
echo "================================================================================"
