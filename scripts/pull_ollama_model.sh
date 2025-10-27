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
LOGFILE_BASE="$LOGDIR/pull-${MODEL//[:\/]/_}-$TIMESTAMP"

# Determine whether /tmp is tmpfs and too small; if so, use /var/tmp as TMPDIR
MIN_TMP_MB=2000
TMPDIR_FALLBACK=""
if df -T /tmp >/dev/null 2>&1; then
  TMP_FS_TYPE=$(df -T /tmp | awk 'NR==2 {print $2}')
  TMP_FREE_MB=$(df -Pm /tmp | awk 'NR==2 {print $4}')
  if [ "$TMP_FS_TYPE" = "tmpfs" ] && [ "$TMP_FREE_MB" -lt "$MIN_TMP_MB" ]; then
    TMPDIR_FALLBACK="/var/tmp"
  fi
fi

# Try pulling the model with retries and exponential backoff. Run in foreground so we can detect failures.
ATTEMPTS=3
BACKOFF=5
SUCCESS=1
for ATTEMPT in $(seq 1 $ATTEMPTS); do
  LOGFILE="${LOGFILE_BASE}-attempt${ATTEMPT}.log"
  echo "Starting pull attempt ${ATTEMPT}/${ATTEMPTS}, log -> $LOGFILE"

  if [ -n "${TMPDIR_FALLBACK}" ]; then
    echo "Using TMPDIR=${TMPDIR_FALLBACK} for this pull (tmpfs detected on /tmp with low free space)" >> "$LOGFILE"
    env TMPDIR="${TMPDIR_FALLBACK}" ollama pull "$MODEL" &> "$LOGFILE"
  else
    ollama pull "$MODEL" &> "$LOGFILE"
  fi

  RC=$?
  if [ $RC -eq 0 ]; then
    echo "Pull succeeded on attempt ${ATTEMPT} (log: $LOGFILE)"
    SUCCESS=0
    break
  else
    echo "Pull failed on attempt ${ATTEMPT} (rc=$RC). See $LOGFILE for details." >&2
    if [ $ATTEMPT -lt $ATTEMPTS ]; then
      SLEEP=$((BACKOFF * ATTEMPT))
      echo "Retrying in ${SLEEP}s..."
      sleep $SLEEP
    fi
  fi
done

if [ $SUCCESS -ne 0 ]; then
  echo "ERROR: ollama pull failed after ${ATTEMPTS} attempts. Last logs at ${LOGFILE_BASE}-attempt*.log" >&2
  exit 4
else
  echo "Pull completed successfully. Logs: ${LOGFILE_BASE}-attempt*.log"
fi
