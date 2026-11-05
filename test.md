# Project Zia // Ultimate Verification & Manual Testing Guide

## 1. Automated Master Verification Suite (100% Passing)

Run the full end-to-end diagnostic suite covering all 15 subsystems and 40 sprint features:

```bash
python tests/ultimate_test_suite.py
```

### Chained CLI Quick Smoke Test:
```bash
python cli.py "sys troubleshoot && sys health && net audit && ports && secscan && fim check && prayer next && alarm list && schedule list && agent list && cam status && stt status && mac health && battery && route && clip get && weather && digest && habit streaks && theme cyan"
```

---

## 2. Comprehensive Manual Testing Checklist

While the automated suite validates 100% of internal logic, AST parsing, cryptography, database persistence, and API schemas, the physical hardware, acoustics, sensors, and cross-device network require real-world manual verification.

| Category | Component | What to Test Manually | Why it Requires Manual Testing |
| :--- | :--- | :--- | :--- |
| **Acoustics & Voice** | **Xperia Physical Mic** | In Termux, run `python cli.py xperia listen 5` and speak. | Validates physical MEMS microphone hardware gain, Android Termux audio capture permissions, and software noise gate under real ambient noise. |
| **Acoustics & Voice** | **Xperia Stereo Speakers** | Run `python cli.py xperia speak "Testing physical speakers"`. | Validates audio playback through the Sony Xperia 1 III front-facing stereo speakers via `termux-tts-speak` or `mpv`. |
| **Acoustics & Voice** | **Hands-Free Wake-Word** | Run `python cli.py wakeword on` and say *"Hey Zia"* from 2–3 meters away. | Requires live acoustic room reflections, human speech pitch variations, and Vosk audio stream processing. |
| **Acoustics & Voice** | **Audio Route Switcher** | Run `python cli.py route mac` then `python cli.py route bt`. | Tests physical audio jack switching or Bluetooth A2DP audio sink pairing with real headphones/laptop. |
| **Cross-Device LAN** | **Termux Wake-Lock** | Boot `./start_xperia.sh`, turn off phone screen, leave for 30+ mins. | Tests that Android Doze / power management does not suspend the Snapdragon 888 CPU while phone screen is black. |
| **Cross-Device LAN** | **MacBook RPC Agent** | From phone/PC: `python cli.py mac exec "uname -a"`. | Confirms physical Wi-Fi router packet routing between `192.168.1.X` (phone) and `192.168.1.Y` (MacBook). |
| **Cross-Device LAN** | **Desktop Notify Banner** | Run `python cli.py mac notify "Task Completed"`. | Confirms `notify-send` creates a visual XFCE notification popup on the MacBook display. |
| **Cross-Device LAN** | **Wake-on-LAN (WoL)** | Put a LAN PC to sleep and run `python cli.py wol <target_mac>`. | Requires motherboard BIOS WoL support and Ethernet NIC listening for UDP port 9 Magic Packets. |
| **Vision & Sensors** | **Xperia Camera Stream** | Run `python cli.py camstream` or browse `http://<phone_ip>:5000/api/camera/frame`. | Tests Termux rear camera lens hardware, autofocus, exposure, and JPEG encoding. |
| **Vision & Sensors** | **Webcam Behavior Senses** | Run `python cli.py cam scan` while looking away or resting head on hand. | Tests real lighting conditions, face detection angles, and behavioral triggers (<2% CPU). |
| **Visual Frontends** | **Live2D Portrait Window** | Run `python run.py`. | Verifies Live2D Kaguya shoulder portrait framing, 28 FPS rendering smoothness, and texture atlas loading. |
| **Visual Frontends** | **Dual-Mode Client UI** | Open `http://localhost:5000/` or run `python run.py`. Verify Default Minimal Mode (animated cyber eyes & audio waveform). Click `Load Live2D` or say `"load avatar"`, then `"stop avatar"`. | Verifies dual-mode client UI: Minimal mode runs with 0% VRAM / <15MB RAM; Live2D dynamically mounts and unmounts Cubism WebGL runtime without memory leaks. |
| **Visual Frontends** | **Vocal Mouth Lip-Sync** | Trigger a voice reply while watching Live2D model. | Confirms audio amplitude analysis properly drives the Live2D mouth open parameter (`ParamMouthOpenY`). |
| **Visual Frontends** | **Frameless Overlay** | Run `python run.py --overlay`. | Confirms the desktop background is 100% transparent and the avatar is freely draggable over code editors. |
| **LifeDesk Database** | **Habit Streak Sync** | Run `python cli.py habit log coding 60 "Built server.py"` then `python cli.py habit streaks`. | Validates persistent SQLite write to `data/lifedesk/habits.db`, calculation of contiguous streaks, and ASCII-safe CLI output. |
| **LifeDesk Database** | **Expense Natural Language** | Run `python cli.py "spent 120 on lunch"` or POST to `/api/lifedesk/expenses`. | Validates regex pattern matching, auto-categorization into `finance.db`, and daily running expense total accumulator. |
| **Telegram Gateway** | **Remote Bot Text Alert** | Set `.env` `TELEGRAM_BOT_TOKEN` & `TELEGRAM_CHAT_ID`, run `python cli.py tg send "Zia Online"`. | Validates Telegram Bot API HTTP connection, chat ID routing, and markdown parsing without third-party bloat. |
| **Telegram Gateway** | **Remote Voice Note (TTS)** | Run `python cli.py tg voice "Palakkad prayer time in 15 minutes"`. | Validates Microsoft Edge-TTS neural speech synthesis into `.ogg/.mp3` and Telegram `sendVoice` multipart upload. |
| **Smart IoT & ADB** | **Wireless ADB Projector** | Run `python cli.py projector "https://miruro.tv"`. | Confirms wireless ADB (`5555`) handshake with projector IP (`192.168.1.65`) and Android `am start -a android.intent.action.VIEW` intent. |
| **Smart IoT & ADB** | **Tablet Botim VoIP Calling** | Run `python cli.py botim "Family"`. | Confirms wireless ADB handshake with Android tablet (`192.168.1.75`) and launch of Botim calling intent. |
| **Smart IoT & ADB** | **ESP8266 / Relay Control** | Run `python cli.py relay desk_lamp on` or `relay ceiling_fan toggle`. | Validates local REST HTTP dispatch to Tasmota/Shelly/NodeMCU microcontroller relay board. |
| **MacBook Hardware** | **SMC Fan Manual Control** | On Linux Mint: `python cli.py fan max` then `python cli.py fan auto`. | Requires physical MacBook Pro 2007 SMC controller (`applesmc`) to spin fans up to 6000 RPM. |
| **MacBook Hardware** | **Display Brightness** | Run `python cli.py sys bright down` and `python cli.py sys bright up`. | Confirms hardware backlight inverter PWM control (`/sys/class/backlight`) physically dims LCD panel. |
| **MacBook Hardware** | **XFCE Compositor Toggle** | Run `python cli.py sys compositor off`. | Confirms window shadows disable, dropping GPU VRAM usage and boosting Core 2 Duo framerates. |
| **OS Privileges** | **Passwordless Sudo** | Run `python cli.py sudo apt update`. | Confirms `/etc/sudoers.d/zia` allows non-interactive root commands without prompting for password. |

