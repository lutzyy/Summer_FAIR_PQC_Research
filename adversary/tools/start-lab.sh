#!/bin/bash
# Starts the sealed red-team lab. Run from adversary/tools/.
set -e
cd "$(dirname "$0")"

docker network inspect lab-net >/dev/null 2>&1 || docker network create --internal lab-net

if ! docker ps --filter name=practice-target --format '{{.Names}}' | grep -q practice-target; then
  docker run -d --name practice-target --network lab-net \
    -v "$PWD/target-certs":/certs:ro \
    -v "$PWD/nginx.conf":/etc/nginx/nginx.conf:ro \
    nginx
fi

if ! docker ps --filter name=attacker --format '{{.Names}}' | grep -q attacker; then
  docker run -d --name attacker --network lab-net \
    --cap-add=NET_RAW --cap-add=NET_ADMIN \
    -v "$PWD":/opt/redteam \
    redteam-attacker
fi

echo "Running safety checks..."
bash "$(dirname "$0")/verify-lab-safety.sh"