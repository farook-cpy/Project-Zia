/**
 * Project Zia // Minimalist Grey Companion Client UI (client_ui/app.js)
 * Clean, uncluttered, expressive desktop AI companion:
 * - Expressive HTML/CSS eyes & procedural mouth with organic emotions.
 * - Interactive mouse-following eye tracking & click interactions.
 * - Procedural Web Audio API sound effects (chimes, thinking hum, ready ping).
 * - Real-time speech audio waveform mouth synchronization.
 * - Dynamic Live2D mount/unmount strictly on demand via voice/chat command ("load avatar" / "stop avatar").
 */

class ZiaCompanionUI {
  constructor() {
    this.activeMode = "minimal"; // "minimal" (default) or "live2d"
    this.currentMood = "F1";
    this.isThinking = false;
    this.isSpeaking = false;
    this.isListening = false;
    this.ws = null;
    this.wsConnected = false;
    this.audioContext = null;
    this.analyser = null;
    this.audioElement = new Audio();
    this.pixiApp = null;
    this.live2dModel = null;
    this.subtitleTimer = null;
    this.thinkingHumNode = null;
    this.lastBlinkTime = 0;
    this.nextBlinkDelay = 3500;

    // DOM Elements
    this.dom = {
      container: document.getElementById("app-container"),
      minimalStage: document.getElementById("minimal-stage"),
      live2dStage: document.getElementById("live2d-stage"),
      live2dCanvas: document.getElementById("live2d-canvas"),
      animeSpriteStage: document.getElementById("anime-sprite-stage"),
      animeSpriteWrapper: document.getElementById("anime-sprite-wrapper"),
      animeSpriteImg: document.getElementById("anime-sprite-img"),
      animeSpeechBubble: document.getElementById("anime-speech-bubble"),
      animeSpeechText: document.getElementById("anime-speech-text"),
      avatarFace: document.getElementById("avatar-face"),
      eyeLeft: document.getElementById("eye-left"),
      eyeRight: document.getElementById("eye-right"),
      pupilLeft: document.getElementById("pupil-left"),
      pupilRight: document.getElementById("pupil-right"),
      mouthContainer: document.getElementById("mouth-container"),
      mouthCanvas: document.getElementById("mouth-waveform-canvas") || document.getElementById("mouth-canvas"),
      thinkingDots: document.getElementById("thinking-dots"),
      subtitleBox: document.getElementById("subtitle-box"),
      subtitleText: document.getElementById("subtitle-text"),
      chatInput: document.getElementById("chat-input"),
      btnSend: document.getElementById("btn-send"),
      btnMic: document.getElementById("btn-mic")
    };

    this.init();
  }

  async init() {
    this.setupAudioContext();
    this.spriteController = new AnimeSpriteController(this);
    this.setupEventListeners();
    this.setupEyeTracking();
    this.setupBlinkLoop();
    this.setupSpeechRecognition();
    this.setupMinimizationHandler();
    this.startMouthRenderLoop();
    this.connectWebSocket();
  }

