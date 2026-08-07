#!/usr/bin/env bash
# verify_containment.sh — I1 pre-flight gate.
#
# Proves that the `range` network has NO egress, before the agent is allowed to run.
# This is the control AISI had written down and did not apply. It runs on EVERY start.
#
# It does not trust the compose file's `internal: true` — it MEASURES. A probe container
# is attached to the same network and told to reach a public address. If it can, the
# network is not contained and this script exits non-zero, which the launcher treats as
# an abort. Egress proven absent, never assumed.
#
# Exit codes:  0 = contained (no egress)   1 = EGRESS DETECTED, abort   2 = could not test
set -u

NET="agent-autonomy-lab_range"
PROBE_IMAGE="alpine:latest"
# Two independent public targets, by IP so the test does not depend on DNS (which the
# internal net also lacks). If EITHER is reachable, containment has failed.
TARGETS=("1.1.1.1" "8.8.8.8")

say() { printf '%s\n' "$*"; }

# --- daemon up? ---
if ! docker info >/dev/null 2>&1; then
  say "CONTAINMENT: CANNOT TEST — docker daemon is not running (start Docker Desktop)."
  exit 2
fi

# --- does the range network exist? ---
if ! docker network inspect "$NET" >/dev/null 2>&1; then
  say "CONTAINMENT: CANNOT TEST — network '$NET' does not exist yet."
  say "  Bring the range up first:  docker compose -f docker/compose.yml up -d target"
  exit 2
fi

# --- the network must actually be marked internal ---
INTERNAL=$(docker network inspect "$NET" --format '{{.Internal}}' 2>/dev/null)
if [ "$INTERNAL" != "true" ]; then
  say "CONTAINMENT: FAILED — network '$NET' is Internal=$INTERNAL, expected true."
  say "  The compose file's containment primitive is not in effect. ABORT."
  exit 1
fi
say "  network '$NET' is Internal=true (no gateway by construction)."

# --- MEASURE: can a probe on this network reach the internet? ---
# -w 4: 4s timeout per attempt. A contained network yields no route → connection fails fast.
egress_hit=0
for ip in "${TARGETS[@]}"; do
  if docker run --rm --network "$NET" "$PROBE_IMAGE" \
        sh -c "wget -q -T 4 -O /dev/null http://$ip/ 2>/dev/null || nc -w 4 -z $ip 53 2>/dev/null"; then
    say "CONTAINMENT: FAILED — a probe on '$NET' REACHED $ip. There is egress. ABORT."
    egress_hit=1
  else
    say "  probe could not reach $ip (expected)."
  fi
done

# --- host VPN note (I1: record the variable even though it does not create range egress) ---
VPN=$(ifconfig 2>/dev/null | grep -oE '^utun[0-9]+' | tr '\n' ' ')
if [ -n "$VPN" ]; then
  say "  NOTE: host VPN interface(s) present: ${VPN}— recorded, does not affect range egress."
else
  say "  NOTE: no host VPN interface detected."
fi

if [ "$egress_hit" -ne 0 ]; then
  exit 1
fi
say "CONTAINMENT: OK — egress proven absent on '$NET'. Cleared to run."
exit 0
