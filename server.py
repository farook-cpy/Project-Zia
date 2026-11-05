#!/usr/bin/env python3
"""
Project Zia - Xperia Server Backend (server.py)
24/7 autonomous background server node running inside Termux on Sony Xperia 1 III
(Snapdragon 888, 12GB RAM, Android + Termux) listening on 0.0.0.0:5000.

Handles:
1. Incoming text/voice queries from clients (MacBook, phones, web UI)
2. Gemini Flash API routing for the AI brain
3. Persistent state management (data/memory.json)
4. Subagent worker thread pool (strictly capped to max_workers=2 for mobile efficiency)
5. Ambient room audio capture & physical speaker playback via Android Termux API
6. Secure JSON-RPC bridge for remote MacBook executions & notify-send banners
7. Palakkad daily prayer calculations & natural language alarm scheduling
8. Cross-Device Ecosystem & Security Vault endpoints (AirDrop, camera, FIM, port audit)
"""

import os
import sys
import time
import json
import psutil
from pathlib import Path
from flask import Flask, request, jsonify, Response, send_file

# Engine Modules
from engine.config import GEMINI_API_KEY
from engine.brain import brain_engine
from engine.memory import memory_engine
from engine.subagents import subagent_pool
from engine.local_commands import local_router
from engine.prayer_times import prayer_engine
from engine.alarm_manager import alarm_manager
from engine.scheduler import scheduler
from engine.audio_bridge import audio_bridge
from engine.rpc_bridge import rpc_bridge
from engine.tts_engine import tts_engine
from engine.ecosystem_bridge import ecosystem_bridge
from engine.security_vault import security_vault
from engine.agentic_ops import agentic_ops
from engine.ambient_intelligence import ambient_engine
from engine.lifedesk_bridge import lifedesk_bridge
from engine.remote_gateway import telegram_gateway
from engine.iot_bridge import iot_bridge
from engine.browser_agent import browser_agent
from engine.family_bridge import family_bridge

BASE_DIR = Path(__file__).resolve().parent
CLIENT_UI_DIR = BASE_DIR / "client_ui"
ASSETS_DIR = BASE_DIR / "assets"

app = Flask("ZiaXperiaServer")

SERVER_PORT = int(os.environ.get("PORT", 5000))
WS_PORT = int(os.environ.get("WS_PORT", 8765))
RPC_SECRET = os.environ.get("RPC_SECRET", "zia_palakkad_xperia_secure_key_888")
START_TIME = time.time()


# -----------------------------------------------------------------------------
# 1. Server Health, Telemetry & Client UI Static Serving
# -----------------------------------------------------------------------------
@app.route("/", methods=["GET"])
def index_root():
    """Serves the Client UI dashboard if requested by browser, or returns node status."""
    accept = request.headers.get("Accept", "")
    if "text/html" in accept or ("*/*" in accept and not request.is_json):
        index_html = CLIENT_UI_DIR / "index.html"
        if index_html.exists():
            return send_file(index_html, mimetype="text/html")
    return jsonify({
        "status": "online",
        "service": "Project Zia // Xperia Server Node",
        "node": "Sony Xperia 1 III (Android Termux)",
        "uptime_sec": int(time.time() - START_TIME)
    })


@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({
        "status": "online",
        "service": "Project Zia // Xperia Server Node",
        "node": "Sony Xperia 1 III (Android Termux)",
        "uptime_sec": int(time.time() - START_TIME)
    })


@app.route("/style.css", methods=["GET"])
def serve_css():
    css_file = CLIENT_UI_DIR / "style.css"
    if css_file.exists():
        return send_file(css_file, mimetype="text/css")
    return ("Not Found", 404)


@app.route("/app.js", methods=["GET"])
def serve_js():
    js_file = CLIENT_UI_DIR / "app.js"
    if js_file.exists():
        return send_file(js_file, mimetype="application/javascript")
    return ("Not Found", 404)


