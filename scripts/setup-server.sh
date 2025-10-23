#!/bin/bash
set -euo pipefail
# Usage: MODEL_NAME="llama3.1:8b" ./scripts/setup-server.sh

MODEL_NAME=${MODEL_NAME:-llama3.1:8b}
REPO_DIR=${REPO_DIR:-/opt/piazzati}

echo "[setup-server] Starting server setup (model=${MODEL_NAME})"

echo "[setup-server] Installing system packages (tesseract, poppler)"
apt-get update -qq
apt-get install -y tesseract-ocr tesseract-ocr-eng tesseract-ocr-ita poppler-utils curl

# Install ollama if missing
if ! command -v ollama >/dev/null 2>&1; then
  echo "[setup-server] Installing Ollama..."
  curl -fsSL https://ollama.com/install.sh | sh
else
  echo "[setup-server] Ollama already installed"
fi

# Determine path to ollama binary
OLLAMA_BIN=$(command -v ollama || echo "/usr/local/bin/ollama")

# Create systemd service to run ollama serve
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

echo "[setup-server] Waiting a few seconds for Ollama to initialize"
sleep 5
if ! curl -fsS http://localhost:11434/api/tags >/dev/null 2>&1; then
  echo "[setup-server] Warning: Ollama API not responding yet"
fi

# Pull model if not present
if ! ${OLLAMA_BIN} list | grep -q "${MODEL_NAME}"; then
  echo "[setup-server] Pulling model ${MODEL_NAME} (this may take several minutes)"
  ${OLLAMA_BIN} pull "${MODEL_NAME}"
else
  echo "[setup-server] Model ${MODEL_NAME} already present"
fi

# Install Python requirements if file exists in repo
if [ -f "${REPO_DIR}/backend/requirements.txt" ]; then
  echo "[setup-server] Installing Python requirements"
  pip3 install -r "${REPO_DIR}/backend/requirements.txt"
else
  echo "[setup-server] No requirements.txt found at ${REPO_DIR}/backend/requirements.txt"
fi

echo "[setup-server] Setup complete"
