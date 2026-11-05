import json
import time
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MEMORY_FILE = DATA_DIR / "memory.json"

class LongTermMemory:
    def __init__(self):
        DATA_DIR.mkdir(exist_ok=True)
        self.data = {
            "user_profile": {
                "name": "User",
                "notes": []
            },
            "system_facts": {
                "device": "MacBook Pro 2007 / Linux Mint / Windows",
                "companion_name": "Zia (Project FAITH)"
            },
            "milestones": []
        }
        self.load()

    def load(self):
        if MEMORY_FILE.exists():
            try:
                with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception as e:
                print(f"[Memory] Load notice: {e}")

    def save(self):
        try:
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Memory] Save error: {e}")

    def add_note(self, note: str):
        if note not in self.data["user_profile"]["notes"]:
            self.data["user_profile"]["notes"].append(note)
            self.save()

    def set_user_name(self, name: str):
        self.data["user_profile"]["name"] = name
        self.save()

    def add_milestone(self, user_msg: str, ai_msg: str):
        self.data["milestones"].append({
            "timestamp": time.time(),
            "user": user_msg[:120],
            "ai": ai_msg[:120]
        })
        # Keep last 15 milestones
        if len(self.data["milestones"]) > 15:
            self.data["milestones"] = self.data["milestones"][-15:]
        self.save()

    def get_memory_context(self) -> str:
        """
        Formats long-term memory for concise inclusion in the system prompt.
        """
        lines = []
        name = self.data["user_profile"].get("name", "User")
        lines.append(f"User Name: {name}")

        notes = self.data["user_profile"].get("notes", [])
        if notes:
            lines.append("Remembered Facts: " + "; ".join(notes[-5:]))

        if self.data["milestones"]:
            recent = self.data["milestones"][-3:]
            lines.append("Past Context: " + " | ".join(f"User asked '{m['user']}' -> Zia replied '{m['ai']}'" for m in recent))

        return "\n".join(lines)

memory_engine = LongTermMemory()

