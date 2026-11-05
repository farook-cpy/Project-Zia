import sys
import os
import time
from pathlib import Path

# Ensure UTF-8 output on Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

# Load config
from engine.config import GEMINI_API_KEY
from engine.local_commands import local_router
from engine.system_control import system_controller
from engine.bluetooth_manager import bluetooth_manager
from engine.subagents import subagent_pool
from engine.mcp_gateway import mcp_gateway
from engine.memory import memory_engine
from engine.iot_bridge import iot_bridge
from engine.brain import brain_engine
from engine.terminal_avatar import terminal_avatar
from engine.local_stt import local_stt
from engine.error_debugger import error_debugger
from engine.shell_compiler import shell_compiler
from engine.vault import encrypted_vault
from engine.scheduler import scheduler
from engine.network_sentinel import network_sentinel
from engine.clipboard_sync import clipboard_sync, ClipboardManager
from engine.senses import screen_sensor
from engine.vision_senses import vision_senses
from engine.prayer_times import prayer_engine
from engine.alarm_manager import alarm_manager
from engine.rpc_bridge import rpc_bridge
from engine.audio_bridge import audio_bridge
from engine.agentic_ops import agentic_ops
from engine.ecosystem_bridge import ecosystem_bridge
from engine.security_vault import security_vault
from engine.ambient_intelligence import ambient_engine
from engine.lifedesk_bridge import lifedesk_bridge
from engine.remote_gateway import telegram_gateway

ANSI_CYAN = "\033[96m"
ANSI_GREEN = "\033[92m"
ANSI_YELLOW = "\033[93m"
ANSI_RED = "\033[91m"
ANSI_GRAY = "\033[90m"
ANSI_BOLD = "\033[1m"
ANSI_RESET = "\033[0m"

def print_banner():
    banner = f"""{ANSI_CYAN}{ANSI_BOLD}======================================================================
 PROJECT FAITH // ZIA  [CLI v1.3.0 - High Performance Terminal]
 Cross-OS Engine | 0% VRAM | <0.5% CPU | Local STT | ANSI Avatar 24FPS
 Type 'help' for command reference. Type 'exit' to quit.
======================================================================{ANSI_RESET}"""
    print(banner)

def print_help():
    print(f"""
{ANSI_BOLD}CORE INTERFACES & AGENTS:{ANSI_RESET}
  {ANSI_GREEN}chat <prompt>{ANSI_RESET}               Query Gemini Flash directly (or type raw question)
  {ANSI_GREEN}plan <goal>{ANSI_RESET}                 Multi-step reasoning tree plan visualizer
  {ANSI_GREEN}review <file>{ANSI_RESET}               Smart code reviewer subagent & security linting
  {ANSI_GREEN}testgen <file>{ANSI_RESET}              Automated AST unit test generator
  {ANSI_GREEN}qtask <role> <desc>{ANSI_RESET}        Enqueue task to persistent SQLite queue
  {ANSI_GREEN}qprocess{ANSI_RESET}                    Process pending tasks in SQLite queue
  {ANSI_GREEN}budget{ANSI_RESET}                      Dynamic Gemini token budget & real-time cost accumulator
  {ANSI_GREEN}ocr <image_path>{ANSI_RESET}            Local OCR text extraction (0 cloud dependencies)
  {ANSI_GREEN}docs <url> [tag]{ANSI_RESET}            Autonomous documentation scraper & markdown cache
  {ANSI_GREEN}deps <script.py>{ANSI_RESET}            Background dependency resolver & import scanner
  {ANSI_GREEN}agent run <role> <task>{ANSI_RESET}     Spawn background subagent (roles: coder, researcher, system)
  {ANSI_GREEN}agent list / status <id>{ANSI_RESET}    List or inspect subagent workers

{ANSI_BOLD}CROSS-DEVICE ECOSYSTEM & HARDWARE:{ANSI_RESET}
  {ANSI_GREEN}mac [status|health|exec|vol]{ANSI_RESET} Remote MacBook Control via secure JSON-RPC Bridge
  {ANSI_GREEN}xperia [status|listen|speak]{ANSI_RESET} Android/Termux ambient room listening & stereo speakers
  {ANSI_GREEN}drop [send <file>|list]{ANSI_RESET}     Phone-to-laptop local file drop (AirDrop clone)
  {ANSI_GREEN}battery{ANSI_RESET}                     Remote battery status mirroring (Xperia / Mac)
  {ANSI_GREEN}route [phone|mac|bt]{ANSI_RESET}        Audio routing switcher (speakers/jack/bluetooth)
  {ANSI_GREEN}wol <mac_address>{ANSI_RESET}           Remote Wake-on-LAN trigger (UDP Magic Packet)
  {ANSI_GREEN}pinglan [host]{ANSI_RESET}              Network ping & link quality watchdog
  {ANSI_GREEN}camstream{ANSI_RESET}                  Remote camera frame streamer from Xperia node
  {ANSI_GREEN}dashboard{ANSI_RESET}                  Device health responsive dashboard URL (:5000/dashboard)

{ANSI_BOLD}SECURITY, PRIVACY & CRYPTOGRAPHY:{ANSI_RESET}
  {ANSI_GREEN}incognito [on|off]{ANSI_RESET}          Ephemeral chat mode (zero trace on disk)
  {ANSI_GREEN}fim [check|update]{ANSI_RESET}          File Integrity Monitor (SHA-256 project baseline)
  {ANSI_GREEN}ports{ANSI_RESET}                      Exposed port auditor (scans 0.0.0.0 listeners)
  {ANSI_GREEN}sslcert <host>{ANSI_RESET}              SSL certificate expiry watchdog
  {ANSI_GREEN}secscan [dir]{ANSI_RESET}               Scan codebase for leaked secrets & API keys
  {ANSI_GREEN}tunnel <user> <host>{ANSI_RESET}        Generate reverse SSH tunnel command

{ANSI_BOLD}SMART AMBIENT INTELLIGENCE:{ANSI_RESET}
  {ANSI_GREEN}weather [lat lon]{ANSI_RESET}           Context-aware weather adaptive greeter (Open-Meteo)
  {ANSI_GREEN}chime [ping|alert|prayer]{ANSI_RESET}   Procedural retro-futuristic audio soundboard generator
  {ANSI_GREEN}focus [start|stop]{ANSI_RESET}          Adaptive focus music stream & session tracking
  {ANSI_GREEN}conflict <HH:MM> [min]{ANSI_RESET}      Smart meeting vs prayer conflict resolver
  {ANSI_GREEN}digest{ANSI_RESET}                     Daily developer digest report (git, alarms, prayers)
  {ANSI_GREEN}presence{ANSI_RESET}                   Geofence Wi-Fi home presence check
  {ANSI_GREEN}theme [cyan|amber|matrix|mono]{ANSI_RESET} Customizable retro HUD theme engine
  {ANSI_GREEN}habit [log <name>|streaks]{ANSI_RESET}  Smart habit streak tracker (coding, prayer, writing)
  {ANSI_GREEN}macro <word>{ANSI_RESET}                 Interactive voice/text shortcut macro executor

{ANSI_BOLD}LIFEDESK, TELEGRAM & SMART IOT:{ANSI_RESET}
  {ANSI_GREEN}lifedesk [summary]{ANSI_RESET}          LifeDesk SQLite productivity & financial ledger
  {ANSI_GREEN}expense [log <amt> <cat>|list]{ANSI_RESET} Natural language or structured expense logging
  {ANSI_GREEN}habit [log <name> [val]|streaks]{ANSI_RESET} Habit streak tracking & daily logging
  {ANSI_GREEN}tg [status|send <msg>|voice <msg>]{ANSI_RESET} Remote Telegram Bot text & Edge-TTS voice gateway
  {ANSI_GREEN}projector [url]{ANSI_RESET}             Wireless ADB projector bridge (miruro.tv)
  {ANSI_GREEN}botim [contact]{ANSI_RESET}             Wireless ADB VoIP calling bridge on tablet
  {ANSI_GREEN}relay <device> <action>{ANSI_RESET}     ESP8266/NodeMCU smart home relay control

{ANSI_BOLD}SYSTEM, PRAYER & AUTOMATION:{ANSI_RESET}
  {ANSI_GREEN}prayer [times|next|done]{ANSI_RESET}   Palakkad daily prayer schedule & gentle check-in
  {ANSI_GREEN}alarm [list|set <time>]{ANSI_RESET}    Natural language clock alarms (e.g. 'alarm set 8:00 pm')
  {ANSI_GREEN}timer <duration> [label]{ANSI_RESET}   Relative countdown timers (e.g. 'timer 20m push code')
  {ANSI_GREEN}sys health / troubleshoot{ANSI_RESET}   Live CPU %, Temp, RAM, Disk & device auto-repair
  {ANSI_GREEN}sys vol <up|down|mute>{ANSI_RESET}     Adjust OS audio volume
  {ANSI_GREEN}sys bright <up|down>{ANSI_RESET}       Adjust screen brightness
  {ANSI_GREEN}avatar [live|demo]{ANSI_RESET}          ASCII/ANSI Retro Terminal Avatar (24 FPS, 0% VRAM)
  {ANSI_GREEN}listen / voice{ANSI_RESET}             Local Offline Speech Input (Vosk ~25MB RAM)
  {ANSI_GREEN}bt list / scan / connect{ANSI_RESET}   Bluetooth device management
  {ANSI_GREEN}debug [command]{ANSI_RESET}           Automated traceback debugger & terminal code fix
  {ANSI_GREEN}vision [query]{ANSI_RESET}             Multimodal screen vision analysis
  {ANSI_GREEN}mcp read <path> / search{ANSI_RESET}   Zero-OCR precision file crawling
  {ANSI_GREEN}help / exit{ANSI_RESET}                Show reference or quit
""")

