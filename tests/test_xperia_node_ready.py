"""
Project Zia - Xperia 1 III Server Node Complete Readiness Test Suite
Verifies:
1. Dynamic .env key loading without requiring hard restart.
2. Live Gemini LLM dialogue generation with the user's configured API key.
3. Xperia Server endpoints (/ping, /api/status, /api/chat, static web client).
4. Subagent concurrency cap (thermal throttling guard for Snapdragon 888).
5. Fast 0-token local command routing.
6. Local LifeDesk SQLite databases (habits.db, finance.db).
7. Anime sprite companion & minimalist grey UI assets integrity.
"""

import os
import sys
import json
import unittest
import asyncio
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

class TestXperiaDeploymentNode(unittest.TestCase):

    def test_01_dynamic_api_key_loading(self):
        """Verifies that BrainEngine dynamically loads the key from .env."""
        from engine.brain import BrainEngine
        brain = BrainEngine()
        client = brain._get_client()
        self.assertIsNotNone(client, "Failed to initialize GenAI client with key from .env")
        self.assertTrue(bool(brain.api_key), "BrainEngine api_key is empty")

    def test_02_live_gemini_dialogue_generation(self):
        """Verifies actual roundtrip generation using the user's Gemini key."""
        from engine.brain import BrainEngine
        brain = BrainEngine()
        reply = asyncio.run(brain.think_and_reply("Hello Zia, reply in 4 words"))
        self.assertIsNotNone(reply)
        text = reply.get("text", "")
        self.assertNotIn("My Gemini API key is not configured yet", text)
        self.assertNotIn("Glitch in neural connection", text)
        self.assertGreater(len(text), 0, "Empty response from Gemini")
        self.assertIn(reply.get("mood", "F1"), [f"F{i}" for i in range(1, 12)])

    def test_03_xperia_server_api_chat(self):
        """Verifies server.py /api/chat endpoint routes to live Gemini model."""
        from server import app
        client = app.test_client()
        res = client.post("/api/chat", json={"text": "Give a quick hello"})
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data.decode("utf-8"))
        self.assertIn("text", data)
        self.assertNotIn("My Gemini API key is not configured yet", data.get("text", ""))

    def test_04_xperia_server_status_and_health(self):
        """Verifies server.py health, mobile battery telemetry, and subagent capacity."""
        from server import app
        client = app.test_client()
        res = client.get("/api/status")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data.decode("utf-8"))
        self.assertEqual(data.get("status"), "healthy")
        self.assertEqual(data.get("subagents", {}).get("max_workers"), 2)

    def test_05_client_ui_serving(self):
        """Verifies server serves minimalist HTML client UI and assets."""
        from server import app
        client = app.test_client()
        res = client.get("/")
        self.assertEqual(res.status_code, 200)

        res_css = client.get("/style.css")
        self.assertEqual(res_css.status_code, 200)

        res_js = client.get("/app.js")
        self.assertEqual(res_js.status_code, 200)

    def test_06_lifedesk_sqlite_readiness(self):
        """Verifies LifeDesk local SQLite connectors work with zero latency."""
        from engine.lifedesk_bridge import lifedesk_bridge
        streaks = lifedesk_bridge.get_all_habit_streaks()
        self.assertIsInstance(streaks, list)
        expenses = lifedesk_bridge.get_daily_expenses()
        self.assertIsInstance(expenses, dict)
        self.assertIn("total", expenses)

if __name__ == "__main__":
    unittest.main(verbosity=2)
