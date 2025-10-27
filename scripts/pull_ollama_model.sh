#!/usr/bin/env bash
set -euo pipefail

MODEL="$1"
TARGET="/usr/local/lib/ollama"
MIN_FREE_MB=1500

if [ -z "${MODEL:-}" ]; then
  echo "Usage: $0 <ollama-model>"
  exit 2
fi

FREE_MB=$(df -Pm "$TARGET" | awk 'NR==2 {print $4}')

echo "Spazio libero su $TARGET: ${FREE_MB}MB (richiesto >= ${MIN_FREE_MB}MB)"
if [ "$FREE_MB" -lt "$MIN_FREE_MB" ]; then
  echo "Errore: spazio insufficiente per scaricare ${MODEL}."
  exit 3
fi

TIMESTAMP=$(date -u +"%Y%m%dT%H%M%SZ")
LOGDIR="/var/log/ollama-pulls"
mkdir -p "$LOGDIR"
LOGFILE="$LOGDIR/pull-${MODEL//[:\/]/_}-$TIMESTAMP.log"

systemd-run --scope --unit="ollama-pull-$(date +%s)" bash -lc "ollama pull '$MODEL' &> '$LOGFILE'"

echo "Pull avviato in background, log -> $LOGFILE"