def handle_bluetooth_cli(args):
    sub = args[0].lower() if args else "list"
    if sub == "list":
        res = bluetooth_manager.get_paired_devices()
        devs = res.get("devices", [])
        if not devs:
            print(f"{ANSI_GRAY}[BT] No paired Bluetooth devices found on this system.{ANSI_RESET}")
            return
        print(f"\n{ANSI_BOLD}PAIRED BLUETOOTH DEVICES:{ANSI_RESET}")
        for d in devs:
            name = d.get("name") or d.get("mac")
            status = f"{ANSI_GREEN}CONNECTED{ANSI_RESET}" if d.get("connected") else f"{ANSI_GRAY}DISCONNECTED{ANSI_RESET}"
            mac = f" ({d['mac']})" if d.get("mac") else ""
            print(f" - {name}{mac} [{status}]")
        print()
    elif sub == "scan":
        print(f"{ANSI_CYAN}[BT] Scanning for nearby Bluetooth devices (6s)...{ANSI_RESET}")
        res = bluetooth_manager.scan_devices()
        devs = res.get("devices", [])
        if devs:
            for d in devs:
                print(f" - {d.get('name', 'Unknown')} ({d.get('mac', '')})")
        else:
            print(res.get("message", "Scan complete. No new devices found."))
    elif sub == "connect":
        if len(args) < 2:
            print(f"{ANSI_RED}Usage: bt connect <device_name_or_mac>{ANSI_RESET}")
            return
        target = " ".join(args[1:])
        res = bluetooth_manager.connect(target)
        print(f"{ANSI_GREEN}[BT]{ANSI_RESET} {res.get('output') or res.get('message') or res}")

def handle_subagent_cli(args):
    sub = args[0].lower() if args else "list"
    if sub == "list":
        tasks = subagent_pool.list_tasks()
        if not tasks:
            print(f"{ANSI_GRAY}[Subagents] No active or previous subagent tasks.{ANSI_RESET}")
            return
        print(f"\n{ANSI_BOLD}SUBAGENT TASKS:{ANSI_RESET}")
        for t in tasks:
            color = ANSI_GREEN if t['status'] == 'completed' else (ANSI_YELLOW if t['status'] == 'running' else ANSI_RED)
            print(f" [{t['id']}] {t['role'].upper()} | {color}{t['status'].upper()}{ANSI_RESET} ({t['progress']}%) | {t['description'][:50]} | {t['elapsed_sec']}s")
        print()
    elif sub == "run":
        if len(args) < 3:
            print(f"{ANSI_RED}Usage: agent run <coder|researcher|system> <description>{ANSI_RESET}")
            return
        role = args[1]
        desc = " ".join(args[2:])
        task_id = subagent_pool.spawn(role, desc)
        print(f"{ANSI_GREEN}[Subagents] Spawned {role.upper()} task [{task_id}]. Running in background thread.{ANSI_RESET}")
    elif sub == "status":
        if len(args) < 2:
            print(f"{ANSI_RED}Usage: agent status <task_id>{ANSI_RESET}")
            return
        tid = args[1]
        t = subagent_pool.get_task(tid)
        if not t:
            print(f"{ANSI_RED}[Subagents] Task ID '{tid}' not found.{ANSI_RESET}")
            return
        print(f"\n{ANSI_BOLD}TASK DETAILS [{tid}]:{ANSI_RESET}")
        print(f" Role:        {t['role'].upper()}")
        print(f" Status:      {t['status'].upper()} ({t['progress']}%)")
        print(f" Description: {t['description']}")
        if t['result']:
            print(f" Result:      {t['result']}")
        if t['error']:
            print(f" Error:       {t['error']}")
        print(f" Elapsed:     {t['elapsed_sec']}s\n")

def handle_sys_cli(args):
    sub = args[0].lower() if args else "health"
    if sub in ["health", "status"]:
        h = system_controller.get_system_health()
        print(f"\n{ANSI_BOLD}SYSTEM DIAGNOSTICS:{ANSI_RESET}")
        temp_str = f" ({int(h['cpu_temp'])}°C)" if h.get("cpu_temp") else ""
        print(f" CPU Usage:   {h['cpu_percent']}%{temp_str}")
        print(f" RAM Usage:   {h['ram_percent']}% ({h['ram_used_gb']} GB / {h['ram_total_gb']} GB)")
        print(f" Swap Memory: {h['swap_percent']}% ({h['swap_used_mb']} MB / {h['swap_total_mb']} MB)")
        print(f" Uptime:      {h['uptime']}")
        print(f" Disk Free:   {h['disk_free_gb']} GB")
        print(f" Internet:    {'ONLINE' if h['internet_connected'] else 'OFFLINE'}")
        if h.get("battery"):
            plugged = "PLUGGED IN" if h['battery']['plugged_in'] else "DISCHARGING"
            print(f" Battery:     {int(h['battery']['percent'])}% [{plugged}]")
        if h['top_processes']:
            print(f" Heavy Tasks: {', '.join(h['top_processes'][:3])}")
        print()
    elif sub == "troubleshoot":
        print(f"{ANSI_CYAN}[Zia]{ANSI_RESET} {system_controller.troubleshoot()}")
    elif sub == "vol":
        action = args[1] if len(args) > 1 else "up"
        res = system_controller.change_volume(action)
        print(f"{ANSI_GREEN}[System]{ANSI_RESET} Adjusted volume: {action}")
    elif sub == "bright":
        action = args[1] if len(args) > 1 else "up"
        res = system_controller.change_brightness(action)
        print(f"{ANSI_GREEN}[System]{ANSI_RESET} Adjusted brightness: {action}")
    elif sub == "lock":
        res = system_controller.lock_session()
        print(f"{ANSI_GREEN}[System]{ANSI_RESET} {res.get('message', res)}")
    elif sub == "unlock":
        res = system_controller.unlock_session()
        print(f"{ANSI_GREEN}[System]{ANSI_RESET} {res.get('message', res)}")
    elif sub in ["compositor", "comp"]:
        val = args[1].lower() if len(args) > 1 else "toggle"
        enable = True if val in ["on", "enable", "1"] else (False if val in ["off", "disable", "0"] else None)
        res = system_controller.toggle_compositor(enable)
        print(f"{ANSI_GREEN}[System]{ANSI_RESET} {res.get('message', res)}")
    elif sub == "sudo":
        if len(args) > 1 and args[1] == "setup":
            res = system_controller.setup_passwordless_sudo()
            print(f"{ANSI_GREEN}[System]{ANSI_RESET} {res.get('message', res)}")
        else:
            print(f"{ANSI_RED}Usage: sys sudo setup{ANSI_RESET}")

def handle_wakeword_cli(args):
    sub = args[0].lower() if args else "status"
    if sub in ["on", "start", "enable"]:
        def on_wake(command):
            print(f"\n{ANSI_BOLD}🎙️ [WakeWord]: Executing \"{command}\"...{ANSI_RESET}")
            process_command(command)
            sys.stdout.write(f"\n{ANSI_BOLD}zia>{ANSI_RESET} ")
            sys.stdout.flush()

        ok = local_stt.start_wake_word_daemon(on_wake)
        if ok:
            print(f"{ANSI_GREEN}[WakeWord] Hands-free wake-word listener is now active! Say 'Hey Zia, <command>'.{ANSI_RESET}")
        else:
            print(f"{ANSI_RED}[WakeWord] Failed to activate wake-word listener (model not downloaded). Run 'stt download' first.{ANSI_RESET}")
    elif sub in ["off", "stop", "disable"]:
        local_stt.stop_wake_word_daemon()
        print(f"{ANSI_YELLOW}[WakeWord] Hands-free listener disabled.{ANSI_RESET}")
    elif sub in ["status", "check"]:
        active = local_stt.is_wake_word_active()
        status_str = f"{ANSI_GREEN}ACTIVE (Listening for 'Hey Zia'){ANSI_RESET}" if active else f"{ANSI_GRAY}OFF (Type 'wakeword on' to activate){ANSI_RESET}"
        print(f"\n{ANSI_BOLD}WAKE-WORD ENGINE STATUS:{ANSI_RESET} {status_str}\n")
    else:
        print(f"{ANSI_RED}Usage: wakeword [on | off | status]{ANSI_RESET}")

def handle_avatar_cli(args):
    sub = args[0].lower() if args else "show"
    if sub in ["show", "view", "render"]:
        expr = args[1].upper() if len(args) > 1 else terminal_avatar.active_expression
        print(terminal_avatar.render_frame(expr=expr, mouth_val=0.0, tick=0.0))
    elif sub in ["live", "play", "animate"]:
        expr = args[1].upper() if len(args) > 1 else terminal_avatar.active_expression
        print(f"{ANSI_CYAN}Starting 24 FPS ANSI Terminal Avatar... Press Ctrl+C to return to CLI.{ANSI_RESET}")
        time.sleep(0.8)
        try:
            terminal_avatar.run_live(expr=expr)
        except KeyboardInterrupt:
            print(f"\n{ANSI_GRAY}[Avatar] Exited animated mode. Returning to CLI.{ANSI_RESET}\n")
    elif sub == "set":
        if len(args) < 2:
            print(f"{ANSI_RED}Usage: avatar set <F1-F11>{ANSI_RESET}")
            return
        expr = args[1].upper()
        terminal_avatar.active_expression = expr
        print(terminal_avatar.render_frame(expr=expr, mouth_val=0.0, tick=0.0))
        print(f"{ANSI_GREEN}[Avatar] Expression set to {expr}.{ANSI_RESET}")
    elif sub == "demo":
        print(f"{ANSI_CYAN}Cycling through F1-F11 expressions (Ctrl+C to abort)...{ANSI_RESET}")
        try:
            for exp in ["F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11"]:
                print(f"{ANSI_BOLD}--- Expression {exp} ---{ANSI_RESET}")
                print(terminal_avatar.render_frame(expr=exp, mouth_val=0.0, tick=0.0))
                time.sleep(1.0)
        except KeyboardInterrupt:
            print(f"\n{ANSI_GRAY}[Avatar Demo] Stopped.{ANSI_RESET}")
    else:
        print(f"{ANSI_RED}Usage: avatar [show | live | set <F1-F11> | demo]{ANSI_RESET}")

