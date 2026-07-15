#!/bin/bash
# Safety checks for the sealed red-team lab. Run from adversary/tools/ on MIDAS 2.
# Run every session and after any lab change (pcap, container, config, code).
set -e

cd "$(dirname "$0")"
REPO_ROOT="$(cd ../.. && pwd)"
FAIL=0

pass() { echo "  PASS: $1"; }
fail() { echo "  FAIL: $1"; FAIL=1; }

echo "=== Lab safety verification ==="
echo ""

# 1. lab-net exists and is internal
if docker network inspect lab-net >/dev/null 2>&1; then
  INTERNAL=$(docker network inspect lab-net --format '{{.Internal}}')
  if [ "$INTERNAL" = "true" ]; then
    pass "lab-net exists and is internal (no internet route)"
  else
    fail "lab-net exists but is NOT internal — recreate with: docker network create --internal lab-net"
  fi
else
  fail "lab-net does not exist — create with: docker network create --internal lab-net"
fi

# 2. practice-target on lab-net only
if docker ps --filter name=^practice-target$ --format '{{.Names}}' | grep -qx practice-target; then
  NETS=$(docker inspect practice-target --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}} {{end}}')
  if [ "$NETS" = "lab-net " ] || [ "$NETS" = "lab-net" ]; then
    pass "practice-target is on lab-net only"
  else
    fail "practice-target networks: '$NETS' (expected lab-net only)"
  fi
else
  fail "practice-target is not running"
fi

# 2b. practice-target-pqc on lab-net only (optional stretch — warn if missing)
if docker ps --filter name=^practice-target-pqc$ --format '{{.Names}}' | grep -qx practice-target-pqc; then
  NETS=$(docker inspect practice-target-pqc --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}} {{end}}')
  if [ "$NETS" = "lab-net " ] || [ "$NETS" = "lab-net" ]; then
    pass "practice-target-pqc is on lab-net only"
  else
    fail "practice-target-pqc networks: '$NETS' (expected lab-net only)"
  fi
else
  pass "practice-target-pqc not running (optional PQC target)"
fi

# 3. attacker on lab-net only
if docker ps --filter name=^attacker$ --format '{{.Names}}' | grep -qx attacker; then
  NETS=$(docker inspect attacker --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}} {{end}}')
  if [ "$NETS" = "lab-net " ] || [ "$NETS" = "lab-net" ]; then
    pass "attacker is on lab-net only"
  else
    fail "attacker networks: '$NETS' (expected lab-net only)"
  fi
else
  fail "attacker is not running"
fi

# 4. brain not on lab-net
if docker ps -a --filter name=brain --format '{{.Names}}' | grep -q '^brain$'; then
  NETS=$(docker inspect brain --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}} {{end}}')
  if echo "$NETS" | grep -q 'lab-net'; then
    fail "brain must NOT be on lab-net (found: $NETS)"
  else
    pass "brain is not on lab-net"
  fi
else
  pass "brain container not present (skip)"
fi

# 5. records not on lab-net
if docker ps -a --filter name=records --format '{{.Names}}' | grep -q '^records$'; then
  NETS=$(docker inspect records --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}} {{end}}')
  if echo "$NETS" | grep -q 'lab-net'; then
    fail "records must NOT be on lab-net (found: $NETS)"
  else
    pass "records is not on lab-net"
  fi
else
  pass "records container not present (skip)"
fi

# 6. attacker cannot reach internet
if docker ps --filter name=^attacker$ --format '{{.Names}}' | grep -qx attacker; then
  if docker exec attacker ping -c 2 -W 3 8.8.8.8 >/dev/null 2>&1; then
    fail "attacker can reach the internet — lab is NOT sealed"
  else
    pass "attacker cannot reach the internet"
  fi
fi

# 7. attacker can reach practice-target
if docker ps --filter name=^attacker$ --format '{{.Names}}' | grep -qx attacker; then
  if docker exec attacker ping -c 2 -W 3 practice-target >/dev/null 2>&1; then
    pass "attacker can reach practice-target"
  else
    fail "attacker cannot reach practice-target"
  fi
  if docker ps --filter name=^practice-target-pqc$ --format '{{.Names}}' | grep -qx practice-target-pqc; then
    if docker exec attacker ping -c 2 -W 3 practice-target-pqc >/dev/null 2>&1; then
      pass "attacker can reach practice-target-pqc"
    else
      fail "attacker cannot reach practice-target-pqc"
    fi
  fi
fi

# 8. no sensitive files staged for git
if command -v git >/dev/null 2>&1 && [ -d "$REPO_ROOT/.git" ]; then
  if (cd "$REPO_ROOT" && git status --porcelain 2>/dev/null) | grep -qE '(captures/|\.pcap|target-certs/|\.env|\.pem)'; then
    fail "sensitive files may be staged or untracked — do not commit pcaps, certs, or .env"
  else
    pass "no sensitive capture/cert files in git status"
  fi
fi

echo ""
if [ "$FAIL" -eq 0 ]; then
  echo "=== All safety checks passed. Lab is safe to use. ==="
  exit 0
else
  echo "=== SAFETY CHECK FAILED — fix issues before running attacks or pcap replay. ==="
  exit 1
fi
