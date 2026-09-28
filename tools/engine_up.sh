#!/usr/bin/env bash
# engine_up.sh - start the ShieldBid Zcash engines (mainnet 8000 + testnet 8001) if down.
# Run from Windows:  bash tools/engine_up.sh   (it shells into WSL itself)
set -u
DISTRO="${SB_DISTRO:-shieldbid}"

start() {
  local port="$1" db="$2" lwd="$3" coin="$4" log="$5"
  wsl -d "$DISTRO" -u root -- bash -lc \
    "pgrep -f \"zkool_graphql.*-p ${port}\" >/dev/null && { echo 'port ${port}: already running'; exit 0; }
     cd /root && setsid ./zkool_graphql -d ${db} -l ${lwd} -p ${port} ${coin} > ${log} 2>&1 &
     sleep 8; pgrep -f \"zkool_graphql.*-p ${port}\" >/dev/null && echo 'port ${port}: started' || { echo 'port ${port}: FAILED'; tail -5 ${log}; }"
}

start 8000 /root/sb_main.db https://zec.rocks:443 "" /root/engine.log
start 8001 /root/sb_test.db https://testnet.zec.rocks:443 "-C 1" /root/engine_test.log
