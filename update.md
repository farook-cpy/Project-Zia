[PROJECT ZIA - ADVANCED AGENTIC CAPABILITIES IMPLEMENTATION PROMPT]

Target Architecture: Sony Xperia 1 III headless server node (Termux) integrated with local LifeDesk SQLite bridges, IoT relays, ADB remote intent bridges, remote Telegram/audio gateways, and agent-browser automation tools.

### Objective
Implement and wire the following core feature set into Project Zia's backend engine (`server.py`, `engine/`), ensuring zero resource bloat and robust local execution:

---

### 1. Agent-Browser Integration (`engine/browser_agent.py`)
- **Integration:** Integrate the `agent-browser` (CDP-based CLI tool) into Zia's tool-use registry to replace heavy web scraping/automation suites.
- **Token Efficiency:** Ensure the tool leverages compact accessibility tree snapshots (using reference tokens like `@e1`, `@e2`) instead of raw HTML dumps to keep LLM context minimal.
- **Workflow Execution:** Write Python wrappers that allow Zia to natively execute commands such as:
  1. Opening URLs (e.g., navigating to YouTube or travel/ticketing portals).
  2. Taking interactive accessibility snapshots.
  3. Clicking, typing, and extracting structured data (e.g., searching for video links or checking live schedules/ticket pricing) on demand.

### 2. Multi-Device Ambient & IoT Relays (`engine/iot_bridge.py` & `rpc_bridge.py`)
- **Smart Home IoT:** Implement local HTTP/MQTT command dispatchers communicating directly over the home network to ESP8266/NodeMCU relay nodes for physical appliance control (e.g., *"Turn on the desk light"*).
- **ADB Android Projector & Tablet Bridge:** Set up wireless ADB intent handlers so the Xperia server can remotely push commands to:
  - Your Android projector to launch browsers and stream media directly to `miruro.tv` (e.g., *"Play the latest episode of Black Clover"*).
  - Your Android tablet to wake up and trigger VoIP applications like Botim for hands-free calling (e.g., *"Call my dad on Botim on my tab"*).

### 3. Family OTP, Notifications & LifeDesk Sync (`engine/lifedesk_bridge.py`)
- **LifeDesk SQLite Connector:** Connect Zia's backend directly to your existing `habits.db` and `finance.db` files via native Python SQLite bindings. Enable natural language parsing for instant habit logging (e.g., *"Mark morning workout as done"*) and expense tracking (e.g., *"Log 150 rupees for lunch under food"*).
- **Local OTP/Notification Bridge:** Implement secure local webhooks to capture background notifications or SMS verifications forwarded from family Android devices (Samsung phones) to the Xperia server's secure local queue.

---

### Implementation Constraints
- Maintain an asynchronous, non-blocking architecture across all background daemons (`max_workers=2` thread pools).
- Keep all data flows strictly local to the home network with zero third-party cloud data storage for personal finance, habits, or private family notifications.
- Ensure all modules return clean, structured JSON payloads to be consumed seamlessly by Zia's central router (`server.py`).