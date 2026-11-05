#!/data/data/com.termux/files/usr/bin/bash
# ==============================================================================
# PROJECT ZIA // SONY XPERIA 1 III 24/7 BACKGROUND SERVER NODE
# Snapdragon 888 | 12GB RAM | Termux Android Environment
# ==============================================================================

echo -e "\033[96m\033[1m======================================================================"
echo -e " STARTING PROJECT ZIA 24/7 SERVER NODE ON SONY XPERIA 1 III"
echo -e "======================================================================\033[0m"

# 1. Acquire Termux wake lock so Android Doze does not sleep the CPU
if command -v termux-wake-lock &> /dev/null; then
    echo -e "\033[93m[1/3] Acquiring Termux Wake Lock (protecting 24/7 background loop)...\033[0m"
    termux-wake-lock
else
    echo -e "\033[90m[Notice] termux-wake-lock not found; skipping wake lock.\033[0m"
fi

# 2. Check Termux:API tools
if command -v termux-tts-speak &> /dev/null; then
    echo -e "\033[92m[2/3] Termux:API detected (physical speakers and mic ready).\033[0m"
else
    echo -e "\033[93m[Notice] Termux:API not found. Install 'pkg install termux-api'.\033[0m"
fi

# 3. Export environment variables
export PORT=5000
export RPC_SECRET="zia_palakkad_xperia_secure_key_888"

# 4. Launch 24/7 Flask server node
echo -e "\033[92m[3/3] Launching Xperia Server on 0.0.0.0:5000...\033[0m"
python server.py