def handle_stt_cli(args):
    sub = args[0].lower() if args else "listen"
    if sub in ["listen", "mic", "rec"]:
        print(f"{ANSI_CYAN}🎙️ [LocalSTT] Listening via microphone (sample rate 16000Hz, speak now)...{ANSI_RESET}")
        text = local_stt.listen_and_transcribe(timeout_sec=7)
        if text and not text.startswith("Audio capture error") and not text.startswith("Local speech model"):
            print(f"{ANSI_BOLD}🎙️ [Heard]: \"{text}\"{ANSI_RESET}")
            # Feed transcription directly into command pipeline
            process_command(text)
        else:
            print(f"{ANSI_YELLOW}[LocalSTT] {text or 'No speech detected.'}{ANSI_RESET}")
    elif sub == "status":
        is_ready = local_stt.ensure_model(auto_download=False)
        status_str = f"{ANSI_GREEN}READY (~25MB RAM){ANSI_RESET}" if is_ready else f"{ANSI_YELLOW}NOT LOADED (will auto-download on first use){ANSI_RESET}"
        print(f"\n{ANSI_BOLD}OFFLINE STT ENGINE STATUS:{ANSI_RESET}")
        print(f" Model:        Vosk Quantized Small (vosk-model-small-en-us-0.15)")
        print(f" State:        {status_str}")
        print(f" Sample Rate:  {local_stt.sample_rate} Hz")
        print(f" Dependencies: sounddevice + vosk (Offline, No Browser)\n")
    elif sub == "download":
        print(f"{ANSI_CYAN}[LocalSTT] Verifying/Downloading model files...{ANSI_RESET}")
        ok = local_stt.ensure_model(auto_download=True)
        if ok:
            print(f"{ANSI_GREEN}[LocalSTT] Model ready and verified.{ANSI_RESET}")
        else:
            print(f"{ANSI_RED}[LocalSTT] Failed to acquire model.{ANSI_RESET}")
    else:
        print(f"{ANSI_RED}Usage: stt [listen | status | download]{ANSI_RESET}")

def handle_debug_cli(args):
    import asyncio
    cmd_to_debug = " ".join(args) if args else None
    print(f"{ANSI_GRAY}[Consulting Gemini Flash error debugger...]{ANSI_RESET}")
    res = asyncio.run(error_debugger.debug_error(command=cmd_to_debug))
    if res.get("success"):
        print(f"\n{ANSI_BOLD}ERROR DIAGNOSIS & RECOVERY:{ANSI_RESET}")
        print(f"{ANSI_CYAN}{res['analysis']}{ANSI_RESET}\n")
    else:
        print(f"{ANSI_YELLOW}{res.get('analysis')}{ANSI_RESET}")

def handle_vision_cli(args):
    import asyncio
    query = " ".join(args).strip() if args else "Analyze my screen and describe what is visible."
    print(f"{ANSI_CYAN}[Capturing screen and analyzing with Gemini Flash multimodal vision...]{ANSI_RESET}")
    img = screen_sensor.capture_screen(scale_width=1024)
    res = asyncio.run(brain_engine.think_and_reply(user_message=query, screen_image=img))
    print(f"\n{ANSI_BOLD}SCREEN VISION ANALYSIS:{ANSI_RESET}")
    print(f"{res['text']}\n")

def handle_compiler_cli(args):
    import asyncio
    req = " ".join(args).strip()
    if not req:
        print(f"{ANSI_RED}Usage: cmd <natural language task (e.g. 'find files larger than 100mb')>{ANSI_RESET}")
        return
    print(f"{ANSI_GRAY}[Compiling natural language to shell pipeline...]{ANSI_RESET}")
    res = asyncio.run(shell_compiler.compile_to_shell(req))
    if res.get("success"):
        print(f"\n{ANSI_BOLD}COMPILED SHELL PIPELINE:{ANSI_RESET}")
        print(f"{ANSI_CYAN}{res['output']}{ANSI_RESET}\n")
    else:
        print(f"{ANSI_RED}Compilation error: {res.get('error')}{ANSI_RESET}")

def handle_vault_cli(args):
    sub = args[0].lower() if args else "list"
    if sub == "store":
        if len(args) < 4:
            print(f"{ANSI_RED}Usage: vault store <service> <key_name> <secret_value>{ANSI_RESET}")
            return
        res = encrypted_vault.store_credential(args[1], args[2], args[3])
        print(f"{ANSI_GREEN}[Vault]{ANSI_RESET} {res['message']}")
    elif sub == "get":
        if len(args) < 2:
            print(f"{ANSI_RED}Usage: vault get <service> [key_name]{ANSI_RESET}")
            return
        svc = args[1]
        kname = args[2] if len(args) > 2 else None
        res = encrypted_vault.get_credential(svc, kname)
        if res.get("success"):
            if "value" in res:
                print(f"{ANSI_GREEN}[Vault]{ANSI_RESET} {res['service']} / {res['key']}: {ANSI_BOLD}{res['value']}{ANSI_RESET}")
            else:
                print(f"{ANSI_GREEN}[Vault]{ANSI_RESET} {res['service']} keys: {', '.join(res.get('keys', []))}")
        else:
            print(f"{ANSI_RED}[Vault] {res.get('error')}{ANSI_RESET}")
    elif sub in ["list", "ls"]:
        res = encrypted_vault.list_services()
        print(f"\n{ANSI_BOLD}ENCRYPTED VAULT SERVICES ({res['count']}):{ANSI_RESET}")
        for svc, keys in res["services"].items():
            print(f" - {ANSI_CYAN}{svc}{ANSI_RESET}: {', '.join(keys)}")
        print()
    elif sub in ["del", "delete", "rm"]:
        if len(args) < 2:
            print(f"{ANSI_RED}Usage: vault del <service> [key_name]{ANSI_RESET}")
            return
        svc = args[1]
        kname = args[2] if len(args) > 2 else None
        res = encrypted_vault.delete_credential(svc, kname)
        print(f"{ANSI_GREEN}[Vault]{ANSI_RESET} {res.get('message') or res.get('error')}")
    else:
        print(f"{ANSI_RED}Usage: vault [store | get | list | del]{ANSI_RESET}")

def handle_schedule_cli(args):
    sub = args[0].lower() if args else "list"
    if sub in ["list", "ls"]:
        tasks = scheduler.list_schedules()
        if not tasks:
            print(f"{ANSI_GRAY}[Scheduler] No active schedules. Add one: schedule \"remind me\" every 30m{ANSI_RESET}")
            return
        print(f"\n{ANSI_BOLD}ACTIVE SCHEDULES & CRON TASKS:{ANSI_RESET}")
        for t in tasks:
            rec_str = "RECURRING" if t["is_recurring"] else "ONE-SHOT"
            print(f" [{t['id']}] '{t['label']}' | {rec_str} every {t['interval_sec']}s | Next in: {t['seconds_until_next']}s | Runs: {t['runs_count']}")
        print()
    elif sub in ["cancel", "rm", "delete"]:
        if len(args) < 2:
            print(f"{ANSI_RED}Usage: schedule cancel <task_id>{ANSI_RESET}")
            return
        res = scheduler.cancel_schedule(args[1])
        print(f"{ANSI_GREEN}[Scheduler]{ANSI_RESET} {res.get('message') or res.get('error')}")
    else:
        prompt = " ".join(args)
        res = scheduler.add_schedule(prompt)
        print(f"{ANSI_GREEN}[Scheduler]{ANSI_RESET} {res['message']}")

def handle_net_cli(args):
    sub = args[0].lower() if args else "ports"
    if sub in ["ports", "listeners", "ls"]:
        ports = network_sentinel.scan_listening_ports()
        print(f"\n{ANSI_BOLD}ACTIVE LISTENING PORTS ({len(ports)}):{ANSI_RESET}")
        for p in ports:
            scope = f"{ANSI_GREEN}LOCAL{ANSI_RESET}" if p["is_local_only"] else f"{ANSI_YELLOW}PUBLIC / LAN{ANSI_RESET}"
            print(f" - [{p['protocol']}] Port {p['port']} ({scope}) -> {p['process']} (PID {p['pid']})")
        print()
    elif sub in ["speed", "bandwidth", "rate"]:
        b = network_sentinel.get_bandwidth_rate()
        print(f"\n{ANSI_BOLD}NETWORK BANDWIDTH SENTINEL:{ANSI_RESET}")
        print(f" Download Rate: {b['download_kb_s']} KB/s (Total: {b['total_received_mb']} MB)")
        print(f" Upload Rate:   {b['upload_kb_s']} KB/s (Total: {b['total_sent_mb']} MB)\n")
    elif sub in ["active", "connections", "conn"]:
        conns = network_sentinel.scan_active_connections()
        print(f"\n{ANSI_BOLD}ACTIVE ESTABLISHED TCP SESSIONS ({len(conns)}):{ANSI_RESET}")
        for c in conns:
            print(f" - {c['process']} (PID {c['pid']}) -> {c['remote_ip']}:{c['remote_port']}")
        print()
    elif sub in ["audit", "sentinel", "check"]:
        a = network_sentinel.audit_security_alert()
        flagged = a["flagged_open_ports"]
        status = f"{ANSI_YELLOW}WARNING: {len(flagged)} unverified public port(s) open!{ANSI_RESET}" if flagged else f"{ANSI_GREEN}SECURE: All ports expected/local.{ANSI_RESET}"
        print(f"\n{ANSI_BOLD}SECURITY AUDIT:{ANSI_RESET} {status}")
        for f in flagged:
            print(f" ! [{f['protocol']}] Port {f['port']} open on {f['ip']} by {f['process']}")
        print()
    else:
        print(f"{ANSI_RED}Usage: net [ports | bandwidth | active | audit]{ANSI_RESET}")

