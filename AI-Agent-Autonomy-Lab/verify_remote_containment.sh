#!/usr/bin/env bash
# verify_remote_containment.sh — FAIL-CLOSED pre-flight gate for the REMOTE-TARGET (Pi) track.
#
# The primary track proves containment structurally (Docker `internal`, no gateway). The remote
# track CANNOT: the agent must reach a real LAN host, so it sits on a non-internal bridge and its
# containment is a Mac-side pf destination-filter (agent → Pi only). That is weaker to prove, so
# here we MEASURE it from multiple vantages and REFUSE TO RUN unless every core assertion holds.
#
# Assertions (all required; ANY failure => exit 1 => the caller aborts + tears down):
#   (a) the agent CAN reach the Pi (else the run is pointless)
#   (b) the agent CANNOT reach anything else — gateway, a sample LAN host, the internet   <-- the core
#   (c) the Pi CANNOT reach the world  (target -> world = nothing)
#   (d) the Pi has IP forwarding OFF   (no pivot through the Pi)
#   (e) the model path is still alive  (so a lockdown that severed it fails closed, not silently)
#
# Exit: 0 = contained, cleared to run   1 = a containment assertion FAILED, abort   2 = cannot test
set -u

AGENT=lab-agent-remote
PI_HOST="${PI_TARGET_HOST:-192.168.178.27}"
PI_SSH="pi@${PI_HOST}"
SSH_OPTS=(-o BatchMode=yes -o ConnectTimeout=8 -o StrictHostKeyChecking=accept-new)
GATEWAY="${LAN_GATEWAY:-192.168.178.1}"
LAN_SAMPLE="${LAN_SAMPLE:-192.168.178.20}"   # a known LAN host that is NOT the Pi (Hue bridge)
EXT_A="1.1.1.1"; EXT_B="8.8.8.8"
fail=0
say() { printf '%s\n' "$*"; }

command -v docker >/dev/null 2>&1 || { say "REMOTE-CONTAINMENT: CANNOT TEST — no docker."; exit 2; }
docker inspect "$AGENT" >/dev/null 2>&1 || { say "REMOTE-CONTAINMENT: CANNOT TEST — $AGENT not up (run pi_target_up.sh)."; exit 2; }

# helper: run a reachability probe INSIDE the agent container; returns 0 if it REACHED the dest.
areach() { docker exec "$AGENT" sh -c "nc -z -w4 $1 $2 >/dev/null 2>&1"; }

# (a) agent CAN reach the Pi (:80 and :22)
if areach "$PI_HOST" 80 || areach "$PI_HOST" 22; then
  say "  (a) agent reaches the Pi ($PI_HOST) — OK"
else
  say "  (a) FAILED — agent cannot reach the Pi at all; nothing to test."; fail=1
fi

# (b) agent CANNOT reach anything else — THE CORE PROOF. Each of these MUST be unreachable.
for probe in "$GATEWAY 443" "$GATEWAY 53" "$LAN_SAMPLE 80" "$EXT_A 443" "$EXT_B 53"; do
  set -- $probe
  if areach "$1" "$2"; then
    say "  (b) FAILED — agent REACHED $1:$2 (should be blocked). The pf lockdown is not sealing. ABORT."
    fail=1
  else
    say "  (b) agent cannot reach $1:$2 (expected)"
  fi
done

# (c) the Pi cannot reach the world (target -> world = nothing)
if ssh "${SSH_OPTS[@]}" "$PI_SSH" \
     "nc -z -w4 $EXT_A 443 >/dev/null 2>&1 || nc -z -w4 $EXT_B 53 >/dev/null 2>&1"; then
  say "  (c) FAILED — the Pi REACHED the internet; its egress block is not in effect. ABORT."; fail=1
elif [ $? -eq 255 ]; then
  say "  (c) CANNOT TEST — SSH to $PI_SSH failed (key/host). Treating as UNPROVEN. ABORT."; fail=1
else
  say "  (c) Pi cannot reach the world (expected)"
fi

# (d) the Pi has forwarding OFF (no pivot)
fwd=$(ssh "${SSH_OPTS[@]}" "$PI_SSH" "cat /proc/sys/net/ipv4/ip_forward /proc/sys/net/ipv6/conf/all/forwarding 2>/dev/null" 2>/dev/null)
if [ "$(printf '%s' "$fwd" | tr -d '[:space:]')" = "00" ]; then
  say "  (d) Pi ip_forward=0 (v4+v6) — OK"
else
  say "  (d) FAILED — Pi forwarding is not fully off (got '$fwd'); pivot path open. ABORT."; fail=1
fi

# (e) model path still alive from the agent
if docker exec "$AGENT" sh -c "curl -s -m5 -o /dev/null -w '%{http_code}' http://host.docker.internal:11434/api/tags" 2>/dev/null | grep -q 200; then
  say "  (e) model endpoint reachable from agent — OK"
else
  say "  (e) FAILED — the agent cannot reach the model endpoint; the lockdown severed it. ABORT."; fail=1
fi

if [ "$fail" -ne 0 ]; then
  say "REMOTE-CONTAINMENT: FAILED — one or more assertions did not hold. The remote track REFUSES to run."
  exit 1
fi
say "REMOTE-CONTAINMENT: OK — agent boxed to the Pi, Pi has no egress, no pivot, model alive. Cleared."
exit 0
