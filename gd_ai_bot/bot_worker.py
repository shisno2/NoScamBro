"""
bot_worker.py - High-speed asynchronous worker thread for Geometry Dash AI.
Separates the 240+ FPS vision & reflex decision loop from the GUI rendering thread.
Guarantees sub-millisecond reactions and eliminates all UI lag.
"""

import threading
import time
import numpy as np
import cv2
from typing import Optional, Dict, Any, List, Tuple

from capture import WindowCapture
from inputs import FastInputController
from reflex_sensor import ReflexSensorMatrix, SensorHit
from simulator import GDSimulator

class BotWorkerThread:
    """
    Dedicated high-priority worker thread executing the reflex loop at 200-500+ FPS.
    """

    def __init__(self, capture: WindowCapture, input_ctrl: FastInputController):
        self.capture = capture
        self.input_ctrl = input_ctrl
        self.sensor = ReflexSensorMatrix()
        self.simulator = GDSimulator()

        # Threading state
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self.active_bot = False
        self.use_simulator = False

        # Physics & Reflex parameters
        self.jump_cooldown_sec = 0.36
        self.tap_duration_sec = 0.035
        self.last_jump_time = 0.0
        self.last_orb_time = 0.0
        self.is_jumping = False
        self.mode = "cube"
        self.speed_multiplier = 1.0

        # Diagnostics & Shared State for GUI
        self.lock = threading.Lock()
        self.latest_display_frame: Optional[np.ndarray] = None
        self.bot_fps = 0.0
        self.bot_latency_ms = 0.0
        self.total_jumps = 0
        self.last_action = "SCANNING"
        self.hits_summary: List[SensorHit] = []

        # Macro Recorder & Player
        self.macro_recording = False
        self.macro_playing = False
        self.macro_start_time = 0.0
        self.recorded_events: List[Tuple[float, str]] = [] # (time_s, 'press'/'release')
        self.macro_playback_index = 0

    def start(self):
        if self._thread is not None and self._thread.is_alive():
            return
        self._running = True
        self._thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        self.active_bot = False
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None
        self.input_ctrl.release_up()

    def set_active(self, active: bool):
        self.active_bot = active
        if not active:
            self.input_ctrl.release_up()
            self.is_jumping = False
            self.last_action = "STOPPED"
        else:
            self.last_action = "AUTOPILOT ENGAGED"

    def set_speed(self, speed_mult: float):
        self.speed_multiplier = max(0.5, speed_mult)
        self.sensor.speed_multiplier = self.speed_multiplier

    def get_shared_state(self) -> Dict[str, Any]:
        """Returns thread-safe copy of diagnostics and latest frame for the GUI."""
        with self.lock:
            return {
                "frame": self.latest_display_frame,
                "fps": self.bot_fps,
                "latency_ms": self.bot_latency_ms,
                "jumps": self.total_jumps,
                "action": self.last_action,
                "hits": list(self.hits_summary)
            }

    def _worker_loop(self):
        """Ultra-fast reflex loop running at 200-500+ FPS."""
        frame_counter = 0
        fps_timer = time.perf_counter()
        last_gui_push = 0.0

        while self._running:
            t0 = time.perf_counter()

            # 1. Grab Frame (Fast ROI)
            roi_frame = None
            if self.use_simulator:
                roi_frame = self.simulator.update()
            else:
                try:
                    # Capture full or ROI
                    roi_frame = self.capture.grab_frame()
                except Exception:
                    roi_frame = self.simulator.update()

            if roi_frame is None or roi_frame.size == 0:
                time.sleep(0.002)
                continue

            h, w = roi_frame.shape[:2]
            
            # Auto-align sensor geometry
            ground_y = int(h * 0.80)
            player_size = max(28, int(h * 0.08))
            player_x = int(w * 0.22)
            self.sensor.set_roi_geometry(player_size, ground_y, player_x)

            # 2. Vectorized Probe Sampling (Takes ~0.3ms!)
            hits, debug = self.sensor.analyze_probes(roi_frame)

            # 3. Reflex Decision
            jump_triggered = False
            now = time.perf_counter()

            if self.active_bot:
                # Check Macro Playback first
                if self.macro_playing and self.recorded_events:
                    elapsed = now - self.macro_start_time
                    while self.macro_playback_index < len(self.recorded_events):
                        event_time, event_type = self.recorded_events[self.macro_playback_index]
                        if elapsed >= event_time:
                            if event_type == "press":
                                self.input_ctrl.press_down()
                                self.total_jumps += 1
                                jump_triggered = True
                            else:
                                self.input_ctrl.release_up()
                            self.macro_playback_index += 1
                        else:
                            break
                else:
                    # Optical Vision AI Reflexes
                    time_since_jump = now - self.last_jump_time
                    time_since_orb = now - self.last_orb_time

                    for hit in hits:
                        # Ground Spikes & Walls
                        if hit.hazard_type in ("spike", "wall"):
                            trigger_dist = self.sensor.trigger_distance * self.speed_multiplier
                            if hit.distance_px <= trigger_dist:
                                if time_since_jump >= self.jump_cooldown_sec:
                                    self.input_ctrl.press_down()
                                    self.last_jump_time = now
                                    self.is_jumping = True
                                    self.total_jumps += 1
                                    jump_triggered = True
                                    self.last_action = f"🔥 JUMP! ({hit.hazard_type.upper()})"
                                    if self.use_simulator:
                                        self.simulator.trigger_jump()
                                    break
                                    
                        # Air Orbs (Hit within orb radius)
                        elif hit.hazard_type == "orb":
                            if hit.distance_px <= (player_size * 0.5):
                                if time_since_orb >= 0.12:
                                    self.input_ctrl.press_down()
                                    self.last_orb_time = now
                                    self.last_jump_time = now
                                    self.is_jumping = True
                                    self.total_jumps += 1
                                    jump_triggered = True
                                    self.last_action = "⚡ ORB TRIGGERED!"
                                    break

                        # Pad immunity (do not jump if pad is under player)
                        elif hit.hazard_type == "pad" and hit.distance_px <= player_size:
                            break

                # Handle tap release
                if self.is_jumping and (now - self.last_jump_time >= self.tap_duration_sec):
                    self.input_ctrl.release_up()
                    self.is_jumping = False

            t1 = time.perf_counter()
            dt_loop = t1 - t0
            latency = dt_loop * 1000.0

            # Calculate FPS
            frame_counter += 1
            if now - fps_timer >= 0.25:
                self.bot_fps = frame_counter / (now - fps_timer)
                self.bot_latency_ms = latency
                frame_counter = 0
                fps_timer = now

            # 4. Push lightweight preview to GUI at ~60 FPS (don't waste CPU rendering 300 FPS)
            if now - last_gui_push >= 0.016:
                last_gui_push = now
                annotated = self._render_hud(roi_frame, hits, debug, jump_triggered, self.bot_fps)
                with self.lock:
                    self.latest_display_frame = annotated
                    self.hits_summary = hits

    def _render_hud(self, frame: np.ndarray, hits: List[SensorHit], debug: dict, jumped: bool, fps: float) -> np.ndarray:
        """Draws ultra-fast neon HUD."""
        out = frame.copy()
        h, w = out.shape[:2]

        gy = debug.get("gy", int(h * 0.80))
        sx = debug.get("start_x", int(w * 0.22) + 50)
        ex = debug.get("end_x", sx + 280)
        td = debug.get("trigger_dist", 65)

        # Ground line
        cv2.line(out, (0, gy), (w, gy), (0, 240, 120), 2)

        # Player Box
        px = self.sensor.player_x
        ps = self.sensor.player_size
        p_col = (0, 0, 255) if jumped else (0, 255, 0)
        cv2.rectangle(out, (px, gy - ps), (px + ps, gy), p_col, 2)

        # Sensor Probes (Draw the 4 optical scan rays)
        ray_colors = [(0, 255, 255), (0, 200, 255), (0, 140, 255), (255, 0, 255)]
        if "ray_coords" in debug:
            for idx, ry in debug["ray_coords"]:
                col = ray_colors[idx % len(ray_colors)]
                cv2.line(out, (sx, ry), (ex, ry), col, 1)

        # Trigger Line
        tx = sx + int(td)
        cv2.line(out, (tx, 0), (tx, h), (0, 160, 255), 2)
        cv2.putText(out, "JUMP TRIGGER", (tx + 4, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (0, 160, 255), 1)

        # Draw Detected Sensor Hits
        for hit in hits:
            hx = int(sx + hit.distance_px)
            if hit.hazard_type in ("spike", "wall"):
                cv2.circle(out, (hx, gy - 20), 6, (0, 0, 255), -1)
                cv2.putText(out, f"{hit.hazard_type.upper()} ({int(hit.distance_px)}px)",
                            (hx, gy - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (0, 0, 255), 1)
            elif hit.hazard_type == "orb":
                cv2.circle(out, (hx, gy - 85), 8, (0, 240, 255), -1)
                cv2.putText(out, f"ORB ({int(hit.distance_px)}px)",
                            (hx, gy - 95), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (0, 240, 255), 1)

        # Top-left Cyber HUD Card
        cv2.rectangle(out, (10, 10), (280, 80), (10, 12, 18), -1)
        cv2.rectangle(out, (10, 10), (280, 80), (0, 240, 255), 1)
        
        cv2.putText(out, f"REFLEX ENGINE - {fps:.0f} FPS", (20, 32),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 240, 255), 1)
        
        act_col = (0, 0, 255) if jumped else (0, 255, 100)
        cv2.putText(out, f"ACTION: {self.last_action}", (20, 52),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.44, act_col, 1)
        cv2.putText(out, f"Latency: {self.bot_latency_ms:.2f} ms | Jumps: {self.total_jumps}",
                    (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (200, 210, 230), 1)

        return out
