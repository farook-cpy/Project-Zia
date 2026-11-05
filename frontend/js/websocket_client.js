class FaithWebSocketClient {
  constructor() {
    this.ws = null;
    this.reconnectTimer = null;
    this.subtitleContainer = document.getElementById("subtitle-box");
    this.subtitleText = document.getElementById("subtitle-content");
    this.subtitleHideTimer = null;
  }

  connect() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host || "127.0.0.1:8080";
    const wsUrl = `${protocol}//${host}/ws`;

    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log("[WS] Connected to Project FAITH local engine.");
      clearTimeout(this.reconnectTimer);
    };

    this.ws.onclose = () => {
      this.reconnectTimer = setTimeout(() => this.connect(), 3000);
    };

    this.ws.onerror = (err) => {
      console.error("[WS] Error:", err);
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.handleMessage(data);
      } catch (e) {}
    };
  }

  handleMessage(data) {
    if (data.type === "expression") {
      if (window.live2DStudio) {
        window.live2DStudio.setExpression(data.id);
      }
    } else if (data.type === "reload_texture") {
      if (window.live2DStudio) {
        window.live2DStudio.swapTexture(data.index || 0, data.url);
      }
    } else if (data.type === "set_framerate") {
      if (window.live2DStudio) {
        window.live2DStudio.setFramerateOverride(data.fps, data.reason);
      }
    } else if (data.type === "response" || data.type === "proactive_response") {
      // Show clean subtitle
      if (this.subtitleContainer && this.subtitleText && data.text) {
        clearTimeout(this.subtitleHideTimer);
        this.subtitleText.innerText = data.text;
        this.subtitleContainer.classList.add("active");
      }

      // Update expression
      if (data.mood && window.live2DStudio) {
        window.live2DStudio.setExpression(data.mood);
      }

      // Play audio & lip sync
      if (data.audio && window.audioLipSync) {
        window.audioLipSync.playSpeech(data.audio, () => {
          // Callback when speech ends: fade out subtitle
          this.subtitleHideTimer = setTimeout(() => {
            if (this.subtitleContainer) {
              this.subtitleContainer.classList.remove("active");
            }
          }, 1800);
        });
      }
    }
  }

  sendChat(text, includeScreen = false) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      if (window.showToast) window.showToast("Engine offline. Run 'python run.py'");
      return;
    }
    this.ws.send(JSON.stringify({
      type: "chat",
      text: text,
      include_screen: includeScreen
    }));
  }

  sendExpressionOverride(key) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: "expression_override",
        id: key
      }));
    }
    if (window.live2DStudio) {
      window.live2DStudio.setExpression(key);
    }
  }

  requestLocalListen(includeScreen = false, timeout = 7) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      if (window.showToast) window.showToast("Engine offline. Run 'python run.py'");
      return;
    }
    this.ws.send(JSON.stringify({
      type: "listen",
      include_screen: includeScreen,
      timeout: timeout
    }));
  }
}

window.faithClient = new FaithWebSocketClient();
