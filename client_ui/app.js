/**
 * Project Zia // Minimalist Grey Companion Client UI (client_ui/app.js)
 * Optimised for Sony Xperia 1 III — 21:9 CinemaWide 4K HDR OLED (3840×1644)
 *
 * Features:
 *  - Expressive HTML/CSS eyes & procedural mouth with organic emotions.
 *  - Pointer-event eye tracking (mouse + touch) & click/tap interactions.
 *  - Procedural Web Audio API sound effects (chimes, thinking hum, ready ping).
 *  - Real-time speech audio waveform mouth synchronisation.
 *  - Dynamic Live2D mount/unmount strictly on demand via voice/chat command.
 *  - Full-body Anime Sprite Avatar with:
 *      • 24 FPS locked animation loop across all 21 frames.
 *      • Mobile tap-to-react + drag-to-reposition touch interactions.
 *      • Visibility-change & minimisation triggers.
 */

class ZiaCompanionUI {
  constructor() {
    this.activeMode = "minimal"; // "minimal" | "live2d" | "sprite"
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
    this.moodResetTimer = null;
    this.lastBlinkTime = 0;
    this.nextBlinkDelay = 3500;

    // DOM Elements
    this.dom = {
      container:          document.getElementById("app-container"),
      minimalStage:       document.getElementById("minimal-stage"),
      live2dStage:        document.getElementById("live2d-stage"),
      live2dCanvas:       document.getElementById("live2d-canvas"),
      animeSpriteStage:   document.getElementById("anime-sprite-stage"),
      animeSpriteWrapper: document.getElementById("anime-sprite-wrapper"),
      animeSpriteImg:     document.getElementById("anime-sprite-img"),
      animeSpeechBubble:  document.getElementById("anime-speech-bubble"),
      animeSpeechText:    document.getElementById("anime-speech-text"),
      avatarFace:         document.getElementById("avatar-face"),
      eyeLeft:            document.getElementById("eye-left"),
      eyeRight:           document.getElementById("eye-right"),
      pupilLeft:          document.getElementById("pupil-left"),
      pupilRight:         document.getElementById("pupil-right"),
      mouthContainer:     document.getElementById("mouth-container"),
      mouthCanvas:        document.getElementById("mouth-waveform-canvas"),
      subtitleBox:        document.getElementById("subtitle-box"),
      subtitleText:       document.getElementById("subtitle-text"),
      chatInput:          document.getElementById("chat-input"),
      btnSend:            document.getElementById("btn-send"),
      btnMic:             document.getElementById("btn-mic")
    };

    this.init();
  }

  async init() {
    this.setupAudioContext();
    this.spriteController = new AnimeSpriteController(this);
    this.setupEventListeners();
    this.setupEyeTracking();   // calls setupPointerTracking() internally
    this.setupBlinkLoop();
    this.setupSpeechRecognition();
    this.setupMinimizationHandler();
    this.startMouthRenderLoop();
    this.connectWebSocket();
  }

