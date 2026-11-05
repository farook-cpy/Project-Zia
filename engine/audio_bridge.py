"""
Project Zia - Android / Termux Audio & Room-Listening Pipeline
Engineered for Sony Xperia 1 III (Android + Termux) and cross-platform desktop.
Handles ambient room audio capture via Termux API microphones, software noise
suppression, and routes TTS audio directly to the device's physical speakers.
"""

import os
import sys
import time
import shutil
import subprocess
import threading
from pathlib import Path
from typing import Dict, Any, Optional

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    np = None
    NUMPY_AVAILABLE = False

BASE_DIR = Path(__file__).resolve().parent.parent
TMP_DIR = BASE_DIR / "data" / "tmp"
TMP_DIR.mkdir(parents=True, exist_ok=True)


class AndroidAudioBridge:
    """
    Audio bridge utilizing Android Termux API hooks:
    - `termux-microphone-record` for ambient room capture
    - `termux-tts-speak` and `termux-media-player` for physical speaker output
    - Graceful fallback to desktop sound utilities (ALSA, pulse, sounddevice, winsound)
    """

    def __init__(self):
        self.is_termux = bool(shutil.which("termux-microphone-record") or shutil.which("termux-tts-speak") or "com.termux" in os.environ.get("PREFIX", ""))
        self.has_termux_mic = bool(shutil.which("termux-microphone-record"))
        self.has_termux_tts = bool(shutil.which("termux-tts-speak"))
        self.has_termux_media = bool(shutil.which("termux-media-player"))

        self.is_recording = False
        self._record_process = None
        self._lock = threading.Lock()

        # Noise filter parameters
        self.PRE_EMPHASIS_COEFF = 0.92
        self.RMS_NOISE_THRESHOLD = 0.015

    def get_hardware_status(self) -> Dict[str, Any]:
        """Returns audio hardware capabilities and Termux API status."""
        return {
            "is_termux": self.is_termux,
            "has_termux_mic": self.has_termux_mic,
            "has_termux_tts": self.has_termux_tts,
            "has_termux_media": self.has_termux_media,
            "platform": sys.platform,
            "speaker_ready": self.has_termux_tts or self.has_termux_media or bool(shutil.which("aplay") or shutil.which("mpv")),
            "mic_ready": self.has_termux_mic or bool(shutil.which("arecord") or sys.platform in ["win32", "darwin"])
        }

    # -------------------------------------------------------------------------
    # 1. Microphone & Ambient Room Audio Capture
    # -------------------------------------------------------------------------
    def record_room_audio(self, duration_sec: int = 5, output_wav: Optional[str] = None) -> Dict[str, Any]:
        """
        Records ambient room audio from the Xperia's built-in microphone.
        Uses `termux-microphone-record` on Android or desktop fallbacks.
        """
        if output_wav is None:
            output_wav = str(TMP_DIR / f"ambient_{int(time.time())}.wav")

        duration_sec = max(1, int(duration_sec))

        # 1. Android Termux API
        if self.has_termux_mic:
            try:
                # termux-microphone-record -d (default mic) -f <file> -l <seconds> -b 16 -r 16000
                cmd = [
                    "termux-microphone-record",
                    "-d",
                    "-f", output_wav,
                    "-l", str(duration_sec),
                    "-b", "16",
                    "-r", "16000"
                ]
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=duration_sec + 4)
                if os.path.exists(output_wav) and os.path.getsize(output_wav) > 100:
                    self.apply_noise_suppression_to_file(output_wav)
                    return {
                        "success": True,
                        "file": output_wav,
                        "duration_sec": duration_sec,
                        "backend": "termux-microphone-record",
                        "size_bytes": os.path.getsize(output_wav)
                    }
            except Exception as e:
                print(f"[AudioBridge] Termux mic error: {e}")

        # 2. Linux Mint (arecord) fallback
        if shutil.which("arecord"):
            try:
                cmd = ["arecord", "-D", "default", "-f", "S16_LE", "-r", "16000", "-c", "1", "-d", str(duration_sec), output_wav]
                subprocess.run(cmd, capture_output=True, timeout=duration_sec + 2)
                if os.path.exists(output_wav) and os.path.getsize(output_wav) > 100:
                    self.apply_noise_suppression_to_file(output_wav)
                    return {"success": True, "file": output_wav, "duration_sec": duration_sec, "backend": "arecord"}
            except Exception:
                pass

        # 3. Python sounddevice fallback
        try:
            import sounddevice as sd
            import scipy.io.wavfile as wavfile
            sample_rate = 16000
            audio_data = sd.rec(int(duration_sec * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
            sd.wait()
            wavfile.write(output_wav, sample_rate, audio_data)
            return {"success": True, "file": output_wav, "duration_sec": duration_sec, "backend": "sounddevice"}
        except Exception:
            pass

        # Clean fallback stub if no audio hardware attached during testing
        return {
            "success": False,
            "error": "No physical microphone recording backend available (install termux-api or arecord).",
            "file": None
        }

    # -------------------------------------------------------------------------
    # 2. Software Noise Suppression & High-Pass Hum Filter
    # -------------------------------------------------------------------------
    def apply_noise_suppression_to_file(self, wav_path: str):
        """
        Applies a high-pass digital filter (y[i] = x[i] - 0.92*x[i-1]) and RMS
        silence gate to strip fan vibration, AC hum, and ambient room noise.
        """
        if not os.path.exists(wav_path):
            return

        try:
            import wave
            with wave.open(wav_path, 'rb') as wf:
                params = wf.getparams()
                raw_frames = wf.readframes(params.nframes)

            if NUMPY_AVAILABLE and len(raw_frames) > 0:
                audio_np = np.frombuffer(raw_frames, dtype=np.int16).astype(np.float32)

                # Pre-emphasis high-pass filter
                filtered = np.zeros_like(audio_np)
                filtered[0] = audio_np[0]
                filtered[1:] = audio_np[1:] - self.PRE_EMPHASIS_COEFF * audio_np[:-1]

                # RMS noise gate
                rms = np.sqrt(np.mean(filtered**2)) / 32768.0
                if rms < self.RMS_NOISE_THRESHOLD:
                    filtered *= 0.1  # Attenuate background hum

                processed_bytes = np.clip(filtered, -32768, 32767).astype(np.int16).tobytes()

                with wave.open(wav_path, 'wb') as wf:
                    wf.setparams(params)
                    wf.writeframes(processed_bytes)
        except Exception as e:
            # Keep original file if post-processing encounters an error
            pass

    # -------------------------------------------------------------------------
    # 3. Physical Speaker Audio Output & TTS Routing
    # -------------------------------------------------------------------------
    def speak(self, text: str, mood: str = "F1") -> Dict[str, Any]:
        """
        Routes text-to-speech directly out of the Sony Xperia's physical stereo speakers.
        Uses Android Termux TTS if available, or synthesizes Edge-TTS audio.
        """
        text = text.strip()
        if not text:
            return {"error": "Empty text provided."}

        # 1. Termux Native Android TTS (Immediate, 0MB RAM, zero latency)
        if self.has_termux_tts:
            try:
                # termux-tts-speak -p (pitch) -r (rate)
                pitch = "1.0"
                rate = "1.0"
                if mood in ["F4", "F7"]:
                    pitch = "1.15"
                    rate = "1.1"
                elif mood in ["F6", "F11"]:
                    pitch = "0.9"
                    rate = "0.9"

                subprocess.Popen(["termux-tts-speak", "-p", pitch, "-r", rate, text])
                return {"success": True, "backend": "termux-tts-speak", "text": text}
            except Exception as e:
                print(f"[AudioBridge] Termux TTS notice: {e}")

        # 2. Edge-TTS synthesis & physical speaker playback via media player
        try:
            import asyncio
            from engine.tts_engine import tts_engine

            out_file = str(TMP_DIR / f"tts_{int(time.time())}.mp3")

            async def _synthesize():
                import edge_tts
                comm = edge_tts.Communicate(text, voice="en-US-AnaNeural")
                await comm.save(out_file)

            asyncio.run(_synthesize())

            if os.path.exists(out_file):
                self.play_audio_file(out_file)
                return {"success": True, "backend": "edge-tts-speaker", "file": out_file}
        except Exception as e:
            pass

        # 3. Terminal bell fallback
        sys.stdout.write("\a")
        sys.stdout.flush()
        return {"success": True, "backend": "terminal_bell", "text": text}

    def play_audio_file(self, file_path: str) -> bool:
        """
        Plays any WAV/MP3 audio file out of the device's physical speakers.
        """
        if not os.path.exists(file_path):
            return False

        # Android Termux Media Player
        if self.has_termux_media:
            try:
                subprocess.Popen(["termux-media-player", "play", file_path], stderr=subprocess.DEVNULL)
                return True
            except Exception:
                pass

        # Desktop utilities (Linux Mint, macOS, Windows)
        for player in ["mpv", "ffplay", "paplay", "aplay"]:
            if shutil.which(player):
                try:
                    args = [player, file_path]
                    if player == "ffplay":
                        args = [player, "-nodisp", "-autoexit", file_path]
                    elif player == "mpv":
                        args = [player, "--no-video", file_path]
                    subprocess.Popen(args, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                    return True
                except Exception:
                    continue

        if sys.platform == "darwin":
            subprocess.Popen(["afplay", file_path], stderr=subprocess.DEVNULL)
            return True

        if sys.platform == "win32":
            try:
                import winsound
                if file_path.endswith(".wav"):
                    winsound.PlaySound(file_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                    return True
            except Exception:
                pass

        return False


# Global audio bridge singleton
audio_bridge = AndroidAudioBridge()