  setupMinimizationHandler() {
    this.previousModeBeforeMinimize = "minimal";
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) {
        // Window of the project is MINIMISED! Activate Anime Sprite Avatar!
        this.previousModeBeforeMinimize = this.activeMode;
        this.toggleMode("sprite");
        if (this.spriteController) {
          this.spriteController.triggerSpeech("Zia window minimized! I'm watching over your screen.", 3200);
        }
      } else {
        // Window of the project is RESTORED! Return back to previous state!
        if (this.previousModeBeforeMinimize && this.previousModeBeforeMinimize !== "sprite") {
          this.toggleMode(this.previousModeBeforeMinimize);
        }
      }
    });
  }

  // =========================================================================
  // 1. Procedural Web Audio Synthesizer & SFX Engine
  // =========================================================================
  setupAudioContext() {
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtx) return;
      this.audioContext = new AudioCtx();
      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 64;

      const source = this.audioContext.createMediaElementSource(this.audioElement);
      source.connect(this.analyser);
      this.analyser.connect(this.audioContext.destination);
    } catch (e) {
      console.log("[Audio Context Init]", e);
    }
  }

  resumeAudio() {
    if (this.audioContext && this.audioContext.state === "suspended") {
      this.audioContext.resume();
    }
  }

  playTone(freq, type = "sine", duration = 0.15, gainVal = 0.08) {
    if (!this.audioContext) return;
    this.resumeAudio();
    try {
      const osc = this.audioContext.createOscillator();
      const gain = this.audioContext.createGain();
      osc.type = type;
      osc.frequency.setValueAtTime(freq, this.audioContext.currentTime);

      gain.gain.setValueAtTime(gainVal, this.audioContext.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.audioContext.currentTime + duration);

      osc.connect(gain);
      gain.connect(this.audioContext.destination);
      osc.start();
      osc.stop(this.audioContext.currentTime + duration);
    } catch (e) {}
  }

  playWakeChime() {
    // Elegant two-tone ascending chime (480Hz -> 720Hz)
    this.playTone(480, "sine", 0.12, 0.09);
    setTimeout(() => this.playTone(720, "sine", 0.22, 0.08), 90);
  }

  playReadyChime() {
    // Soft high-frequency crystal bell ping (880Hz)
    this.playTone(880, "triangle", 0.35, 0.07);
  }

  playClickBlip() {
    // Playful interactive blip
    this.playTone(600, "sine", 0.08, 0.06);
    setTimeout(() => this.playTone(900, "sine", 0.1, 0.06), 60);
  }

  startThinkingHum() {
    if (!this.audioContext || this.thinkingHumNode) return;
    this.resumeAudio();
    try {
      const osc = this.audioContext.createOscillator();
      const gain = this.audioContext.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(140, this.audioContext.currentTime);

      gain.gain.setValueAtTime(0.001, this.audioContext.currentTime);
      gain.gain.linearRampToValueAtTime(0.015, this.audioContext.currentTime + 0.4);

      osc.connect(gain);
      gain.connect(this.audioContext.destination);
      osc.start();
      this.thinkingHumNode = { osc, gain };
    } catch (e) {}
  }

  stopThinkingHum() {
    if (this.thinkingHumNode && this.audioContext) {
      try {
        const { osc, gain } = this.thinkingHumNode;
        gain.gain.linearRampToValueAtTime(0.001, this.audioContext.currentTime + 0.15);
        setTimeout(() => {
          try { osc.stop(); } catch (e) {}
        }, 160);
      } catch (e) {}
      this.thinkingHumNode = null;
    }
  }

  // =========================================================================
  // 2. Interactive Eye Tracking & Natural Blinking Loop
  // =========================================================================
  setupEyeTracking() {
    let mouseX = 0;
    let mouseY = 0;
    let isMouseActive = false;
    let idleTimer = null;

    window.addEventListener("mousemove", (e) => {
      mouseX = e.clientX;
      mouseY = e.clientY;
      isMouseActive = true;
      clearTimeout(idleTimer);
      idleTimer = setTimeout(() => { isMouseActive = false; }, 2500);

      if (!this.isThinking) {
        this.updatePupilTracking(mouseX, mouseY);
      }
    });

    // Face Click: Playful wink interaction
    this.dom.avatarFace.addEventListener("click", () => {
      this.playClickBlip();
      this.setMood("F9"); // Smug / Wink
      setTimeout(() => this.setMood("F4"), 1200); // Smile
      setTimeout(() => this.setMood("F1"), 2800); // Return to neutral
    });
  }

  updatePupilTracking(targetX, targetY) {
    const faceRect = this.dom.avatarFace.getBoundingClientRect();
    const faceCenterX = faceRect.left + faceRect.width / 2;
    const faceCenterY = faceRect.top + faceRect.height / 2;

    const deltaX = (targetX - faceCenterX) / (window.innerWidth / 2);
    const deltaY = (targetY - faceCenterY) / (window.innerHeight / 2);

    // Clamp pupil displacement within physical socket
    const maxShiftX = 9;
    const maxShiftY = 7;
    const shiftX = Math.max(-maxShiftX, Math.min(maxShiftX, deltaX * maxShiftX));
    const shiftY = Math.max(-maxShiftY, Math.min(maxShiftY, deltaY * maxShiftY));

    this.dom.pupilLeft.style.transform = `translate(${shiftX}px, ${shiftY}px)`;
    this.dom.pupilRight.style.transform = `translate(${shiftX}px, ${shiftY}px)`;
  }

  setupBlinkLoop() {
    const runBlink = () => {
      // Trigger blink class
      this.dom.eyeLeft.classList.add("blink");
      this.dom.eyeRight.classList.add("blink");

      setTimeout(() => {
        this.dom.eyeLeft.classList.remove("blink");
        this.dom.eyeRight.classList.remove("blink");

        // 18% chance of a realistic quick double-blink
        if (Math.random() < 0.18) {
          setTimeout(() => {
            this.dom.eyeLeft.classList.add("blink");
            this.dom.eyeRight.classList.add("blink");
            setTimeout(() => {
              this.dom.eyeLeft.classList.remove("blink");
              this.dom.eyeRight.classList.remove("blink");
            }, 90);
          }, 120);
        }
      }, 100);

      // Randomize next blink delay between 3.2s and 6.8s
      this.nextBlinkDelay = 3200 + Math.random() * 3600;
      setTimeout(runBlink, this.nextBlinkDelay);
    };

    setTimeout(runBlink, 2000);
  }

  // =========================================================================
  // 3. Expressive Mouth Waveform & Thinking Animation Canvas
  // =========================================================================
  startMouthRenderLoop() {
    const canvas = this.dom.mouthCanvas;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const width = canvas.width;
    const height = canvas.height;
    const bufferLength = this.analyser ? this.analyser.frequencyBinCount : 32;
    const dataArray = new Uint8Array(bufferLength);
    const bars = 22;
    const smoothedBars = new Float32Array(bars);
    let smoothedVolume = 0;
    let wavePhase = 0;

    const draw = () => {
      requestAnimationFrame(draw);
      ctx.clearRect(0, 0, width, height);

      let currentVol = 0;
      if (this.analyser && !this.audioElement.paused) {
        this.analyser.getByteFrequencyData(dataArray);
        let sum = 0;
        for (let i = 0; i < bufferLength; i++) sum += dataArray[i];
        currentVol = sum / bufferLength;
      }

      // Smooth attack/decay hysteresis to prevent mouth glitching/flicker
      if (currentVol > smoothedVolume) {
        smoothedVolume = smoothedVolume * 0.35 + currentVol * 0.65; // Fast attack
      } else {
        smoothedVolume = smoothedVolume * 0.82 + currentVol * 0.18; // Smooth decay
      }

      const isActiveAudio = smoothedVolume > 3.5;
      this.isSpeaking = isActiveAudio;

      const centerY = height / 2;

      // MODE A: Speaking - Clean Silver/Grey Audio-Reactive Waveform (Glitch-free)
      if (isActiveAudio) {
        const barWidth = 4;
        const spacing = (width - bars * barWidth) / (bars - 1);

        for (let i = 0; i < bars; i++) {
          const rawVal = dataArray[i % bufferLength] || 0;
          // Exponential bar interpolation
          smoothedBars[i] = smoothedBars[i] * 0.65 + rawVal * 0.35;
          const barHeight = Math.max(3, (smoothedBars[i] / 255) * (height - 6));
          const x = i * (barWidth + spacing);
          const y = centerY - barHeight / 2;

          ctx.fillStyle = "#e4e4e7"; // Clean silver grey
          ctx.beginPath();
          ctx.roundRect(x, y, barWidth, barHeight, 2);
          ctx.fill();
        }
        return;
      }

      // MODE B: Thinking - Undulating Sine Wave Ripple
      if (this.isThinking) {
        wavePhase += 0.08;
        ctx.beginPath();
        ctx.strokeStyle = "#a1a1aa";
        ctx.lineWidth = 2.5;
        ctx.lineCap = "round";

        const startX = 40;
        const endX = width - 40;

        for (let x = startX; x <= endX; x += 2) {
          const progress = (x - startX) / (endX - startX);
          // Envelope: tapers at ends
          const envelope = Math.sin(progress * Math.PI);
          const y = centerY + Math.sin(progress * 10 - wavePhase) * 6 * envelope;
          if (x === startX) ctx.moveTo(x, y);
          else ctx.lineTo(x, y);
        }
        ctx.stroke();
        return;
      }

      // MODE C: Happy (F4) - Gentle Upward Curved Smile Arc
      if (this.currentMood === "F4") {
        ctx.beginPath();
        ctx.strokeStyle = "#d4d4d8";
        ctx.lineWidth = 3;
        ctx.lineCap = "round";
        const startX = 65;
        const endX = width - 65;
        ctx.moveTo(startX, centerY - 2);
        ctx.quadraticCurveTo(width / 2, centerY + 10, endX, centerY - 2);
        ctx.stroke();
        return;
      }

      // MODE D: Surprised / Shocked (F7 / F10) - Open Round Mouth O
      if (this.currentMood === "F7" || this.currentMood === "F10") {
        ctx.beginPath();
        ctx.strokeStyle = "#d4d4d8";
        ctx.lineWidth = 2.5;
        ctx.arc(width / 2, centerY, 8, 0, Math.PI * 2);
        ctx.stroke();
        return;
      }

      // MODE E: Sad / Empathetic (F6) - Downward Turned Curve
      if (this.currentMood === "F6") {
        ctx.beginPath();
        ctx.strokeStyle = "#71717a";
        ctx.lineWidth = 2.5;
        ctx.lineCap = "round";
        const startX = 70;
        const endX = width - 70;
        ctx.moveTo(startX, centerY + 4);
        ctx.quadraticCurveTo(width / 2, centerY - 4, endX, centerY + 4);
        ctx.stroke();
        return;
      }

      // MODE F: Smug / Playful (F9) - Asymmetric Smirk Curve
      if (this.currentMood === "F9") {
        ctx.beginPath();
        ctx.strokeStyle = "#d4d4d8";
        ctx.lineWidth = 2.5;
        ctx.lineCap = "round";
        const startX = 68;
        const endX = width - 68;
        ctx.moveTo(startX, centerY + 2);
        ctx.quadraticCurveTo(width / 2, centerY + 4, endX, centerY - 5);
        ctx.stroke();
        return;
      }

      // MODE G: Annoyed / Pout (F3) - Compressed tight straight line
      if (this.currentMood === "F3") {
        ctx.beginPath();
        ctx.strokeStyle = "#a1a1aa";
        ctx.lineWidth = 2.5;
        ctx.lineCap = "round";
        const startX = (width - 42) / 2;
        const endX = startX + 42;
        ctx.moveTo(startX, centerY);
        ctx.lineTo(endX, centerY);
        ctx.stroke();
        return;
      }

      // MODE H: Shy / Bashful (F2 / F5) - Soft petite curved line
      if (this.currentMood === "F2" || this.currentMood === "F5") {
        ctx.beginPath();
        ctx.strokeStyle = "#d4d4d8";
        ctx.lineWidth = 2.2;
        ctx.lineCap = "round";
        const startX = 78;
        const endX = width - 78;
        ctx.moveTo(startX, centerY - 1);
        ctx.quadraticCurveTo(width / 2, centerY + 5, endX, centerY - 1);
        ctx.stroke();
        return;
      }

      // MODE I: Default Idle - Soft Breathing Minimal Silver Line
      const breath = Math.sin(performance.now() * 0.002) * 1.5;
      const lineWidth = 60 + breath * 4;
      const startX = (width - lineWidth) / 2;
      const endX = startX + lineWidth;

      ctx.beginPath();
      ctx.strokeStyle = "#71717a"; // Matte muted graphite
      ctx.lineWidth = 2.5;
      ctx.lineCap = "round";
      ctx.moveTo(startX, centerY);
      ctx.lineTo(endX, centerY);
      ctx.stroke();
    };

    draw();
  }

  // =========================================================================
  // 4. Emotional Mood Engine (Context-Matched & Auto-Resetting)
  // =========================================================================
  setMood(moodCode, autoReset = true) {
    if (!moodCode) return;
    this.currentMood = moodCode.toUpperCase();
    this.dom.avatarFace.className = "avatar-face";
    this.dom.avatarFace.classList.add(`mood-${this.currentMood.toLowerCase()}`);

    // Sync mood to sprite companion
    if (this.spriteController) {
      this.spriteController.setMood(this.currentMood);
    }

    // Auto-return back to neutral (F1) after 4.2 seconds so expressions are dynamic and don't stay permanently stuck!
    clearTimeout(this.moodResetTimer);
    if (autoReset && this.currentMood !== "F1" && this.currentMood !== "F11") {
      this.moodResetTimer = setTimeout(() => {
        if (!this.isThinking && !this.isSpeaking) {
          this.setMood("F1", false);
        }
      }, 4200);
    }
  }

  showSubtitle(text, mood = "F1") {
    if (!text) return;
    clearTimeout(this.subtitleTimer);
    this.dom.subtitleText.innerText = text;
    this.dom.subtitleBox.classList.add("show");

    // Auto-dismiss after reading interval
    const duration = Math.max(3000, text.length * 75);
    this.subtitleTimer = setTimeout(() => {
      this.dom.subtitleBox.classList.remove("show");
    }, duration);
  }

  playBase64Audio(base64Data) {
    if (!base64Data) return;
    try {
      this.resumeAudio();
      this.audioElement.src = `data:audio/mp3;base64,${base64Data}`;
      this.audioElement.play().catch(() => {});
    } catch (e) {
      console.warn("[Audio Play Error]", e);
    }
  }

  // =========================================================================
  // 5. Query Handling & Communication
  // =========================================================================
  async sendQuery(queryText) {
    const text = (queryText || this.dom.chatInput.value).trim();
    if (!text) return;

    this.dom.chatInput.value = "";
    this.resumeAudio();

    // Check voice/text toggle for Live2D / Sprite
    const low = text.toLowerCase();
    if (low === "load avatar" || low === "live2d mode" || low === "switch to live2d") {
      this.toggleMode("live2d");
      this.showSubtitle("Loading avatar.", "F4");
      return;
    }
    if (low === "sprite mode" || low === "anime mode" || low === "load sprite" || low === "switch to sprite" || low === "anime girl") {
      this.toggleMode("sprite");
      this.showSubtitle("Anime sprite companion active.", "F4");
      return;
    }
    if (low === "stop avatar" || low === "minimal mode" || low === "switch to minimal" || low === "hide avatar") {
      this.toggleMode("minimal");
      this.showSubtitle("Minimal mode active.", "F1");
      return;
    }

    // Set Thinking State
    this.isThinking = true;
    this.setMood("F8"); // Thinking expression
    this.startThinkingHum();

    if (this.wsConnected && this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: "chat", text: text }));
    } else {
      // Direct REST fallback to port 5000
      try {
        const resp = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: text })
        });
        const data = await resp.json();
        this.handleServerResponse(data);
      } catch (err) {
        this.stopThinkingHum();
        this.isThinking = false;
        this.setMood("F3");
        this.showSubtitle(`Connection error: ${err.message}`, "F3");
      }
    }
  }

  handleServerResponse(data) {
    this.stopThinkingHum();
    this.isThinking = false;

    if (!data) return;

    const mood = data.mood || "F1";
    this.setMood(mood);
    this.playReadyChime();

    if (data.text) {
      this.showSubtitle(data.text, mood);
      if (this.activeMode === "sprite" && this.spriteController) {
        this.spriteController.triggerSpeech(data.text, Math.max(3000, data.text.length * 80));
      }
    }

    if (data.audio) {
      this.playBase64Audio(data.audio);
    }

    // Handle actions
    for (const act of data.actions || []) {
      if (act.type === "switch_mode") {
        this.toggleMode(act.mode);
      }
    }
  }

  // =========================================================================
  // 6. WebSocket Protocol Connection
  // =========================================================================
  connectWebSocket() {
    const loc = window.location;
    const proto = loc.protocol === "https:" ? "wss:" : "ws:";
    const hostname = loc.hostname || "127.0.0.1";
    let wsUrl = `${proto}//${loc.host || "127.0.0.1:5000"}/ws`;

    if (loc.port === "5000") {
      wsUrl = `${proto}//${hostname}:8765`;
    } else if (loc.port === "8080") {
      wsUrl = `${proto}//${loc.host}/ws`;
    }

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        this.wsConnected = true;
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "response" || data.text) {
            this.handleServerResponse(data);
          } else if (data.type === "expression") {
            this.setMood(data.id || "F1");
          }
        } catch (e) {}
      };

      this.ws.onclose = () => {
        this.wsConnected = false;
        setTimeout(() => this.connectWebSocket(), 3500);
      };

      this.ws.onerror = () => {
        this.ws.close();
      };
    } catch (e) {
      this.wsConnected = false;
    }
  }

  // =========================================================================
  // 7. Dynamic Mode Switcher (Minimal vs Live2D vs Anime Sprite)
  // =========================================================================
  async toggleMode(requestedMode) {
    const target = requestedMode || (this.activeMode === "minimal" ? "live2d" : "minimal");

    if (target === "live2d") {
      this.activeMode = "live2d";
      this.dom.minimalStage.classList.add("hidden");
      this.dom.animeSpriteStage.classList.remove("active");
      this.dom.live2dStage.classList.add("active");
      if (this.spriteController) this.spriteController.stop();
      await this.mountLive2D();
    } else if (target === "sprite") {
      this.activeMode = "sprite";
      this.dom.minimalStage.classList.add("hidden");
      this.dom.live2dStage.classList.remove("active");
      this.unmountLive2D();
      this.dom.animeSpriteStage.classList.add("active");
      if (this.spriteController) this.spriteController.start();
    } else {
      this.activeMode = "minimal";
      this.dom.live2dStage.classList.remove("active");
      this.dom.animeSpriteStage.classList.remove("active");
      this.dom.minimalStage.classList.remove("hidden");
      this.unmountLive2D();
      if (this.spriteController) this.spriteController.stop();
    }
  }

  async mountLive2D() {
    if (this.pixiApp) return;

    await this.ensureScriptLoaded("vendor/live2dcubismcore.min.js");
    await this.ensureScriptLoaded("vendor/pixi.min.js");
    await this.ensureScriptLoaded("vendor/cubism4.min.js");

    try {
      const canvas = this.dom.live2dCanvas;
      this.pixiApp = new PIXI.Application({
        view: canvas,
        resizeTo: this.dom.live2dStage,
        backgroundAlpha: 0,
        antialias: false,
        resolution: 1,
        powerPreference: "low-power"
      });

      if (window.PIXI && PIXI.live2d && PIXI.live2d.Live2DModel) {
        PIXI.live2d.Live2DModel.registerTicker(PIXI.Ticker);
        const modelUrl = "/assets/models/Kaguya/Kaguya.model3.json";
        this.live2dModel = await PIXI.live2d.Live2DModel.from(modelUrl, { autoInteract: false });
        this.pixiApp.stage.addChild(this.live2dModel);

        this.live2dModel.anchor.set(0.5, 0.0);
        const stageH = this.dom.live2dStage.clientHeight || 500;
        const scale = (stageH * 0.95) / (this.live2dModel.height || 1000);
        this.live2dModel.scale.set(scale);
        this.live2dModel.x = (this.dom.live2dStage.clientWidth || 360) / 2;
        this.live2dModel.y = 20;
      }
    } catch (e) {
      console.warn("[Live2D Mount Notice]", e);
    }
  }

  unmountLive2D() {
    if (this.pixiApp) {
      try {
        this.pixiApp.destroy(true, { children: true, texture: true, baseTexture: true });
      } catch (e) {}
      this.pixiApp = null;
      this.live2dModel = null;
    }
  }

  ensureScriptLoaded(src) {
    return new Promise((resolve) => {
      const existing = document.querySelector(`script[src="${src}"]`);
      if (existing) return resolve();
      const s = document.createElement("script");
      s.src = src;
      s.onload = () => resolve();
      s.onerror = () => resolve();
      document.head.appendChild(s);
    });
  }

  // =========================================================================
  // 8. Event Listeners & Voice Setup
  // =========================================================================
  setupEventListeners() {
    const footer = document.querySelector(".minimal-footer");

    // Send Button & Enter Key
    this.dom.btnSend.addEventListener("click", () => {
      this.sendQuery();
      if (footer) footer.classList.remove("active");
    });

    this.dom.chatInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        this.sendQuery();
        if (footer) footer.classList.remove("active");
      }
    });

    // Spacebar to trigger Voice Input; Any typing automatically focuses input
    window.addEventListener("keydown", (e) => {
      if (e.code === "Space" && document.activeElement !== this.dom.chatInput) {
        e.preventDefault();
        this.triggerVoiceInput();
      } else if (!e.ctrlKey && !e.metaKey && !e.altKey && e.key.length === 1 && document.activeElement !== this.dom.chatInput) {
        if (footer) footer.classList.add("active");
        this.dom.chatInput.focus();
      }
    });

    this.dom.btnMic.addEventListener("click", () => this.triggerVoiceInput());
  }

  setupSpeechRecognition() {
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRec) return;

    this.recognition = new SpeechRec();
    this.recognition.continuous = false;
    this.recognition.interimResults = false;
    this.recognition.lang = "en-US";

    this.recognition.onstart = () => {
      this.isListening = true;
      this.playWakeChime();
      this.dom.btnMic.classList.add("recording");
    };

    this.recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript.trim();
      this.sendQuery(transcript);
    };

    this.recognition.onend = () => {
      this.isListening = false;
      this.dom.btnMic.classList.remove("recording");
    };
  }

  triggerVoiceInput() {
    if (!this.recognition) return;
    try {
      if (this.isListening) {
        this.recognition.stop();
      } else {
        this.recognition.start();
      }
    } catch (e) {}
  }
}

