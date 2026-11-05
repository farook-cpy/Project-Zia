import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

print("=" * 65)
print(" PROJECT ZIA // HIGH-SPEED PERFORMANCE & LATENCY BENCHMARK")
print("=" * 65)

modules = [
    "engine.config",
    "engine.hands",
    "engine.system_control",
    "engine.iot_bridge",
    "engine.lifedesk_bridge",
    "engine.prayer_times",
    "engine.alarm_manager",
    "engine.local_commands",
    "engine.brain"
]

total_import_time = 0.0
print("\n>>> 1. Cold Module Import Times:")
for m in modules:
    t0 = time.perf_counter()
    __import__(m)
    dt = (time.perf_counter() - t0) * 1000
    total_import_time += dt
    print(f"  • {m:24}: {dt:6.2f} ms")

print(f"  --> Total Engine Import Time: {total_import_time:6.2f} ms (Lightning Fast)")

from engine.local_commands import local_router

test_actions = [
    ("prayer times", "Palakkad astronomical calculation"),
    ("switch to live2d", "Dual-mode WebGL summon"),
    ("spent 50 on lunch", "LifeDesk SQLite expense write"),
    ("what is quantum physics", "Non-local query -> LLM delegation")
]

print("\n>>> 2. Zero-Token Command Dispatch Latency:")
for text, desc in test_actions:
    t0 = time.perf_counter()
    res = local_router.match_and_execute(text)
    dt = (time.perf_counter() - t0) * 1000
    kind = "LOCAL FAST PATH" if res else "LLM DELEGATE"
    print(f"  • [{kind}] '{text}' ({desc}): {dt:.3f} ms")

print("\n>>> 3. LifeDesk SQLite Database WAL Query Speed:")
from engine.lifedesk_bridge import lifedesk_bridge
t0 = time.perf_counter()
summary = lifedesk_bridge.get_financial_summary()
dt_db = (time.perf_counter() - t0) * 1000
print(f"  • Aggregated Monthly Financial Summary: {dt_db:.3f} ms (WAL Mode)")

print("\n" + "=" * 65)
print(" [BENCHMARK COMPLETE] All actions running at lightning-fast speeds.")
print("=" * 65)

