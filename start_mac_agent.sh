#!/bin/bash
# ==============================================================================
# PROJECT ZIA // MACBOOK PRO 2007 REMOTE AGENT LISTENER (Linux Mint XFCE)
# Core 2 Duo | 0% VRAM | Low Overhead JSON-RPC 2.0 Daemon (Port 5001)
# ==============================================================================

echo -e "\033[96m\033[1m======================================================================"
echo -e " STARTING MACBOOK PRO 2007 REMOTE AGENT LISTENER"
echo -e "======================================================================\033[0m"

export MAC_PORT=5001
export RPC_SECRET="zia_palakkad_xperia_secure_key_888"

# If Xperia IP is known on LAN, export it for auto-registration:
# export XPERIA_SERVER_URL="http://192.168.1.50:5000"

python3 mac_agent.py

