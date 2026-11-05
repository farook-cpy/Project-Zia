@echo off
title Project Zia - MacBook Agent Listener (Port 5001)
echo Starting MacBook Remote Agent Listener on Port 5001...
set MAC_PORT=5001
set RPC_SECRET=zia_palakkad_xperia_secure_key_888
python mac_agent.py
pause