def handle_clip_cli(args):
    sub = args[0].lower() if args else "get"
    if sub == "get":
        text = ClipboardManager.get_text()
        print(f"{ANSI_BOLD}CLIPBOARD CONTENT:{ANSI_RESET}\n{text}\n")
    elif sub == "set":
        if len(args) < 2:
            print(f"{ANSI_RED}Usage: clip set <text_to_copy>{ANSI_RESET}")
            return
        content = " ".join(args[1:])
        ClipboardManager.set_text(content)
        print(f"{ANSI_GREEN}[Clipboard]{ANSI_RESET} Copied {len(content)} characters to clipboard.")
    elif sub == "sync":
        action = args[1].lower() if len(args) > 1 else "status"
        if action in ["on", "start"]:
            res = clipboard_sync.start()
            print(f"{ANSI_GREEN}[ClipSync]{ANSI_RESET} {res['message']}")
            print(f"{ANSI_CYAN}Open on your phone/tablet (Samsung S24 FE): {res.get('url')}{ANSI_RESET}")
        elif action in ["off", "stop"]:
            res = clipboard_sync.stop()
            print(f"{ANSI_YELLOW}[ClipSync]{ANSI_RESET} {res['message']}")
        else:
            state = f"{ANSI_GREEN}LIVE{ANSI_RESET} at http://{clipboard_sync.get_lan_ip()}:{clipboard_sync.port}/" if clipboard_sync.is_running else f"{ANSI_GRAY}STOPPED{ANSI_RESET}"
            print(f"\n{ANSI_BOLD}MULTI-DEVICE CLIPBOARD SYNC:{ANSI_RESET} {state}\n")
    else:
        print(f"{ANSI_RED}Usage: clip [get | set <text> | sync on/off/status]{ANSI_RESET}")

def handle_mount_cli(args):
    sub = args[0].lower() if args else "list"
    if sub in ["list", "ls"]:
        parts = system_controller.list_partitions()
        print(f"\n{ANSI_BOLD}DISK PARTITIONS & MOUNTED STORAGE:{ANSI_RESET}")
        for p in parts:
            u_str = f"({p['usage']['free_gb']} GB free / {p['usage']['total_gb']} GB)" if p["usage"] else ""
            print(f" - {ANSI_CYAN}{p['device']}{ANSI_RESET} -> {p['mountpoint']} [{p['fstype']}] {u_str}")
        print()
    elif sub in ["mount"]:
        if len(args) < 2:
            print(f"{ANSI_RED}Usage: mount <device_path (e.g. /dev/sdb1)>{ANSI_RESET}")
            return
        res = system_controller.mount_device(args[1])
        print(f"{ANSI_GREEN}[Mount]{ANSI_RESET} {res.get('output') or res.get('message')}")
    elif sub in ["unmount", "umount"]:
        if len(args) < 2:
            print(f"{ANSI_RED}Usage: unmount <device_or_mountpoint>{ANSI_RESET}")
            return
        res = system_controller.unmount_device(args[1])
        print(f"{ANSI_GREEN}[Mount]{ANSI_RESET} {res.get('output') or res.get('message')}")

def handle_cpu_gov_cli(args):
    sub = args[0].lower() if args else "status"
    if sub == "status":
        gov = system_controller.get_cpu_governor()
        print(f"{ANSI_BOLD}CPU FREQUENCY GOVERNOR:{ANSI_RESET} {gov}")
    else:
        res = system_controller.set_cpu_governor(sub)
        print(f"{ANSI_GREEN}[CPU Governor]{ANSI_RESET} {res.get('message') or res.get('error')}")

def handle_disp_profile_cli(args):
    sub = args[0].lower() if args else "reading"
    res = system_controller.apply_display_profile(sub)
    if res.get("success"):
        print(f"{ANSI_GREEN}[Display Profile]{ANSI_RESET} Applied '{res['profile']}': {res['description']} ({res['brightness']}% luminance).")
    else:
        print(f"{ANSI_RED}[Display Profile]{ANSI_RESET} {res.get('error')}")

def handle_fan_cli(args):
    sub = args[0].lower() if args else "status"
    if sub == "status":
        res = system_controller.get_fan_speed()
        print(f"{ANSI_BOLD}COOLING FAN STATUS:{ANSI_RESET} {res.get('fans') or res.get('message')}")
    else:
        res = system_controller.set_fan_speed(sub)
        print(f"{ANSI_GREEN}[Fan Control]{ANSI_RESET} {res.get('message')}")

def handle_audio_cli(args):
    sub = args[0].lower() if args else "list"
    if sub in ["list", "ls"]:
        sinks = system_controller.list_audio_sinks()
        print(f"\n{ANSI_BOLD}AUDIO OUTPUT SINKS:{ANSI_RESET}")
        for s in sinks:
            print(f" - [{s['id']}] {s['name']}")
        print()
    elif sub == "set":
        if len(args) < 2:
            print(f"{ANSI_RED}Usage: audio set <sink_id_or_name>{ANSI_RESET}")
            return
        res = system_controller.set_audio_sink(args[1])
        print(f"{ANSI_GREEN}[Audio Route]{ANSI_RESET} {res.get('message') or res.get('error')}")

def handle_cam_cli(args):
    sub = args[0].lower() if args else "status"
    if sub == "status":
        st = vision_senses.get_current_state()
        print(f"\n{ANSI_BOLD}LOCAL WEBCAM BEHAVIORAL SENSES:{ANSI_RESET}")
        print(f" State:             {ANSI_GREEN}{st['state'].upper()}{ANSI_RESET} (Active for {st['duration_sec']}s)")
        print(f" Confidence:        {int(st['confidence'] * 100)}%")
        print(f" Background Worker: {'RUNNING' if st['is_running'] else 'STOPPED'}")
        print(f" Camera Hardware:   {'CONNECTED' if st['camera_available'] else 'NOT DETECTED / SIMULATED'}")
        if st['is_simulated']:
            print(f" Mode:              {ANSI_YELLOW}SIMULATION OVERRIDE ACTIVE{ANSI_RESET}")
        if st.get('metrics'):
            m = st['metrics']
            print(f" Metrics:           faces={m.get('faces', 0)}, tilt={m.get('tilt_angle', 0)}°, vertical_ratio={m.get('vertical_ratio', 0)}, jitter={m.get('jitter_streak', 0)}")
        print()
    elif sub in ["start", "on"]:
        res = vision_senses.start()
        print(f"{ANSI_GREEN}[Cam Senses]{ANSI_RESET} {res['message']}")
    elif sub in ["stop", "off"]:
        res = vision_senses.stop()
        print(f"{ANSI_YELLOW}[Cam Senses]{ANSI_RESET} {res['message']}")
    elif sub == "scan":
        print(f"{ANSI_CYAN}[Cam Senses] Performing immediate single-frame scan...{ANSI_RESET}")
        res = vision_senses.scan_once()
        if res.get("success"):
            print(f" Detected State: {ANSI_GREEN}{res['detected_state'].upper()}{ANSI_RESET} (confidence: {int(res['confidence']*100)}%)")
            print(f" Metrics:        {res.get('metrics')}")
        else:
            print(f"{ANSI_RED}Scan failed: {res.get('error')}{ANSI_RESET}")
    elif sub == "test":
        if len(args) < 2:
            print(f"{ANSI_RED}Usage: cam test <neutral | thinking | stressed | away | reset>{ANSI_RESET}")
            return
        res = vision_senses.simulate_state(args[1])
        print(f"{ANSI_GREEN}[Cam Senses]{ANSI_RESET} {res.get('message') or res.get('error')}")
    elif sub in ["interval", "throttle"]:
        if len(args) < 2:
            print(f"{ANSI_RED}Usage: cam interval <seconds (e.g. 2.5)>{ANSI_RESET}")
            return
        try:
            sec = float(args[1])
            vision_senses.set_sampling_interval(sec)
            print(f"{ANSI_GREEN}[Cam Senses]{ANSI_RESET} Sampling interval set to {vision_senses.sampling_interval}s.")
        except ValueError:
            print(f"{ANSI_RED}Invalid seconds value.{ANSI_RESET}")
    else:
        print(f"{ANSI_RED}Usage: cam [status | start | stop | scan | test <state> | interval <sec>]{ANSI_RESET}")

def handle_prayer_cli(args):
    sub = args[0].lower() if args else "times"
    if sub in ["times", "schedule", "today", "show", "list"]:
        print()
        print(prayer_engine.format_schedule_table())
        print()
    elif sub in ["next"]:
        p = prayer_engine.get_next_prayer()
        day = "tomorrow" if p["is_tomorrow"] else "today"
        print(f"\n{ANSI_GREEN}[Next Prayer]{ANSI_RESET} {p['name']} at {p['time_12h']} {day} ({p['countdown']} remaining).\n")
    elif sub in ["log", "history"]:
        logs = prayer_engine.get_prayer_log(limit=10)
        if not logs:
            print(f"{ANSI_GRAY}[Prayer] No prayer completions logged yet in persistent memory.{ANSI_RESET}")
            return
        print(f"\n{ANSI_BOLD}PRAYER COMPLETION HISTORY (PALAKKAD):{ANSI_RESET}")
        for l in logs:
            print(f" - {l['date']} {l['time']}: {ANSI_GREEN}{l['prayer']}{ANSI_RESET} [{l['status'].upper()}]")
        print()
    elif sub in ["check", "prompt"]:
        res = prayer_engine.check_prayer_prompt_needed()
        if res:
            print(f"\n{ANSI_CYAN}[Zia // Prayer Check-in]{ANSI_RESET} {res['prompt']}\n")
        else:
            next_p = prayer_engine.get_next_prayer()
            print(f"{ANSI_GRAY}[Prayer] No active prayer check-in required right now. Next prayer is {next_p['name']} at {next_p['time_12h']} ({next_p['countdown']} remaining).{ANSI_RESET}")
    elif sub in ["done", "prayed", "mark"]:
        prayer_name = args[1] if len(args) > 1 else None
        res = prayer_engine.record_prayer_status(prayer_name, status="completed")
        print(f"{ANSI_GREEN}[Prayer Logged]{ANSI_RESET} Recorded {res['prayer']} completion in persistent memory.")
    else:
        print(f"{ANSI_RED}Usage: prayer [times | next | log | check | done <prayer_name>]{ANSI_RESET}")

