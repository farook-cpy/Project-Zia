# Project FAITH // Zia Desktop Companion

An autonomous, multimodal, and expressive desktop companion designed for 24/7 low-power execution across Linux Mint, macOS, and Windows.

---

## ⚡ Operational Modes: Visual Window, Floating Overlay, or Text CLI

### 1. Hybrid 24/7 Server Node (Sony Xperia 1 III + Android Termux)
- **Xperia (Termux)**: Run `./start_xperia.sh`
- Boots the autonomous background server on `0.0.0.0:5000` with `termux-wake-lock`, capped subagent worker pool (`max_workers=2`), ambient room audio capture, physical speaker output, Palakkad prayer calculator, and alarm scheduler.
- **MacBook Pro (Linux Mint XFCE)**: Run `./start_mac_agent.sh`
- Boots the lightweight RPC agent on `0.0.0.0:5001` allowing the Xperia server to safely run system actions, health checks, and `notify-send` desktop banners on the laptop.

### 2. Visual Mode (Framed Window)
- **Windows**: Double-click [`start.bat`](file:///c:/Users/Student/Documents/Project%20Zia/start.bat) or run `python run.py`
- **Linux Mint / macOS**: `./start.sh`
- Runs in a framed window with Live2D shoulder portrait framing, real-time vocal lip-sync, and Web Speech API listening (**Spacebar**).

### 3. Transparent Floating Desktop Overlay Mode
- **Windows**: Double-click [`start_overlay.bat`](file:///c:/Users/Student/Documents/Project%20Zia/start_overlay.bat) or run `python run.py --overlay`
- **Linux Mint / macOS**: `./start_overlay.sh`
- Zero-background frameless Live2D companion that sits on top of all desktop windows and is draggable anywhere.

### 4. Pure Text CLI Mode (0% VRAM, <0.5% CPU, Zero Clutter)
- **Windows**: Double-click [`start_cli.bat`](file:///c:/Users/Student/Documents/Project%20Zia/start_cli.bat) or run `python cli.py`
- **Linux Mint / macOS**: `./start_cli.sh`
- Direct UNIX-style terminal prompt (`zia> `) without any WebGL graphics or speech synthesis. Access all features (chat, webcam senses, debugger, compiler, vault, scheduler, network sentinel, bluetooth, subagents, system diagnostics, MCP files, and hardware controls).

---

## 🛠️ CLI Command Reference

```bash
zia> plan "Migrate auth service" # Multi-step reasoning plan visualizer tree
zia> review engine/server.py     # Smart code reviewer & static security linting
zia> testgen engine/prayer_times.py # Automated AST unit test generator (tests/test_*.py)
zia> qtask coder "Optimize loop" # Enqueue task to persistent SQLite queue
zia> qprocess                    # Process pending queue tasks
zia> budget                      # Dynamic Gemini API token budget & USD accumulator
zia> ocr screenshot.png          # Local OCR text extraction (0 cloud dependencies)
zia> docs https://docs.python.org# Autonomous documentation scraper & markdown cache
zia> deps server.py              # Background dependency resolver & missing import scanner
zia> drop send report.pdf        # Phone-to-laptop local file drop (AirDrop clone)
zia> drop list                   # List received files in data/transfers/
zia> battery                     # Mirrored Xperia battery % and thermal state
zia> route phone | mac | bt      # Audio route switcher
zia> wol 00:11:22:33:44:55       # Remote Wake-on-LAN trigger (UDP Magic Packet)
zia> pinglan 192.168.1.50        # Network ping & latency watchdog
zia> camstream                   # Capture snapshot from Xperia camera
zia> dashboard                   # Access web health dashboard (:5000/dashboard)
zia> incognito on / off          # Ephemeral chat mode (zero trace on disk)
zia> fim check / fim update      # File Integrity Monitor (SHA-256 baseline audit)
zia> ports                       # Exposed port auditor (flags 0.0.0.0 listeners)
zia> sslcert google.com          # SSL certificate expiry watchdog
zia> secscan engine/             # Codebase scanner for leaked secrets & API keys
zia> tunnel user host.com        # Generate reverse SSH tunnel command
zia> weather                     # Context-aware Palakkad weather greeter (Open-Meteo)
zia> chime notification          # Procedural retro audio soundboard synthesis
zia> focus start / focus stop    # Adaptive focus music stream & session tracking
zia> conflict 12:30              # Smart meeting vs prayer conflict resolver
zia> digest                      # End-of-day developer digest (git, alarms, prayers)
zia> presence                    # Geofence home presence detection via router
zia> theme cyan | amber | matrix # Retro HUD color theme switcher
zia> habit log coding / streaks  # Smart habit streak tracker
zia> macro deploy                # Interactive single-word shortcut macro executor
zia> mac status                  # Inspect remote MacBook RPC bridge connection
zia> mac health                  # Read MacBook CPU %, core temp, RAM, battery via RPC
zia> mac exec uname -a           # Remotely execute command on MacBook terminal
zia> mac notify "Task Done"      # Dispatch notify-send banner to MacBook screen
zia> xperia status               # Check Android Termux audio hardware status
zia> xperia speak "Hello"        # Play TTS speech directly out of Xperia speakers
zia> xperia listen 5             # Capture ambient room audio from Xperia microphones
zia> prayer times                # Palakkad, Kerala daily prayer schedule (100% offline)
zia> alarm set 8:00 pm           # Absolute clock alarm ("Wake me at 8:00 pm")
zia> timer 20m push code         # Relative countdown timer ("Remind me in 20m")
zia> cam status                  # Local Webcam Senses (<2% CPU, detects thinking/stressed/away)
zia> cam test stressed           # Test behavioral trigger simulation
zia> debug                       # Automated Error Traceback Debugger & terminal code fix
zia> vision What is on screen?   # Multimodal Screen Vision Analysis via Gemini Flash
zia> cmd find files larger 100mb # Compile natural language to safe shell pipelines
zia> vault store github token ghp# Encrypted machine-bound credential vault
zia> schedule "Check backups" 2h # Automated Natural Language Cron & Task Scheduler
zia> net ports                   # Network Traffic & Bandwidth Sentinel (ports & speed)
zia> clip get / clip sync on     # Multi-Device LAN Clipboard Sync Server (Port 8767)
zia> mount list                  # Disk Partition & Storage Mount Manager
zia> cpu gov powersave           # CPU Frequency Governor Switcher (battery saving)
zia> disp profile reading        # Display luminance & contrast calibration curves
zia> fan max / fan auto          # Cooling Fan Manual Override (MacBook SMC/hwmon)
zia> audio list                  # Audio Sink / Route Switcher (Speakers/Headphones/BT)
zia> wakeword on                 # Hands-free background listener ("Hey Zia")
zia> avatar live                  # 24 FPS ANSI/ASCII Retro Terminal Avatar (0% VRAM)
zia> listen                       # Capture voice offline via Vosk (~25MB RAM, no browser)
zia> stt status                   # Check offline speech recognition status
zia> sys health                   # Live CPU %, core temp, RAM, Swap, Disk, Uptime
zia> sys troubleshoot             # Automatic system troubleshooting
zia> sys vol up / vol down        # Adjust master volume
zia> sys bright up / down         # Adjust monitor brightness
zia> sys lock / sys unlock        # Lock or unlock desktop session (XFCE loginctl / Win)
zia> sys compositor off           # Disable XFCE compositor to boost legacy GPU
zia> sys sudo setup               # Auto-configure passwordless visudo rule
zia> sudo apt update              # Run root command via passwordless sudo
zia> bt list                      # List paired Bluetooth devices
zia> agent run coder "search def" # Spawn background subagent (<20% CPU budget)
zia> mcp read engine/brain.py     # Raw code reading (100% precision, zero OCR)
zia> organize downloads           # Auto-categorize unorganized files into folders
zia> iot toggle                   # Toggle Wi-Fi relay lights
zia> mem show                     # View persistent long-term memory
zia> run dir / ls                 # Terminal command execution (auto-records failures for debug)
zia> chat <your question>         # Direct Gemini Flash query
```
