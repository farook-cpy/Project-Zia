# Project FAITH // Zia: Complete Engineering & Architecture Overview

> **System Codename**: Zia (Project FAITH)  
> **Platform Target**: Cross-OS (Linux Mint, macOS, Windows 10/11)  
> **Hardware Target**: Engineered for legacy hardware (e.g. 2007 MacBook Pro with Core 2 Duo) to modern high-end PCs  
> **Status**: Full autonomous AI companion with Live2D body, Web Speech & Offline Vosk local voice recognition, OS/terminal automation, Bluetooth manager, multi-task subagents, dedicated thermal watchdog daemon, and 24 FPS ANSI/ASCII retro terminal avatar mode.

---

## 1. Operational Presentation Modes

Project Zia offers four distinct, purpose-built interfaces sharing the same underlying local Python engine:

| Interface | Technology | Best For | CPU Footprint | VRAM Footprint |
| :--- | :--- | :--- | :--- | :--- |
| **Native Visual Window** | PixiJS v6.5.8 + Cubism 4 | Expressive companion, lip-sync, shoulder portrait camera, Web Speech & local STT voice recognition | **< 15% CPU** (28 FPS active / 16 FPS idle / 5 FPS thermal throttled / 0% sleep) | **64 MB VRAM** (4K texture tier) |
| **Transparent Desktop Overlay** | Frameless Pywebview + Transparent WebGL (`--overlay`) | Zero-background floating desktop companion draggable anywhere on top of all windows | **< 15% CPU** (28 FPS / 5 FPS idle) | **64 MB VRAM** |
| **Pure Text CLI Mode** | Raw Terminal REPL (`cli.py`) | Professional, distraction-free hacker shell; remote SSH, tmux, low battery | **< 0.5% CPU** | **0 MB VRAM** |
| **Retro Terminal Avatar Mode** | ANSI 256-color ASCII Engine (`terminal_avatar.py`) | Animated companion directly inside standard terminal (SSH/tmux) with procedural breathing, lip-sync, and F1–F11 expressions | **< 0.5% CPU** (24 FPS) | **0 MB VRAM** |

---

## 2. System Architecture

```
+---------------------------------------------------------------------------------------------------------+
|                                         USER INTERACTION LAYER                                          |
|                                                                                                         |
|  [ Native Visual Window Mode ]           [ Pure Text CLI Mode (cli.py) ]   [ ANSI Retro Terminal Avatar ]|
|   - Standalone pywebview window           - Direct UNIX-style REPL          - 24 FPS ANSI 256-color engine|
|   - Live2D Kaguya shoulder portrait       - 0% VRAM, <0.5% CPU              - F1-F11 facial expressions   |
|   - Real-time vocal mouth lip-sync        - Full tool & command access      - Procedural blinking & breath|
|   - Autonomous smooth idle movement       - Zero cursor tracking overhead   - 0% VRAM, <0.5% CPU footprint|
|   - Web Speech + Local Vosk voice         - Works over SSH / tmux           - Instant responsiveness      |
+---------------------------------------------------+-----------------------------------------------------+
                                                    |
                                              Local Engine
                                                    |
+---------------------------------------------------v-----------------------------------------------------+
|                                      LOCAL PYTHON ENGINE CORE                                           |
|                                                                                                         |
|  [ Lightweight Local STT Engine ]  (engine/local_stt.py)                                                |
|   - Completely offline speech recognition via quantized Vosk (~40MB model, ~25MB RAM)                  |
|   - Unix Domain Socket (/tmp/zia_stt.sock) & TCP Loopback (127.0.0.1:8766) IPC bridge                   |
|   - Zero browser dependency, real-time voice input from CLI, scripts, or WebUI fallback                 |
|                                                                                                         |
|  [ Dedicated Thermal Watchdog Daemon ]  (engine/heartbeat.py)                                           |
|   - Hardware core temperature tracking via lm-sensors (psutil.sensors_temperatures() & ACPI)            |
|   - Automatic emergency throttling at >=80°C: restricts subagents to 1 worker + drops UI to 5 FPS      |
|   - Automatic performance restoration at <=68°C: restores subagent pool and 28 FPS UI                   |
|   - Idle physics (F11 Sleep after 20m), battery alerts (<=15%), and ambient day/night shifts            |
|                                                                                                         |
|  [ Bluetooth Device Manager ]  (engine/bluetooth_manager.py)                                            |
|   - Cross-OS paired device scanning, enumeration, and instant connection (bluetoothctl / Win32)        |
|                                                                                                         |
|  [ Autonomous Multi-Task Subagents ]  (engine/subagents.py)                                             |
|   - Thread-pool worker pool strictly capped to 2 workers (<20% CPU budget)                              |
|   - Rate-limited worker execution (pacing delay increased to 1.5s during thermal throttling)            |
|   - Specialized roles: Coder, Researcher, SystemWorker                                                  |
|                                                                                                         |
|  [ Structured Model Context Protocol Gateway ]  (engine/mcp_gateway.py)                                 |
|   - JSON-RPC 2.0 raw code and file reading (100% precision, zero OCR bloat)                            |
|                                                                                                         |
|  [ Wi-Fi Relay IoT Bridge ]  (engine/iot_bridge.py)                                                     |
|   - Direct local HTTP commands to Tasmota, WLED, Shelly microcontrollers                                |
|                                                                                                         |
|  [ Fast Local Command Router ]  (engine/local_commands.py)                                              |
|   - Executes in 0ms (0 LLM Tokens): YouTube, Spotify, Apps, File Organization                           |
|   - Master Volume, Screen Brightness, Notepad Typing Automation, Shell & Admin Elevation                |
|                                                                                                         |
|  [ Gemini Flash Brain & Persistent Memory ]  (engine/brain.py & memory.py)                              |
|   - Token-capped sliding memory (6 turns), multimodal screen vision                                     |
|   - Persistent cross-session user profile & milestone storage (data/memory.json)                        |
+---------------------------------------------------------------------------------------------------------+
```

---

## 3. Advanced Features Breakdown