def handle_alarm_cli(args):
    sub = args[0].lower() if args else "list"
    if sub in ["list", "ls"]:
        active = alarm_manager.list_active()
        if not active:
            print(f"{ANSI_GRAY}[Alarms] No active alarms or timers. Set one: alarm set 8:00 pm OR timer 20m{ANSI_RESET}")
            return
        print(f"\n{ANSI_BOLD}ACTIVE ALARMS & TIMERS ({len(active)}):{ANSI_RESET}")
        for a in active:
            print(f" [{a['id']}] {a['type'].upper()}: '{a['label']}' -> Rings at {a['target_time_str']} (in {a['countdown']})")
        print()
    elif sub == "set":
        if len(args) < 2:
            print(f"{ANSI_RED}Usage: alarm set <time (e.g. 8:00 pm, 07:30)> [label]{ANSI_RESET}")
            return
        time_str = args[1]
        label = " ".join(args[2:]) if len(args) > 2 else "Alarm"
        res = alarm_manager.set_alarm(time_str, label)
        if res.get("success"):
            print(f"{ANSI_GREEN}[Alarm]{ANSI_RESET} {res['message']}")
        else:
            print(f"{ANSI_RED}[Alarm] {res.get('error')}{ANSI_RESET}")
    elif sub in ["cancel", "rm", "del"]:
        if len(args) < 2:
            print(f"{ANSI_RED}Usage: alarm cancel <alarm_id>{ANSI_RESET}")
            return
        res = alarm_manager.cancel(args[1])
        print(f"{ANSI_GREEN}[Alarm]{ANSI_RESET} {res.get('message') or res.get('error')}")
    else:
        # Try natural language parsing directly
        res = alarm_manager.parse_natural_language(" ".join(args))
        if res:
            print(f"{ANSI_GREEN}[Alarm]{ANSI_RESET} {res['message']}")
        else:
            print(f"{ANSI_RED}Usage: alarm [list | set <time> [label] | cancel <id>]{ANSI_RESET}")

def handle_timer_cli(args):
    if not args or args[0].lower() in ["list", "ls"]:
        handle_alarm_cli(["list"])
        return
    if args[0].lower() in ["cancel", "rm", "del"]:
        handle_alarm_cli(args)
        return

    # Parse e.g. "timer 20m push code"
    res = alarm_manager.parse_natural_language("timer " + " ".join(args))
    if res:
        print(f"{ANSI_GREEN}[Timer]{ANSI_RESET} {res['message']}")
    else:
        print(f"{ANSI_RED}Usage: timer <duration (e.g. 20m, 30s, 1h)> [label]{ANSI_RESET}")

def handle_mac_rpc_cli(args):
    sub = args[0].lower() if args else "status"
    if sub in ["status", "ping"]:
        online = rpc_bridge.is_mac_online()
        state = f"{ANSI_GREEN}ONLINE{ANSI_RESET}" if online else f"{ANSI_RED}OFFLINE / UNREACHABLE{ANSI_RESET}"
        print(f"\n{ANSI_BOLD}REMOTE MACBOOK RPC STATUS:{ANSI_RESET}")
        print(f" Target Host:       http://{rpc_bridge.mac_host}:{rpc_bridge.mac_port}")
        print(f" Connection:        {state}")
        print(f" Last Communicated: {int(time.time() - rpc_bridge.last_seen)}s ago" if rpc_bridge.last_seen > 0 else " Never")
        print()
    elif sub in ["health", "diag"]:
        res = rpc_bridge.get_remote_mac_health()
        if "error" in res:
            print(f"{ANSI_RED}[RPC Error] {res['error']}{ANSI_RESET}")
            return
        print(f"\n{ANSI_BOLD}REMOTE MACBOOK HEALTH DIAGNOSTICS:{ANSI_RESET}")
        print(f" Device:      {res.get('device', 'MacBook Pro')}")
        print(f" CPU Usage:   {res.get('cpu_percent')}%")
        if res.get('cpu_temp_c'):
            print(f" Core Temp:   {res.get('cpu_temp_c')}°C")
        if res.get('ram_percent'):
            print(f" RAM Usage:   {res.get('ram_percent')}% ({res.get('ram_used_mb')}/{res.get('ram_total_mb')} MB)")
        if 'battery_percent' in res:
            plugged = " (Charging)" if res.get('power_plugged') else " (Battery)"
            print(f" Battery:     {res.get('battery_percent')}%{plugged}")
        print()
    elif sub in ["exec", "run"]:
        if len(args) < 2:
            print(f"{ANSI_RED}Usage: mac exec <command_to_run_on_macbook>{ANSI_RESET}")
            return
        cmd = " ".join(args[1:])
        print(f"{ANSI_GRAY}[Dispatching command to remote MacBook via RPC...]{ANSI_RESET}")
        res = rpc_bridge.execute_remote_command(cmd)
        if res.get("stdout"):
            print(res["stdout"])
        if res.get("stderr"):
            print(f"{ANSI_RED}{res['stderr']}{ANSI_RESET}")
        if not res.get("success") and "error" in res:
            print(f"{ANSI_RED}{res['error']}{ANSI_RESET}")
    elif sub in ["notify", "alert"]:
        if len(args) < 2:
            print(f"{ANSI_RED}Usage: mac notify <message>{ANSI_RESET}")
            return
        msg = " ".join(args[1:])
        res = rpc_bridge.send_remote_notification("Project Zia", msg)
        print(f"{ANSI_GREEN}[MacAgent]{ANSI_RESET} Dispatched notification to MacBook screen: {res}")
    elif sub in ["vol", "volume"]:
        action = args[1].lower() if len(args) > 1 else "up"
        res = rpc_bridge.remote_volume(action)
        print(f"{ANSI_GREEN}[MacAgent]{ANSI_RESET} Set MacBook volume: {action}")
    elif sub == "lock":
        res = rpc_bridge.remote_lock_session()
        print(f"{ANSI_GREEN}[MacAgent]{ANSI_RESET} Locked remote MacBook desktop session.")
    elif sub in ["target", "set"]:
        if len(args) < 2:
            print(f"{ANSI_RED}Usage: mac target <ip_address> [port]{ANSI_RESET}")
            return
        host = args[1]
        port = int(args[2]) if len(args) > 2 else 5001
        rpc_bridge.register_client(host, port)
    else:
        print(f"{ANSI_RED}Usage: mac [status | health | exec <cmd> | notify <msg> | vol <up/down> | lock | target <ip>]{ANSI_RESET}")

def handle_audio_bridge_cli(args):
    sub = args[0].lower() if args else "status"
    if sub == "status":
        st = audio_bridge.get_hardware_status()
        print(f"\n{ANSI_BOLD}ANDROID / XPERIA AUDIO BRIDGE STATUS:{ANSI_RESET}")
        print(f" Environment:        {'Android Termux' if st['is_termux'] else 'Desktop / Fallback'}")
        print(f" Termux Mic API:     {'READY' if st['has_termux_mic'] else 'NOT DETECTED'}")
        print(f" Termux TTS Output:  {'READY' if st['has_termux_tts'] else 'NOT DETECTED'}")
        print(f" Termux Media Player:{'READY' if st['has_termux_media'] else 'NOT DETECTED'}")
        print()
    elif sub in ["listen", "record"]:
        sec = int(args[1]) if len(args) > 1 and args[1].isdigit() else 5
        print(f"{ANSI_CYAN}[AudioBridge] Recording {sec}s ambient room audio from Xperia microphones...{ANSI_RESET}")
        res = audio_bridge.record_room_audio(duration_sec=sec)
        if res.get("success"):
            print(f"{ANSI_GREEN}[AudioBridge]{ANSI_RESET} Recorded to {res['file']} (Backend: {res.get('backend')})")
        else:
            print(f"{ANSI_RED}[AudioBridge] {res.get('error')}{ANSI_RESET}")
    elif sub in ["speak", "say"]:
        if len(args) < 2:
            print(f"{ANSI_RED}Usage: xperia speak <text_to_speak_out_loud>{ANSI_RESET}")
            return
        phrase = " ".join(args[1:])
        res = audio_bridge.speak(phrase)
        print(f"{ANSI_GREEN}[AudioBridge]{ANSI_RESET} Playing on Xperia speakers (Backend: {res.get('backend')})")
    else:
        print(f"{ANSI_RED}Usage: xperia [status | listen [sec] | speak <text>]{ANSI_RESET}")

