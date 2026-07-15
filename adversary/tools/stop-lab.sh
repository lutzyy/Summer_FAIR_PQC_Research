#!/bin/bash
# Stops the sealed red-team lab. Run from adversary/tools/.
set -e
cd "$(dirname "$0")"

docker stop practice-target attacker 2>/dev/null || true

echo "Lab stopped."