### 🎙️ 1. Lightweight Local STT Engine & Hands-Free Wake-Word Detection
- **Engine File**: [`engine/local_stt.py`](file:///c:/Users/Student/Documents/Project%20Zia/engine/local_stt.py)
- **Features**:
  - Offline speech recognition powered by quantized Kaldi/Vosk (`vosk-model-small-en-us-0.15`).
  - **Hands-Free Wake-Word Recognition**: Zia continuously listens for `"Hey Zia"` or `"Zia [command]"` with zero keyboard interaction required.
  - **Dual Engine Architecture**:
    - **Visual Mode**: Continuous Web Speech API passive listener auto-extracts commands (e.g. *"Hey Zia, open YouTube"* or *"Zia, lock screen"*) and dispatches them instantly.
    - **Offline CLI Mode**: Low-overhead Vosk background thread (`wakeword on`) runs at < 0.5% CPU on Core 2 Duo hardware.
  - Ultra-low memory footprint: model consumes only ~25 MB RAM and ~40 MB disk.
  - Captures microphone input directly using `sounddevice` with automatic voice activity and silence detection (1.2s trailing silence cutoff).
  - Exposes an ultra-fast IPC server (`/tmp/zia_stt.sock` on Linux/macOS, `127.0.0.1:8766` on Windows).
- **CLI Commands**:
  - `wakeword [on|off|status]`: Toggle or inspect hands-free background wake-word detection.
  - `listen` or `voice`: Push-to-talk microphone capture.
  - `stt status` / `download`: Manage offline model cache.

### 🔐 2. Passwordless Sudo Automation & Session Lock/Unlock
- **Engine File**: [`engine/system_control.py`](file:///c:/Users/Student/Documents/Project%20Zia/engine/system_control.py)
- **Features**:
  - **Passwordless Root Execution**: Automatically sets up non-interactive visudo rules (`/etc/sudoers.d/zia`) so diagnostic and maintenance tasks run seamlessly via `sudo -n <command>` without terminal password prompts.
  - **Session Screen Locker & Unlocker**: Programmatically locks or resumes desktop sessions:
    - Linux Mint / XFCE: Dispatches `loginctl lock-session` / `loginctl unlock-sessions` and forces monitor wake via DPMS (`xset dpms force on`).
    - Windows: Locks workstation via `LockWorkStation` and wakes display via keyboard simulation.
  - **Display Compositor Toggle**: Dynamically toggles XFCE window compositing (`xfconf-query -c xfwm4 -p /general/use_compositing -s false`) to instantly reclaim GPU VRAM and fillrate on legacy Intel GMA and GeForce 8600M GT hardware.
- **CLI Commands**:
  - `sudo <command>`: Run command with root privileges non-interactively.
  - `sys sudo setup`: Auto-configure passwordless visudo rule in `/etc/sudoers.d/zia`.
  - `sys lock` / `sys unlock`: Lock or unlock/wake the desktop session.
  - `sys compositor [on|off]`: Toggle XFCE window compositing for maximum gaming/GUI framerates.

### 🌡️ 3. CPU/RAM Load Governor & Dedicated Thermal Watchdog Daemon
- **Engine File**: [`engine/heartbeat.py`](file:///c:/Users/Student/Documents/Project%20Zia/engine/heartbeat.py)
- **Features**:
  - **CPU/RAM Load Governor**: Automatically detects when host CPU usage exceeds 85% or RAM exceeds 88%, instantly throttling subagent worker pools to protect 2007 Core 2 Duo systems from freezing. Restores full performance once system metrics normalize.
  - **Thermal Watchdog**: Actively polls core temperatures via `lm-sensors` (`psutil.sensors_temperatures()`).
  - **Critical Temperature (>= 80°C)**:
    - Throttles subagents to 1 worker with 1.5s delay pacing.
    - Drops WebGL Live2D UI to 5 FPS (`set_framerate`).
    - Zia announces an emergency vocal warning.
  - **Recovery Temperature (<= 68°C)**:
    - Restores subagents and resets UI to 28 FPS.
  - **Battery Health Daemon**: Warns at $\le 15\%$ battery charge with audio/text prompts.

### 👾 3. ASCII / ANSI Terminal Avatar Mode (Retro Terminal Graphics)
- **Engine File**: [`engine/terminal_avatar.py`](file:///c:/Users/Student/Documents/Project%20Zia/engine/terminal_avatar.py)
- **Features**:
  - Allows Zia to have a rich visual presence directly inside terminal environments (SSH sessions, tmux splits, virtual consoles, or text terminals).
  - Renders Zia's portrait, crown, eyes, blush, and bust using high-density Unicode box-drawing characters and ANSI 256-color escape sequences.
  - Complete expression support matching all 11 Live2D states (F1 Neutral, F2 Blush, F3 Angry, F4 Star Eyes, F5 Love Eyes, F6 Sad, F7 Surprised, F8 Thinking, F9 Smug, F10 Shocked, F11 Sleep).
  - Real-time 24 FPS animation loop featuring procedural eye blinking (~every 3.5s), natural sine-wave breathing movement, and simulated audio lip-sync mouth movement.
  - **Resource Usage**: **0 MB VRAM** and **< 0.5% CPU**, perfect for running 24/7 on antique hardware without drawing battery power.
- **CLI Commands**:
  - `avatar` or `ascii`: Print a static ANSI portrait of Zia with current expression.
  - `avatar live`: Start interactive 24 FPS animation loop (press `Ctrl+C` to return to prompt).
  - `avatar set <F1-F11>`: Preview and lock a specific facial expression.
  - `avatar demo`: Cycle through all 11 facial expressions in sequence.

### 🔵 4. Cross-OS Bluetooth Device Management
- **Engine File**: [`engine/bluetooth_manager.py`](file:///c:/Users/Student/Documents/Project%20Zia/engine/bluetooth_manager.py)
- **Features**:
  - Enumerate paired Bluetooth devices cross-OS (`bluetoothctl` on Linux Mint, PowerShell Win32 on Windows).
  - Scan for nearby Bluetooth devices in pairing mode.
  - Connect and disconnect audio headsets, speakers, and peripherals.
  - CLI usage: `bt list`, `bt scan`, `bt connect <name_or_mac>`.

### 🤖 5. Autonomous Multi-Task Subagents
- **Engine File**: [`engine/subagents.py`](file:///c:/Users/Student/Documents/Project%20Zia/engine/subagents.py)
- **Strict CPU Safeguard**:
  - Background task pool strictly capped at `max_workers=2` with low CPU scheduling priority to guarantee load stays strictly **under 20% CPU with zero spikes**.
  - Integrated with the Thermal Watchdog to throttle down to 1 worker during high temperature events.
- **Specialized Roles**:
  - `Coder`: Evaluates code syntax, searches symbols via MCP gateway.
  - `Researcher`: Fetches, summarizes, and synthesizes documentation without cluttering main memory.
  - `SystemWorker`: Performs disk cleaning, file categorization, and log inspections.
- **CLI usage**: `agent run <role> <task>`, `agent list`, `agent status <task_id>`.

### 💻 6. Pure Text-Only CLI Interface (No AI Slop, No Cliches)
- **File**: [`cli.py`](file:///c:/Users/Student/Documents/Project%20Zia/cli.py)
- **Launchers**: Double-click [`start_cli.bat`](file:///c:/Users/Student/Documents/Project%20Zia/start_cli.bat) on Windows or run `./start_cli.sh` on Linux Mint / macOS.
- **Design**:
  - Direct, distraction-free UNIX terminal prompt: `zia> `
  - 0% VRAM, <0.5% CPU.
  - Access to every single engine feature (chat, terminal execution, system diagnostics, bluetooth, subagents, MCP files, file organization, IoT lights, persistent memory, offline voice STT, ANSI avatar).

### 📂 7. Structured Model Context Protocol Gateway (JSON-RPC 2.0)
- **Engine File**: [`engine/mcp_gateway.py`](file:///c:/Users/Student/Documents/Project%20Zia/engine/mcp_gateway.py)
- **Features**:
  - Standardized JSON-RPC 2.0 schema for direct filesystem inspection.
  - Safely reads raw text from files without screenshot downscaling or OCR hallucination.
  - CLI usage: `mcp read <file>`, `mcp search <query>`, `mcp ls <dir>`.

### ⚡ 8. Fast Local Command Router (0 LLM Tokens)
- **Engine File**: [`engine/local_commands.py`](file:///c:/Users/Student/Documents/Project%20Zia/engine/local_commands.py)
- **Features**:
  - Executes instant system actions without touching the cloud model:
    - App and URL launching (YouTube, Spotify, Instagram, Calculator, Terminal, Notepad).
    - OS volume and brightness control.
    - Sudo and Administrator terminal command execution.
    - Automatic folder cleanup (Downloads / Desktop sorting).
    - Automated text typing in Notepad.

### 🏠 9. Wi-Fi Relay Local IoT Bridge
- **Engine File**: [`engine/iot_bridge.py`](file:///c:/Users/Student/Documents/Project%20Zia/engine/iot_bridge.py)
- **Features**:
  - HTTP routing to local microcontrollers (Tasmota, WLED, Shelly) with zero CPU overhead.
  - CLI usage: `iot on`, `iot off`, `iot toggle`.

### 🧠 10. Gemini Flash Brain & Persistent Memory
- **Engine Files**: [`engine/brain.py`](file:///c:/Users/Student/Documents/Project%20Zia/engine/brain.py), [`engine/memory.py`](file:///c:/Users/Student/Documents/Project%20Zia/engine/memory.py)
- **Features**:
  - Gemini Flash model integration for high-speed, cost-effective reasoning.
  - Multimodal vision input with screen-capture downscaling to keep latency under 1.5s.
  - Sliding conversation window (capped to 6 turns) combined with long-term persistent memory (`data/memory.json`).

### 👁️ 11. Offline Local Webcam Vision Senses Engine (<2% CPU)
- **Engine File**: [`engine/vision_senses.py`](file:///c:/Users/Student/Documents/Project%20Zia/engine/vision_senses.py)
- **Features**:
  - Continuous offline webcam polling throttled strictly to 1 frame every 2.5 seconds (0.4 FPS capture) to guarantee CPU utilization remains **< 2%** on vintage Core 2 Duo processors.
  - Powered by OpenCV's state-of-the-art **YuNet ONNX quantized face & 5-landmark detector** (`data/face_detection_yunet.onnx`, 232 KB) running on downscaled 320x240 frames in < 2ms without cloud tokens or network lag.
  - Computes geometric landmark vectors and frame-to-frame optical flow to classify real-time user behavioral states:
    - **Thinking**: Detected via downward head tilt (compressed vertical nose-to-mouth ratio), hand-to-chin occlusion, or prolonged stillness with face centered.
    - **Stressed**: Detected via squinting / furrowed brow facial compression or high micro-jitter streaks without bodily translation.
    - **Walking / Away**: Detected via absence of face landmarks combined with sudden whole-frame optical difference.
    - **Neutral / Engaged**: Normal relaxed face geometry.
  - **Proactive Heartbeat Trigger Integration (Vector 6 in `engine/heartbeat.py`)**:
    - **Stressed $\ge 60$s**: Triggers comforting Live2D smile expression (`F3`) and Zia softly speaks/pipes: *"You've been frowning at the screen for a while. Want me to clear your notification queue or play a background soundscape?"* (includes 5-minute cooldown).
    - **Away $\ge 60$s**: Engages idle power-saving mode, drops Live2D to 5 FPS, and sets expression to `F11` (Sleep).
    - **User Return**: Instantly restores 28 FPS active rendering and wakes Zia to `F1` Neutral.
    - **Thinking $\ge 10$s**: Sets expression to `F8` (Think).
  - CLI commands: `cam status`, `cam start`, `cam stop`, `cam scan`, `cam test <state>`, `cam interval <sec>`.

### 🪟 12. Transparent Frameless Desktop Overlay Companion
- **Launchers**: `python run.py --overlay`, [`start_overlay.bat`](file:///c:/Users/Student/Documents/Project%20Zia/start_overlay.bat), `start_overlay.sh`
- **Features**:
  - Zero-background Live2D companion that floats directly on top of all desktop windows (`on_top=True`, `frameless=True`, `transparent=True`).
  - WebGL canvas configured with `backgroundAlpha: 0.0` and CSS `-webkit-app-region: drag` for instant, smooth drag-and-drop placement anywhere on screen.
  - Zero VRAM overhead for the transparent background layer.

### 🐛 13. Automated Error Traceback Debugger
- **Engine File**: [`engine/error_debugger.py`](file:///c:/Users/Student/Documents/Project%20Zia/engine/error_debugger.py)
- **Features**:
  - Automatically intercepts and records stdout/stderr and exit codes whenever terminal commands executed via `run <cmd>` or `sudo <cmd>` fail.
  - Pipes execution context and raw stack traces to Gemini Flash.
  - Outputs immediate root-cause diagnosis, verified terminal commands, and code patches.
  - CLI usage: `debug` (diagnoses the last failed command) or `debug <command>`.

### 🖥️ 14. Multimodal Screen Vision Analysis
- **Engine Files**: [`engine/senses.py`](file:///c:/Users/Student/Documents/Project%20Zia/engine/senses.py), [`cli.py`](file:///c:/Users/Student/Documents/Project%20Zia/cli.py)
- **Features**:
  - High-speed screen capture scaled cleanly to 1024px to preserve token efficiency.
  - Analyzes UI layouts, error modals, code windows, and diagrams directly from the terminal or Web UI.
  - CLI command: `vision <query>` or `look <query>` (e.g. `vision What is this error dialog showing?`).

### 🐚 15. Natural Language to Shell Compiler
- **Engine File**: [`engine/shell_compiler.py`](file:///c:/Users/Student/Documents/Project%20Zia/engine/shell_compiler.py)
- **Features**:
  - Compiles plain English queries into safe, single-line OS-tailored shell pipelines (`awk`, `sed`, `grep`, `find`, `ffmpeg`, PowerShell).
  - Categorizes commands with clear safety ratings (`SAFE_READONLY`, `FILE_MODIFY`, `DESTRUCTIVE`).
  - CLI usage: `cmd find files larger than 100mb` or `compile convert video.mov to mp4`.

### 🔒 16. Encrypted Machine-Bound Credential Vault
- **Engine File**: [`engine/vault.py`](file:///c:/Users/Student/Documents/Project%20Zia/engine/vault.py)
- **Features**:
  - Stores and retrieves sensitive API keys and credentials locally.
  - Employs PBKDF2 HMAC-SHA256 (390,000 iterations) with Fernet encryption tied to machine-bound hardware GUIDs in `data/vault.enc`.
  - Bridges with Linux `secret-tool` / libsecret when running on Linux Mint.
  - CLI commands: `vault store <svc> <key> <val>`, `vault get <svc> [key]`, `vault list`, `vault del <svc>`.

### ⏱️ 17. Automated Natural Language Cron & Task Scheduler
- **Engine File**: [`engine/scheduler.py`](file:///c:/Users/Student/Documents/Project%20Zia/engine/scheduler.py)
- **Features**:
  - Rule-based natural language parser extracting intervals (*"every 30m"*, *"every 2 hours"*, *"every 10s"*).
  - Background daemon thread runs recurring or one-shot tasks with persistent storage in `data/tasks.json`.
  - Dispatches vocal speech reminders and automated system actions.
  - CLI commands: `schedule <prompt> every X`, `schedule list`, `schedule cancel <id>`.

### 📡 18. Network Traffic & Bandwidth Sentinel
- **Engine File**: [`engine/network_sentinel.py`](file:///c:/Users/Student/Documents/Project%20Zia/engine/network_sentinel.py)
- **Features**:
  - Scans and catalogs active listening TCP/UDP ports, identifying local-only vs. public/LAN interfaces.
  - Computes real-time download and upload transfer rates in KB/s without third-party network bloat.
  - Audits listening ports against security baselines and alerts on unexpected exposed public ports.
  - CLI commands: `net ports`, `net speed`, `net active`, `net audit`.

### 🎭 19. TTS Dynamic Emotion Modulation
- **Engine File**: [`engine/tts_engine.py`](file:///c:/Users/Student/Documents/Project%20Zia/engine/tts_engine.py)
- **Features**:
  - Dynamically modulates Edge-TTS vocal parameters (`pitch` and `rate`) to reflect Zia's active expression state:
    - Urgent / Shocked (`F10`): Faster pace (`+18%`), higher pitch (`+15Hz`).
    - Thinking (`F8`): Slower deliberate pace (`-10%`), calm pitch.
    - Sad / Low battery (`F6`): Subdued pace (`-12%`), low pitch (`-10Hz`).
    - Cheerful / Star Eyes (`F4`): Energetic pace (`+8%`), bright pitch (`+12Hz`).

### 🎙️ 20. Microphone Noise Suppression & Chassis Hum Filter
- **Engine File**: [`engine/local_stt.py`](file:///c:/Users/Student/Documents/Project%20Zia/engine/local_stt.py)
- **Features**:
  - Implements a pre-emphasis high-pass digital filter ($y[i] = x[i] - 0.92 x[i-1]$) to strip low-frequency MacBook aluminum chassis fan vibration and 50/60Hz AC hum.
  - Applies an RMS silence gate threshold to prevent background fan noise from spurious Vosk wake triggers.

### 📋 21. Multi-Device LAN Clipboard Synchronization Server
- **Engine File**: [`engine/clipboard_sync.py`](file:///c:/Users/Student/Documents/Project%20Zia/engine/clipboard_sync.py)
- **Features**:
  - Lightweight P2P clipboard bridge running a local HTTP REST server on port `8767`.
  - Responsive mobile web interface for syncing text between the MacBook/PC and mobile devices (Samsung phone / tablet).
  - CLI commands: `clip get`, `clip set <text>`, `clip sync on`, `clip sync off`.

### ⚙️ 22. Vintage Hardware Governors & Controls
- **Engine File**: [`engine/system_control.py`](file:///c:/Users/Student/Documents/Project%20Zia/engine/system_control.py)
- **Features**:
  - **Partition & Mount Manager**: Lists partitions, mounts external USB storage devices (`mount <dev>`), and cleanly unmounts (`unmount <dev>`).
  - **CPU Governor Switcher**: Toggles CPU power profiles (`powersave`, `performance`, `ondemand`) to extend battery life on Core 2 Duo hardware.
  - **Display Calibration Profiles**: Instant software gamma and brightness calibration curves (`reading` 40%, `movie` 85%, `outdoor` 100%, `night` 20%).
  - **Cooling Fan Manual Override**: Adjusts cooling fans via Linux AppleSMC sysfs (`/sys/devices/platform/applesmc.768/fan*_manual`) or reports BIOS SMC telemetry.
  - **Audio Sink / Route Switcher**: Reroutes audio between internal speakers, headphones, and Bluetooth outputs (`audio list`, `audio set <sink>`).

### 🕌 23. Palakkad Islamic Prayer Times & Gentle Check-in Feature
- **Engine File**: [`engine/prayer_times.py`](file:///c:/Users/Student/Documents/Project%20Zia/engine/prayer_times.py)
- **Features**:
  - Solar astronomical calculations specific to Palakkad, Kerala (**Latitude: 10.7867° N, Longitude: 76.6548° E**; Timezone: `Asia/Kolkata` IST +5:30).
  - Employs Kerala Shafi'i shadow adjustment ($S=1$) and standard 18° angles for Subhi (Fajr) and Isha. Computes Subhi, Sunrise, Dhuhr, Asr, Maghrib, and Isha in $<0.05\text{ ms}$ with **0 cloud tokens** and **0 external dependencies**.
  - **Daily Gentle Conversational Check-in (Vector 7 in `engine/heartbeat.py`)**:
    - When a prayer timestamp is reached, Zia softly adjusts Live2D expression (`F1`) and delivers a respectful, pressure-free prompt:
      `"Hey, Subhi time in Palakkad has started. Did you manage to pray yet?"`
    - If user replies affirmatively (*"yes"*, *"prayed"*, *"done"*, *"alhamdulillah"*), Zia logs it silently into `data/memory.json` to track habits (*"Alhamdulillah, I've noted that down for you"*).
    - If ignored, she stays quiet to maintain a calm, respectful environment ("without heaviness").
  - CLI usage: `prayer times`, `prayer next`, `prayer log`, `prayer check`, `prayer done [name]`.

### ⏰ 24. Natural Language Alarm & Countdown Timer Scheduling Feature
- **Engine File**: [`engine/alarm_manager.py`](file:///c:/Users/Student/Documents/Project%20Zia/engine/alarm_manager.py)
- **Features**:
  - Zero-token rule-based parser in [`engine/local_commands.py`](file:///c:/Users/Student/Documents/Project%20Zia/engine/local_commands.py) executing instant scheduling without touching the LLM:
    - **Relative Countdown Timers**: *"Remind me to push code in 20 minutes"*, *"timer 5m"*, *"wake me in 30 seconds"*.
    - **Absolute Clock Alarms**: *"Wake me at 8:00 pm"*, *"wake me in 8:00 pm"*, *"set alarm for 6:00 am"*.
  - Managed via non-blocking background `threading.Timer` with persistent state in `data/alarms.json`.
  - **Multi-Vector Alert Action**:
    - Plays subtle system sound notification (`aplay` / `paplay` / `winsound` / `afplay` or terminal bell `\a`).
    - Flashes desktop notification banner (`notify-send` / PowerShell / macOS).
    - Live2D / TTS broadcast: vocal reminder and expression shift (`F4`).
  - CLI usage: `alarm list`, `alarm set <time> [label]`, `alarm cancel <id>`, `timer <duration> [label]`.

### 📱 25. Xperia 24/7 Server Backend (`server.py`)
- **Backend File**: [`server.py`](file:///c:/Users/Student/Documents/Project%20Zia/server.py)
- **Launcher**: [`start_xperia.sh`](file:///c:/Users/Student/Documents/Project%20Zia/start_xperia.sh)
- **Features**:
  - Turns a broken-screen Sony Xperia 1 III (Snapdragon 888, 12GB RAM, Android + Termux) into an autonomous 24/7 background AI companion server node listening on `0.0.0.0:5000`.
  - Runs persistently under `termux-wake-lock` to keep the mobile CPU active with the screen turned off.
  - Subagent worker thread pool strictly throttled to **`max_workers=2`** to protect mobile thermal envelope and battery efficiency.
  - Endpoints:
    - `POST /api/chat`: Dual router (0-token local commands + Gemini Flash).
    - `POST /api/query`: Direct Gemini Flash reasoning API.
    - `GET/POST /api/memory`: Persistent cross-session facts and prayer logs (`data/memory.json`).
    - `GET/POST /api/subagents`: Background worker management (`max_workers=2`).
    - `GET /api/status`: Mobile CPU, RAM, battery telemetry, audio hardware, active alarms, and next prayer countdown.

### 🎙️ 26. Audio & Ambient Room-Listening Pipeline (`engine/audio_bridge.py`)
- **Engine File**: [`engine/audio_bridge.py`](file:///c:/Users/Student/Documents/Project%20Zia/engine/audio_bridge.py)
- **Features**:
  - **Ambient Room Audio Capture**: Utilizes Android Termux API hooks (`termux-microphone-record -d -l <sec> -b 16 -r 16000`) or desktop audio buffers to record room sound directly from the Xperia's built-in microphones.
  - **Software Noise Gate**: Applies a pre-emphasis high-pass filter ($y[i] = x[i] - 0.92 x[i-1]$) and RMS silence thresholding to strip AC hum, fan noise, and background room hiss before STT.
  - **Direct Physical Speaker Playback**: Routes TTS voice outputs directly to the Xperia's physical stereo speakers via `termux-tts-speak` or `termux-media-player` / Edge-TTS audio.
  - CLI usage: `xperia status`, `xperia listen [seconds]`, `xperia speak <text>`.

### 🌉 27. Client-Server RPC Bridge for Remote MacBook Actions (`engine/rpc_bridge.py` & `mac_agent.py`)
- **Server Bridge**: [`engine/rpc_bridge.py`](file:///c:/Users/Student/Documents/Project%20Zia/engine/rpc_bridge.py)
- **Client Agent**: [`mac_agent.py`](file:///c:/Users/Student/Documents/Project%20Zia/mac_agent.py) | [`start_mac_agent.sh`](file:///c:/Users/Student/Documents/Project%20Zia/start_mac_agent.sh)
- **Features**:
  - Secure JSON-RPC 2.0 communication bridge connecting the Xperia server to the MacBook Pro (Linux Mint XFCE) over local LAN (port `5001`).
  - Protected with `X-Zia-Secret` authorization token.
  - **Remote Execution Operations**:
    - `system.exec`: Dispatches commands from Xperia server to safely run on MacBook terminal via `subprocess`.
    - `system.health`: Returns MacBook CPU %, core temperatures, RAM, and battery status to the Xperia server.
    - `ui.notify`: Dispatches native `notify-send` desktop banners on Linux Mint XFCE styled in dark cyberpunk aesthetic.
    - `audio.volume`: Adjusts master volume on MacBook.
    - `system.lock`: Programmatically locks the MacBook XFCE session via `loginctl`.
  - Automatic discovery registration: `mac_agent.py` automatically registers its LAN IP with the Xperia server upon startup.
  - CLI usage: `mac status`, `mac health`, `mac exec <cmd>`, `mac notify <msg>`, `mac vol <up/down>`, `mac lock`.

---

## 4. Directory Layout

```
Project Zia/
├── assets/models/Kaguya/             # Live2D Cubism 4 assets (Kaguya.moc3, textures, expressions)
├── assets/models/TianYeLulu/         # Backward-compatible model redirect manifests
├── data/
│   ├── memory.json                    # Persistent cross-session memory & prayer completion log
│   ├── alarms.json                    # Persistent active alarms & countdown timers
│   ├── tasks.json                     # Scheduled cron tasks & background reminders
│   ├── vault.enc                      # Machine-bound PBKDF2 encrypted credential vault
│   ├── face_detection_yunet.onnx      # Quantized YuNet face & 5-landmark detector (232 KB)
│   └── models/                        # Quantized models (Vosk offline STT ~40MB)
├── frontend/                          # Zero-framework flat WebGL interface (Visual & Overlay Mode)
│   ├── index.html                     # Minimal black viewport & hotkey coordinator
│   ├── css/style.css                  # Hardware-accelerated minimal dark styling & overlay support
│   └── js/
│       ├── live2d_engine.js           # PixiJS + Cubism runtime, framerate throttler, transparent canvas
│       ├── audio_sync.js              # Web Audio API vocal RMS lip-sync
│       ├── websocket_client.js        # Local WebSocket bridge & subtitle controller
│       ├── live2dcubismcore.min.js    # Local Cubism Core runtime (100% offline)
│       ├── pixi.min.js                # PixiJS v6.5.8 (100% offline)
│       └── cubism4.min.js             # Pixi-Live2D display plugin (100% offline)
├── engine/                            # Local Python daemon
│   ├── audio_bridge.py                # Android/Termux microphone record & physical speaker playback
│   ├── rpc_bridge.py                  # Client-Server JSON-RPC bridge for remote MacBook actions
│   ├── prayer_times.py                # Astronomical Islamic prayer engine for Palakkad (0% CPU)
│   ├── alarm_manager.py               # Natural language alarm & countdown timer scheduler
│   ├── vision_senses.py               # Throttled local webcam behavioral vision (<2% CPU, YuNet ONNX)
│   ├── error_debugger.py              # Automated terminal error traceback debugger (Gemini Flash)
│   ├── shell_compiler.py              # Natural language to safe shell compiler
│   ├── vault.py                       # PBKDF2 HMAC-SHA256 encrypted credential vault
│   ├── scheduler.py                   # Unified task, alarm, prayer & remote notification scheduler
│   ├── network_sentinel.py            # Listening port auditor & real-time bandwidth sentinel
│   ├── clipboard_sync.py              # Multi-device LAN clipboard synchronization server (port 8767)
│   ├── local_stt.py                   # Offline Vosk STT engine & noise gate / chassis filter
│   ├── heartbeat.py                   # V2 Heartbeat, Thermal Watchdog, Vision & Prayer Router
│   ├── terminal_avatar.py             # 24 FPS ANSI 256-color retro terminal avatar renderer
│   ├── bluetooth_manager.py           # Cross-OS Bluetooth discovery & connection
│   ├── subagents.py                   # Multi-task autonomous subagent pool (max_workers=2)
│   ├── mcp_gateway.py                 # Structured MCP Gateway (JSON-RPC 2.0 raw text reader)
│   ├── texture_mod.py                 # Living Asset dynamic skin generator
│   ├── iot_bridge.py                  # Local Wi-Fi IoT relay controller (Tasmota / WLED)
│   ├── brain.py                       # Gemini Flash router, persistent memory, vision actions
│   ├── local_commands.py              # Zero-token local execution engine (YouTube, Spotify, Apps)
│   ├── system_control.py              # Hardware controls: Mounts, CPU Gov, Fan, Display Profiles, Audio
│   ├── senses.py                      # MSS/PIL screen capture & active window tracker
│   ├── hands.py                       # Cross-OS mouse clicks, typing, and URL launchers
│   ├── memory.py                      # JSON-backed persistent memory manager
│   ├── tts_engine.py                  # Edge-TTS voice streaming with emotion pitch/rate modulation
│   ├── agentic_ops.py                 # Multi-agent ops, SQLite task queue, AST testgen, OCR, plan visualizer
│   ├── ecosystem_bridge.py            # Local AirDrop clone, battery mirror, camera streamer, WoL, latency watchdog
│   ├── security_vault.py              # Zero-knowledge AES-256 logs, prompt scrubber, FIM, port auditor, SSL watchdog
│   ├── ambient_intelligence.py        # Weather greeter, procedural soundboard WAV synthesizer, habits, retro HUD themes
│   ├── config.py                      # Settings & .env loader
│   └── server.py                      # Unified static web server & WebSocket daemon
├── server.py                          # Dedicated 24/7 Xperia server backend (Flask, 0.0.0.0:5000, 31 endpoints)
├── mac_agent.py                       # MacBook Pro remote agent listener (0.0.0.0:5001)
├── cli.py                             # Dedicated pure text CLI interface (No WebGL, No Audio, 40+ commands)
├── run.py                             # Visual & Overlay launcher (boots daemon & native window)
├── start_xperia.sh                    # 1-Click Android Termux 24/7 server launcher (termux-wake-lock)
├── start_mac_agent.sh                 # 1-Click Linux Mint MacBook remote agent listener launcher
├── start_mac_agent.bat                # 1-Click Windows remote agent listener launcher
├── start.bat                          # 1-Click Windows Visual launcher
├── start.sh                           # 1-Click Linux Mint Visual launcher
├── start_overlay.bat                  # 1-Click Windows Frameless Overlay launcher
├── start_overlay.sh                   # 1-Click Linux Mint Frameless Overlay launcher
├── start_cli.bat                      # 1-Click Windows Text CLI launcher
├── start_cli.sh                       # 1-Click Linux Mint Text CLI launcher
├── update.md                          # Latest engineering specifications & sprint requirements
├── requirements.txt                   # Cross-platform Python dependencies
├── README.md                          # Quick start instructions
└── PROJECT_OVERVIEW.md                # This complete architectural log
```

---

## 4. Full 40-Feature Autonomous Sprint Breakdown

### Part 1: Advanced Agentic & Multi-Agent Operations (`engine/agentic_ops.py`)
1. **Self-Correction Loop for Subagents**: Intercepts syntax errors or failed JSON responses and automatically re-prompts worker threads with corrected context (`execute_with_self_correction`).
2. **Dynamic Subagent Token Cost Budgeter**: Real-time accumulator (`track_token_usage`) tracking Gemini API input/candidate tokens per thread to prevent accidental budget overruns.
3. **Asynchronous Task Queuing & Persistence**: SQLite queue (`data/task_queue.db`) that caches complex user tasks if connection drops, auto-processing them when connectivity restores.
4. **Automated Unit Test Generator**: AST-based code inspector (`generate_unit_tests`) that parses Python functions and generates standalone companion `test_*.py` test suites.
5. **Multi-Step Reasoning Plan Visualizer**: Decomposes complex user goals into hierarchical ASCII breakdown trees (`visualize_plan`) before code execution.
6. **Smart Code Reviewer Subagent**: Static analysis and security linting engine (`review_code_snippet`) that scans modified files for style, security risks, and optimization suggestions.
7. **Incremental Context Primmer**: Automatically summarizes past conversation turns older than the sliding window (`prime_context`) and stores them in long-term memory.
8. **Local OCR Text Extraction Pipeline**: Extracts text from images and screenshots locally (`extract_text_local_ocr`) with zero cloud latency or token cost.
9. **Autonomous Documentation Scraper**: Fetches official documentation pages via HTTP (`fetch_and_cache_docs`), parses text, and saves markdown files to `data/docs/` for offline browsing.
10. **Background Dependency Resolver**: Scans Python scripts for imports (`scan_missing_dependencies`) and reports missing third-party packages with recommended pip install flags.

### Part 2: Cross-Device Ecosystem & Remote Bridge Extensions (`engine/ecosystem_bridge.py`)
11. **Phone-to-Laptop File Drop (Local AirDrop Clone)**: Transfers files over local HTTP socket bridges between Xperia server and MacBook (`send_file_to_remote`, `save_received_file` in `data/transfers/`).
12. **Remote Battery Status Mirroring**: Mirrors Xperia server battery percentage and thermal state directly into MacBook CLI status bars (`get_mirrored_battery_status`).
13. **Universal Clipboard P2P Sync Bridge**: Synchronizes clipboard text between Android server, MacBook, and tablets over port 8767 (`clipboard_sync.py`).
14. **Audio Routing Switcher via CLI**: Dynamically reroutes audio playback between phone speakers, MacBook audio jacks, or connected Bluetooth headsets (`set_audio_route`).
15. **Remote Camera Feed Streamer**: Captures snapshots from the Xperia's rear camera (`capture_remote_camera_frame`) and serves them to remote clients.
16. **Cross-Device Notification Forwarding**: Pipes Android alerts straight to MacBook terminal overlays via JSON-RPC (`send_remote_notification`).
17. **Network Ping & Latency Watchdog**: Continuously measures local Wi-Fi link quality (`measure_network_latency`) between nodes and flags packet drops.
18. **Remote Wake-on-LAN Trigger**: Broadcasts UDP Magic Packets on port 9 (`send_wake_on_lan`) to wake up sleeping PCs or NAS boxes.
19. **Device Health Dashboard Webpage**: Ultra-lightweight responsive HTML dashboard (`http://<ip>:5000/dashboard`) showing live CPU, thermals, battery, subagents, and prayer times.
20. **Multi-Client Session Coordinator**: Manages multiple simultaneous client connections (`register_client_session`) without state or memory collision.

### Part 3: Security, Privacy, & Local Cryptography (`engine/security_vault.py`)
21. **Local API Key Vault & Redaction Guard**: Scans outgoing prompt payloads (`scrub_prompt_payload`) and redacts Gemini, OpenAI, GitHub, and AWS keys before cloud transmission.
22. **Zero-Knowledge Local Chat Logger**: Encrypts local conversation logs using AES-256 (`log_encrypted_event`, `read_encrypted_logs` in `data/secure_logs.enc`).
23. **Secure SSH Tunnel Manager**: Generates reverse SSH tunnel commands (`generate_ssh_tunnel_command`) for encrypted remote access outside LAN.
24. **File Integrity Monitor (FIM)**: Maintains SHA-256 hashes of critical files (`data/fim_hashes.json`) and flags unauthorized tampering (`check_fim_integrity`).
25. **Ephemeral Chat Mode ("Incognito Session")**: Bypasses persistent disk logging entirely (`toggle_incognito`) for sensitive queries.
26. **Automated Log Redacter**: Strips private IPs, MAC addresses, and user home directories (`redact_log_dump`) from error logs.
27. **Local Passkey Guard for Destructive Actions**: Protects against high-risk commands (`verify_action_permission`, `is_destructive_command`) requiring local confirmation.
28. **Exposed Port Auditor**: Scans local network interfaces (`audit_exposed_ports`) and warns if non-whitelisted ports listen on `0.0.0.0`.
29. **SSL Certificate Expiry Watchdog**: Probes SSL certificate validity (`check_ssl_cert_expiry`) and warns 14 days before expiration.
30. **Secure Environment Variable Enforcer**: Scans codebase (`scan_codebase_for_leaked_credentials`) to prevent hardcoded credentials in git repositories.

### Part 4: Smart Notifications, Contextual Shortcuts, & Ambient Intelligence (`engine/ambient_intelligence.py`)
31. **Context-Aware Weather Adaptive Greeter**: Queries Open-Meteo API (`get_weather_greeting`) for live Palakkad climate (0 tokens, 0 API keys) and tailors greetings to weather.
32. **Custom Audio Soundboard Generator**: Procedurally synthesizes retro-futuristic WAV audio chimes (`synthesize_chime` in `data/sounds/`) via pure math and `wave` stdlib.
33. **Adaptive Focus Music Player**: Initiates ambient electronic/lofi audio streams (`toggle_focus_mode`) and tracks deep work duration.
34. **Smart Meeting / Prayer Conflict Resolver**: Cross-references proposed meeting times against Palakkad prayer schedules (`check_prayer_meeting_conflict`) with a 20-minute buffer.
35. **Idle Productivity Nudge**: Monitors inactivity (`check_idle_nudge`) and prompts to refocus on active milestones from `memory.json`.
36. **Daily Developer Digest Summarizer**: Compiles end-of-day reports (`compile_daily_digest`) of git commits, alarms, completed queue tasks, and prayer statistics.
37. **Geofence-Inspired Home Presence Trigger**: Tests home router gateway reachability (`check_presence`) to toggle server presence states between `HOME` and `AWAY`.
38. **Interactive Voice Command Shortcuts**: Maps single-word triggers (`execute_shortcut` in `data/voice_shortcuts.json`) to multi-step terminal pipelines.
39. **Customizable Retro HUD Theme Engine**: Dynamically switches CLI ANSI color palettes (`set_theme`): `cyan` (Neon Cyberpunk), `amber` (Phosphor CRT), `matrix` (Terminal Green), `mono` (Monochrome Slate).
40. **Smart Habit Streak Tracker**: Logs daily consistency on development milestones, writing goals, and prayer logs (`log_habit`, `get_habit_streaks` in `data/habits.json`).

---

## 5. Controls & Commands Cheatsheet

### Visual & Overlay Mode
- **Overlay Launch**: `python run.py --overlay`, `start_overlay.bat`, `start_overlay.sh`
- **Voice**: Say `"Hey Zia"` or `"Zia [command]"` hands-free anytime
- **`Space`**: Manual push-to-talk voice input
- **`Enter`**: Open/close minimalist dark prompt box
- **`V`**: Scan screen for visual analysis
- **`F1` – `F11`**: Live2D facial expressions
- **`H`**: On-screen hotkey reference
- **`Esc`**: Dismiss modals
- **Mouse Drag**: Draggable anywhere in overlay mode; pan & zoom in window mode

### Pure Text CLI Commands (`zia> `)
#### Advanced Agentic & Multi-Agent Operations
- `plan <goal>`: Multi-step reasoning tree plan visualizer before execution
- `review <file>`: Smart code reviewer subagent & static security linting
- `testgen <file>`: Automated AST unit test generator (outputs `tests/test_*.py`)
- `qtask <role> <desc>`: Enqueue task into persistent SQLite queue (`data/task_queue.db`)
- `qprocess`: Process pending offline tasks in SQLite queue
- `budget`: Dynamic Gemini API token budget & real-time cost accumulator
- `ocr <image_path>`: Local OCR text extraction (0 cloud tokens, 0 cloud dependencies)
- `docs <url> [tag]`: Autonomous documentation scraper & offline markdown cache
- `deps <script.py>`: Background dependency resolver & missing import scanner

#### Cross-Device Ecosystem & Remote Bridge
- `mac [status|health|exec|notify|vol]`: Remote MacBook Control via secure JSON-RPC Bridge
- `xperia [status|listen|speak]`: Android/Termux ambient room listening & physical speaker playback
- `drop [send <file> [url]|list]`: Phone-to-laptop local file drop (AirDrop clone)
- `battery`: Mirrored battery status & thermals across Xperia and MacBook
- `route [phone|mac|bt]`: Audio routing switcher (phone speakers / laptop / Bluetooth)
- `wol <mac_address>`: Remote Wake-on-LAN trigger (UDP Magic Packet on port 9)
- `pinglan [host]`: Network ping & Wi-Fi link quality watchdog
- `camstream`: Remote camera snapshot streamer from Xperia node
- `dashboard`: Responsive device health dashboard URL (`http://<ip>:5000/dashboard`)

#### Security, Privacy & Local Cryptography
- `incognito [on|off]`: Ephemeral chat mode (zero persistent trace on disk)
- `fim [check|update]`: File Integrity Monitor (SHA-256 baseline audit)
- `ports`: Exposed port auditor (flags services listening on `0.0.0.0`)
- `sslcert <host>`: SSL certificate expiry watchdog (warns 14 days before expiration)
- `secscan [dir]`: Scans codebase for leaked API keys, tokens, and passwords
- `tunnel <user> <host>`: Generate reverse SSH tunnel command for remote access outside LAN

#### Smart Notifications & Ambient Intelligence
- `weather [lat lon]`: Context-aware weather adaptive greeter for Palakkad (Open-Meteo, 0 tokens)
- `chime [notification|alert|prayer|success]`: Procedural retro audio soundboard synthesis
- `focus [start|stop|toggle]`: Adaptive focus music stream & session tracking
- `conflict <HH:MM> [duration]`: Smart meeting vs prayer conflict resolver (20-min buffer)
- `digest`: Daily developer digest report (git commits, alarms, prayer statistics)
- `presence`: Geofence home presence detection via home router gateway
- `theme [cyan|amber|matrix|mono]`: Customizable retro HUD theme engine
- `habit [log <name>|streaks]`: Smart habit streak tracker (coding, writing, prayer, focus)
- `macro <word>`: Interactive voice/text shortcut macro executor

#### System, Prayer & Automation
- `prayer [times|next|log|done]`: Palakkad, Kerala daily prayer schedule & gentle check-in
- `alarm [list|set <time>|cancel]`: Absolute clock alarms (e.g. `alarm set 8:00 pm`)
- `timer <duration> [label]`: Relative countdown timers (e.g. `timer 20m push code`)
- `cam [status|start|stop|scan|test]`: Local Webcam Senses (<2% CPU, detects thinking/stressed/away)
- `debug [command]`: Automated Error Traceback Debugger & terminal code fix
- `vision / look [query]`: Multimodal Screen Vision Analysis via Gemini Flash
- `cmd <natural language task>`: Compile natural language to safe shell pipelines
- `vault [store|get|list|del]`: Encrypted machine-bound credential & password vault
- `schedule <task> every X`: Automated Natural Language Cron & Task Scheduler
- `net [ports|speed|active|audit]`: Network Traffic & Bandwidth Sentinel
- `clip [get|set|sync on/off]`: Multi-Device Clipboard Sync Server (Port 8767)
- `mount [list|<device>]`: Disk Partition & Storage Mount Manager
- `cpu gov [powersave|perf]`: CPU Frequency Governor Switcher
- `disp profile [reading|movie]`: Luminance & Contrast Display Calibration Profiles
- `fan [status|auto|max|quiet]`: Cooling Fan Manual Override (MacBook SMC/hwmon)
- `audio [list|set <sink>]`: Audio Sink / Route Switcher (Speakers/Headphones/BT)
- `chat <prompt>`: Query Gemini Flash directly (or type raw prompt directly)
- `wakeword [on|off|status]`: Hands-free background wake-word ('Hey Zia' / 'Zia')
- `avatar [show|live|set|demo]`: ANSI 256-color retro terminal avatar (24 FPS, 0% VRAM)
- `listen` / `voice`: Local offline speech recognition via Vosk (~25MB RAM, no browser)
- `stt status` / `stt download`: Manage offline Speech-to-Text model
- `bt list` / `bt scan` / `bt connect <name>`: Bluetooth controls
- `agent run <role> <task>`: Spawn background subagent (<20% CPU budget)
- `agent list` / `agent status <id>`: Inspect subagent workers
- `sys health`: Hardware diagnostics (CPU temp, RAM, Swap, Disk, Uptime, Processes)
- `sys troubleshoot`: Automatic device diagnostics & optimization advice
- `sys vol <up|down|mute>`: Adjust master OS volume
- `sys bright <up|down>`: Adjust monitor screen brightness
- `sys lock` / `sys unlock`: Programmatically lock or resume desktop session
- `sys compositor [on|off]`: Toggle XFCE window compositor for GPU performance
- `sys sudo setup`: Configure passwordless sudo (/etc/sudoers.d/zia)
- `sudo <cmd>`: Shell execution with passwordless admin elevation
- `run <cmd>`: Standard shell execution (auto-records failures for `debug`)
- `mcp read <path>` / `mcp search <query>`: Zero-OCR precision file reading
- `organize [downloads|desktop]`: Auto-categorize unorganized files into folders
- `iot <on|off|toggle>`: Send local command to Wi-Fi relay (Tasmota / WLED)
- `mem show` / `mem note <fact>`: Inspect or append persistent long-term memory
- `open <app/site>`: Instant local app launch (yt, spotify, ig, notepad, calc, etc.)
- `help`: Display full CLI command reference
- `exit` / `quit`: Clean exit