def handle_agentic_ops_cli(cmd: str, args: list):
    if cmd == "plan":
        goal = " ".join(args) if args else "Develop and test new Project Zia features"
        print(agentic_ops.visualize_plan(goal))
    elif cmd == "review":
        target = args[0] if args else "cli.py"
        res = agentic_ops.review_code_snippet(target)
        status_color = ANSI_GREEN if res.get("status") == "PASSED" else ANSI_YELLOW
        print(f"\n{ANSI_BOLD}CODE REVIEW FOR: {target}{ANSI_RESET}")
        print(f" Status: {status_color}{res.get('status')}{ANSI_RESET} | Warnings: {res.get('warnings_count')}")
        for w in res.get("warnings", []):
            print(f"  - {w}")
        print()
    elif cmd == "testgen":
        target = args[0] if args else "engine/prayer_times.py"
        res = agentic_ops.generate_unit_tests(target)
        if "error" in res:
            print(f"{ANSI_RED}{res['error']}{ANSI_RESET}")
        else:
            print(f"{ANSI_GREEN}Generated test file: {res.get('test_file_path')}{ANSI_RESET}")
            print(f"{ANSI_GRAY}Functions found: {res.get('functions_found')}{ANSI_RESET}")
            print(f"{ANSI_GRAY}Classes found: {res.get('classes_found')}{ANSI_RESET}")
    elif cmd == "qtask":
        if len(args) < 2:
            print(f"{ANSI_RED}Usage: qtask <role> <task description>{ANSI_RESET}")
            return
        task_id = agentic_ops.enqueue_task(args[0], " ".join(args[1:]))
        print(f"{ANSI_GREEN}[Queue] Enqueued task '{task_id}' (status: pending, role: {args[0]}){ANSI_RESET}")
    elif cmd == "qprocess":
        count = agentic_ops.process_pending_queue()
        print(f"{ANSI_GREEN}[Queue] Processed {count} pending tasks.{ANSI_RESET}")
    elif cmd == "budget":
        b = agentic_ops.token_usage_tracker
        print(f"\n{ANSI_BOLD}GEMINI API TOKEN BUDGET REPORT:{ANSI_RESET}")
        print(f" Total Prompt Tokens:    {b['total_prompt_tokens']}")
        print(f" Total Candidate Tokens: {b['total_candidate_tokens']}")
        print(f" Estimated Spend (USD):  ${b['estimated_cost_usd']:.5f}")
        print(f" Safety Budget Cap:      {agentic_ops.token_budget_limit} tokens")
        print()
    elif cmd == "ocr":
        if not args:
            print(f"{ANSI_RED}Usage: ocr <image_path>{ANSI_RESET}")
            return
        res = agentic_ops.extract_text_local_ocr(args[0])
        print(f"\n{ANSI_BOLD}LOCAL OCR EXTRACTED TEXT ({res.get('engine')}):{ANSI_RESET}")
        print(res.get("text", "(No text detected)"))
        print()
    elif cmd == "docs":
        if not args:
            print(f"{ANSI_RED}Usage: docs <url> [tag]{ANSI_RESET}")
            return
        tag = args[1] if len(args) > 1 else "latest"
        res = agentic_ops.fetch_and_cache_docs(args[0], tag)
        print(f"{ANSI_GREEN}[Docs] Cached to {res.get('cached_file')}{ANSI_RESET}")
    elif cmd == "deps":
        target = args[0] if args else "server.py"
        res = agentic_ops.scan_missing_dependencies(target)
        print(f"\n{ANSI_BOLD}DEPENDENCY SCAN FOR {target}:{ANSI_RESET}")
        print(f" Missing imports: {res.get('missing_imports', [])}")
        print(f" Required installs: {res.get('recommended_pip_installs', [])}")
        print()

def handle_ecosystem_cli(cmd: str, args: list):
    if cmd == "drop":
        sub = args[0].lower() if args else "list"
        if sub == "send" and len(args) > 1:
            fpath = args[1]
            remote_url = args[2] if len(args) > 2 else "http://127.0.0.1:5000"
            res = ecosystem_bridge.send_file_to_remote(fpath, remote_url)
            print(f"{ANSI_GREEN}[Drop] {res}{ANSI_RESET}")
        else:
            files = ecosystem_bridge.list_received_files()
            print(f"\n{ANSI_BOLD}LOCAL AIRDROP RECEIVED FILES ({len(files)}):{ANSI_RESET}")
            for f in files:
                print(f" |-- {f['name']} ({f['size_kb']} KB, {f['date']})")
            print()
    elif cmd == "battery":
        bat = ecosystem_bridge.get_mirrored_battery_status()
        print(f"\n{ANSI_BOLD}REMOTE / LOCAL BATTERY STATUS:{ANSI_RESET}")
        print(f" Node:    {bat.get('device')}")
        print(f" Battery: {bat.get('percent')}% ({'Plugged In' if bat.get('plugged') else 'Discharging'})")
        print(f" Thermal: {bat.get('thermal_status')}")
        print()
    elif cmd == "route":
        dest = args[0] if args else "phone"
        res = ecosystem_bridge.set_audio_route(dest)
        print(f"{ANSI_GREEN}[AudioRoute] {res.get('message')}{ANSI_RESET}")
    elif cmd == "wol":
        mac = args[0] if args else "00:11:22:33:44:55"
        res = ecosystem_bridge.send_wake_on_lan(mac)
        print(f"{ANSI_GREEN}[Wake-on-LAN] Sent Magic Packet to {mac}{ANSI_RESET}")
    elif cmd == "pinglan":
        host = args[0] if args else "127.0.0.1"
        res = ecosystem_bridge.measure_network_latency(host)
        print(f"{ANSI_GREEN}[PingWatchdog] Host: {host} | Latency: {res.get('latency_ms')} ms | Quality: {res.get('link_quality')}{ANSI_RESET}")
    elif cmd == "camstream":
        res = ecosystem_bridge.capture_remote_camera_frame()
        print(f"{ANSI_GREEN}[CamStream] Frame captured: {res}{ANSI_RESET}")
    elif cmd == "dashboard":
        print(f"{ANSI_CYAN}[Dashboard] Web Dashboard online at http://127.0.0.1:5000/dashboard{ANSI_RESET}")

def handle_security_cli(cmd: str, args: list):
    if cmd == "incognito":
        sub = args[0].lower() if args else "toggle"
        if sub in ["on", "true", "1"]:
            val = security_vault.toggle_incognito(True)
        elif sub in ["off", "false", "0"]:
            val = security_vault.toggle_incognito(False)
        else:
            val = security_vault.toggle_incognito()
        status = f"{ANSI_YELLOW}ACTIVE (Zero trace mode){ANSI_RESET}" if val else f"{ANSI_GREEN}DISABLED (Normal logging){ANSI_RESET}"
        print(f"{ANSI_BOLD}[Security] Ephemeral Incognito Mode: {status}")
    elif cmd == "fim":
        sub = args[0].lower() if args else "check"
        if sub == "update":
            res = security_vault.update_fim_baseline()
            print(f"{ANSI_GREEN}[FIM] Updated SHA-256 baseline for {len(res.get('monitored_files', []))} files.{ANSI_RESET}")
        else:
            res = security_vault.check_fim_integrity()
            status_color = ANSI_GREEN if res.get("is_intact") else ANSI_RED
            print(f"\n{ANSI_BOLD}FILE INTEGRITY AUDIT REPORT:{ANSI_RESET}")
            print(f" Status: {status_color}{res.get('status')}{ANSI_RESET}")
            print(f" Verified Files: {res.get('verified_count')}")
            if res.get("tampered_files"):
                print(f" {ANSI_RED}Tampered / Deleted:{ANSI_RESET} {res.get('tampered_files')}")
            print()
    elif cmd == "ports":
        res = security_vault.audit_exposed_ports()
        print(f"\n{ANSI_BOLD}EXPOSED PORT AUDITOR ({res.get('status')}):{ANSI_RESET}")
        print(f" Total Listeners: {res.get('total_listeners')} | Public Exposed (0.0.0.0): {res.get('public_exposed_count')}")
        for l in res.get("listeners", []):
            pub = f"{ANSI_RED}[PUBLIC]{ANSI_RESET}" if l.get("is_publicly_exposed") else f"{ANSI_GREEN}[LOCAL]{ANSI_RESET}"
            print(f"  {pub} {l.get('ip')}:{l.get('port')} (PID: {l.get('pid')})")
        print()
    elif cmd == "sslcert":
        host = args[0] if args else "google.com"
        res = security_vault.check_ssl_cert_expiry(host)
        print(f"\n{ANSI_BOLD}SSL CERTIFICATE AUDIT:{ANSI_RESET}")
        print(f" Host: {res.get('host')} | Days Remaining: {res.get('days_remaining')} | Status: {res.get('status')}")
        print(f" Expiry: {res.get('expires')}")
        print()
    elif cmd == "secscan":
        target = args[0] if args else None
        res = security_vault.scan_codebase_for_leaked_credentials(target)
        if not res:
            print(f"{ANSI_GREEN}[SecScan] Zero leaked credentials or secrets found in codebase.{ANSI_RESET}")
        else:
            print(f"{ANSI_RED}[SecScan] ALERT: Leaked secrets detected!{ANSI_RESET}")
            for item in res:
                print(f"  File: {item['file']}:{item['line']} -> {item['matched_secret']}")
    elif cmd == "tunnel":
        user = args[0] if len(args) > 0 else "user"
        host = args[1] if len(args) > 1 else "remote.server.com"
        cmd_str = security_vault.generate_ssh_tunnel_command(user, host)
        print(f"{ANSI_CYAN}[SSH Tunnel] Generated reverse tunnel command:{ANSI_RESET}")
        print(f"  {cmd_str}")

