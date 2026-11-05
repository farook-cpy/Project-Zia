import os
import sys
import re
import json
import socket
import threading
import time
import zipfile
import urllib.request
from pathlib import Path
import sounddevice as sd

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "data" / "models" / "vosk-model-small-en-us-0.15"
SOCKET_PATH = "/tmp/zia_stt.sock" if sys.platform != "win32" else None
TCP_HOST = "127.0.0.1"
TCP_PORT = 8766

MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"

class LocalSTTEngine:
    """
    Lightweight local Speech-to-Text engine using quantized Vosk models.
    Operates completely offline with zero browser dependencies and provides
    a Unix domain socket / IPC bridge for instant, low-RAM transcription.
    """
    def __init__(self):
        self.model = None
        self.sample_rate = 16000
        self.server_thread = None
        self.is_running = False
        self._init_lock = threading.Lock()

    def ensure_model(self, auto_download: bool = False) -> bool:
        """
        Ensures the tiny Vosk model (~40MB) is available.
        """
        with self._init_lock:
            if self.model is not None:
                return True

            if not MODEL_DIR.exists():
                if not auto_download:
                    return False
                print(f"[LocalSTT] Downloading tiny Vosk speech model (~40MB)...")
                MODEL_DIR.parent.mkdir(parents=True, exist_ok=True)
                zip_path = MODEL_DIR.parent / "vosk_model.zip"
                try:
                    urllib.request.urlretrieve(MODEL_URL, zip_path)
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(MODEL_DIR.parent)
                    if zip_path.exists():
                        zip_path.unlink()
                    print(f"[LocalSTT] Speech model downloaded and ready.")
                except Exception as e:
                    print(f"[LocalSTT] Model download error: {e}")
                    return False

            try:
                import vosk
                vosk.SetLogLevel(-1) # Suppress debug logging
                self.model = vosk.Model(str(MODEL_DIR))
                print(f"[LocalSTT] Vosk quantized model loaded into memory (~25MB RAM).")
                return True
            except Exception as e:
                print(f"[LocalSTT] Model load error: {e}")
                return False

    def apply_noise_gate_and_filter(self, data: bytes, gate_threshold: int = 140) -> bytes:
        """
        Lightweight audio pre-processing filter:
        1. High-pass filter to strip 60Hz/120Hz fan hum from MacBook chassis.
        2. Noise Gate: silences background room hiss below RMS threshold.
        """
        if not data or len(data) < 4:
            return data

        import struct
        import math

        num_samples = len(data) // 2
        try:
            samples = list(struct.unpack(f"<{num_samples}h", data))
            sum_sq = sum(s * s for s in samples[::4])
            rms = math.sqrt(sum_sq / (num_samples / 4.0))

            if rms < gate_threshold:
                return bytes(len(data))

            filtered = []
            prev = 0
            for s in samples:
                val = int(s - 0.92 * prev)
                filtered.append(max(-32768, min(32767, val)))
                prev = s

            return struct.pack(f"<{num_samples}h", *filtered)
        except Exception:
            return data

    def listen_and_transcribe(self, timeout_sec: int = 7) -> str:
        """
        Captures microphone audio locally via sounddevice and transcribes in real-time.
        Stops automatically when speech ends or timeout is reached.
        """
        if not self.ensure_model(auto_download=True):
            return "Local speech model is initializing or not downloaded."

        import vosk
        recognizer = vosk.KaldiRecognizer(self.model, self.sample_rate)

        q = []
        silence_start = None
        has_spoken = False

        def audio_callback(indata, frames, time_info, status):
            q.append(bytes(indata))

        print(f"[LocalSTT] Listening via microphone (sample rate {self.sample_rate}Hz)...")
        start_time = time.time()

        try:
            with sd.RawInputStream(samplerate=self.sample_rate, blocksize=4000,
                                   dtype='int16', channels=1, callback=audio_callback):
                while time.time() - start_time < timeout_sec:
                    if q:
                        data = q.pop(0)
                        data = self.apply_noise_gate_and_filter(data)
                        if recognizer.AcceptWaveform(data):
                            res = json.loads(recognizer.Result())
                            text = res.get("text", "").strip()
                            if text:
                                return text
                        else:
                            partial = json.loads(recognizer.PartialResult()).get("partial", "").strip()
                            if partial:
                                has_spoken = True
                                silence_start = None
                            elif has_spoken:
                                if silence_start is None:
                                    silence_start = time.time()
                                elif time.time() - silence_start > 1.2:
                                    # Detected 1.2s of silence after speech -> finish
                                    break
                    time.sleep(0.02)

            # Final result flush
            final_res = json.loads(recognizer.FinalResult())
            return final_res.get("text", "").strip()

        except Exception as e:
            return f"Audio capture error: {str(e)}"

    def start_wake_word_daemon(self, callback) -> bool:
        """
        Runs a low-overhead continuous background listener (<1% CPU) for 'Hey Zia' / 'Zia'.
        When heard, it extracts any trailing command or captures the immediate command,
        and triggers callback(command_text).
        """
        if getattr(self, "_wake_running", False):
            return True

        if not self.ensure_model(auto_download=True):
            print("[LocalSTT] Cannot start wake word: speech model not loaded.")
            return False

        self._wake_running = True
        self._wake_thread = threading.Thread(
            target=self._wake_word_loop,
            args=(callback,),
            daemon=True,
            name="ZiaWakeWordThread"
        )
        self._wake_thread.start()
        print("[LocalSTT] Continuous Wake-Word detection active ('Hey Zia' / 'Zia').")
        return True

    def stop_wake_word_daemon(self):
        """Stops the continuous wake-word listener thread."""
        self._wake_running = False
        print("[LocalSTT] Wake-Word daemon stopped.")

    def is_wake_word_active(self) -> bool:
        return getattr(self, "_wake_running", False)

    def _wake_word_loop(self, callback):
        import vosk
        recognizer = vosk.KaldiRecognizer(self.model, self.sample_rate)

        q = []
        def audio_callback(indata, frames, time_info, status):
            if getattr(self, "_wake_running", False):
                q.append(bytes(indata))

        try:
            with sd.RawInputStream(samplerate=self.sample_rate, blocksize=4000,
                                   dtype='int16', channels=1, callback=audio_callback):
                while getattr(self, "_wake_running", False):
                    if q:
                        data = q.pop(0)
                        data = self.apply_noise_gate_and_filter(data)
                        if recognizer.AcceptWaveform(data):
                            res = json.loads(recognizer.Result())
                            text = res.get("text", "").strip().lower()
                            if text:
                                wake_match = re.search(r"\b(?:hey\s+|ok\s+)?zia\b(?:\s*[,:\-]?\s*(.*))?", text)
                                if wake_match:
                                    cmd = (wake_match.group(1) or "").strip()
                                    if not cmd:
                                        # Heard 'Hey Zia' alone -> listen for immediate command
                                        cmd = self.listen_and_transcribe(timeout_sec=5)
                                    if cmd and not cmd.startswith("Audio capture error") and not cmd.startswith("Local speech model"):
                                        try:
                                            callback(cmd)
                                        except Exception as cb_err:
                                            print(f"[WakeWord Callback Error] {cb_err}")
                    time.sleep(0.04) # 40ms interval yields < 0.5% CPU on Core 2 Duo
        except Exception as e:
            print(f"[LocalSTT WakeWord Error] {e}")
        finally:
            self._wake_running = False

    def start_ipc_server(self):
        """
        Launches Unix domain socket / Local loopback IPC server in background thread.
        Allows CLI, scripts, or subagents to request transcription with zero overhead.
        """
        if self.is_running:
            return

        self.is_running = True
        self.server_thread = threading.Thread(target=self._socket_listener, daemon=True, name="ZiaSTTServer")
        self.server_thread.start()

    def _socket_listener(self):
        # Setup socket
        if SOCKET_PATH:
            if os.path.exists(SOCKET_PATH):
                try:
                    os.unlink(SOCKET_PATH)
                except Exception:
                    pass
            server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            server.bind(SOCKET_PATH)
            print(f"[LocalSTT] Unix Domain Socket server listening on {SOCKET_PATH}")
        else:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((TCP_HOST, TCP_PORT))
            print(f"[LocalSTT] Local loopback IPC server listening on {TCP_HOST}:{TCP_PORT}")

        server.listen(5)

        while self.is_running:
            try:
                conn, _ = server.accept()
                threading.Thread(target=self._handle_client, args=(conn,), daemon=True).start()
            except Exception:
                break

    def _handle_client(self, conn):
        try:
            data = conn.recv(1024).decode("utf-8")
            if data:
                req = json.loads(data)
                cmd = req.get("command", "listen")
                timeout = req.get("timeout", 7)

                if cmd == "listen":
                    transcription = self.listen_and_transcribe(timeout_sec=timeout)
                    resp = json.dumps({"success": True, "text": transcription})
                elif cmd == "status":
                    resp = json.dumps({"ready": self.model is not None, "sample_rate": self.sample_rate})
                else:
                    resp = json.dumps({"error": f"Unknown command: {cmd}"})

                conn.sendall(resp.encode("utf-8"))
        except Exception as e:
            err = json.dumps({"success": False, "error": str(e)})
            try:
                conn.sendall(err.encode("utf-8"))
            except Exception:
                pass
        finally:
            conn.close()

local_stt = LocalSTTEngine()