// =========================================================================
// Anime PNG Sprite Controller (Cute shoulder-level view, 0% VRAM, 60fps)
// =========================================================================
class AnimeSpriteController {
  constructor(ui) {
    this.ui = ui;
    this.stage = ui.dom.animeSpriteStage;
    this.wrapper = ui.dom.animeSpriteWrapper;
    this.img = ui.dom.animeSpriteImg;
    this.bubble = ui.dom.animeSpeechBubble;
    this.bubbleText = ui.dom.animeSpeechText;

    this.isRunning = false;
    this.animFrameId = null;
    this.tick = 0;

    this.currentState = "idle"; // "idle", "talking", "walking"
    this.isSpeaking = false;
    this.speechEndTick = 0;

    // Walk physics
    this.isWalking = false;
    this.walkDirection = 1; // 1 = right, -1 = left
    this.walkPosX = 0;
    this.walkDestX = 0;

    // Blinking
    this.nextBlinkTick = 80;

    // Preload image assets into cache
    this.cache = {};
    this.currentMood = "F1";
    this.activeEmotionFrame = null;
    this.emotionResetTimer = null;
    this.preloadSprites();
    this.setupInteractions();
  }

  preloadSprites() {
    const list = [
      "idle_open", "idle_half", "idle_blink", "idle_wink",
      "talk_closed", "talk_half", "talk_open", "talk_o", "talk_smile",
      "walk_0", "walk_1", "walk_2", "walk_3",
      "emotion_happy", "emotion_thinking", "emotion_surprised",
      "emotion_sad", "emotion_shy", "emotion_annoyed", "emotion_smug", "emotion_sleepy"
    ];
    list.forEach(name => {
      const im = new Image();
      im.src = `/assets/sprites/zia_anime/${name}.png`;
      this.cache[name] = im;
    });
  }