@app.route("/vendor/<path:filename>", methods=["GET"])
def serve_vendor(filename):
    vendor_file = CLIENT_UI_DIR / "vendor" / filename
    if vendor_file.exists():
        mimetype = "application/javascript" if filename.endswith(".js") else "application/octet-stream"
        return send_file(vendor_file, mimetype=mimetype)
    return ("Not Found", 404)


@app.route("/assets/<path:filename>", methods=["GET"])
def serve_assets(filename):
    asset_file = ASSETS_DIR / filename
    if asset_file.exists():
        return send_file(asset_file)
    return ("Not Found", 404)


@app.route("/api/status", methods=["GET"])
def get_status():
    """Returns comprehensive server diagnostics, mobile battery, and subagents."""
    cpu_pct = psutil.cpu_percent(interval=0.1)
    vm = psutil.virtual_memory()

    # Android / Host battery telemetry
    battery_info = {}
    bat = psutil.sensors_battery()
    if bat:
        battery_info = {
            "percent": int(bat.percent),
            "power_plugged": bat.power_plugged
        }

    next_prayer = prayer_engine.get_next_prayer()
    active_alarms = alarm_manager.list_active()
    mac_online = rpc_bridge.is_mac_online()

    return jsonify({
        "status": "healthy",
        "node": "Sony Xperia 1 III (Snapdragon 888)",
        "uptime_sec": int(time.time() - START_TIME),
        "cpu_percent": cpu_pct,
        "ram_used_mb": int(vm.used / (1024 * 1024)),
        "ram_total_mb": int(vm.total / (1024 * 1024)),
        "battery": battery_info,
        "audio_hardware": audio_bridge.get_hardware_status(),
        "macbook_client_online": mac_online,
        "macbook_host": f"{rpc_bridge.mac_host}:{rpc_bridge.mac_port}",
        "subagents": {
            "max_workers": 2,
            "tasks_count": len(subagent_pool.list_tasks())
        },
        "next_prayer": next_prayer,
        "active_alarms_count": len(active_alarms)
    })


# -----------------------------------------------------------------------------
# 2. Client Query & Chat Router (Zero-Token Local + Gemini Flash)
# -----------------------------------------------------------------------------
@app.route("/api/chat", methods=["POST"])
def handle_chat():
    """
    Main dialogue router:
    - Scrubs prompt payload with Security Vault to prevent secret leaks.
    - First evaluates local zero-token command router (apps, volume, prayer, alarms).
    - If command requires remote MacBook action, dispatches via RPC bridge.
    - Otherwise routes to Gemini Flash model with encrypted logging & token tracking.
    """
    data = request.get_json(silent=True) or {}
    raw_text = data.get("text", "").strip()

    if not raw_text:
        return jsonify({"error": "Empty prompt provided."}), 400

    ambient_engine.record_activity()

    # Pre-flight prompt scrub (prevents leaking API keys or secrets to Gemini)
    user_text = security_vault.scrub_prompt_payload(raw_text)

    # 1. Fast Local Command Router (0 LLM Tokens)
    local_match = local_router.match_and_execute(user_text)
    if local_match:
        # Check if any action requires remote execution on MacBook
        for act in local_match.get("actions", []):
            if isinstance(act, dict) and act.get("target_mac"):
                rpc_bridge.execute_remote_command(act["target_mac"])

        security_vault.log_encrypted_event({
            "source": "local_router",
            "prompt": user_text,
            "reply": local_match["text"]
        })

        import asyncio
        audio_b64 = None
        try:
            audio_b64 = asyncio.run(tts_engine.generate_speech_base64(local_match["text"], mood=local_match.get("mood", "F1")))
        except Exception:
            pass

        return jsonify({
            "source": "local_router",
            "tokens_consumed": 0,
            "text": local_match["text"],
            "mood": local_match.get("mood", "F1"),
            "audio": audio_b64,
            "actions": local_match.get("actions", [])
        })

    # 2. Gemini Flash AI Brain Routing
    import asyncio
    active_win = data.get("active_window")
    try:
        reply = asyncio.run(brain_engine.think_and_reply(user_message=user_text, active_window=active_win))

        # Track estimated tokens
        prompt_tokens = len(user_text.split()) * 2
        candidate_tokens = len(reply.get("text", "").split()) * 2
        agentic_ops.track_token_usage("gemini_flash", prompt_tokens, candidate_tokens)

        security_vault.log_encrypted_event({
            "source": "gemini_flash",
            "prompt": user_text,
            "reply": reply["text"]
        })

        audio_b64 = None
        try:
            audio_b64 = asyncio.run(tts_engine.generate_speech_base64(reply["text"], mood=reply.get("mood", "F1")))
        except Exception:
            pass

        return jsonify({
            "source": "gemini_flash",
            "text": reply["text"],
            "mood": reply.get("mood", "F1"),
            "audio": audio_b64,
            "actions": reply.get("actions", [])
        })
    except Exception as e:
        return jsonify({
            "source": "fallback",
            "error": str(e),
            "text": f"Error consulting Gemini Flash: {e}",
            "mood": "F3"
        }), 500