  // =========================================================================
  // Minimisation / Visibility Handler
  // =========================================================================
  setupMinimizationHandler() {
    this.previousModeBeforeMinimize = "minimal";
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) {
        // Page hidden (tab switched, screen off, minimised WebView on Android)
        this.previousModeBeforeMinimize = this.activeMode;
        this.toggleMode("sprite");
        if (this.spriteController) {
          this.spriteController.triggerSpeech("Zia is watching over you~", 3200);
        }
      } else {
        // Page restored
        const prev = this.previousModeBeforeMinimize;
        if (prev && prev !== "sprite") {
          this.toggleMode(prev);
        }
      }
    });
  }

  // =========================================================================
  // 1. Procedural Web Audio Synthesiser & SFX Engine
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
      const osc  = this.audioContext.createOscillator();
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
    this.playTone(480, "sine", 0.12, 0.09);
    setTimeout(() => this.playTone(720, "sine", 0.22, 0.08), 90);
  }

  playReadyChime() {
    this.playTone(880, "triangle", 0.35, 0.07);
  }

  playClickBlip() {
    this.playTone(600, "sine", 0.08, 0.06);
    setTimeout(() => this.playTone(900, "sine", 0.1, 0.06), 60);
  }

  startThinkingHum() {
    if (!this.audioContext || this.thinkingHumNode) return;
    this.resumeAudio();
    try {
      const osc  = this.audioContext.createOscillator();
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
        setTimeout(() => { try { osc.stop(); } catch (e) {} }, 160);
      } catch (e) {}
      this.thinkingHumNode = null;
    }
  }

  // =========================================================================
  // 2. Pointer Tracking (Mouse + Touch) & Natural Blinking Loop
  // setupEyeTracking() is the legacy public alias kept for API/test contract.
  // =========================================================================
  setupEyeTracking() { return this.setupPointerTracking(); }

  setupPointerTracking() {
    let isPointerActive = false;
    let idleTimer = null;

    const track = (clientX, clientY) => {
      isPointerActive = true;
      clearTimeout(idleTimer);
      idleTimer = setTimeout(() => { isPointerActive = false; }, 2500);
      if (!this.isThinking) {
        this.updatePupilTracking(clientX, clientY);
      }
    };

    // Mouse
    window.addEventListener("mousemove", (e) => track(e.clientX, e.clientY));

    // Touch — single finger moves pupils
    window.addEventListener("touchmove", (e) => {
      if (e.touches.length === 1) {
        track(e.touches[0].clientX, e.touches[0].clientY);
      }
    }, { passive: true });

    // Face Click/Tap: Playful wink interaction
    if (this.dom.avatarFace) {
      this.dom.avatarFace.addEventListener("click", () => {
        this.playClickBlip();
        this.setMood("F9"); // Smug / Wink
        setTimeout(() => this.setMood("F4"), 1200);
        setTimeout(() => this.setMood("F1"), 2800);
      });
    }
  }

  updatePupilTracking(targetX, targetY) {
    if (!this.dom.avatarFace) return;
    const faceRect = this.dom.avatarFace.getBoundingClientRect();
    const faceCX   = faceRect.left + faceRect.width  / 2;
    const faceCY   = faceRect.top  + faceRect.height / 2;

    const deltaX = (targetX - faceCX) / (window.innerWidth  / 2);
    const deltaY = (targetY - faceCY) / (window.innerHeight / 2);

    const maxX  = 9, maxY = 7;
    const shiftX = Math.max(-maxX, Math.min(maxX, deltaX * maxX));
    const shiftY = Math.max(-maxY, Math.min(maxY, deltaY * maxY));

    if (this.dom.pupilLeft)  this.dom.pupilLeft.style.transform  = `translate(${shiftX}px,${shiftY}px)`;
    if (this.dom.pupilRight) this.dom.pupilRight.style.transform = `translate(${shiftX}px,${shiftY}px)`;
  }

  setupBlinkLoop() {
    const runBlink = () => {
      if (this.dom.eyeLeft)  this.dom.eyeLeft.classList.add("blink");
      if (this.dom.eyeRight) this.dom.eyeRight.classList.add("blink");

      setTimeout(() => {
        if (this.dom.eyeLeft)  this.dom.eyeLeft.classList.remove("blink");
        if (this.dom.eyeRight) this.dom.eyeRight.classList.remove("blink");

        // 18% chance of a realistic quick double-blink
        if (Math.random() < 0.18) {
          setTimeout(() => {
            if (this.dom.eyeLeft)  this.dom.eyeLeft.classList.add("blink");
            if (this.dom.eyeRight) this.dom.eyeRight.classList.add("blink");
            setTimeout(() => {
              if (this.dom.eyeLeft)  this.dom.eyeLeft.classList.remove("blink");
              if (this.dom.eyeRight) this.dom.eyeRight.classList.remove("blink");
            }, 90);
          }, 120);
        }
      }, 100);

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
    const ctx    = canvas.getContext("2d");

    // Scale canvas to its CSS display size for crisp rendering on 4K OLED
    const dpr = Math.min(window.devicePixelRatio || 1, 3); // cap at 3× for perf
    const cssW = canvas.offsetWidth  || 220;
    const cssH = canvas.offsetHeight || 42;
    canvas.width  = Math.round(cssW * dpr);
    canvas.height = Math.round(cssH * dpr);
    ctx.scale(dpr, dpr);
    const W = cssW;
    const H = cssH;

    const bufLen       = this.analyser ? this.analyser.frequencyBinCount : 32;
    const dataArray    = new Uint8Array(bufLen);
    const bars         = 22;
    const smoothedBars = new Float32Array(bars);
    let smoothedVol    = 0;
    let wavePhase      = 0;

    const draw = () => {
      requestAnimationFrame(draw);
      ctx.clearRect(0, 0, W, H);

      let currentVol = 0;
      if (this.analyser && !this.audioElement.paused) {
        this.analyser.getByteFrequencyData(dataArray);
        let sum = 0;
        for (let i = 0; i < bufLen; i++) sum += dataArray[i];
        currentVol = sum / bufLen;
      }

      // Smooth attack/decay hysteresis
      if (currentVol > smoothedVol) {
        smoothedVol = smoothedVol * 0.35 + currentVol * 0.65;
      } else {
        smoothedVol = smoothedVol * 0.82 + currentVol * 0.18;
      }

      const isActiveAudio = smoothedVol > 3.5;
      this.isSpeaking = isActiveAudio;

      const cy = H / 2;

      // MODE A: Speaking — Silver/Grey Audio-Reactive Bar Waveform
      if (isActiveAudio) {
        const barW   = 4;
        const gap    = (W - bars * barW) / (bars - 1);
        for (let i = 0; i < bars; i++) {
          const raw = dataArray[i % bufLen] || 0;
          smoothedBars[i] = smoothedBars[i] * 0.65 + raw * 0.35;
          const bh  = Math.max(3, (smoothedBars[i] / 255) * (H - 6));
          const x   = i * (barW + gap);
          const y   = cy - bh / 2;
          ctx.fillStyle = "#e0e0e2";
          ctx.beginPath();
          ctx.roundRect(x, y, barW, bh, 2);
          ctx.fill();
        }
        return;
      }

      // MODE B: Thinking — Undulating Sine Wave Ripple
      if (this.isThinking) {
        wavePhase += 0.08;
        ctx.beginPath();
        ctx.strokeStyle = "#8a8a94";
        ctx.lineWidth   = 2.2;
        ctx.lineCap     = "round";
        const sx = 36, ex = W - 36;
        for (let x = sx; x <= ex; x += 2) {
          const progress = (x - sx) / (ex - sx);
          const env = Math.sin(progress * Math.PI);
          const y  = cy + Math.sin(progress * 10 - wavePhase) * 6 * env;
          if (x === sx) ctx.moveTo(x, y); else ctx.lineTo(x, y);
        }
        ctx.stroke();
        return;
      }

      // MODE C: Happy (F4) — Upward Curved Smile
      if (this.currentMood === "F4") {
        ctx.beginPath();
        ctx.strokeStyle = "#c8c8cc";
        ctx.lineWidth = 2.8; ctx.lineCap = "round";
        const sx = 60, ex = W - 60;
        ctx.moveTo(sx, cy - 2);
        ctx.quadraticCurveTo(W / 2, cy + 10, ex, cy - 2);
        ctx.stroke();
        return;
      }

      // MODE D: Surprised (F7 / F10) — Open Round Mouth
      if (this.currentMood === "F7" || this.currentMood === "F10") {
        ctx.beginPath();
        ctx.strokeStyle = "#c8c8cc";
        ctx.lineWidth   = 2.2;
        ctx.arc(W / 2, cy, 8, 0, Math.PI * 2);
        ctx.stroke();
        return;
      }

      // MODE E: Sad (F6) — Downward Turned Curve
      if (this.currentMood === "F6") {
        ctx.beginPath();
        ctx.strokeStyle = "#606068";
        ctx.lineWidth = 2.2; ctx.lineCap = "round";
        const sx = 68, ex = W - 68;
        ctx.moveTo(sx, cy + 4);
        ctx.quadraticCurveTo(W / 2, cy - 4, ex, cy + 4);
        ctx.stroke();
        return;
      }

      // MODE F: Smug / Playful (F9) — Asymmetric Smirk
      if (this.currentMood === "F9") {
        ctx.beginPath();
        ctx.strokeStyle = "#c8c8cc";
        ctx.lineWidth = 2.2; ctx.lineCap = "round";
        ctx.moveTo(66, cy + 2);
        ctx.quadraticCurveTo(W / 2, cy + 4, W - 66, cy - 5);
        ctx.stroke();
        return;
      }

      // MODE G: Annoyed / Pout (F3) — Tight Compressed Line
      if (this.currentMood === "F3") {
        ctx.beginPath();
        ctx.strokeStyle = "#8a8a94";
        ctx.lineWidth = 2.2; ctx.lineCap = "round";
        const sx = (W - 40) / 2;
        ctx.moveTo(sx, cy);
        ctx.lineTo(sx + 40, cy);
        ctx.stroke();
        return;
      }

      // MODE H: Shy / Bashful (F2 / F5) — Soft Petite Curve
      if (this.currentMood === "F2" || this.currentMood === "F5") {
        ctx.beginPath();
        ctx.strokeStyle = "#c8c8cc";
        ctx.lineWidth = 2.0; ctx.lineCap = "round";
        const sx = 76, ex = W - 76;
        ctx.moveTo(sx, cy - 1);
        ctx.quadraticCurveTo(W / 2, cy + 5, ex, cy - 1);
        ctx.stroke();
        return;
      }

      // MODE I: Default Idle — Soft Breathing Minimal Silver Line
      const breath   = Math.sin(performance.now() * 0.002) * 1.5;
      const lw       = 58 + breath * 4;
      const sx       = (W - lw) / 2;
      ctx.beginPath();
      ctx.strokeStyle = "#606068"; // OLED-safe muted graphite
      ctx.lineWidth   = 2.2;
      ctx.lineCap     = "round";
      ctx.moveTo(sx, cy);
      ctx.lineTo(sx + lw, cy);
      ctx.stroke();
    };

    draw();
  }

  // =========================================================================
  // 4. Emotional Mood Engine
  // =========================================================================
  setMood(moodCode, autoReset = true) {
    if (!moodCode) return;
    this.currentMood = moodCode.toUpperCase();
    if (this.dom.avatarFace) {
      this.dom.avatarFace.className = "avatar-face";
      this.dom.avatarFace.classList.add(`mood-${this.currentMood.toLowerCase()}`);
    }

    if (this.spriteController) {
      this.spriteController.setMood(this.currentMood);
    }

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
    if (this.dom.subtitleText) this.dom.subtitleText.innerText = text;
    if (this.dom.subtitleBox)  this.dom.subtitleBox.classList.add("show");

    const duration = Math.max(3000, text.length * 75);
    this.subtitleTimer = setTimeout(() => {
      if (this.dom.subtitleBox) this.dom.subtitleBox.classList.remove("show");
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

    const low = text.toLowerCase();
    if (low === "load avatar" || low === "live2d mode" || low === "switch to live2d") {
      this.toggleMode("live2d");
      this.showSubtitle("Loading avatar.", "F4");
      return;
    }
    if (["sprite mode","anime mode","load sprite","switch to sprite","anime girl"].includes(low)) {
      this.toggleMode("sprite");
      this.showSubtitle("Anime sprite companion active.", "F4");
      return;
    }
    if (["stop avatar","minimal mode","switch to minimal","hide avatar"].includes(low)) {
      this.toggleMode("minimal");
      this.showSubtitle("Minimal mode active.", "F1");
      return;
    }

    this.isThinking = true;
    this.setMood("F8");
    this.startThinkingHum();

    if (this.wsConnected && this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: "chat", text }));
    } else {
      try {
        const resp = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text })
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

    for (const act of data.actions || []) {
      if (act.type === "switch_mode") this.toggleMode(act.mode);
    }
  }

  // =========================================================================
  // 6. WebSocket Protocol Connection
  // =========================================================================
  connectWebSocket() {
    const loc    = window.location;
    const proto  = loc.protocol === "https:" ? "wss:" : "ws:";
    const hostname = loc.hostname || "127.0.0.1";
    let wsUrl = `${proto}//${loc.host || "127.0.0.1:5000"}/ws`;

    if (loc.port === "5000") {
      wsUrl = `${proto}//${hostname}:8765`;
    } else if (loc.port === "8080") {
      wsUrl = `${proto}//${loc.host}/ws`;
    }

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => { this.wsConnected = true; };

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

      this.ws.onerror = () => { this.ws.close(); };
    } catch (e) {
      this.wsConnected = false;
    }
  }

  // =========================================================================
  // 7. Dynamic Mode Switcher (Minimal / Live2D / Anime Sprite)
  // =========================================================================
  async toggleMode(requestedMode) {
    const target = requestedMode || (this.activeMode === "minimal" ? "live2d" : "minimal");

    if (target === "live2d") {
      this.activeMode = "live2d";
      this.dom.minimalStage.classList.add("hidden");
      this.dom.animeSpriteStage.classList.remove("active");
      this.dom.animeSpriteStage.classList.add("hidden");
      this.dom.live2dStage.classList.add("active");
      if (this.spriteController) this.spriteController.stop();
      await this.mountLive2D();

    } else if (target === "sprite") {
      this.activeMode = "sprite";
      this.dom.minimalStage.classList.add("hidden");
      this.dom.live2dStage.classList.remove("active");
      this.unmountLive2D();
      this.dom.animeSpriteStage.classList.remove("hidden");
      // rAF ensures the hidden class is removed before opacity transition starts
      requestAnimationFrame(() => {
        this.dom.animeSpriteStage.classList.add("active");
      });
      if (this.spriteController) this.spriteController.start();

    } else {
      this.activeMode = "minimal";
      this.dom.live2dStage.classList.remove("active");
      this.dom.animeSpriteStage.classList.remove("active");
      this.dom.animeSpriteStage.classList.add("hidden");
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
        view:            canvas,
        resizeTo:        this.dom.live2dStage,
        backgroundAlpha: 0,
        antialias:       false,
        resolution:      1,
        powerPreference: "low-power"
      });

      if (window.PIXI && PIXI.live2d && PIXI.live2d.Live2DModel) {
        PIXI.live2d.Live2DModel.registerTicker(PIXI.Ticker);
        const modelUrl = "/assets/models/Kaguya/Kaguya.model3.json";
        this.live2dModel = await PIXI.live2d.Live2DModel.from(modelUrl, { autoInteract: false });
        this.pixiApp.stage.addChild(this.live2dModel);

        this.live2dModel.anchor.set(0.5, 0.0);
        const stageH = this.dom.live2dStage.clientHeight || 500;
        const scale  = (stageH * 0.95) / (this.live2dModel.height || 1000);
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
      this.pixiApp    = null;
      this.live2dModel = null;
    }
  }

  ensureScriptLoaded(src) {
    return new Promise((resolve) => {
      if (document.querySelector(`script[src="${src}"]`)) return resolve();
      const s = document.createElement("script");
      s.src    = src;
      s.onload  = () => resolve();
      s.onerror = () => resolve();
      document.head.appendChild(s);
    });
  }

  // =========================================================================
  // 8. Event Listeners & Voice Setup
  // =========================================================================
  setupEventListeners() {
    const footer = document.querySelector(".minimal-footer");

    this.dom.btnSend.addEventListener("click", () => {
      this.sendQuery();
      footer?.classList.remove("active");
    });

    this.dom.chatInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        this.sendQuery();
        footer?.classList.remove("active");
      }
    });

    // Spacebar = voice; any printable key = focus input
    window.addEventListener("keydown", (e) => {
      if (e.code === "Space" && document.activeElement !== this.dom.chatInput) {
        e.preventDefault();
        this.triggerVoiceInput();
      } else if (!e.ctrlKey && !e.metaKey && !e.altKey &&
                 e.key.length === 1 && document.activeElement !== this.dom.chatInput) {
        footer?.classList.add("active");
        this.dom.chatInput.focus();
      }
    });

    this.dom.btnMic.addEventListener("click", () => this.triggerVoiceInput());

    // Show footer on any touch in lower 20% of screen
    document.addEventListener("touchstart", (e) => {
      if (e.touches[0].clientY > window.innerHeight * 0.80) {
        footer?.classList.add("active");
      }
    }, { passive: true });
  }

  setupSpeechRecognition() {
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRec) return;

    this.recognition = new SpeechRec();
    this.recognition.continuous     = false;
    this.recognition.interimResults = false;
    this.recognition.lang           = "en-US";

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


