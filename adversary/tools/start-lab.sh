#!/bin/bash
# Starts the sealed red-team lab. Run from adversary/tools/.
set -e
cd "$(dirname "$0")"

docker network inspect lab-net >/dev/null 2>&1 || docker network create --internal lab-net

# Classical TLS practice hospital (port 443)
if ! docker ps -a --filter name=^practice-target$ --format '{{.Names}}' | grep -qx practice-target; then
  docker run -d --name practice-target --network lab-net \
    -v "$PWD/target-certs":/certs:ro \
    -v "$PWD/nginx.conf":/etc/nginx/nginx.conf:ro \
    nginx
elif ! docker ps --filter name=^practice-target$ --format '{{.Names}}' | grep -qx practice-target; then
  docker start practice-target
fi

# PQC / hybrid TLS target — Open Quantum Safe nginx demo (port 4433)
if ! docker ps -a --filter name=^practice-target-pqc$ --format '{{.Names}}' | grep -qx practice-target-pqc; then
  docker run -d --name practice-target-pqc --network lab-net \
    openquantumsafe/nginx
elif ! docker ps --filter name=^practice-target-pqc$ --format '{{.Names}}' | grep -qx practice-target-pqc; then
  docker start practice-target-pqc
fi

if ! docker ps -a --filter name=^attacker$ --format '{{.Names}}' | grep -qx attacker; then
  docker run -d --name attacker --network lab-net \
    --cap-add=NET_RAW --cap-add=NET_ADMIN \
    -v "$PWD":/opt/redteam \
    redteam-attacker
elif ! docker ps --filter name=^attacker$ --format '{{.Names}}' | grep -qx attacker; then
  docker start attacker
fi

echo "Running safety checks..."
bash "$(dirname "$0")/verify-lab-safety.sh"