@app.route("/api/query", methods=["POST"])
def direct_query():
    """Direct raw prompt execution via Gemini Flash."""
    data = request.get_json(silent=True) or {}
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return jsonify({"error": "Prompt required"}), 400

    import asyncio
    try:
        reply = asyncio.run(brain_engine.think_and_reply(user_message=prompt))
        return jsonify(reply)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -----------------------------------------------------------------------------
# 2.5 Agent-Browser CDP Automation & Family OTP Webhook Endpoints
# -----------------------------------------------------------------------------
@app.route("/api/browser/open", methods=["POST"])
def browser_open():
    """Navigates to URL using agent-browser CDP wrapper."""
    data = request.get_json(silent=True) or {}
    url = data.get("url", "https://youtube.com")
    res = browser_agent.open_url(url)
    return jsonify(res)


@app.route("/api/browser/snapshot", methods=["GET"])
def browser_snapshot():
    """Returns compact token-efficient accessibility tree snapshot."""
    return jsonify(browser_agent.get_accessibility_snapshot())


@app.route("/api/webhook/notification", methods=["POST"])
def family_notification_webhook():
    """
    Secure local webhook to capture background SMS/App notifications forwarded
    from family Android devices (Samsung Galaxy phones). Zero cloud tokens.
    """
    data = request.get_json(silent=True) or {}
    device = data.get("device", "Samsung Galaxy")
    app_name = data.get("app", "SMS")
    message = data.get("message", "").strip()
    sender = data.get("sender", "Unknown")

    if not message:
        return jsonify({"error": "No notification message provided"}), 400

    res = family_bridge.enqueue_notification(
        device=device,
        app_name=app_name,
        message=message,
        sender=sender
    )
    return jsonify(res), 200


@app.route("/api/otp", methods=["GET"])
def get_latest_otp():
    """Returns the latest extracted OTP code from family SMS verifications."""
    latest = family_bridge.get_latest_otp()
    recent = family_bridge.list_recent_otps(limit=5)
    return jsonify({
        "latest_otp": latest,
        "recent_otps": recent,
        "queue_count": len(family_bridge.notifications)
    })


# -----------------------------------------------------------------------------
# 3. Persistent Memory & State Management
# -----------------------------------------------------------------------------
@app.route("/api/memory", methods=["GET"])
def get_memory():
    return jsonify(memory_engine.data)


@app.route("/api/memory/note", methods=["POST"])
def add_memory_note():
    data = request.get_json(silent=True) or {}
    note = data.get("note", "").strip()
    if not note:
        return jsonify({"error": "Note text required"}), 400

    memory_engine.add_note(note)
    return jsonify({"success": True, "note": note})