// =============================================================================
// Anime PNG Sprite Controller
// Full-body 24 FPS companion — 0% VRAM, <15 MB RAM
// All 21 frames: idle_* (4), talk_* (5), walk_* (4), emotion_* (8)
// Mobile touch: tap to react, drag to reposition
// =============================================================================
class AnimeSpriteController {
  constructor(ui) {
    this.ui           = ui;
    this.stage        = ui.dom.animeSpriteStage;
    this.wrapper      = ui.dom.animeSpriteWrapper;
    this.img          = ui.dom.animeSpriteImg;
    this.bubble       = ui.dom.animeSpeechBubble;
    this.bubbleText   = ui.dom.animeSpeechText;

    this.isRunning    = false;
    this.animFrameId  = null;
    this.tick         = 0;
    this.lastFrameTime = 0;

    this.currentState   = "idle"; // "idle" | "talking" | "walking"
    this.isSpeaking     = false;
    this.speechEndTick  = 0;

    // Walk physics
    this.isWalking    = false;
    this.walkDirection = 1; // 1 = right, -1 = left
    this.walkPosX     = 0;
    this.walkDestX    = 0;

    // Blinking
    this.nextBlinkTick = 80;

    // Preload image assets into cache
    this.cache = {};
    this.currentMood       = "F1";
    this.activeEmotionFrame = null;
    this.emotionResetTimer  = null;

    // Touch drag state
    this._dragActive   = false;
    this._dragOffsetX  = 0;
    this._dragOffsetY  = 0;
    this._dragStartX   = 0;
    this._dragStartY   = 0;
    this._dragMoved    = false;
    // Wrapper absolute position (set during dragging)
    this._posX = 0;
    this._posY = 0;

    this.preloadSprites();
    this.setupInteractions();
  }

