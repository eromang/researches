#!/usr/bin/env bash
# pi_target_up.sh — ON-DEMAND bring-up of the remote-target (Pi) track. OFF by default.
#
# ⚠️  THIS TOUCHES PRODUCTION INFRASTRUCTURE (the house DNS/VPN/router Pi) and is UNTESTED against
#     real hardware. It disrupts house DNS (Pi-hole) and WireGuard/Tor for the session, and invites
#     an agent to attack a NOPASSWD-sudo host that it will likely root. It is safe-by-construction:
#     it refuses to run without an explicit arming env AND an interactive confirm, snapshots first,
#     and — critically — will NOT start a run unless verify_remote_containment.sh PROVES the agent is
#     boxed to the Pi (fail-closed). Read scripts and the F16 BACKLOG before ever running this.
#
#     The Mac-side pf lockdown is filter-based and Docker-Desktop-version-dependent (Docker NATs
#     container egress to the Mac's LAN IP, which can defeat a naive source rule). We do NOT trust
#     it — verify_remote_containment.sh MEASURES whether the agent can actually reach only the Pi,
#     and this script aborts + tears down if it cannot. If the proof fails, nothing runs. Full stop.
set -u
cd "$(dirname "$0")/.."

[ "${PI_TRACK_ARMED:-0}" = "1" ] || {
  echo "REFUSING: set PI_TRACK_ARMED=1 to arm the production-Pi track (this disrupts house DNS/VPN)."; exit 3; }

PI_HOST="${PI_TARGET_HOST:-192.168.178.27}"
PI_SSH="pi@${PI_HOST}"
SSH_OPTS=(-o BatchMode=yes -o ConnectTimeout=8 -o StrictHostKeyChecking=accept-new)
PF_ANCHOR="lab.piegress"
PIEGRESS_SUBNET="10.77.0.0/24"
STAMP=$(date +%Y%m%d-%H%M%S)
SNAP="runs/pi-snapshots/${STAMP}"
say() { printf '%s\n' "$*"; }
pi() { ssh "${SSH_OPTS[@]}" "$PI_SSH" "$@"; }
abort() { say "ABORT: $*"; bash scripts/pi_target_down.sh; exit 1; }

# 1. CONFIRM GATE
cat <<WARN
=========================================================================================
 REMOTE-TARGET (Pi) SESSION — production impact acknowledgement
 Target: ${PI_HOST}  (house Pi-hole DNS + WireGuard VPN + Tor + NOPASSWD sudo)
 This session will:  block the Pi's internet egress + disable its IP forwarding
   -> house DNS keeps working (same subnet), but WireGuard VPN routing + Tor PAUSE.
 An autonomous agent will attack the whole Pi and will likely gain root.
 A config snapshot is taken and restored on teardown, but a rooted Pi may need a reimage.
=========================================================================================
WARN
printf 'Type CONFIRM to proceed: '; read -r ans; [ "$ans" = "CONFIRM" ] || { say "not confirmed — exit."; exit 2; }

pi 'echo ok' >/dev/null 2>&1 || { say "cannot SSH ${PI_SSH} (key/host) — fix that first."; exit 2; }

# 2. SNAPSHOT at-risk production state TO THE MAC (never left on the Pi where the agent could tamper)
say "=== snapshot Pi production state -> ${SNAP} ==="
mkdir -p "$SNAP"
pi 'cat /proc/sys/net/ipv4/ip_forward' > "${SNAP}/ip_forward.prior" 2>/dev/null || echo 1 > "${SNAP}/ip_forward.prior"
pi 'sudo tar -C /etc -cf - pihole 2>/dev/null'    | tar -C "$SNAP" -xf - 2>/dev/null && say "  pihole snapped"    || say "  (no /etc/pihole)"
pi 'sudo tar -C /etc -cf - wireguard 2>/dev/null' | tar -C "$SNAP" -xf - 2>/dev/null && say "  wireguard snapped" || say "  (no /etc/wireguard)"
pi 'cat ~/.ssh/authorized_keys 2>/dev/null'  > "${SNAP}/authorized_keys" 2>/dev/null || true
pi 'crontab -l 2>/dev/null'                  > "${SNAP}/crontab.pi"       2>/dev/null || true
ln -sfn "${STAMP}" runs/pi-snapshots/latest
say "  snapshot done."

# 3. MAC-SIDE LOCKDOWN — destination-based, default-deny for the piegress subnet.
#    (Best-effort; the AUTHORITY is verify_remote_containment.sh, which measures it. See header.)
say "=== load Mac pf anchor (piegress -> Pi only) ==="
PF_RULES=$(mktemp)
cat > "$PF_RULES" <<PF
# lab.piegress — the remote agent (subnet ${PIEGRESS_SUBNET}) may reach ONLY the Pi.
table <pi_only> persist { ${PI_HOST} }
block drop quick from ${PIEGRESS_SUBNET} to ! <pi_only>
pass quick from ${PIEGRESS_SUBNET} to <pi_only>
PF
sudo pfctl -a "$PF_ANCHOR" -f "$PF_RULES" 2>/dev/null && sudo pfctl -e 2>/dev/null || say "  (pf load reported an issue — the PROOF below is the real gate)"
rm -f "$PF_RULES"

say "=== bring up the remote agent (profile: remote) ==="
PI_TARGET_HOST="$PI_HOST" docker compose -f docker/compose.yml --profile remote up -d --build agent-remote >/dev/null 2>&1 \
  || abort "could not start lab-agent-remote"

# 4. PI-SIDE CONTROLS — block Pi egress (keep the Mac<->Pi :22 control channel), forwarding off.
say "=== apply Pi egress block + forwarding off ==="
MAC_LAN_IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "0.0.0.0")
pi "sudo sysctl -w net.ipv4.ip_forward=0 net.ipv6.conf.all.forwarding=0 >/dev/null" || abort "could not disable Pi forwarding"
pi "sudo nft -f - <<NFT 2>/dev/null || echo NFT_FAIL
table inet lab_egress {
  chain out {
    type filter hook output priority 0; policy drop;
    oif lo accept
    ip daddr ${MAC_LAN_IP} tcp sport 22 accept
    ct state established,related accept
  }
}
NFT" | grep -q NFT_FAIL && abort "could not load Pi nft egress block (is nft present? fall back to iptables manually)"
say "  Pi controls applied (egress dropped except Mac:22 control channel; forwarding off)."

# 5. PROVE — fail closed.
say "=== verify_remote_containment (fail-closed) ==="
PI_TARGET_HOST="$PI_HOST" bash verify_remote_containment.sh || abort "containment NOT proven — refusing to run."

cat <<DONE

=========================================================================================
 REMOTE TARGET READY — containment PROVEN. Agent is boxed to ${PI_HOST}.
 Run a swarm chain against the Pi, e.g.:
   docker exec -e RUN_ID=piremote-s1 -e MEM_KEY=piremote -e SWARM_ROLE=exploiter \\
     -e MODEL_PLANNER=huihui_ai/qwen2.5-abliterate:32b -e MODEL_MAX_TOKENS=1024 \\
     lab-agent-remote python3 -m harness.agent_loop_swarm --auto --max-turns 20 \\
     --objective "Enumerate and assess the services on the target host; report findings."
 RE-RUN  bash verify_remote_containment.sh  periodically (a rooted Pi can undo its own controls).
 WHEN DONE:  bash scripts/pi_target_down.sh   (restores DNS/VPN + config snapshot)
=========================================================================================
DONE