@app.route("/api/memory/prayer", methods=["POST"])
def log_prayer_completion():
    data = request.get_json(silent=True) or {}
    prayer_name = data.get("prayer")
    res = prayer_engine.record_prayer_status(prayer_name, status="completed")
    return jsonify(res)


# -----------------------------------------------------------------------------
# 4. Mobile-Optimized Subagents Pool (Strictly Max 2 Workers)
# -----------------------------------------------------------------------------
@app.route("/api/subagents", methods=["GET"])
def list_subagents():
    return jsonify({
        "max_workers": 2,
        "tasks": subagent_pool.list_tasks()
    })


@app.route("/api/subagents/spawn", methods=["POST"])
def spawn_subagent():
    data = request.get_json(silent=True) or {}
    role = data.get("role", "researcher")
    description = data.get("description", "").strip()
    if not description:
        return jsonify({"error": "Task description required"}), 400

    task_id = subagent_pool.spawn(role, description)
    return jsonify({
        "success": True,
        "task_id": task_id,
        "role": role,
        "message": f"Spawned subagent [{task_id}] with role '{role}' (max_workers=2)."
    })


@app.route("/api/subagents/<task_id>", methods=["GET"])
def get_subagent_task(task_id):
    task = subagent_pool.get_task(task_id)
    if task:
        return jsonify(task)
    return jsonify({"error": "Task not found"}), 404


# -----------------------------------------------------------------------------
# 5. Audio & Room Listening (Android Termux API)
# -----------------------------------------------------------------------------
@app.route("/api/audio/listen", methods=["POST"])
def record_ambient_audio():
    """Captures ambient room audio from Xperia microphones with software noise gate."""
    data = request.get_json(silent=True) or {}
    duration = int(data.get("duration_sec", 5))
    res = audio_bridge.record_room_audio(duration_sec=duration)
    return jsonify(res)


@app.route("/api/audio/speak", methods=["POST"])
def speak_out_loud():
    """Speaks text directly out of the Xperia's physical stereo speakers."""
    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()
    mood = data.get("mood", "F1")
    if not text:
        return jsonify({"error": "Text required"}), 400

    res = audio_bridge.speak(text, mood=mood)
    return jsonify(res)


# -----------------------------------------------------------------------------
# 6. Client-Server RPC Bridge for Remote MacBook Actions
# -----------------------------------------------------------------------------
@app.route("/api/rpc/register", methods=["POST"])
def register_macbook_client():
    """
    Called by mac_agent.py upon startup to register its IP address on the LAN.
    """
    data = request.get_json(silent=True) or {}
    client_ip = request.remote_addr
    port = int(data.get("agent_port", 5001))
    token = request.headers.get("X-Zia-Secret", "")

    if RPC_SECRET and token != RPC_SECRET:
        return jsonify({"error": "Unauthorized"}), 401

    res = rpc_bridge.register_client(client_ip, port)
    return jsonify(res)


@app.route("/api/mac/exec", methods=["POST"])
def execute_on_mac():
    """Dispatches a command for remote execution on the MacBook."""
    data = request.get_json(silent=True) or {}
    cmd = data.get("command", "").strip()
    if not cmd:
        return jsonify({"error": "Command required"}), 400

    res = rpc_bridge.execute_remote_command(cmd)
    return jsonify(res)


@app.route("/api/mac/health", methods=["GET"])
def get_remote_mac_health():
    """Queries MacBook CPU temperature, usage, RAM, and battery via RPC."""
    res = rpc_bridge.get_remote_mac_health()
    return jsonify(res)


@app.route("/api/mac/notify", methods=["POST"])
def notify_mac():
    """Triggers notify-send desktop notification on the MacBook."""
    data = request.get_json(silent=True) or {}
    title = data.get("title", "Project Zia")
    message = data.get("message", "")
    res = rpc_bridge.send_remote_notification(title, message)
    return jsonify(res)


@app.route("/api/mac/volume", methods=["POST"])
def remote_mac_volume():
    data = request.get_json(silent=True) or {}
    action = data.get("action", "up")
    step = int(data.get("step", 5))
    res = rpc_bridge.remote_volume(action, step)
    return jsonify(res)


