import asyncio
import json
import time
from pathlib import Path
from aiohttp import web

from engine.config import (
    HOST, HTTP_PORT, FRONTEND_DIR, ASSETS_DIR,
    PROACTIVE_IDLE_SECONDS, GEMINI_API_KEY
)
from engine.brain import brain_engine
from engine.local_commands import local_router
from engine.senses import screen_sensor
from engine.tts_engine import tts_engine
from engine.heartbeat import heartbeat_engine
from engine.local_stt import local_stt

CLIENT_UI_DIR = Path(__file__).resolve().parent.parent / "client_ui"

connected_websockets = set()
last_user_activity = time.time()

async def broadcast_to_clients(payload: dict):
    """Broadcasts a payload dict to all connected WebSocket clients."""
    msg = json.dumps(payload)
    for ws in list(connected_websockets):
        try:
            await ws.send_str(msg)
        except Exception:
            pass

async def ws_handler(request):
    global last_user_activity
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    connected_websockets.add(ws)
    print(f"[WebSocket] Client connected: {request.remote}")

    # Register activity
    heartbeat_engine.register_activity()

    # Send initial welcome and configuration status
    await ws.send_str(json.dumps({
        "type": "status",
        "message": "Connected to Project FAITH local engine.",
        "has_api_key": bool(brain_engine.api_key)
    }))

    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                last_user_activity = time.time()
                woke_up = heartbeat_engine.register_activity()
                if woke_up:
                    await ws.send_str(json.dumps({"type": "expression", "id": "F1"}))
                try:
                    payload = json.loads(msg.data)
                except Exception:
                    continue

                event_type = payload.get("type", "chat")

                if event_type == "ping":
                    await ws.send_str(json.dumps({"type": "pong"}))

                elif event_type == "chat":
                    user_text = payload.get("text", "")
                    with_screen = payload.get("include_screen", False)

                    # 1. Fast Local Command Routing (Zero Tokens, Instant Execution)
                    local_match = local_router.match_and_execute(user_text) if not with_screen else None
                    if local_match:
                        # Check for texture swap
                        for act in local_match.get("actions", []):
                            if act.get("type") == "reload_texture":
                                await broadcast_to_clients(act)

                        # Send mood expression
                        await ws.send_str(json.dumps({
                            "type": "expression",
                            "id": local_match["mood"]
                        }))

                        # Generate speech with emotional pitch/rate modulation
                        audio_b64 = await tts_engine.generate_speech_base64(local_match["text"], mood=local_match["mood"])

                        # Send response immediately
                        await ws.send_str(json.dumps({
                            "type": "response",
                            "text": local_match["text"],
                            "mood": local_match["mood"],
                            "audio": audio_b64,
                            "actions": local_match.get("actions", []),
                            "executed": []
                        }))
                        continue

                    # 2. Otherwise delegate to Gemini Brain
                    await ws.send_str(json.dumps({
                        "type": "status",
                        "message": "Faith is thinking..."
                    }))

                    screen_img = None
                    active_window = screen_sensor.get_active_window_title()

                    if with_screen:
                        await ws.send_str(json.dumps({
                            "type": "status",
                            "message": "Analyzing screen vision..."
                        }))
                        screen_img = screen_sensor.capture_screen()

                    # Query Brain
                    reply_data = await brain_engine.think_and_reply(
                        user_message=user_text,
                        screen_image=screen_img,
                        active_window=active_window
                    )

                    # Send expression trigger first for immediate visual response
                    await ws.send_str(json.dumps({
                        "type": "expression",
                        "id": reply_data["mood"]
                    }))

                    # Generate low-latency TTS with emotional voice modulation
                    audio_b64 = await tts_engine.generate_speech_base64(reply_data["text"], mood=reply_data["mood"])

                    # Send response package
                    await ws.send_str(json.dumps({
                        "type": "response",
                        "text": reply_data["text"],
                        "mood": reply_data["mood"],
                        "audio": audio_b64,
                        "actions": reply_data["actions"],
                        "executed": reply_data["executed"]
                    }))

                elif event_type == "expression_override":
                    mood_id = payload.get("id", "F1")
                    await ws.send_str(json.dumps({
                        "type": "expression",
                        "id": mood_id
                    }))

                elif event_type == "listen":
                    timeout = payload.get("timeout", 7)
                    await ws.send_str(json.dumps({
                        "type": "status",
                        "message": "🎙️ Listening via Local STT Engine..."
                    }))
                    transcription = await asyncio.to_thread(local_stt.listen_and_transcribe, timeout)
                    if transcription and not transcription.startswith("Audio capture error") and not transcription.startswith("Local speech model"):
                        await ws.send_str(json.dumps({
                            "type": "status",
                            "message": f'Heard: "{transcription}"'
                        }))
                        # Dispatch as a regular user chat
                        payload["text"] = transcription
                        event_type = "chat"
                        # We execute the chat handling below directly
                        user_text = transcription
                        with_screen = payload.get("include_screen", False)

                        local_match = local_router.match_and_execute(user_text) if not with_screen else None
                        if local_match:
                            for act in local_match.get("actions", []):
                                if act.get("type") == "reload_texture":
                                    await broadcast_to_clients(act)
                            await ws.send_str(json.dumps({"type": "expression", "id": local_match["mood"]}))
                            audio_b64 = await tts_engine.generate_speech_base64(local_match["text"])
                            await ws.send_str(json.dumps({
                                "type": "response",
                                "text": local_match["text"],
                                "mood": local_match["mood"],
                                "audio": audio_b64,
                                "actions": local_match.get("actions", []),
                                "executed": []
                            }))
                            continue

                        await ws.send_str(json.dumps({"type": "status", "message": "Faith is thinking..."}))
                        screen_img = None
                        active_window = screen_sensor.get_active_window_title()
                        if with_screen:
                            screen_img = screen_sensor.capture_screen()

                        reply_data = await brain_engine.think_and_reply(
                            user_message=user_text,
                            screen_image=screen_img,
                            active_window=active_window
                        )
                        await ws.send_str(json.dumps({"type": "expression", "id": reply_data["mood"]}))
                        audio_b64 = await tts_engine.generate_speech_base64(reply_data["text"])
                        await ws.send_str(json.dumps({
                            "type": "response",
                            "text": reply_data["text"],
                            "mood": reply_data["mood"],
                            "audio": audio_b64,
                            "actions": reply_data["actions"],
                            "executed": reply_data["executed"]
                        }))
                    else:
                        await ws.send_str(json.dumps({
                            "type": "status",
                            "message": transcription or "No speech detected."
                        }))

                elif event_type == "set_api_key":
                    new_key = payload.get("key", "").strip()
                    if new_key:
                        brain_engine.set_api_key(new_key)
                        await ws.send_str(json.dumps({
                            "type": "status",
                            "message": "Gemini API key updated successfully!",
                            "has_api_key": True
                        }))

    finally:
        connected_websockets.discard(ws)
        print(f"[WebSocket] Client disconnected: {request.remote}")

    return ws

