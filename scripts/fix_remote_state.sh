#!/usr/bin/env bash
set -euo pipefail

# Helper to run on the server to ensure /var/lib/piazzati/last_deployed_tag exists
# and to create docker-compose.deploy.yml pinned to the running backend image.
# Usage (on server): sudo bash /opt/piazzati/scripts/fix_remote_state.sh

REPO_DIR="/opt/piazzati"
DEPLOY_FILE="$REPO_DIR/docker-compose.deploy.yml"
TAG_FILE="/var/lib/piazzati/last_deployed_tag"

echo "Using repo dir: $REPO_DIR"
cd "$REPO_DIR"

# find running backend container
container_id=$(docker ps --filter "name=piazzati-backend" -q | head -n1 || true)
if [ -z "$container_id" ]; then
  echo "No running piazzati-backend container found. If you expect one, please start the service or run docker compose up first." >&2
else
  image_name=$(docker inspect --format='{{.Config.Image}}' "$container_id" 2>/dev/null || true)
  echo "Detected running container $container_id using image: $image_name"
  mkdir -p "$(dirname "$TAG_FILE")"
  if [ -n "$image_name" ]; then
    if printf '%s' "$image_name" | grep -q ':'; then
      echo "${image_name##*:}" > "$TAG_FILE" || true
      echo "Wrote tag to $TAG_FILE: ${image_name##*:}"
    else
      echo "$image_name" > "$TAG_FILE" || true
      echo "Wrote full image name to $TAG_FILE: $image_name"
    fi
  else
    echo "unknown" > "$TAG_FILE" || true
    echo "Wrote placeholder 'unknown' to $TAG_FILE"
  fi

  # create docker-compose.deploy.yml pinned to the running image
  cat > "$DEPLOY_FILE" <<YML
services:
  piazzati-backend:
    image: $image_name
YML
  echo "Created $DEPLOY_FILE pinned to $image_name"
fi

# show a summary
echo "--- summary ---"
ls -la "$DEPLOY_FILE" || true
cat "$TAG_FILE" || true

echo "Done."