# -----------------------------------------------------------------------------
# 7. Palakkad Prayer Times & Natural Language Alarms
# -----------------------------------------------------------------------------
@app.route("/api/prayer", methods=["GET"])
def get_prayers():
    return jsonify({
        "schedule": prayer_engine.get_prayer_times(),
        "next": prayer_engine.get_next_prayer()
    })


@app.route("/api/alarms", methods=["GET"])
def list_alarms():
    return jsonify({
        "active_alarms": alarm_manager.list_active(),
        "cron_tasks": scheduler.list_schedules()
    })


@app.route("/api/alarms", methods=["POST"])
def create_alarm():
    data = request.get_json(silent=True) or {}
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return jsonify({"error": "Prompt required"}), 400

    res = scheduler.schedule_from_natural_language(prompt)
    return jsonify(res)


# -----------------------------------------------------------------------------
# 8. Responsive Device Health Dashboard & Camera Feed
# -----------------------------------------------------------------------------
@app.route("/dashboard", methods=["GET"])
def device_health_dashboard():
    """Serves ultra-lightweight responsive status dashboard."""
    html = ecosystem_bridge.generate_dashboard_html()
    return Response(html, mimetype="text/html")


@app.route("/api/camera/frame", methods=["GET"])
def get_camera_snapshot():
    """Returns the latest rear camera frame from the Xperia node."""
    res = ecosystem_bridge.capture_remote_camera_frame()
    if "error" in res:
        return jsonify(res), 500
    cache_path = Path(res["cached_file"])
    if cache_path.exists():
        return send_file(cache_path, mimetype="image/jpeg")
    return jsonify(res)


# -----------------------------------------------------------------------------
# 9. Local File Drop (AirDrop Clone)
# -----------------------------------------------------------------------------
@app.route("/api/drop/receive", methods=["POST"])
def receive_file_drop():
    """Receives dropped file bytes from remote devices (MacBook/phone)."""
    filename = request.headers.get("X-Filename", f"drop_{int(time.time())}.bin")
    file_bytes = request.data
    if not file_bytes:
        return jsonify({"error": "No file content received."}), 400

    res = ecosystem_bridge.save_received_file(filename, file_bytes)
    return jsonify(res)


# -----------------------------------------------------------------------------
# 10. Ambient Intelligence, Weather, Habits, Focus & Security Endpoints
# -----------------------------------------------------------------------------
@app.route("/api/weather", methods=["GET"])
def get_weather():
    """Returns context-aware Palakkad weather greeting."""
    lat = float(request.args.get("lat", 10.7867))
    lon = float(request.args.get("lon", 76.6548))
    return jsonify(ambient_engine.get_weather_greeting(lat, lon))


@app.route("/api/digest", methods=["GET"])
def get_daily_digest():
    """Returns end-of-day developer digest summary."""
    return jsonify(ambient_engine.compile_daily_digest())


@app.route("/api/habits", methods=["GET", "POST"])
def handle_habits():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        habit = data.get("habit", "coding")
        note = data.get("note", "")
        return jsonify(ambient_engine.log_habit(habit, note))
    return jsonify(ambient_engine.get_habit_streaks())


@app.route("/api/focus", methods=["POST"])
def toggle_focus():
    data = request.get_json(silent=True) or {}
    action = data.get("action", "toggle")
    return jsonify(ambient_engine.toggle_focus_mode(action))


@app.route("/api/chime", methods=["POST"])
def trigger_soundboard_chime():
    data = request.get_json(silent=True) or {}
    sound_type = data.get("sound", "notification")
    p = ambient_engine.synthesize_chime(sound_type)
    return jsonify({"success": True, "chime": sound_type, "file": str(p)})


