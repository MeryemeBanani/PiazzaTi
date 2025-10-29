#!/usr/bin/env bash
set -euo pipefail

# remote_rollback.sh
# Usage:
#   sudo bash scripts/remote_rollback.sh <tag> [--yes]
# Examples:
#   sudo bash scripts/remote_rollback.sh 0123456 --yes
#   sudo bash scripts/remote_rollback.sh v1.2.3
#
# This script performs a safe deploy of a specific image tag by creating a
# small compose override that pins the backend image, pulling the image with
# retries and then running `docker compose up -d` without building.

REGISTRY="rg.nl-ams.scw.cloud/piazzati/backend"
IMAGE_NAME="piazzati-backend"
DEPLOY_DIR="/opt/piazzati"
HISTORY_FILE="/var/lib/piazzati/deploy_history.log"
LAST_TAG_FILE="/var/lib/piazzati/last_deployed_tag"

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <tag> [--yes]"
  echo "Example: $0 0123456 --yes"
  echo
  if [ -f "$LAST_TAG_FILE" ]; then
    echo "Current last deployed tag: $(cat $LAST_TAG_FILE)"
  fi
  exit 2
fi

TAG="$1"
FORCE=false
if [ "${2:-}" = "--yes" ]; then
  FORCE=true
fi

IMAGE_FULL="${REGISTRY}/${IMAGE_NAME}:${TAG}"

echo "Rollback target: ${IMAGE_FULL}"

if [ "$FORCE" = false ]; then
  read -r -p "Proceed to deploy ${IMAGE_FULL}? [y/N] " ans
  case "$ans" in
    [yY]|[yY][eE][sS]) ;;
    *) echo "Aborted."; exit 1;;
  esac
fi

if [ ! -d "$DEPLOY_DIR" ]; then
  echo "Error: repo directory $DEPLOY_DIR not found. Please run this from the server where /opt/piazzati exists." >&2
  exit 3
fi

cd "$DEPLOY_DIR"

# Ensure history dir
mkdir -p "$(dirname "$HISTORY_FILE")"

PREV_TAG="none"
if [ -f "$LAST_TAG_FILE" ]; then
  PREV_TAG=$(cat "$LAST_TAG_FILE" || echo "none")
fi

echo "[rollback] From: $PREV_TAG -> To: $TAG  (started at $(date -Is))" | tee -a "$HISTORY_FILE"

# Create compose override
cat > docker-compose.rollback.yml <<YML
services:
  ${IMAGE_NAME}:
    image: ${IMAGE_FULL}
YML

# Pull with retry/backoff
attempts=0
until docker compose -f docker-compose.yml -f docker-compose.rollback.yml pull ${IMAGE_NAME}; do
  attempts=$((attempts+1))
  if [ "$attempts" -ge 3 ]; then
    echo "[rollback] docker pull failed after $attempts attempts" | tee -a "$HISTORY_FILE"
    docker compose logs --no-color ${IMAGE_NAME} --tail 500 || true
    exit 4
  fi
  sleep $((attempts * 5))
done

echo "[rollback] Image pulled: ${IMAGE_FULL}"

# Deploy
docker compose -f docker-compose.yml -f docker-compose.rollback.yml up -d

echo "[rollback] Waiting for health check..."
max_wait=120
interval=5
waited=0
until curl -sS --fail --max-time 10 http://localhost:8000/health >/dev/null; do
  if [ "$waited" -ge "$max_wait" ]; then
    echo "[rollback] Health check failed after $max_wait s" | tee -a "$HISTORY_FILE"
    docker compose logs --no-color ${IMAGE_NAME} --tail 500 || true
    exit 5
  fi
  sleep $interval
  waited=$((waited + interval))
done

echo "[rollback] Health check passed"

# Record
echo "${TAG}" > "$LAST_TAG_FILE" || true
echo "[rollback] Completed at $(date -Is)" | tee -a "$HISTORY_FILE"

exit 0