async def proactive_monitor_loop():
    """
    Token-conservative proactive check: fires only if idle > threshold AND window changed.
    """
    global last_user_activity
    if PROACTIVE_IDLE_SECONDS <= 0:
        return

    last_active_win = ""

    while True:
        await asyncio.sleep(20)
        idle_time = time.time() - last_user_activity
        
        # Trigger only after prolonged idle (minimum 90s)
        if idle_time > max(90, PROACTIVE_IDLE_SECONDS) and connected_websockets and brain_engine.api_key:
            active_win = screen_sensor.get_active_window_title()

            # Prevent token burn: if window didn't change and user is completely away, skip
            if active_win == last_active_win:
                continue

            last_active_win = active_win
            last_user_activity = time.time()
            print(f"[Proactive Engine] Triggering proactive check on active window: {active_win}")
            
            try:
                screen_img = screen_sensor.capture_screen(scale_width=800)
                prompt = (
                    f"The user has been focused on '{active_win}'. Make a 1-sentence quick, friendly observation or offer assistance."
                )

                reply_data = await brain_engine.think_and_reply(
                    user_message=prompt,
                    screen_image=screen_img,
                    active_window=active_win
                )

                audio_b64 = await tts_engine.generate_speech_base64(reply_data["text"])

                payload = json.dumps({
                    "type": "proactive_response",
                    "text": reply_data["text"],
                    "mood": reply_data["mood"],
                    "audio": audio_b64
                })

                for ws in list(connected_websockets):
                    try:
                        await ws.send_str(payload)
                    except Exception:
                        pass
            except Exception as e:
                print(f"[Proactive Error] {e}")

async def index_handler(request):
    client_ui_index = CLIENT_UI_DIR / "index.html"
    if client_ui_index.exists():
        return web.FileResponse(client_ui_index)
    index_file = FRONTEND_DIR / "index.html"
    return web.FileResponse(index_file)

@web.middleware
async def cache_control_middleware(request, handler):
    response = await handler(request)
    if request.path.startswith("/assets/") or request.path.startswith("/js/") or request.path.startswith("/css/") or request.path.startswith("/vendor/"):
        response.headers["Cache-Control"] = "public, max-age=604800"
    return response

async def start_server():
    app = web.Application(middlewares=[cache_control_middleware])

    # Index route (serves client_ui dual-mode interface by default)
    app.router.add_get("/", index_handler)

    # Client UI core assets
    if CLIENT_UI_DIR.exists():
        if (CLIENT_UI_DIR / "style.css").exists():
            app.router.add_get("/style.css", lambda req: web.FileResponse(CLIENT_UI_DIR / "style.css"))
        if (CLIENT_UI_DIR / "app.js").exists():
            app.router.add_get("/app.js", lambda req: web.FileResponse(CLIENT_UI_DIR / "app.js"))
        if (CLIENT_UI_DIR / "vendor").exists():
            app.router.add_static("/vendor/", path=str(CLIENT_UI_DIR / "vendor"), show_index=True)

    # WebSocket route
    app.router.add_get("/ws", ws_handler)

    # Static assets routes
    if ASSETS_DIR.exists():
        app.router.add_static("/assets/", path=str(ASSETS_DIR), show_index=True)
    if (FRONTEND_DIR / "css").exists():
        app.router.add_static("/css/", path=str(FRONTEND_DIR / "css"))
    if (FRONTEND_DIR / "js").exists():
        app.router.add_static("/js/", path=str(FRONTEND_DIR / "js"))

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, HOST, HTTP_PORT)
    await site.start()

    print(f"==================================================")
    print(f"[+] Project FAITH / Zia Engine is LIVE!")
    print(f"[+] Web UI:      http://{HOST}:{HTTP_PORT}/")
    print(f"[+] WebSocket:   ws://{HOST}:{HTTP_PORT}/ws")
    print(f"==================================================")

    # Launch heartbeat loop in background
    asyncio.create_task(heartbeat_engine.run_loop(broadcast_to_clients))

    # Launch local offline STT IPC server (Unix Domain Socket / TCP Loopback)
    try:
        local_stt.start_ipc_server()
    except Exception as e:
        print(f"[Engine] Warning: STT IPC Server could not start: {e}")

    # Keep server running
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        print("\n[Engine] Shutting down cleanly.")