@app.route("/api/security/audit", methods=["GET"])
def security_audit():
    """Returns exposed port audit and file integrity status."""
    ports = security_vault.audit_exposed_ports()
    fim = security_vault.check_fim_integrity()
    return jsonify({
        "status": "secure" if fim.get("is_intact") else "warning",
        "exposed_ports": ports,
        "file_integrity": fim,
        "incognito_active": security_vault.incognito_active
    })


# -----------------------------------------------------------------------------
# 11. LifeDesk SQLite Bridge Endpoints (Habits & Personal Finance)
# -----------------------------------------------------------------------------
@app.route("/api/lifedesk/habits", methods=["GET", "POST"])
def lifedesk_habits():
    """Returns habit streaks or logs a habit via natural language or fields."""
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        text = data.get("text")
        if text:
            res = lifedesk_bridge.parse_and_log_habit(text)
            return jsonify(res)
        habit_name = data.get("habit") or data.get("name")
        if not habit_name:
            return jsonify({"error": "Habit name or text required."}), 400
        duration = float(data.get("duration", data.get("value", 1.0)))
        note = data.get("note", "")
        res = lifedesk_bridge.log_habit(habit_name, value=duration, note=note)
        return jsonify(res)
    return jsonify(lifedesk_bridge.get_habit_streaks())


@app.route("/api/lifedesk/expenses", methods=["GET", "POST"])
def lifedesk_expenses():
    """Returns daily/monthly expense ledgers or logs transactions."""
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        text = data.get("text")
        if text:
            res = lifedesk_bridge.parse_and_log_expense(text)
            return jsonify(res)
        amount = data.get("amount")
        if amount is None:
            return jsonify({"error": "Amount or text required."}), 400
        category = data.get("category", "general")
        desc = data.get("description", "")
        tx_type = data.get("type", "expense")
        res = lifedesk_bridge.log_expense(float(amount), category, desc, tx_type)
        return jsonify(res)
    daily = lifedesk_bridge.get_daily_expenses()
    breakdown = lifedesk_bridge.get_monthly_breakdown()
    return jsonify({
        "daily": daily,
        "monthly_breakdown": breakdown
    })


@app.route("/api/lifedesk/summary", methods=["GET"])
def lifedesk_summary():
    """Returns overall financial ledger summary."""
    return jsonify(lifedesk_bridge.get_financial_summary())


# -----------------------------------------------------------------------------
# 12. Remote Telegram Gateway Endpoints
# -----------------------------------------------------------------------------
@app.route("/api/telegram/status", methods=["GET"])
def telegram_status():
    """Returns Telegram gateway connection and configuration status."""
    return jsonify(telegram_gateway.get_status())


@app.route("/api/telegram/send", methods=["POST"])
def telegram_send():
    """Dispatches a text message or voice note to configured Telegram chat."""
    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "Text required."}), 400
    msg_type = data.get("type", "text")
    chat_id = data.get("chat_id")
    if msg_type == "voice":
        res = telegram_gateway.send_voice_note(text, chat_id=chat_id)
    else:
        res = telegram_gateway.send_message(text, chat_id=chat_id)
    return jsonify(res)


# -----------------------------------------------------------------------------
# 13. Smart IoT & Wireless ADB Controller Endpoints
# -----------------------------------------------------------------------------
@app.route("/api/iot/status", methods=["GET"])
def iot_status():
    """Returns IoT relays and wireless ADB devices status."""
    return jsonify(iot_bridge.get_status())


@app.route("/api/iot/command", methods=["POST"])
@app.route("/api/iot/relay", methods=["POST"])
def iot_relay_command():
    """Controls ESP8266/NodeMCU relays (desk lamp, fan, etc.)."""
    data = request.get_json(silent=True) or {}
    device = data.get("device", "desk_lamp")
    action = data.get("action", "toggle")
    res = iot_bridge.control_relay(device, action)
    return jsonify(res)


@app.route("/api/iot/projector", methods=["POST"])
def iot_projector():
    """Launches stream intent on Android projector via wireless ADB."""
    data = request.get_json(silent=True) or {}
    url = data.get("url", "https://miruro.tv")
    res = iot_bridge.launch_projector_stream(url)
    return jsonify(res)