def handle_ambient_cli(cmd: str, args: list):
    if cmd == "weather":
        lat = float(args[0]) if len(args) > 0 else 10.7867
        lon = float(args[1]) if len(args) > 1 else 76.6548
        res = ambient_engine.get_weather_greeting(lat, lon)
        print(f"\n{ANSI_BOLD}WEATHER ADAPTIVE GREETER ({res.get('location')}):{ANSI_RESET}")
        print(f" {res.get('greeting')}")
        print(f" Temperature: {res.get('temperature_c')}°C | Condition: {res.get('condition')}")
        print()
    elif cmd == "chime":
        stype = args[0] if args else "notification"
        p = ambient_engine.synthesize_chime(stype)
        print(f"{ANSI_GREEN}[Soundboard] Synthesized retro chime '{stype}' at {p}{ANSI_RESET}")
    elif cmd == "focus":
        action = args[0] if args else "toggle"
        res = ambient_engine.toggle_focus_mode(action)
        print(f"{ANSI_GREEN}[FocusMode] {res.get('message')}{ANSI_RESET}")
        if res.get("recommended_command"):
            print(f"{ANSI_GRAY}Audio Stream: {res.get('recommended_command')}{ANSI_RESET}")
    elif cmd == "conflict":
        if not args:
            print(f"{ANSI_RED}Usage: conflict <HH:MM> [duration_min]{ANSI_RESET}")
            return
        dur = int(args[1]) if len(args) > 1 and args[1].isdigit() else 30
        res = ambient_engine.check_prayer_meeting_conflict(args[0], dur)
        print(f"\n{ANSI_BOLD}MEETING / PRAYER CONFLICT RESOLUTION:{ANSI_RESET}")
        print(f" Has Conflict: {res.get('has_conflict')}")
        print(f" Recommendation: {res.get('recommendation')}")
        for c in res.get("conflicts", []):
            print(f"  - Overlaps with {c['prayer']} ({c['prayer_time']}) in window {c['conflict_window']}")
        print()
    elif cmd == "digest":
        res = ambient_engine.compile_daily_digest()
        print(f"\n{ANSI_BOLD}DAILY DEVELOPER DIGEST REPORT ({res.get('date')}):{ANSI_RESET}")
        print(f" Git Commits Today: {res.get('commits_today_count')}")
        for c in res.get("commits", []):
            print(f"   * {c}")
        print(f" Active Alarms: {res.get('active_alarms_count')}")
        print(f" Prayer Times Logged: {len(res.get('prayer_schedule', {}))} slots active")
        print()
    elif cmd == "presence":
        res = ambient_engine.check_presence()
        print(f"{ANSI_GREEN}[Presence] State: {res.get('state')} (Gateway: {res.get('gateway_tested')}){ANSI_RESET}")
    elif cmd == "theme":
        if not args:
            t = ambient_engine.get_theme()
            print(f"{ANSI_CYAN}Current Theme: {t['name']}{ANSI_RESET}")
            return
        res = ambient_engine.set_theme(args[0])
        print(f"{ANSI_GREEN}[Theme] {res}{ANSI_RESET}")
    elif cmd == "habit":
        sub = args[0].lower() if args else "streaks"
        if sub == "log" and len(args) > 1:
            res = ambient_engine.log_habit(args[1])
            print(f"{ANSI_GREEN}[Habit] {res}{ANSI_RESET}")
        else:
            streaks = ambient_engine.get_habit_streaks()
            print(f"\n{ANSI_BOLD}SMART HABIT STREAK REPORT:{ANSI_RESET}")
            for h, info in streaks.items():
                print(f" |-- {h.upper()}: Streak: {info.get('streak')} days | Last: {info.get('last_date')} | Total: {info.get('total')}")
            print()
    elif cmd == "macro":
        if not args:
            print(f"{ANSI_RED}Usage: macro <single_word_trigger>{ANSI_RESET}")
            return
        res = ambient_engine.execute_shortcut(args[0])
        if res.get("found"):
            print(f"{ANSI_GREEN}[Macro] Executing shortcut '{args[0]}':{ANSI_RESET}")
            for step in res.get("steps", []):
                print(f"  -> Executing: {step}")
                process_command(step)
        else:
            print(f"{ANSI_RED}{res.get('message')}{ANSI_RESET}")

def handle_lifedesk_cli(cmd: str, args: list):
    """LifeDesk SQLite connector for habits and personal finance."""
    sub = args[0].lower() if args else "summary"
    if cmd in ["lifedesk", "expense", "expenses"]:
        if sub in ["summary", "status"] or not args:
            summary = lifedesk_bridge.get_financial_summary()
            print(f"\n{ANSI_BOLD}LIFEDESK FINANCIAL SUMMARY:{ANSI_RESET}")
            print(f" Total Expenses: Rs. {summary.get('total_expenses', 0):.2f}")
            print(f" Total Income:   Rs. {summary.get('total_income', 0):.2f}")
            print(f" Net Balance:    Rs. {summary.get('net_balance', 0):.2f}")
            breakdown = summary.get("categories", {})
            if breakdown:
                print(f"{ANSI_GRAY}Top Categories:{ANSI_RESET}")
                for cat, val in breakdown.items():
                    print(f"  - {cat}: Rs. {val:.2f}")
            print()
        elif sub == "log":
            if len(args) < 3:
                print(f"{ANSI_RED}Usage: expense log <amount> <category> [description]{ANSI_RESET}")
                return
            try:
                amt = float(args[1])
                cat = args[2]
                desc = " ".join(args[3:]) if len(args) > 3 else ""
                res = lifedesk_bridge.log_expense(amt, cat, desc)
                print(f"{ANSI_GREEN}[LifeDesk]{ANSI_RESET} Logged Rs. {amt:.2f} under '{cat}'.")
            except ValueError:
                print(f"{ANSI_RED}Invalid amount specified.{ANSI_RESET}")
        elif sub in ["list", "daily"]:
            daily = lifedesk_bridge.get_daily_expenses()
            print(f"\n{ANSI_BOLD}TODAY'S EXPENSES:{ANSI_RESET} Total: Rs. {daily.get('total', 0):.2f}")
            txs = daily.get("transactions", [])
            for tx in txs:
                print(f" - Rs. {tx['amount']:.2f} [{tx['category']}] {tx['description']}")
            print()
    elif cmd in ["habit", "habits"]:
        if sub in ["streaks", "list"] or not args:
            streaks = lifedesk_bridge.get_habit_streaks()
            print(f"\n{ANSI_BOLD}LIFEDESK HABIT STREAKS:{ANSI_RESET}")
            for h in streaks:
                h_name = h.get("name") or h.get("habit") or "Habit"
                cur_str = h.get("current_streak", h.get("streak", 0))
                best = h.get("longest_streak", cur_str)
                status = f"{ANSI_GREEN}DONE TODAY{ANSI_RESET}" if h.get("logged_today") else f"{ANSI_YELLOW}PENDING{ANSI_RESET}"
                print(f" - {h_name.capitalize()}: {cur_str} day streak (Best: {best}) [{status}]")
            print()
        elif sub == "log":
            if len(args) < 2:
                print(f"{ANSI_RED}Usage: habit log <name> [duration_min] [note]{ANSI_RESET}")
                return
            name = args[1]
            val = 1.0
            note = ""
            if len(args) > 2:
                try:
                    val = float(args[2])
                    note = " ".join(args[3:]) if len(args) > 3 else ""
                except ValueError:
                    note = " ".join(args[2:])
            res = lifedesk_bridge.log_habit(name, value=val, note=note)
            print(f"{ANSI_GREEN}[LifeDesk]{ANSI_RESET} {res.get('message', 'Habit logged.')}")

def handle_telegram_cli(args: list):
    """Remote Telegram Gateway CLI."""
    sub = args[0].lower() if args else "status"
    if sub == "status":
        st = telegram_gateway.get_status()
        cfg = f"{ANSI_GREEN}CONFIGURED{ANSI_RESET}" if st.get("configured") else f"{ANSI_YELLOW}NOT CONFIGURED{ANSI_RESET}"
        run_st = f"{ANSI_GREEN}POLLING ACTIVE{ANSI_RESET}" if st.get("running") else f"{ANSI_GRAY}IDLE{ANSI_RESET}"
        print(f"\n{ANSI_BOLD}TELEGRAM REMOTE GATEWAY:{ANSI_RESET} [{cfg}] [{run_st}]")
        print(f" Chat ID: {st.get('chat_id_set')} | Bot Token: {st.get('bot_token_set')}")
        print()
    elif sub == "send":
        if len(args) < 2:
            print(f"{ANSI_RED}Usage: tg send <message>{ANSI_RESET}")
            return
        msg = " ".join(args[1:])
        res = telegram_gateway.send_message(msg)
        if res.get("success"):
            print(f"{ANSI_GREEN}[Telegram]{ANSI_RESET} Message sent successfully.")
        else:
            print(f"{ANSI_RED}[Telegram Error]{ANSI_RESET} {res.get('error')}")
    elif sub == "voice":
        if len(args) < 2:
            print(f"{ANSI_RED}Usage: tg voice <text_to_speak>{ANSI_RESET}")
            return
        text = " ".join(args[1:])
        print(f"{ANSI_CYAN}[Telegram]{ANSI_RESET} Synthesizing Edge-TTS voice note...")
        res = telegram_gateway.send_voice_note(text)
        if res.get("success"):
            print(f"{ANSI_GREEN}[Telegram]{ANSI_RESET} Voice note sent successfully.")
        else:
            print(f"{ANSI_RED}[Telegram Error]{ANSI_RESET} {res.get('error')}")

def handle_iot_cli(cmd: str, args: list):
    """Smart Home & Wireless ADB CLI."""
    if cmd == "projector":
        url = args[0] if args else "https://miruro.tv"
        print(f"{ANSI_CYAN}[IoT/ADB]{ANSI_RESET} Launching stream intent on projector: {url}")
        res = iot_bridge.launch_projector_stream(url)
        print(f"{ANSI_GREEN}[Projector]{ANSI_RESET} {res.get('status') or res}")
    elif cmd == "botim":
        contact = " ".join(args) if args else "Family"
        print(f"{ANSI_CYAN}[IoT/ADB]{ANSI_RESET} Triggering Botim VoIP call to {contact} on Android tablet...")
        res = iot_bridge.trigger_botim_call(contact)
        print(f"{ANSI_GREEN}[Botim]{ANSI_RESET} {res.get('status') or res}")
    elif cmd == "relay":
        if len(args) < 2:
            print(f"{ANSI_RED}Usage: relay <desk_lamp|ceiling_fan> <on|off|toggle>{ANSI_RESET}")
            return
        device = args[0]
        action = args[1]
        res = iot_bridge.control_relay(device, action)
        print(f"{ANSI_GREEN}[Relay]{ANSI_RESET} {res.get('message') or res}")

