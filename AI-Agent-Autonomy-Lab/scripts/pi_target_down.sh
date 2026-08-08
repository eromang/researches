#!/usr/bin/env bash
# pi_target_down.sh — teardown + RESTORE for the remote-target (Pi) track. Always safe to run,
# even after a partial/failed bring-up. Undoes every change pi_target_up.sh makes and verifies
# the Pi's production DNS/VPN are healthy again.
#
#   1. stop the remote agent container; unload the Mac pf anchor
#   2. SSH the Pi: flush the session nft table; restore ip_forward to its recorded prior value
#   3. restore the Pi config snapshot (pihole / wireguard / authorized_keys / crontab)
#   4. verify production health (Pi-hole resolves, WireGuard up, key-SSH works)
#
# UNTESTED against real hardware — review before first use. Restore returns CONFIG files only;
# a rooted Pi may persist below that (treat a session as leaving the Pi possibly needing a reimage).
set -u
cd "$(dirname "$0")/.."

PI_HOST="${PI_TARGET_HOST:-192.168.178.27}"
PI_SSH="pi@${PI_HOST}"
SSH_OPTS=(-o BatchMode=yes -o ConnectTimeout=8 -o StrictHostKeyChecking=accept-new)
PF_ANCHOR="lab.piegress"
SNAP_LINK="runs/pi-snapshots/latest"
say() { printf '%s\n' "$*"; }
pi() { ssh "${SSH_OPTS[@]}" "$PI_SSH" "$@"; }

say "=== pi_target_down: stopping remote agent ==="
docker compose -f docker/compose.yml --profile remote stop agent-remote >/dev/null 2>&1 || true
docker compose -f docker/compose.yml --profile remote rm -f agent-remote >/dev/null 2>&1 || true

say "=== unloading Mac pf anchor ==="
sudo pfctl -a "$PF_ANCHOR" -F all 2>/dev/null || say "  (pf anchor already clear or pf not loaded)"

say "=== restoring Pi network state ==="
pi 'sudo nft delete table inet lab_egress 2>/dev/null || sudo iptables -F LAB_EGRESS 2>/dev/null; true' || say "  (nft/iptables session table already gone)"
if [ -f "${SNAP_LINK}/ip_forward.prior" ]; then
  fwd=$(cat "${SNAP_LINK}/ip_forward.prior")
  pi "sudo sysctl -w net.ipv4.ip_forward=${fwd} net.ipv6.conf.all.forwarding=${fwd} >/dev/null" \
    && say "  ip_forward restored to ${fwd}" || say "  WARN: could not restore ip_forward"
else
  say "  WARN: no recorded prior ip_forward; defaulting to 1 (WireGuard needs it)"
  pi 'sudo sysctl -w net.ipv4.ip_forward=1 net.ipv6.conf.all.forwarding=1 >/dev/null' || true
fi

say "=== restoring Pi config snapshot ==="
if [ -d "$SNAP_LINK" ]; then
  for item in pihole wireguard; do
    if [ -d "${SNAP_LINK}/${item}" ]; then
      scp -q -r "${SNAP_LINK}/${item}" "${PI_SSH}:/tmp/lab-restore-${item}" 2>/dev/null \
        && pi "sudo cp -a /tmp/lab-restore-${item}/. /etc/${item}/ && sudo rm -rf /tmp/lab-restore-${item}" \
        && say "  restored /etc/${item}" || say "  WARN: /etc/${item} restore failed — CHECK MANUALLY"
    fi
  done
  if [ -f "${SNAP_LINK}/authorized_keys" ]; then
    scp -q "${SNAP_LINK}/authorized_keys" "${PI_SSH}:/tmp/lab-ak" 2>/dev/null \
      && pi 'cat /tmp/lab-ak > ~/.ssh/authorized_keys && rm /tmp/lab-ak' \
      && say "  restored ~pi/.ssh/authorized_keys" || say "  WARN: authorized_keys restore failed — CHECK MANUALLY"
  fi
  [ -f "${SNAP_LINK}/crontab.pi" ] && { scp -q "${SNAP_LINK}/crontab.pi" "${PI_SSH}:/tmp/lab-cron" 2>/dev/null && pi 'crontab /tmp/lab-cron && rm /tmp/lab-cron' && say "  restored pi crontab"; }
else
  say "  WARN: no snapshot at ${SNAP_LINK} — cannot restore config. CHECK THE PI MANUALLY."
fi

say "=== verifying production health ==="
if command -v dig >/dev/null 2>&1 && dig +time=3 +tries=1 @"$PI_HOST" example.com >/dev/null 2>&1; then
  say "  Pi-hole DNS resolves — OK"
else
  say "  WARN: Pi-hole DNS did NOT resolve — CHECK PI-HOLE."
fi
pi 'sudo wg show >/dev/null 2>&1' && say "  WireGuard up — OK" || say "  WARN: WireGuard not confirmed — CHECK."
pi 'echo ok' >/dev/null 2>&1 && say "  key-SSH to Pi works — OK" || say "  WARN: cannot SSH the Pi."
docker inspect lab-agent-remote >/dev/null 2>&1 && say "  WARN: lab-agent-remote still present" || say "  remote agent gone — OK"

say "=== pi_target_down complete — review any WARN lines above ==="