@app.route("/api/iot/call", methods=["POST"])
def iot_call():
    """Triggers hands-free Botim VoIP call on Android tablet via wireless ADB."""
    data = request.get_json(silent=True) or {}
    contact = data.get("contact", "Family")
    res = iot_bridge.trigger_botim_call(contact)
    return jsonify(res)


# -----------------------------------------------------------------------------
# WebSocket Background Daemon (Port 8765)
# -----------------------------------------------------------------------------
def run_websocket_daemon(port=8765):
    """Background WebSocket listener for real-time client UI streaming."""
    import threading
    import asyncio
    try:
        import websockets
    except ImportError:
        return

    connected_clients = set()

    async def ws_handler(websocket):
        connected_clients.add(websocket)
        try:
            await websocket.send(json.dumps({
                "type": "status",
                "message": "Connected to Project Zia Xperia Node."
            }))
            async for raw in websocket:
                try:
                    payload = json.loads(raw)
                except Exception:
                    continue
                if payload.get("type") == "chat":
                    user_text = payload.get("text", "").strip()
                    if not user_text:
                        continue
                    # 1. Local command
                    local_match = local_router.match_and_execute(user_text)
                    if local_match:
                        audio_b64 = None
                        try:
                            audio_b64 = await tts_engine.generate_speech_base64(local_match["text"], mood=local_match.get("mood", "F1"))
                        except Exception:
                            pass
                        await websocket.send(json.dumps({
                            "type": "response",
                            "text": local_match["text"],
                            "mood": local_match.get("mood", "F1"),
                            "audio": audio_b64,
                            "actions": local_match.get("actions", [])
                        }))
                        continue
                    # 2. Brain
                    try:
                        reply = await brain_engine.think_and_reply(user_message=user_text)
                        audio_b64 = None
                        try:
                            audio_b64 = await tts_engine.generate_speech_base64(reply["text"], mood=reply.get("mood", "F1"))
                        except Exception:
                            pass
                        await websocket.send(json.dumps({
                            "type": "response",
                            "text": reply["text"],
                            "mood": reply.get("mood", "F1"),
                            "audio": audio_b64,
                            "actions": reply.get("actions", [])
                        }))
                    except Exception as e:
                        await websocket.send(json.dumps({
                            "type": "response",
                            "text": f"Brain query error: {e}",
                            "mood": "F3",
                            "audio": None
                        }))
        except Exception:
            pass
        finally:
            connected_clients.discard(websocket)

    async def server_main():
        try:
            async with websockets.serve(ws_handler, "0.0.0.0", port):
                await asyncio.Future()
        except Exception as e:
            print(f"[*] WebSocket daemon notice: {e}")

    def loop_runner():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(server_main())
        except Exception:
            pass

    t = threading.Thread(target=loop_runner, daemon=True)
    t.start()


# -----------------------------------------------------------------------------
# Main Entry Point
# -----------------------------------------------------------------------------
def main():
    print("\033[96m\033[1m======================================================================")
    print(" PROJECT ZIA // XPERIA 1 III 24/7 SERVER NODE (Android + Termux)")
    print(f" Listening on 0.0.0.0:{SERVER_PORT} (Under termux-wake-lock)")
    print(f" Client UI: http://0.0.0.0:{SERVER_PORT}/ | WebSocket: ws://0.0.0.0:{WS_PORT}")
    print(" Subagents: strictly max_workers=2 (Thermal/Battery Guard)")
    print("======================================================================\033[0m")

    # Start WebSocket daemon
    run_websocket_daemon(port=WS_PORT)

    # Start Telegram background poller if configured
    if telegram_gateway.is_configured:
        telegram_gateway.start_polling()

    # Start Flask server
    app.run(host="0.0.0.0", port=SERVER_PORT, debug=False, threaded=True)


if __name__ == "__main__":
    main()