  setMood(moodCode) {
    this.currentMood = moodCode ? moodCode.toUpperCase() : "F1";
    const emotionMap = {
      "F4": "emotion_happy",
      "F8": "emotion_thinking",
      "F7": "emotion_surprised",
      "F10": "emotion_surprised",
      "F6": "emotion_sad",
      "F2": "emotion_shy",
      "F5": "emotion_shy",
      "F3": "emotion_annoyed",
      "F9": "emotion_smug",
      "F11": "emotion_sleepy"
    };

    this.activeEmotionFrame = emotionMap[this.currentMood] || null;
    if (this.activeEmotionFrame && !this.isSpeaking && !this.isWalking) {
      this.setFrame(this.activeEmotionFrame);
    }

    clearTimeout(this.emotionResetTimer);
    if (this.activeEmotionFrame && this.currentMood !== "F11") {
      this.emotionResetTimer = setTimeout(() => {
        this.activeEmotionFrame = null;
        this.currentMood = "F1";
        if (!this.isSpeaking && !this.isWalking) {
          this.setFrame("idle_open");
        }
      }, 4200);
    }
  }

  setupInteractions() {
    if (!this.wrapper) return;
    this.wrapper.addEventListener("click", () => {
      this.ui.playClickBlip();
      this.setMood("F4");
      this.triggerSpeech("I'm right here with you! (^ _ ^)", 3000);
    });
  }

