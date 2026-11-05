class AudioLipSyncManager {
  constructor() {
    this.audioCtx = null;
    this.analyser = null;
    this.dataArray = null;
    this.isPlaying = false;
    this.sensitivity = 1.35;
    this.onLipSyncUpdate = null;
  }

  init() {
    if (!this.audioCtx) {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      this.audioCtx = new AudioContext();
      this.analyser = this.audioCtx.createAnalyser();
      this.analyser.fftSize = 256;
      this.analyser.smoothingTimeConstant = 0.3;
      this.dataArray = new Uint8Array(this.analyser.frequencyBinCount);
    }
    if (this.audioCtx.state === "suspended") {
      this.audioCtx.resume();
    }
  }

  async playSpeech(base64Audio, onEnd) {
    if (!base64Audio) {
      if (onEnd) onEnd();
      return;
    }
    this.init();

    try {
      const binaryString = window.atob(base64Audio);
      const len = binaryString.length;
      const bytes = new Uint8Array(len);
      for (let i = 0; i < len; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }

      const audioBuffer = await this.audioCtx.decodeAudioData(bytes.buffer);
      const source = this.audioCtx.createBufferSource();
      source.buffer = audioBuffer;

      source.connect(this.analyser);
      this.analyser.connect(this.audioCtx.destination);

      this.isPlaying = true;
      source.start(0);
      this._startLipSyncLoop();

      source.onended = () => {
        this.isPlaying = false;
        if (this.onLipSyncUpdate) {
          this.onLipSyncUpdate(0);
        }
        if (onEnd) onEnd();
      };
    } catch (err) {
      console.error("[AudioLipSync Error]", err);
      this.isPlaying = false;
      if (onEnd) onEnd();
    }
  }

  _startLipSyncLoop() {
    const update = () => {
      if (!this.isPlaying) return;

      this.analyser.getByteFrequencyData(this.dataArray);

      let sum = 0;
      let count = 0;
      for (let i = 2; i < Math.min(28, this.dataArray.length); i++) {
        sum += this.dataArray[i];
        count++;
      }

      const avg = count > 0 ? sum / count : 0;
      let mouthOpen = Math.min(1.0, (avg / 125.0) * this.sensitivity);

      if (mouthOpen < 0.08) mouthOpen = 0.0;

      if (this.onLipSyncUpdate) {
        this.onLipSyncUpdate(mouthOpen);
      }

      requestAnimationFrame(update);
    };

    requestAnimationFrame(update);
  }
}

window.audioLipSync = new AudioLipSyncManager();
