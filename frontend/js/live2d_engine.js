class Live2DStudio {
  constructor() {
    this.app = null;
    this.model = null;
    this.modelUrl = "/assets/models/Kaguya/Kaguya.model3.json";
    this.activeMood = "F1";
    this.mouthOpenY = 0.0;
    this.targetMouthOpenY = 0.0;

    // Camera Framing (Shoulder-level close up)
    this.panOffset = { x: 0, y: 0 };
    this.zoomScale = 1.0;
    this.isDragging = false;
    this.dragStart = { x: 0, y: 0 };
    this.framerateOverride = null; // Thermal watchdog override

    // Model expression parameters (Kaguya Live2D model)
    this.currentExprParams = {
      ParamExpression_1: 0.0, // Tears (眼泪)
      ParamExpression_2: 0.0, // Teardrop (泪珠)
      ParamExpression_3: 0.0, // Squint / Smile (笑眯眯)
      ParamExpression_4: 0.0, // Excited >< (眯眯眼)
      ParamCheek: 0.0,        // Cheek blush (脸颊泛红)
      ParamEyeSmile_Angry_L: 0.0, // Angry eye L
      ParamEyeSmile_Angry_R: 0.0, // Angry eye R
      ParamEyeSmile_Happy_L: 0.0, // Happy eye L
      ParamEyeSmile_Happy_R: 0.0, // Happy eye R
      ParamEyeLSmile: 0.0,    // Eye smile L
      ParamEyeRSmile: 0.0,    // Eye smile R
      ParamEyeLOpen: 1.0,     // Eye open L
      ParamEyeROpen: 1.0,     // Eye open R
      ParamBrowLAngle: 0.0,   // Eyebrow angle L
      ParamBrowRAngle: 0.0,   // Eyebrow angle R
      ParamBrowLY: 0.0,       // Eyebrow Y L
      ParamBrowRY: 0.0,       // Eyebrow Y R
      ParamMouthForm: 0.2,    // Subtle mouth smile
      ParamTongueOut: 0.0,    // Tongue out (吐舌)
      ParamCheekPuff: 0.0,    // Cheek puff (鼓腮)
      ParamEyeCircles: 0.0,   // Spiral / Dizzy eyes (蚊香眼)
      ParamPupilQuake_L1: 0.0,// Pupil quake L
      ParamPupilQuake_R1: 0.0,// Pupil quake R
      ParamCryDown_L: 0.0     // Cry drops
    };
  }

  async init() {
    const canvas = document.getElementById("live2d-canvas");

    // Check for Transparent Overlay Desktop Widget Mode (?overlay=1)
    const urlParams = new URLSearchParams(window.location.search);
    const isOverlay = urlParams.get("overlay") === "1";
    if (isOverlay) {
      document.body.classList.add("overlay-mode");
      document.documentElement.classList.add("overlay-mode");
    }

    // Optimized Pixi application for legacy hardware (Core 2 Duo / Mesa / WebKit)
    this.app = new PIXI.Application({
      view: canvas,
      resizeTo: window,
      backgroundColor: isOverlay ? 0x000000 : 0x000000,
      backgroundAlpha: isOverlay ? 0.0 : 1.0,
      transparent: isOverlay,
      antialias: false, // Saves huge GPU memory bandwidth on 2007 hardware
      autoDensity: true,
      resolution: 1,    // 1x native resolution to avoid 2007 GPU fill-rate choke
      powerPreference: "low-power"
    });

    // Pause rendering entirely when window is minimized/hidden (24/7 power saving)
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) {
        this.app.stop();
      } else {
        this.app.start();
      }
    });

    // Register Pixi Ticker for Cubism 4 runtime
    if (window.PIXI && PIXI.live2d && PIXI.live2d.Live2DModel) {
      PIXI.live2d.Live2DModel.registerTicker(PIXI.Ticker);
    }

    // Camera Pan (Click & drag only - NO cursor gaze tracking)
    window.addEventListener("mousemove", (e) => {
      if (this.isDragging && this.model) {
        this.panOffset.x += e.clientX - this.dragStart.x;
        this.panOffset.y += e.clientY - this.dragStart.y;
        this.dragStart.x = e.clientX;
        this.dragStart.y = e.clientY;
        this.adjustFraming();
      }
    });

    canvas.addEventListener("mousedown", (e) => {
      if (e.button === 0) {
        this.isDragging = true;
        this.dragStart.x = e.clientX;
        this.dragStart.y = e.clientY;
      }
    });

    window.addEventListener("mouseup", () => {
      this.isDragging = false;
    });

    canvas.addEventListener("wheel", (e) => {
      e.preventDefault();
      const zoomDelta = e.deltaY * -0.0012;
      this.zoomScale = Math.min(3.5, Math.max(0.4, this.zoomScale + zoomDelta));
      this.adjustFraming();
    }, { passive: false });

    // Double-click to reset camera framing
    canvas.addEventListener("dblclick", () => {
      this.panOffset = { x: 0, y: 0 };
      this.zoomScale = 1.0;
      this.adjustFraming();
    });

    window.addEventListener("resize", () => {
      this.app.renderer.resize(window.innerWidth, window.innerHeight);
      this.adjustFraming();
    });

    // Bind Audio Lip-Sync
    if (window.audioLipSync) {
      window.audioLipSync.onLipSyncUpdate = (value) => {
        this.targetMouthOpenY = value;
      };
    }

    await this.loadModel();
    this.startRenderLoop();
  }

  async loadModel() {
    try {
      if (window.PIXI && PIXI.live2d && PIXI.live2d.Live2DModel) {
        console.log("[Live2D] Loading Kaguya model from:", this.modelUrl);
        this.model = await PIXI.live2d.Live2DModel.from(this.modelUrl, {
          autoInteract: false
        });

        this.app.stage.addChild(this.model);
        this.adjustFraming();

        console.log("[Live2D] Kaguya loaded successfully.");
        return;
      }
    } catch (err) {
      console.error("[Live2D Error] Failed to load model:", err);
      // Fallback attempt to alternate path if needed
      try {
        this.model = await PIXI.live2d.Live2DModel.from("/assets/models/TianYeLulu/TianYeLulu.model3.json", {
          autoInteract: false
        });
        this.app.stage.addChild(this.model);
        this.adjustFraming();
      } catch (fbErr) {
        console.error("[Live2D Fallback Error]", fbErr);
      }
    }
  }

  /**
   * Adjusts camera framing so only head, face, and shoulders are visible.
   */
  adjustFraming() {
    if (!this.model) return;

    this.model.anchor.set(0.5, 0.0);

    // Zoom scale tuned for upper chest, shoulders, and head
    const baseScale = (window.innerHeight * 2.5) / this.model.height;
    const finalScale = baseScale * this.zoomScale;
    this.model.scale.set(finalScale);

    const defaultX = window.innerWidth * 0.5;
    const defaultY = -this.model.height * finalScale * 0.04;

    this.model.x = defaultX + this.panOffset.x;
    this.model.y = defaultY + this.panOffset.y;
  }

  /**
   * Dynamic "Living Asset" Ambient Style Swapping.
   * Swaps model texture atlas in real time with zero frame dropping.
   */
  swapTexture(index = 0, newUrl) {
    if (!this.model || !newUrl) return;
    try {
      const freshTexture = PIXI.Texture.from(newUrl);
      freshTexture.baseTexture.on("loaded", () => {
        if (this.model.textures && this.model.textures[index]) {
          this.model.textures[index].baseTexture = freshTexture.baseTexture;
          this.model.textures[index].update();
        } else if (this.model.internalModel && this.model.internalModel.textureAtlas) {
          if (this.model.internalModel.textureAtlas.textures) {
            this.model.internalModel.textureAtlas.textures[index].baseTexture = freshTexture.baseTexture;
            this.model.internalModel.textureAtlas.textures[index].update();
          }
        }
        console.log("[Live2D] Hot swapped texture:", newUrl);
        if (window.showToast) window.showToast("Living Asset Swapped ✨");
      });
    } catch (e) {
      console.warn("[Live2D] Texture swap error:", e);
    }
  }

  setFramerateOverride(fps, reason) {
    this.framerateOverride = fps;
    console.log(`[Live2D] Framerate override set to ${fps} FPS (${reason})`);
    if (window.showToast) {
      window.showToast(fps <= 5 ? "⚠️ Thermal Throttle: 5 FPS Mode" : `Performance: ${fps} FPS Mode`);
    }
  }

  setExpression(key) {
    this.activeMood = key.toUpperCase();

    // Show temporary minimalist toast
    if (window.showToast) {
      const names = {
        F1: "Neutral",
        F2: "Blush",
        F3: "Angry",
        F4: "Star / Happy Eyes",
        F5: "Love / Joy",
        F6: "Sad / Tears",
        F7: "Surprised",
        F8: "Thinking",
        F9: "Smug",
        F10: "Shocked",
        F11: "Sleep"
      };
      window.showToast(`${this.activeMood} · ${names[this.activeMood] || ""}`);
    }

    // Reset expression parameters to neutral baseline
    for (const p in this.currentExprParams) {
      this.currentExprParams[p] = (p === "ParamEyeLOpen" || p === "ParamEyeROpen") ? 1.0 : (p === "ParamMouthForm" ? 0.2 : 0.0);
    }

    switch (this.activeMood) {
      case "F2": // Blush
        this.currentExprParams.ParamCheek = 1.0;
        this.currentExprParams.ParamEyeLSmile = 0.8;
        this.currentExprParams.ParamEyeRSmile = 0.8;
        this.currentExprParams.ParamMouthForm = 0.6;
        break;
      case "F3": // Angry
        this.currentExprParams.ParamEyeSmile_Angry_L = 1.0;
        this.currentExprParams.ParamEyeSmile_Angry_R = 1.0;
        this.currentExprParams.ParamBrowLAngle = -0.8;
        this.currentExprParams.ParamBrowRAngle = -0.8;
        this.currentExprParams.ParamBrowLY = -0.4;
        this.currentExprParams.ParamBrowRY = -0.4;
        this.currentExprParams.ParamMouthForm = -0.6;
        break;
      case "F4": // Star / Happy Eyes
        this.currentExprParams.ParamExpression_3 = 1.0; // 笑眯眯
        this.currentExprParams.ParamEyeSmile_Happy_L = 1.0;
        this.currentExprParams.ParamEyeSmile_Happy_R = 1.0;
        this.currentExprParams.ParamMouthForm = 0.8;
        break;
      case "F5": // Love / Joy Eyes
        this.currentExprParams.ParamExpression_4 = 1.0; // 眯眯眼 ><
        this.currentExprParams.ParamCheek = 0.9;
        this.currentExprParams.ParamEyeSmile_Happy_L = 1.0;
        this.currentExprParams.ParamEyeSmile_Happy_R = 1.0;
        this.currentExprParams.ParamMouthForm = 0.7;
        break;
      case "F6": // Sad / Tears
        this.currentExprParams.ParamExpression_1 = 1.0; // 眼泪
        this.currentExprParams.ParamCryDown_L = 1.0;
        this.currentExprParams.ParamBrowLAngle = 0.8;
        this.currentExprParams.ParamBrowRAngle = 0.8;
        this.currentExprParams.ParamBrowLY = 0.6;
        this.currentExprParams.ParamBrowRY = 0.6;
        this.currentExprParams.ParamMouthForm = -0.7;
        break;
      case "F7": // Surprised
        this.currentExprParams.ParamExpression_2 = 1.0; // 泪珠
        this.currentExprParams.ParamEyeLOpen = 1.25;
        this.currentExprParams.ParamEyeROpen = 1.25;
        this.currentExprParams.ParamBrowLY = 0.8;
        this.currentExprParams.ParamBrowRY = 0.8;
        this.currentExprParams.ParamMouthForm = 0.0;
        break;
      case "F8": // Thinking
        this.currentExprParams.ParamCheekPuff = 0.8;
        this.currentExprParams.ParamBrowLY = 0.5;
        this.currentExprParams.ParamBrowRY = -0.3;
        this.currentExprParams.ParamBrowRAngle = -0.4;
        this.currentExprParams.ParamMouthForm = 0.1;
        break;
      case "F9": // Smug
        this.currentExprParams.ParamTongueOut = 1.0; // 吐舌
        this.currentExprParams.ParamEyeLSmile = 0.9;
        this.currentExprParams.ParamEyeROpen = 0.4;
        this.currentExprParams.ParamMouthForm = 0.7;
        break;
      case "F10": // Shocked / Dizzy
        this.currentExprParams.ParamEyeCircles = 1.0; // 蚊香眼
        this.currentExprParams.ParamPupilQuake_L1 = 1.0;
        this.currentExprParams.ParamPupilQuake_R1 = 1.0;
        this.currentExprParams.ParamBrowLY = 0.7;
        this.currentExprParams.ParamBrowRY = 0.7;
        this.currentExprParams.ParamMouthForm = -0.5;
        break;
      case "F11": // Sleep
        this.currentExprParams.ParamEyeLOpen = 0.0;
        this.currentExprParams.ParamEyeROpen = 0.0;
        this.currentExprParams.ParamMouthForm = 0.1;
        break;
      case "F1":
      default:
        break;
    }

    if (this.model && this.model.expression) {
      const exprMapping = {
        F4: "smile",
        F5: "squint",
        F6: "crying",
        F7: "teardrop"
      };
      const expName = exprMapping[this.activeMood];
      if (expName) {
        try {
          this.model.expression(expName);
        } catch (e) {}
      }
    }
  }

  /**
   * Ultra-optimized rendering loop:
   * Dynamically caps framerate to 24-28 FPS during speaking, and 14-16 FPS during idle.
   * Uses gentle autonomous procedural sine-wave breathing and head movements.
   * Completely eliminates mouse cursor tracking for smooth, stutter-free performance on Core 2 Duo.
   */
  startRenderLoop() {
    let tick = 0;
    let lastTime = performance.now();

    this.app.ticker.add(() => {
      const now = performance.now();
      // Target 28 FPS when active/speaking, 16 FPS when idle, or 5 FPS if thermally throttled
      const isSpeaking = this.targetMouthOpenY > 0.05 || this.mouthOpenY > 0.05;
      const defaultFps = isSpeaking || this.isDragging ? 28 : 16;
      const targetFps = this.framerateOverride || defaultFps;
      const frameInterval = 1000 / targetFps;

      if (now - lastTime < frameInterval) {
        return; // Skip rendering this tick to save CPU cycles
      }

      const elapsedMs = now - lastTime;
      const delta = elapsedMs / (1000 / 60);
      lastTime = now;

      tick += 0.03 * delta;

      // Soft mouth interpolation
      this.mouthOpenY += (this.targetMouthOpenY - this.mouthOpenY) * 0.45;

      // Natural procedural blinking cycle (~every 3.6s, duration ~0.15s)
      const blinkCycle = tick % 3.6;
      const isNaturalBlink = blinkCycle < 0.15 && this.activeMood !== "F11" && this.activeMood !== "F4" && this.activeMood !== "F5";
      const eyeOpenBase = this.activeMood === "F11" ? 0.0 : (isNaturalBlink ? 0.0 : 1.0);

      // Subtle breathing wave
      const breath = Math.sin(tick * 0.75) * 0.5 + 0.5;

      // Gentle autonomous head sway (Zero cursor tracking)
      const headSwayX = Math.sin(tick * 0.4) * 4.5;
      const headSwayY = Math.cos(tick * 0.3) * 2.5;
      const headSwayZ = Math.sin(tick * 0.25) * 2.0;

      // Subtle eye gaze wandering
      const eyeGazeX = Math.sin(tick * 0.18) * 0.25;
      const eyeGazeY = Math.cos(tick * 0.22) * 0.15;

      if (this.model && this.model.internalModel && this.model.internalModel.coreModel) {
        const core = this.model.internalModel.coreModel;
        try {
          // Vocal Lip Sync
          core.setParameterValueById("ParamMouthOpenY", this.mouthOpenY);

          // Subtle organic breathing
          core.setParameterValueById("ParamBreath", breath);
          core.setParameterValueById("ParamBreathPhysics_L", breath);

          // Gentle autonomous head movements (smooth, zero cursor tracking)
          core.setParameterValueById("ParamAngleX", headSwayX);
          core.setParameterValueById("ParamAngleY", headSwayY);
          core.setParameterValueById("ParamAngleZ", headSwayZ);
          core.setParameterValueById("ParamAngle_HeadX", headSwayX);
          core.setParameterValueById("ParamAngle_HeadY", headSwayY);
          core.setParameterValueById("ParamAngle_HeadZ", headSwayZ);

          // Body subtle follow-through
          core.setParameterValueById("ParamBodyAngleX", headSwayX * 0.4);
          core.setParameterValueById("ParamBodyAngleZ", headSwayZ * 0.3);

          // Subtle natural eye wander
          core.setParameterValueById("ParamEyeBallX", eyeGazeX);
          core.setParameterValueById("ParamEyeBallY", eyeGazeY);

          // Eye Blinking
          core.setParameterValueById("ParamEyeLOpen", this.currentExprParams.ParamEyeLOpen !== undefined ? Math.min(this.currentExprParams.ParamEyeLOpen, eyeOpenBase) : eyeOpenBase);
          core.setParameterValueById("ParamEyeROpen", this.currentExprParams.ParamEyeROpen !== undefined ? Math.min(this.currentExprParams.ParamEyeROpen, eyeOpenBase) : eyeOpenBase);

          // Active expression overrides
          for (const [paramId, val] of Object.entries(this.currentExprParams)) {
            if (paramId !== "ParamEyeLOpen" && paramId !== "ParamEyeROpen") {
              core.setParameterValueById(paramId, val);
            }
          }
        } catch (e) {}
      }
    });
  }
}

window.live2DStudio = new Live2DStudio();