  start() {
    if (this.isRunning) return;
    this.isRunning = true;
    this.tick = 0;
    this.loop();
  }

  stop() {
    this.isRunning = false;
    if (this.animFrameId) {
      cancelAnimationFrame(this.animFrameId);
      this.animFrameId = null;
    }
    this.clearSpeech();
  }

  setFrame(name) {
    if (!this.img) return;
    const url = `/assets/sprites/zia_anime/${name}.png`;
    if (this.img.src.indexOf(url) === -1) {
      this.img.src = url;
    }
  }

  triggerSpeech(text, durationMs = 3500) {
    if (!this.bubble || !this.bubbleText) return;
    this.bubbleText.innerText = text;
    this.bubble.classList.add("show");
    this.isSpeaking = true;
    this.currentState = "talking";
    this.speechEndTick = this.tick + Math.floor(durationMs / 33);
  }

  clearSpeech() {
    if (this.bubble) this.bubble.classList.remove("show");
    this.isSpeaking = false;
    if (this.currentState === "talking") {
      this.currentState = "idle";
      this.setFrame(this.activeEmotionFrame || "talk_closed");
      setTimeout(() => {
        if (!this.isSpeaking) this.setFrame(this.activeEmotionFrame || "idle_open");
      }, 120);
    }
  }

