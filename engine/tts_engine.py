import io
import base64
import edge_tts

class TTSEngine:
    def __init__(self, voice: str = "en-US-AnaNeural", rate: str = "+0%", pitch: str = "+0Hz"):
        self.voice = voice
        self.rate = rate
        self.pitch = pitch

    def _get_emotion_modulation(self, mood: str) -> tuple[str, str]:
        """
        Dynamically shifts speech pitch and speed based on Zia's emotional state.
        """
        mood = (mood or "F1").upper()
        if mood in ["F10", "F3"]: # Shocked / Alert / Angry
            return "+14%", "+15Hz"
        elif mood in ["F4", "F5", "F9"]: # Happy / Excited / Smug
            return "+8%", "+18Hz"
        elif mood in ["F6", "F7"]: # Sad / Serious
            return "-10%", "-8Hz"
        elif mood in ["F11", "F8"]: # Sleep / Calm / Thinking
            return "-14%", "-6Hz"
        else: # F1 Neutral
            return "+0%", "+0Hz"

    async def generate_speech_base64(self, text: str, mood: str = "F1", override_rate: str = None, override_pitch: str = None) -> str:
        """
        Converts text to an in-memory MP3 audio buffer with emotional voice modulation.
        """
        if not text or not text.strip():
            return ""

        rate, pitch = self._get_emotion_modulation(mood)
        rate = override_rate or rate
        pitch = override_pitch or pitch

        communicate = edge_tts.Communicate(text=text, voice=self.voice, rate=rate, pitch=pitch)
        audio_stream = io.BytesIO()

        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_stream.write(chunk["data"])

        audio_bytes = audio_stream.getvalue()
        return base64.b64encode(audio_bytes).decode("utf-8")

tts_engine = TTSEngine()