  // ---------------------------------------------------------------------------
  // Sprite asset pre-loading (all 21 frames)
  // ---------------------------------------------------------------------------
  preloadSprites() {
    const list = [
      // idle (4 frames)
      "idle_open", "idle_half", "idle_blink", "idle_wink",
      // talk (5 frames)
      "talk_closed", "talk_half", "talk_open", "talk_o", "talk_smile",
      // walk (4 frames)
      "walk_0", "walk_1", "walk_2", "walk_3",
      // emotion (8 frames)
      "emotion_happy", "emotion_thinking", "emotion_surprised",
      "emotion_sad", "emotion_shy", "emotion_annoyed", "emotion_smug", "emotion_sleepy"
    ];
    list.forEach(name => {
      const im = new Image();
      im.src   = `/assets/sprites/zia_anime/${name}.png`;
      this.cache[name] = im;
    });
  }

  // ---------------------------------------------------------------------------
  // Mood → emotion frame mapping
  // ---------------------------------------------------------------------------
  setMood(moodCode) {
    this.currentMood = moodCode ? moodCode.toUpperCase() : "F1";
    const emotionMap = {
      "F4":  "emotion_happy",
      "F8":  "emotion_thinking",
      "F7":  "emotion_surprised",
      "F10": "emotion_surprised",
      "F6":  "emotion_sad",
      "F2":  "emotion_shy",
      "F5":  "emotion_shy",
      "F3":  "emotion_annoyed",
      "F9":  "emotion_smug",
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
        this.currentMood        = "F1";
        if (!this.isSpeaking && !this.isWalking) {
          this.setFrame("idle_open");
        }
      }, 4200);
    }
  }

  // ---------------------------------------------------------------------------
  // Touch + mouse interactions: tap to react, drag to reposition
  // ---------------------------------------------------------------------------
  setupInteractions() {
    if (!this.wrapper) return;

    // ---- DRAG TO REPOSITION (Pointer Events API — works for touch + mouse) ----
    this.wrapper.addEventListener("pointerdown", (e) => {
      // Only intercept on the sprite stage (not footer etc.)
      if (this.ui.activeMode !== "sprite") return;
      e.preventDefault();
      this.wrapper.setPointerCapture(e.pointerId);

      this._dragActive  = true;
      this._dragMoved   = false;
      this._dragStartX  = e.clientX;
      this._dragStartY  = e.clientY;
      this._dragOffsetX = e.clientX - this._posX;
      this._dragOffsetY = e.clientY - this._posY;
    }, { passive: false });

    this.wrapper.addEventListener("pointermove", (e) => {
      if (!this._dragActive) return;
      const dx = e.clientX - this._dragStartX;
      const dy = e.clientY - this._dragStartY;
      if (Math.abs(dx) > 6 || Math.abs(dy) > 6) {
        this._dragMoved = true;
      }

      if (this._dragMoved) {
        this._posX = e.clientX - this._dragOffsetX;
        this._posY = e.clientY - this._dragOffsetY;

        // Clamp within viewport
        const stageRect = this.stage ? this.stage.getBoundingClientRect() : { width: window.innerWidth, height: window.innerHeight };
        const imgW = this.img ? this.img.offsetWidth  : 160;
        const imgH = this.img ? this.img.offsetHeight : 290;
        this._posX = Math.max(-stageRect.width  / 2 + imgW / 2,
                     Math.min( stageRect.width  / 2 - imgW / 2, this._posX));
        this._posY = Math.max(-stageRect.height / 2 + imgH / 4,
                     Math.min( stageRect.height / 2 - imgH / 4, this._posY));

        // Apply as translate on top of breathing/walk offsets
        if (this.wrapper) {
          this.wrapper.style.transform = `translateX(${this._posX + this.walkPosX}px) translateY(${this._posY}px)`;
        }
      }
    });

    const endDrag = (e) => {
      if (!this._dragActive) return;
      this._dragActive = false;

      // If pointer barely moved: treat as a TAP → playful reaction
      if (!this._dragMoved) {
        this._onTap();
      }
    };

    this.wrapper.addEventListener("pointerup",     endDrag);
    this.wrapper.addEventListener("pointercancel", endDrag);

    // Click also fires on desktop (no-drag click)
    this.wrapper.addEventListener("click", () => {
      if (!this._dragMoved) this._onTap();
    });
  }

  /** Playful tap reaction — cycles through a set of fun responses */
  _onTap() {
    this.ui.playClickBlip();
    const reactions = [
      { mood: "F9", text: "Hey, that tickles! (≧∇≦)" },
      { mood: "F4", text: "I'm here with you~  (^ _ ^)" },
      { mood: "F2", text: "Ehehe... hi there! (⁄ ⁄>⁄ ▽ ⁄<⁄ ⁄)" },
      { mood: "F7", text: "Oh! You startled me! ( ゜o゜)" },
      { mood: "F9", text: "What's up? Need something?" }
    ];
    const r = reactions[Math.floor(Math.random() * reactions.length)];
    this.setMood(r.mood);
    this.triggerSpeech(r.text, 2800);
  }

  // ---------------------------------------------------------------------------
  // Animation control
  // ---------------------------------------------------------------------------
  start() {
    if (this.isRunning) return;
    this.isRunning     = true;
    this.tick          = 0;
    this.lastFrameTime = performance.now();
    this.loop(this.lastFrameTime);
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
    // Avoid unnecessary src assignment (triggers reflow)
    if (!this.img.src.endsWith(url)) {
      this.img.src = url;
    }
  }

  triggerSpeech(text, durationMs = 3500) {
    if (!this.bubble || !this.bubbleText) return;
    this.bubbleText.innerText = text;
    this.bubble.classList.add("show");
    this.isSpeaking    = true;
    this.currentState  = "talking";
    // Convert ms to tick count at 24 FPS (41.67ms/tick)
    this.speechEndTick = this.tick + Math.ceil(durationMs / 41.67);
  }

  clearSpeech() {
    if (this.bubble) this.bubble.classList.remove("show");
    this.isSpeaking = false;
    if (this.currentState === "talking") {
      this.currentState = "idle";
      this.setFrame(this.activeEmotionFrame || "talk_closed");
      setTimeout(() => {
        if (!this.isSpeaking) {
          this.setFrame(this.activeEmotionFrame || "idle_open");
        }
      }, 120);
    }
  }

  // ---------------------------------------------------------------------------
  // 24 FPS Animation Loop
  // Uses requestAnimationFrame with strict 41.67ms pacing so the loop never
  // double-steps or under-steps on a 60/120/144Hz display.
  // ---------------------------------------------------------------------------
  loop(timestamp = performance.now()) {
    if (!this.isRunning) return;

    const delta = timestamp - (this.lastFrameTime || timestamp);
    if (delta >= 41.6) { // ~24 FPS
      this.lastFrameTime = timestamp - (delta % 41.6);
      this.tick++;

      // Speech timeout
      if (this.isSpeaking && this.tick >= this.speechEndTick) {
        this.clearSpeech();
      }

      // --- STATE 1: Talking lip-sync (smooth syllabic cadence, all mouth frames) ---
      if (this.isSpeaking) {
        // 5-frame cycle uses talk_o for rounder open-mouth phoneme
        const talkCycle = ["talk_half", "talk_open", "talk_o", "talk_half", "talk_smile"];
        const pIdx = Math.floor(this.tick / 3) % talkCycle.length;
        this.setFrame(talkCycle[pIdx]);

      // --- STATE 2: Walking (4-frame walk cycle) ---
      } else if (this.isWalking) {
        const walkFrames = ["walk_0", "walk_1", "walk_2", "walk_3"];
        const wIdx = Math.floor(this.tick / 4) % 4;
        this.setFrame(walkFrames[wIdx]);

        // Mirror image when walking left
        if (this.img) {
          if (this.walkDirection < 0) {
            this.img.classList.add("flipped");
          } else {
            this.img.classList.remove("flipped");
          }
        }

        this.walkPosX += 2.5 * this.walkDirection;

        if (this.wrapper && !this._dragMoved) {
          this.wrapper.style.transform = `translateX(${this._posX + this.walkPosX}px) translateY(${this._posY}px)`;
        }

        if ((this.walkDirection > 0 && this.walkPosX >= this.walkDestX) ||
            (this.walkDirection < 0 && this.walkPosX <= this.walkDestX)) {
          this.isWalking    = false;
          this.currentState = "idle";
          this.setFrame(this.activeEmotionFrame || "idle_open");
        }

      // --- STATE 3: Idle (breathing, blinking, occasional wink, stroll) ---
      } else {
        // Random stroll ~every 10-15 seconds
        if (this.tick % 260 === 0 && Math.random() < 0.45) {
          this.startRandomStroll();
        } else {
          // Natural blink sequence (3-frame + occasional double-blink)
          if (this.tick >= this.nextBlinkTick) {
            const sub = this.tick - this.nextBlinkTick;
            if      (sub < 2) { this.setFrame("idle_half"); }
            else if (sub < 5) { this.setFrame("idle_blink"); }
            else if (sub < 7) { this.setFrame("idle_half"); }
            else {
              this.setFrame(this.activeEmotionFrame || "idle_open");
              const isDouble = Math.random() < 0.20;
              this.nextBlinkTick = this.tick + (isDouble ? 14 : (60 + Math.floor(Math.random() * 90)));
            }
          } else if (this.tick % 360 === 120 && Math.random() < 0.30) {
            // Occasional playful wink
            this.setFrame("idle_wink");
          } else if (this.tick % 360 === 132) {
            this.setFrame(this.activeEmotionFrame || "idle_open");
          } else {
            // Multi-frequency organic breathing + gentle lateral sway
            const breathY = Math.sin(this.tick * 0.05) * 2.2 + Math.cos(this.tick * 0.025) * 0.8;
            const swayX   = Math.cos(this.tick * 0.03) * 1.2;

            if (this.wrapper && !this._dragActive) {
              this.wrapper.style.transform =
                `translateX(${this._posX + this.walkPosX + swayX}px) translateY(${this._posY + breathY}px)`;
            }

            this.setFrame(this.activeEmotionFrame || "idle_open");
          }
        }
      }
    }

    this.animFrameId = requestAnimationFrame((ts) => this.loop(ts));
  }

  startRandomStroll() {
    const maxOffset   = 140;
    const dir         = Math.random() < 0.5 ? -1 : 1;
    this.walkDirection = dir;
    this.walkDestX    = Math.max(-maxOffset,
                        Math.min( maxOffset, this.walkPosX + dir * (70 + Math.random() * 90)));
    this.isWalking    = true;
    this.currentState = "walking";
  }
}


// Instantiate on DOM load
window.addEventListener("DOMContentLoaded", () => {
  window.ziaCompanion = new ZiaCompanionUI();
});