  loop() {
    if (!this.isRunning) return;
    this.tick++;

    // Check speech timeout
    if (this.isSpeaking && this.tick >= this.speechEndTick) {
      this.clearSpeech();
    }

    // State 1: Talking lip-sync with smooth syllabic cadence (no mouth glitching/flickering)
    if (this.isSpeaking) {
      // Natural cadence: holds each mouth shape for 4 ticks (~130ms)
      const talkCycle = ["talk_half", "talk_open", "talk_half", "talk_smile"];
      const pIdx = Math.floor(this.tick / 4) % talkCycle.length;
      this.setFrame(talkCycle[pIdx]);
    }
    // State 2: Walking Cycle
    else if (this.isWalking) {
      const walkFrames = ["walk_0", "walk_1", "walk_2", "walk_3"];
      const wIdx = Math.floor(this.tick / 4) % 4;
      this.setFrame(walkFrames[wIdx]);

      // Move horizontally
      this.walkPosX += 2.5 * this.walkDirection;
      if (this.img) {
        if (this.walkDirection < 0) {
          this.img.classList.add("flipped");
        } else {
          this.img.classList.remove("flipped");
        }
      }
      if (this.wrapper) {
        this.wrapper.style.transform = `translateX(${this.walkPosX}px)`;
      }

      // Check destination
      if ((this.walkDirection > 0 && this.walkPosX >= this.walkDestX) ||
          (this.walkDirection < 0 && this.walkPosX <= this.walkDestX)) {
        this.isWalking = false;
        this.currentState = "idle";
        this.setFrame(this.activeEmotionFrame || "idle_open");
      }
    }
    // State 3: Organic Multi-Frequency Idle Breathing, Gaze Sway & Blinking
    else {
      // Periodic decision to take a stroll (every ~10-15 seconds)
      if (this.tick % 320 === 0 && Math.random() < 0.45) {
        this.startRandomStroll();
      } else {
        // Natural blink sequence (with occasional anime double-blink)
        if (this.tick >= this.nextBlinkTick) {
          const sub = this.tick - this.nextBlinkTick;
          if (sub < 2) {
            this.setFrame("idle_half");
          } else if (sub < 6) {
            this.setFrame("idle_blink");
          } else if (sub < 8) {
            this.setFrame("idle_half");
          } else {
            this.setFrame(this.activeEmotionFrame || "idle_open");
            // 20% chance of double-blink, otherwise 2.5 - 6s delay
            const isDouble = Math.random() < 0.2;
            this.nextBlinkTick = this.tick + (isDouble ? 18 : (80 + Math.floor(Math.random() * 120)));
          }
        } else if (this.tick % 450 === 180 && Math.random() < 0.3) {
          this.setFrame("idle_wink");
        } else if (this.tick % 450 === 194) {
          this.setFrame(this.activeEmotionFrame || "idle_open");
        } else {
          // Multi-frequency organic breathing + gentle lateral gaze sway
          const breathY = Math.sin(this.tick * 0.04) * 2.8 + Math.cos(this.tick * 0.02) * 1.0;
          const swayX = Math.cos(this.tick * 0.025) * 1.5;
          const currentX = this.walkPosX + swayX;

          if (this.wrapper && !this.isWalking) {
            this.wrapper.style.transform = `translateX(${currentX}px) translateY(${breathY}px)`;
          }

          // If an active emotion is active (happy, thinking, annoyed, etc.), display it!
          this.setFrame(this.activeEmotionFrame || "idle_open");
        }
      }
    }

    this.animFrameId = requestAnimationFrame(() => this.loop());
  }

  startRandomStroll() {
    const maxOffset = 140;
    const dir = Math.random() < 0.5 ? -1 : 1;
    this.walkDirection = dir;
    this.walkDestX = Math.max(-maxOffset, Math.min(maxOffset, this.walkPosX + dir * (70 + Math.random() * 90)));
    this.isWalking = true;
    this.currentState = "walking";
  }
}

// Instantiate on DOM load
window.addEventListener("DOMContentLoaded", () => {
  window.ziaCompanion = new ZiaCompanionUI();
});
