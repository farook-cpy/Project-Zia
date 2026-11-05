"""
Project Zia - Offline Computer Vision Senses Engine
Lightweight, throttled local webcam pipeline for user behavioral state detection.
Engineered for legacy hardware (2007 MacBook Pro Core 2 Duo / Linux Mint / cross-OS)
with < 2% CPU utilization.
"""

import os
import sys
import time
import threading
import math
from typing import Optional, Dict, Any

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    cv2 = None
    np = None
    CV2_AVAILABLE = False


class VisionSenses:
    """
    Offline local vision pipeline.
    Samples local webcam at low framerate (1 frame every 2.5s) to detect:
    - Thinking (hand-to-chin, head tilt, prolonged stillness)
    - Stressed (furrowed brow / squinting, micro-jitter)
    - Walking / Away (absence of face, sudden scene shift)
    - Neutral / Engaged (normal relaxed presence)
    """

    STATES = ["neutral", "thinking", "stressed", "away"]

    def __init__(self, sampling_interval: float = 2.5):
        self.sampling_interval = sampling_interval
        self.is_running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Hardware & Model state
        self.camera_device_idx = 0
        self.camera_available = False
        self.detector = None
        self.model_path = os.path.join("data", "face_detection_yunet.onnx")

        # Behavioral state tracking
        self.current_state = "away"
        self.state_confidence = 0.5
        self.state_start_time = time.time()
        self.last_detection_time = 0.0
        self.last_metrics = {}

        # Frame history for micro-movement / stillness tracking
        self._prev_face_box = None
        self._prev_frame_gray = None
        self._stillness_count = 0
        self._jitter_count = 0
        self._simulated_override: Optional[str] = None
        # Lazy detector initialization on start() to guarantee sub-millisecond module load

    def _init_detector(self):
        """Initializes the ultra-lightweight YuNet ONNX face detector (232 KB)."""
        if not CV2_AVAILABLE:
            return

        if os.path.exists(self.model_path):
            try:
                # YuNet input size set to 320x240 for near-zero CPU footprint
                self.detector = cv2.FaceDetectorYN_create(
                    self.model_path,
                    "",
                    (320, 240),
                    score_threshold=0.55,
                    nms_threshold=0.3,
                    top_k=2
                )
            except Exception as e:
                print(f"[VisionSenses] Warning: Could not initialize YuNet ({e}). Falling back to optical flow.")
                self.detector = None

    def start(self) -> Dict[str, Any]:
        """Starts the background throttled webcam capture worker thread."""
        with self._lock:
            if self.is_running:
                return {"success": True, "message": "Vision senses worker already running."}

            if self.detector is None:
                self._init_detector()

            self.is_running = True
            self._thread = threading.Thread(target=self._worker_loop, daemon=True, name="ZiaVisionWorker")
            self._thread.start()
            return {"success": True, "message": f"Vision senses started (sampling every {self.sampling_interval}s)."}

    def stop(self) -> Dict[str, Any]:
        """Stops the vision senses worker thread."""
        with self._lock:
            self.is_running = False
            return {"success": True, "message": "Vision senses stopped."}

    def set_sampling_interval(self, interval_sec: float):
        """Adjusts the capture throttling interval (minimum 1.5s for low CPU)."""
        self.sampling_interval = max(1.5, float(interval_sec))

    def simulate_state(self, state: Optional[str]) -> Dict[str, Any]:
        """Allows testing behavioral triggers by manually overriding detected state."""
        if state is None or state.lower() in ["clear", "reset", "none", "off"]:
            self._simulated_override = None
            return {"success": True, "message": "Simulated state cleared. Returning to live camera."}

        st = state.lower()
        if st not in self.STATES:
            return {"error": f"Invalid state '{state}'. Valid states: {', '.join(self.STATES)}"}

        self._simulated_override = st
        self._update_state(st, confidence=1.0)
        return {"success": True, "message": f"Simulated vision state forced to '{st}'."}

    def _get_capture_device(self):
        """Cross-platform camera acquisition with OS-specific backend flags."""
        if not CV2_AVAILABLE:
            return None

        # Linux (e.g. Linux Mint on 2007 MacBook Pro)
        if sys.platform.startswith("linux"):
            for dev in ["/dev/video0", 0]:
                try:
                    cap = cv2.VideoCapture(dev, cv2.CAP_V4L2)
                    if cap.isOpened():
                        return cap
                except Exception:
                    pass
        elif sys.platform == "darwin":
            try:
                cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
                if cap.isOpened():
                    return cap
            except Exception:
                pass
        else: # Windows
            for backend in [getattr(cv2, "CAP_DSHOW", None), getattr(cv2, "CAP_MSMF", None), None]:
                try:
                    cap = cv2.VideoCapture(0, backend) if backend is not None else cv2.VideoCapture(0)
                    if cap.isOpened():
                        return cap
                except Exception:
                    pass

        # Generic fallback
        try:
            cap = cv2.VideoCapture(0)
            if cap.isOpened():
                return cap
        except Exception:
            pass

        return None

    def _worker_loop(self):
        """
        Non-blocking background loop: captures 1 frame every 2.5 seconds,
        classifies user state offline, and records timestamps.
        """
        cap = None

        while self.is_running:
            # Check for simulated override
            if self._simulated_override:
                time.sleep(self.sampling_interval)
                continue

            try:
                if cap is None or not cap.isOpened():
                    cap = self._get_capture_device()
                    if cap is None:
                        self.camera_available = False
                        self._update_state("away", confidence=0.4)
                        time.sleep(self.sampling_interval)
                        continue

                self.camera_available = True

                # Capture single frame
                ret, frame = cap.read()
                if not ret or frame is None:
                    self._update_state("away", confidence=0.5)
                    time.sleep(self.sampling_interval)
                    continue

                # Immediately downscale to 320x240 for ultra-low CPU load (<2%)
                small = cv2.resize(frame, (320, 240))
                detected_state, confidence, metrics = self._classify_frame(small)
                self.last_metrics = metrics
                self._update_state(detected_state, confidence)

            except Exception as e:
                # Never crash the main loop
                pass

            time.sleep(self.sampling_interval)

        if cap is not None and cap.isOpened():
            cap.release()

    def _classify_frame(self, frame_bgr) -> tuple[str, float, dict]:
        """
        Performs offline inference on a 320x240 frame using YuNet landmarks and optical variance:
        - Away: No face detected or sudden drastic scene transition
        - Thinking: Downward head tilt / chin resting or stillness
        - Stressed: Squinting / furrowed ratios or high micro-jitter
        - Neutral: Relaxed stable face presence
        """
        metrics = {}
        h, w = frame_bgr.shape[:2]
        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)

        # 1. Optical flow / scene shift detection
        frame_diff = 0.0
        if self._prev_frame_gray is not None:
            diff = cv2.absdiff(gray, self._prev_frame_gray)
            frame_diff = float(np.mean(diff))
        self._prev_frame_gray = gray
        metrics["frame_diff"] = round(frame_diff, 2)

        # 2. Face & landmark detection
        if self.detector is None:
            # If detector model missing, use basic presence & motion heuristic
            if frame_diff > 18.0:
                return "stressed", 0.6, metrics
            elif frame_diff < 1.0:
                return "thinking", 0.6, metrics
            return "neutral", 0.7, metrics

        # YuNet detection
        self.detector.setInputSize((w, h))
        res, faces = self.detector.detect(frame_bgr)

        if faces is None or len(faces) == 0:
            self._stillness_count = 0
            self._jitter_count = 0
            self._prev_face_box = None
            metrics["faces"] = 0
            return "away", 0.9, metrics

        # Primary face detection
        face = faces[0]
        metrics["faces"] = len(faces)
        bx, by, bw, bh = face[0:4]
        box_center = (bx + bw / 2.0, by + bh / 2.0)

        # Landmarks: Right eye, Left eye, Nose tip, Right mouth, Left mouth
        re_x, re_y = face[4], face[5]
        le_x, le_y = face[6], face[7]
        nose_x, nose_y = face[8], face[9]
        rm_x, rm_y = face[10], face[11]
        lm_x, lm_y = face[12], face[13]

        # Landmark geometric calculations
        eye_dx = le_x - re_x
        eye_dy = le_y - re_y
        eye_dist = math.sqrt(eye_dx**2 + eye_dy**2)
        tilt_angle_deg = math.degrees(math.atan2(eye_dy, eye_dx))

        # Vertical vectors
        eyes_mid_y = (re_y + le_y) / 2.0
        mouth_mid_y = (rm_y + lm_y) / 2.0
        eye_to_nose = max(1.0, nose_y - eyes_mid_y)
        nose_to_mouth = max(1.0, mouth_mid_y - nose_y)
        vertical_ratio = eye_to_nose / nose_to_mouth

        mouth_dx = lm_x - rm_x
        mouth_dy = lm_y - rm_y
        mouth_width = math.sqrt(mouth_dx**2 + mouth_dy**2)
        eye_to_mouth_ratio = mouth_width / max(1.0, eye_dist)

        metrics["tilt_angle"] = round(tilt_angle_deg, 1)
        metrics["vertical_ratio"] = round(vertical_ratio, 2)
        metrics["eye_to_mouth"] = round(eye_to_mouth_ratio, 2)

        # 3. Micro-jitter and stillness tracking
        displacement = 0.0
        if self._prev_face_box is not None:
            prev_cx, prev_cy = self._prev_face_box
            displacement = math.sqrt((box_center[0] - prev_cx)**2 + (box_center[1] - prev_cy)**2)
        self._prev_face_box = box_center
        metrics["displacement"] = round(displacement, 2)

        if displacement < 1.8:
            self._stillness_count += 1
            self._jitter_count = max(0, self._jitter_count - 1)
        elif 2.2 <= displacement <= 8.5:
            self._jitter_count += 1
            self._stillness_count = max(0, self._stillness_count - 1)
        else:
            self._stillness_count = 0
            self._jitter_count = 0

        metrics["stillness_streak"] = self._stillness_count
        metrics["jitter_streak"] = self._jitter_count

        # 4. Behavioral classification logic
        # Stressed: High micro-jitter streak or compressed tense facial geometry / squinting
        if self._jitter_count >= 3 or eye_to_mouth_ratio < 0.68:
            return "stressed", 0.85, metrics

        # Thinking: Downward head tilt (nose close to mouth or high vertical ratio),
        # significant side tilt, or prolonged stillness with face centered
        if vertical_ratio > 1.35 or abs(tilt_angle_deg) > 16.0 or self._stillness_count >= 4:
            return "thinking", 0.82, metrics

        # Neutral / Engaged: normal relaxed pose
        return "neutral", 0.90, metrics

    def _update_state(self, new_state: str, confidence: float):
        """Updates internal state and tracks how long current state has persisted."""
        now = time.time()
        self.state_confidence = confidence
        self.last_detection_time = now

        if self._simulated_override:
            new_state = self._simulated_override

        if new_state != self.current_state:
            self.current_state = new_state
            self.state_start_time = now

    def get_current_state(self) -> Dict[str, Any]:
        """
        Returns real-time behavioral state summary for the proactive heartbeat:
        {
            "state": "thinking" | "stressed" | "away" | "neutral",
            "duration_sec": 42.5,
            "confidence": 0.85,
            "camera_available": True,
            "is_running": True,
            "is_simulated": False
        }
        """
        now = time.time()
        duration = now - self.state_start_time if self.state_start_time > 0 else 0.0

        return {
            "state": self.current_state,
            "duration_sec": round(duration, 1),
            "confidence": round(self.state_confidence, 2),
            "camera_available": self.camera_available,
            "is_running": self.is_running,
            "is_simulated": bool(self._simulated_override),
            "metrics": self.last_metrics
        }

    def scan_once(self) -> Dict[str, Any]:
        """Captures a single snapshot immediately and runs analysis."""
        if not CV2_AVAILABLE:
            return {"error": "OpenCV (cv2) not available on this platform."}

        cap = self._get_capture_device()
        if cap is None:
            return {
                "success": False,
                "error": "No camera hardware detected (/dev/video0 or DirectShow device not found).",
                "simulated_state": self.current_state
            }

        try:
            ret, frame = cap.read()
            cap.release()
            if not ret or frame is None:
                return {"success": False, "error": "Failed to read frame from camera."}

            small = cv2.resize(frame, (320, 240))
            detected_state, confidence, metrics = self._classify_frame(small)
            self._update_state(detected_state, confidence)

            return {
                "success": True,
                "detected_state": detected_state,
                "confidence": confidence,
                "metrics": metrics
            }
        except Exception as e:
            if cap.isOpened():
                cap.release()
            return {"success": False, "error": str(e)}


# Global vision senses singleton
vision_senses = VisionSenses(sampling_interval=2.5)