def process_command(cmd_line: str):
    cmd_line = cmd_line.strip()
    if not cmd_line:
        return

    parts = cmd_line.split()
    cmd = parts[0].lower()
    args = parts[1:]

    if cmd in ["exit", "quit", "q"]:
        print(f"{ANSI_GRAY}Exiting Project Zia CLI. Goodbye.{ANSI_RESET}")
        sys.exit(0)

    if cmd == "help":
        print_help()
        return

    # Terminal Avatar (ANSI 24 FPS / Retro graphics)
    if cmd in ["avatar", "ascii"]:
        handle_avatar_cli(args)
        return

    # Offline Speech-to-Text
    if cmd in ["listen", "voice"]:
        handle_stt_cli(["listen"] + args)
        return

    if cmd == "stt":
        handle_stt_cli(args)
        return

    # Background Wake-Word Detection
    if cmd in ["wakeword", "wake"]:
        handle_wakeword_cli(args)
        return

    # Bluetooth
    if cmd in ["bt", "bluetooth"]:
        handle_bluetooth_cli(args)
        return

    # Subagents
    if cmd in ["agent", "agents", "subagent"]:
        handle_subagent_cli(args)
        return

    # System
    if cmd == "sys":
        handle_sys_cli(args)
        return

    # Terminal command execution
    if cmd in ["run", "exec"]:
        raw = " ".join(args)
        res = system_controller.execute_terminal(raw, run_as_admin=False)
        print(res.get("output", ""))
        if res.get("returncode", 0) != 0:
            error_debugger.record_failure(raw, res.get("output", ""), res.get("returncode", 1))
            print(f"{ANSI_GRAY}[Debug Hint] Command failed (exit code {res.get('returncode')}). Type 'debug' for AI diagnosis and code fix.{ANSI_RESET}")
        return

    if cmd in ["sudo", "admin"]:
        raw = " ".join(args)
        res = system_controller.execute_terminal(raw, run_as_admin=True)
        print(res.get("output", ""))
        if res.get("returncode", 0) != 0:
            error_debugger.record_failure(raw, res.get("output", ""), res.get("returncode", 1))
            print(f"{ANSI_GRAY}[Debug Hint] Root command failed (exit code {res.get('returncode')}). Type 'debug' for AI diagnosis and code fix.{ANSI_RESET}")
        return

    # Error Traceback Debugger
    if cmd == "debug":
        handle_debug_cli(args)
        return

    # Multimodal Screen Vision Analysis
    if cmd in ["vision", "look", "screen"]:
        handle_vision_cli(args)
        return

    # Natural Language to Shell Compiler
    if cmd in ["cmd", "compile", "how"]:
        handle_compiler_cli(args)
        return

    # Local Webcam Behavioral Senses
    if cmd in ["cam", "webcam"]:
        handle_cam_cli(args)
        return

    # Encrypted Credential Vault
    if cmd == "vault":
        handle_vault_cli(args)
        return

    # Automated Cron & Task Scheduler
    if cmd in ["schedule", "cron"]:
        handle_schedule_cli(args)
        return

    # Network Traffic & Bandwidth Sentinel
    if cmd in ["net", "network"]:
        handle_net_cli(args)
        return

    # Multi-Device Clipboard Sync
    if cmd in ["clip", "clipboard"]:
        handle_clip_cli(args)
        return

    # Partition & Storage Mount Manager
    if cmd in ["mount", "unmount", "umount"]:
        if cmd in ["unmount", "umount"]:
            handle_mount_cli(["unmount"] + args)
        else:
            handle_mount_cli(args)
        return

    # CPU Frequency Governor Switcher
    if cmd == "cpu":
        sub_args = args[1:] if args and args[0].lower() in ["gov", "governor"] else args
        handle_cpu_gov_cli(sub_args)
        return

    # Backlight & Display Calibration Profiles
    if cmd in ["disp", "display"]:
        sub_args = args[1:] if args and args[0].lower() == "profile" else args
        handle_disp_profile_cli(sub_args)
        return

    # Cooling Fan Manual Override
    if cmd == "fan":
        handle_fan_cli(args)
        return

    # Audio Sink / Route Switcher
    if cmd in ["audio", "sound", "sink"]:
        handle_audio_cli(args)
        return

    # Islamic Prayer Times & Daily Check-in (Palakkad, Kerala)
    if cmd in ["prayer", "namaz", "salat"]:
        handle_prayer_cli(args)
        return

    # Natural Language Alarms & Timers
    if cmd in ["alarm", "alarms"]:
        handle_alarm_cli(args)
        return

    if cmd in ["timer", "timers"]:
        handle_timer_cli(args)
        return

    # Remote MacBook Control via JSON-RPC Bridge
    if cmd in ["mac", "macbook"]:
        handle_mac_rpc_cli(args)
        return

    # Android / Xperia Audio Bridge (Room Listening & Physical Speakers)
    if cmd in ["xperia", "phone"]:
        handle_audio_bridge_cli(args)
        return

    # MCP file reading
    if cmd == "mcp":
        sub = args[0].lower() if args else "list"
        if sub == "read" and len(args) > 1:
            res = mcp_gateway.read_file(args[1])
            if "error" in res:
                print(f"{ANSI_RED}{res['error']}{ANSI_RESET}")
            else:
                print(f"{ANSI_GRAY}--- {args[1]} ({res['lines_returned']} lines) ---{ANSI_RESET}")
                print(res["content"])
        elif sub == "search" and len(args) > 1:
            res = mcp_gateway.search_code(" ".join(args[1:]))
            for m in res.get("matches", []):
                print(f" {ANSI_CYAN}{m['file']}:{m['line']}{ANSI_RESET} {m['text']}")
        elif sub == "ls":
            dpath = args[1] if len(args) > 1 else "."
            res = mcp_gateway.list_directory(dpath)
            for item in res.get("items", []):
                prefix = "[DIR] " if item["is_dir"] else "[FILE]"
                print(f" {prefix} {item['name']}")
        return

    # File Organization
    if cmd in ["organize", "organise"]:
        loc = args[0] if args else "downloads"
        res = local_router.organize_directory(loc)
        print(f"{ANSI_GREEN}[Zia]{ANSI_RESET} {res['text']}")
        return

    # IoT Bridge
    if cmd == "iot":
        action = args[0] if args else "toggle"
        import asyncio
        res = asyncio.run(iot_bridge.send_command(action))
        status = f"{ANSI_GREEN}SUCCESS{ANSI_RESET}" if res.get("success") else f"{ANSI_RED}FAILED{ANSI_RESET}"
        print(f"[{status}] Sent '{action}' to IoT relay at {res.get('ip')}")
        return

    # Memory
    if cmd in ["mem", "memory"]:
        sub = args[0].lower() if args else "show"
        if sub == "show":
            print(f"\n{ANSI_BOLD}PERSISTENT MEMORY CONTEXT:{ANSI_RESET}")
            print(memory_engine.get_memory_context())
            print()
        elif sub == "note" and len(args) > 1:
            note = " ".join(args[1:])
            memory_engine.add_note(note)
            print(f"{ANSI_GREEN}[Memory]{ANSI_RESET} Saved note: '{note}'")
        return

    # Category 1: Advanced Agentic Operations
    if cmd in ["plan", "review", "testgen", "qtask", "qprocess", "budget", "ocr", "docs", "deps"]:
        handle_agentic_ops_cli(cmd, args)
        return

    # Category 2: Cross-Device Ecosystem & Remote Bridge
    if cmd in ["drop", "battery", "route", "wol", "pinglan", "camstream", "dashboard"]:
        handle_ecosystem_cli(cmd, args)
        return

    # Category 3: Security, Privacy & Cryptography
    if cmd in ["incognito", "fim", "ports", "sslcert", "secscan", "tunnel"]:
        handle_security_cli(cmd, args)
        return

    # Category 4: Smart Notifications & Ambient Intelligence
    if cmd in ["weather", "chime", "focus", "conflict", "digest", "presence", "theme", "macro"]:
        handle_ambient_cli(cmd, args)
        return

    # Category 5: LifeDesk Database Bridge (Habits & Expenses)
    if cmd in ["lifedesk", "expense", "expenses", "habit", "habits"]:
        handle_lifedesk_cli(cmd, args)
        return

    # Category 6: Remote Telegram Gateway
    if cmd in ["telegram", "tg"]:
        handle_telegram_cli(args)
        return

    # Category 7: Smart IoT & Wireless ADB Bridges
    if cmd in ["projector", "botim", "relay"]:
        handle_iot_cli(cmd, args)
        return

    # 1. Try Fast Local Command Router (0 LLM Tokens)
    local_match = local_router.match_and_execute(cmd_line)
    if local_match:
        terminal_avatar.active_expression = local_match.get("mood", "F1")
        print(f"{ANSI_GREEN}[Zia]{ANSI_RESET} {local_match['text']}")
        return

    # 2. Direct Gemini Brain Query (Text Only, No Audio/Speech)
    print(f"{ANSI_GRAY}[Thinking...]{ANSI_RESET}", end="\r")
    import asyncio
    active_win = None
    try:
        from engine.senses import screen_sensor
        active_win = screen_sensor.get_active_window_title()
    except Exception:
        pass

    prompt = cmd_line.replace("chat ", "").strip()
    reply = asyncio.run(brain_engine.think_and_reply(user_message=prompt, active_window=active_win))
    terminal_avatar.active_expression = reply.get("mood", "F1")
    print(f"\r{ANSI_CYAN}[Zia // {reply['mood']}]{ANSI_RESET} {reply['text']}\n")

def main():
    # If arguments were passed directly on CLI (e.g., `python cli.py sys health`)
    if len(sys.argv) > 1:
        process_command(" ".join(sys.argv[1:]))
        return

    print_banner()

    # Interactive REPL
    while True:
        try:
            prompt_input = input(f"{ANSI_BOLD}zia>{ANSI_RESET} ")
            process_command(prompt_input)
        except (KeyboardInterrupt, EOFError):
            print(f"\n{ANSI_GRAY}Session closed.{ANSI_RESET}")
            break

if __name__ == "__main__":
    main()
