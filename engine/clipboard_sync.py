import os
import sys
import json
import socket
import threading
import subprocess
import shutil
from http.server import HTTPServer, BaseHTTPRequestHandler

class ClipboardManager:
    """
    Cross-platform Local Clipboard Manager.
    Reads and writes system clipboard without heavy dependencies.
    """
    @staticmethod
    def get_text() -> str:
        try:
            if sys.platform == "win32":
                res = subprocess.run(["powershell", "-NoProfile", "-Command", "Get-Clipboard"], capture_output=True, text=True, timeout=2)
                return res.stdout.strip()
            elif sys.platform == "darwin":
                res = subprocess.run(["pbpaste"], capture_output=True, text=True, timeout=2)
                return res.stdout
            else: # Linux
                if shutil.which("xclip"):
                    res = subprocess.run(["xclip", "-selection", "clipboard", "-o"], capture_output=True, text=True, timeout=2)
                    return res.stdout
                elif shutil.which("xsel"):
                    res = subprocess.run(["xsel", "--clipboard", "--output"], capture_output=True, text=True, timeout=2)
                    return res.stdout
        except Exception:
            pass
        return ""

    @staticmethod
    def set_text(text: str) -> bool:
        try:
            if sys.platform == "win32":
                proc = subprocess.Popen(["powershell", "-NoProfile", "-Command", "$input | Set-Clipboard"], stdin=subprocess.PIPE, text=True)
                proc.communicate(input=text)
                return True
            elif sys.platform == "darwin":
                proc = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE, text=True)
                proc.communicate(input=text)
                return True
            else: # Linux
                cmd = ["xclip", "-selection", "clipboard", "-i"] if shutil.which("xclip") else ["xsel", "--clipboard", "--input"]
                proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, text=True)
                proc.communicate(input=text)
                return True
        except Exception:
            return False

class ClipboardSyncHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass # Suppress HTTP access logging in terminal

    def do_GET(self):
        if self.path in ["/api/clip", "/clip"]:
            text = ClipboardManager.get_text()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"success": True, "clipboard": text}).encode("utf-8"))
        else:
            # Minimalist Mobile Web Interface for phone/tablet (Samsung S24 FE)
            current_clip = ClipboardManager.get_text().replace("<", "&lt;").replace(">", "&gt;")
            html = f"""<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Zia // Clipboard Sync</title>
  <style>
    body {{ background: #0f0f12; color: #f0f0f0; font-family: -apple-system, sans-serif; padding: 20px; }}
    .card {{ background: #1a1a24; border: 1px solid #333; border-radius: 12px; padding: 18px; margin-bottom: 20px; }}
    h3 {{ margin-top: 0; color: #00d2ff; }}
    pre {{ background: #08080a; padding: 12px; border-radius: 8px; overflow-x: auto; white-space: pre-wrap; font-size: 14px; max-height: 200px; }}
    textarea {{ width: 100%; height: 100px; background: #08080a; color: #fff; border: 1px solid #444; border-radius: 8px; padding: 10px; font-size: 14px; box-sizing: border-box; }}
    button {{ background: #7928ca; color: #fff; border: none; padding: 12px 18px; border-radius: 8px; font-weight: bold; cursor: pointer; margin-top: 8px; font-size: 15px; width: 100%; }}
    button:active {{ opacity: 0.8; }}
  </style>
</head>
<body>
  <h2>📱 Zia Clipboard Sync</h2>
  <div class="card">
    <h3>💻 Current Laptop Clipboard</h3>
    <pre id="clip-view">{current_clip}</pre>
    <button onclick="navigator.clipboard.writeText(document.getElementById('clip-view').innerText); alert('Copied to phone!');">Copy to Phone</button>
  </div>
  <div class="card">
    <h3>📤 Push to Laptop</h3>
    <textarea id="push-input" placeholder="Type or paste text from your phone..."></textarea>
    <button onclick="fetch('/api/clip', {{method:'POST', body: JSON.stringify({{text: document.getElementById('push-input').value}}), headers:{{'Content-Type':'application/json'}}}}).then(()=>alert('Sent to laptop!'));">Send to Laptop Clipboard</button>
  </div>
</body>
</html>"""
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))

    def do_POST(self):
        if self.path in ["/api/clip", "/clip"]:
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length).decode("utf-8")
                data = json.loads(body)
                text = data.get("text", "")
                ClipboardManager.set_text(text)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"success": True, "message": "Updated laptop clipboard."}).encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

class ClipboardSyncServer:
    def __init__(self, port: int = 8767):
        self.port = port
        self.server = None
        self.thread = None
        self.is_running = False

    def get_lan_ip(self) -> str:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        except Exception:
            ip = "127.0.0.1"
        finally:
            s.close()
        return ip

    def start(self) -> dict:
        if self.is_running:
            return {"success": True, "message": "Clipboard Sync server is already running.", "url": f"http://{self.get_lan_ip()}:{self.port}/"}

        try:
            self.server = HTTPServer(("0.0.0.0", self.port), ClipboardSyncHandler)
            self.is_running = True
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True, name="ZiaClipSyncThread")
            self.thread.start()
            lan_ip = self.get_lan_ip()
            return {
                "success": True,
                "message": f"Clipboard Sync is LIVE at http://{lan_ip}:{self.port}/",
                "lan_ip": lan_ip,
                "port": self.port,
                "url": f"http://{lan_ip}:{self.port}/"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def stop(self) -> dict:
        if not self.is_running:
            return {"success": True, "message": "Clipboard Sync server is not active."}
        try:
            self.server.shutdown()
            self.is_running = False
            return {"success": True, "message": "Clipboard Sync server stopped."}
        except Exception as e:
            return {"success": False, "error": str(e)}

clipboard_sync = ClipboardSyncServer()

