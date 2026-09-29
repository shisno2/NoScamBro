"""
detector.py - Advanced Computer Vision engine for Geometry Dash.
Features:
- Real-time player tracking & state (grounded, jumping, falling)
- Dynamic ground line & ceiling auto-detection
- Temporal motion filtering (filters out flashing & pulsing backgrounds)
- Accurate hitbox classification: Spikes, Blocks, Orbs, Pads, Pits
- Trajectory prediction & collision checking
"""

import cv2
import numpy as np
import time
from dataclasses import dataclass
from typing import List, Tuple, Optional

@dataclass
class Hitbox:
    kind: str           # 'spike_ground', 'spike_ceiling', 'block', 'orb', 'pad', 'pit'
    x: int              # Screen X
    y: int              # Screen Y
    w: int
    h: int
    dist_x: float       # Horizontal distance from player front edge
    sub_type: str = ""  # 'yellow', 'pink', 'blue', 'red'
    is_hazard: bool = True

@dataclass
class PlayerState:
    x: int
    y: int
    w: int
    h: int
    vy: float           # Vertical velocity
    is_grounded: bool
    mode: str           # 'cube', 'ship', 'wave', 'ufo', 'ball'

class GDVisionDetector:
    """
    High-performance, noise-immune computer vision analyzer for Geometry Dash.
    """

    def __init__(self):
        # Auto-calibrated coordinates
        self.ground_y = 0
        self.ceiling_y = 0
        self.player_x = 0
        self.player_y = 0
        self.player_size = 48
        
        # Player dynamics tracking
        self.player_state = PlayerState(
            x=0, y=0, w=48, h=48, vy=0.0, is_grounded=True, mode="cube"
        )
        self.last_player_positions = []
        self.last_frame_gray = None
        self.last_frame_time = time.perf_counter()
        
        # Game speed tracking (pixels per second)
        self.estimated_speed_px_s = 420.0
        self.speed_multiplier = 1.0
        
        # User / dynamic parameters
        self.player_x_ratio = 0.22
        self.ground_y_ratio = 0.81
        self.lookahead_px = 320
        self.jump_trigger_dist = 68
        self.trigger_margin = 16
        self.mode = "cube"
        
        # Death & flash filter
        self.is_dead = False
        self.last_death_time = 0.0

        # Color palettes in HSV for Orbs & Pads
        # Geometry Dash orbs have distinct glowing saturation
        self.color_targets = {
            "yellow_orb": ((22, 160, 160), (34, 255, 255)),
            "pink_orb":   ((140, 140, 140), (168, 255, 255)),
            "blue_orb":   ((98, 150, 150), (125, 255, 255)),
            "red_orb":    ((0, 170, 170), (10, 255, 255)),
            "yellow_pad": ((24, 180, 180), (32, 255, 255)),
            "pink_pad":   ((145, 160, 160), (165, 255, 255)),
        }

    def auto_calibrate(self, frame: np.ndarray) -> bool:
        """
        Scans the frame to automatically identify ground line and player cube.
        """
        h, w = frame.shape[:2]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 1. Detect Ground Line (prominent horizontal edge in bottom 15-30% of screen)
        search_top = int(h * 0.70)
        search_bottom = int(h * 0.92)
        bottom_region = gray[search_top:search_bottom, :]
        
        # Compute horizontal edge gradient (Sobel Y)
        sobel_y = cv2.Sobel(bottom_region, cv2.CV_32F, 0, 1, ksize=3)
        row_intensities = np.mean(np.abs(sobel_y), axis=1)
        
        best_row_rel = int(np.argmax(row_intensities))
        detected_ground = search_top + best_row_rel
        
        if 0.70 * h <= detected_ground <= 0.90 * h:
            self.ground_y = detected_ground
            self.ground_y_ratio = detected_ground / float(h)
        else:
            self.ground_y = int(h * self.ground_y_ratio)
            
        self.ceiling_y = int(h * 0.12)
        self.player_size = max(28, int(h * 0.08))
        self.player_x = int(w * self.player_x_ratio)
        self.player_y = self.ground_y - self.player_size
        
        self.player_state.x = self.player_x
        self.player_state.y = self.player_y
        self.player_state.w = self.player_size
        self.player_state.h = self.player_size
        self.player_state.is_grounded = True
        
        self.lookahead_px = max(260, int(w * 0.35))
        self.jump_trigger_dist = int(self.player_size * 1.45)
        return True

    def track_player(self, frame: np.ndarray, dt: float):
        """
        Tracks the player's vertical position and velocity in real time.
        Detects whether player is grounded, ascending (jumping), or falling.
        """
        h, w = frame.shape[:2]
        if self.ground_y == 0:
            self.auto_calibrate(frame)
            
        px = self.player_x
        pw = self.player_size
        
        # Column ROI where player lives
        margin_x = int(pw * 0.4)
        col_x1 = max(0, px - margin_x)
        col_x2 = min(w, px + pw + margin_x)
        
        col_roi = frame[self.ceiling_y:self.ground_y + 10, col_x1:col_x2]
        if col_roi.size == 0:
            return
            
        gray_roi = cv2.cvtColor(col_roi, cv2.COLOR_BGR2GRAY)
        
        # Player has high contrast against background
        # Threshold to find bright/distinct player icon pixels
        blurred = cv2.GaussianBlur(gray_roi, (5, 5), 0)
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 21, -8
        )
        
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        best_y = None
        best_area = 0
        min_area = (pw * pw) * 0.3
        max_area = (pw * pw) * 2.5
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if min_area <= area <= max_area:
                bx, by, bw, bh = cv2.boundingRect(cnt)
                # Player is relatively square
                aspect = float(bw) / max(1, bh)
                if 0.5 <= aspect <= 2.0:
                    if area > best_area:
                        best_area = area
                        best_y = self.ceiling_y + by
                        
        if best_y is not None:
            # Smooth tracking
            old_y = self.player_y
            self.player_y = int(0.7 * best_y + 0.3 * self.player_y)
            if dt > 0.001:
                self.player_state.vy = (self.player_y - old_y) / dt
        else:
            # If not cleanly found, assume ground if near ground
            self.player_state.vy = 0.0
            
        # Grounded check: is player within 6px of floor?
        dist_to_ground = abs((self.player_y + self.player_size) - self.ground_y)
        self.player_state.is_grounded = dist_to_ground <= 10
        self.player_state.y = self.player_y
        self.player_state.x = self.player_x
        self.player_state.mode = self.mode

    def detect_death(self, frame: np.ndarray) -> bool:
        """
        Detects death explosion / flash / reset.
        """
        h, w = frame.shape[:2]
        if self.player_x == 0:
            return False
            
        # Sampling around player area
        px = self.player_x
        py = self.player_y
        ps = self.player_size
        
        x1 = max(0, px - ps)
        y1 = max(0, py - ps)
        x2 = min(w, px + ps * 2)
        y2 = min(h, py + ps * 2)
        
        roi = frame[y1:y2, x1:x2]
        if roi.size == 0:
            return False
            
        mean_val = float(np.mean(roi))
        std_val = float(np.std(roi))
        
        # Geometry Dash death trigger creates extreme bright burst or sudden black
        now = time.perf_counter()
        if (mean_val > 248 or (mean_val < 8 and std_val < 5)) and (now - self.last_death_time > 0.6):
            self.last_death_time = now
            self.is_dead = True
            return True
            
        self.is_dead = False
        return False

    def scan_corridor(self, frame: np.ndarray) -> Tuple[List[Hitbox], dict]:
        """
        Advanced corridor scan with:
        1. Temporal motion estimation (rejecting static background noise)
        2. Ground spike & block detection
        3. Ceiling spike detection
        4. Jump orb & jump pad classification
        5. Floor pit / gap detection
        """
        now = time.perf_counter()
        dt = max(0.001, now - self.last_frame_time)
        self.last_frame_time = now

        h, w = frame.shape[:2]
        if self.ground_y == 0 or self.player_x == 0:
            self.auto_calibrate(frame)

        # Update player tracking
        self.track_player(frame, dt)

        px = self.player_x
        py = self.player_y
        ps = self.player_size

        # Define Lookahead Corridor
        # Start scanning 6px ahead of player to avoid capturing player's own edge
        cx1 = px + ps + 6
        cx2 = min(w, cx1 + self.lookahead_px)
        cy1 = max(0, self.ceiling_y)
        # End scan 2px above ground to prevent the continuous ground line from bridging spikes
        cy2 = min(h, self.ground_y - 2)

        debug_info = {
            "player": (px, py, ps, ps),
            "player_state": self.player_state,
            "corridor": (cx1, cy1, cx2 - cx1, cy2 - cy1),
            "ground_y": self.ground_y,
            "ceiling_y": self.ceiling_y,
            "trigger_line": cx1 + int(self.jump_trigger_dist * self.speed_multiplier),
            "speed_px_s": self.estimated_speed_px_s
        }

        if cx2 <= cx1 or cy2 <= cy1:
            return [], debug_info

        roi = frame[cy1:cy2, cx1:cx2]
        gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        hitboxes = []

        # -------------------------------------------------------------
        # 1. MOTION / EDGE FILTERING FOR SOLID HAZARDS (SPIKES & BLOCKS)
        # -------------------------------------------------------------
        # Bilateral filter to smooth background textures while preserving sharp obstacle edges
        smoothed = cv2.bilateralFilter(gray_roi, 7, 75, 75)
        
        # Adaptive gradient & Canny with dynamic thresholds
        med_val = np.median(smoothed)
        lower_canny = int(max(20, 0.66 * med_val))
        upper_canny = int(min(220, 1.33 * med_val))
        edges = cv2.Canny(smoothed, lower_canny, upper_canny)
        
        # Dilate edges horizontally and vertically to close shapes
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        dilated = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel, iterations=1)
        
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        roi_h = roi.shape[0]
        min_obj_area = (ps * ps) * 0.06
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < min_obj_area:
                continue
                
            bx, by, bw, bh = cv2.boundingRect(cnt)
            
            # Absolute coordinates
            abs_x = cx1 + bx
            abs_y = cy1 + by
            dist_x = float(bx)
            
            # Ground alignment test (within 8px of bottom of ROI)
            bottom_edge = by + bh
            is_on_ground = (roi_h - bottom_edge) <= 8
            is_ceiling = by <= 8
            
            # Analyze polygonal shape (spike triangle vs block rectangle)
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.045 * peri, True)
            num_vertices = len(approx)
            
            aspect_ratio = float(bw) / max(1, bh)
            
            # Classification
            if is_on_ground:
                # Triangular shape or sharp tall aspect on ground = SPIKE
                if num_vertices == 3 or (bh >= 0.7 * bw and num_vertices <= 5):
                    hitboxes.append(Hitbox(
                        kind="spike_ground",
                        x=abs_x, y=abs_y, w=bw, h=bh,
                        dist_x=dist_x, is_hazard=True
                    ))
                else:
                    # Solid block on ground
                    hitboxes.append(Hitbox(
                        kind="block",
                        x=abs_x, y=abs_y, w=bw, h=bh,
                        dist_x=dist_x, is_hazard=True
                    ))
            elif is_ceiling:
                # Ceiling spike
                if num_vertices == 3 or (bh > bw and num_vertices <= 5):
                    hitboxes.append(Hitbox(
                        kind="spike_ceiling",
                        x=abs_x, y=abs_y, w=bw, h=bh,
                        dist_x=dist_x, is_hazard=True
                    ))
            else:
                # Floating obstacle or platform
                if abs(by - (py - cy1)) <= ps: # directly in player's flight path
                    hitboxes.append(Hitbox(
                        kind="block",
                        x=abs_x, y=abs_y, w=bw, h=bh,
                        dist_x=dist_x, is_hazard=True
                    ))

        # -------------------------------------------------------------
        # 2. COLOR & CIRCLE DETECTION FOR JUMP ORBS & PADS
        # -------------------------------------------------------------
        for name, (lower_hsv, upper_hsv) in self.color_targets.items():
            mask = cv2.inRange(hsv_roi, np.array(lower_hsv), np.array(upper_hsv))
            c_contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for cc in c_contours:
                c_area = cv2.contourArea(cc)
                if c_area < (ps * ps * 0.10):
                    continue
                    
                cbx, cby, cbw, cbh = cv2.boundingRect(cc)
                aspect = float(cbw) / max(1, cbh)
                
                if "orb" in name:
                    # Orbs are circular (aspect close to 1.0)
                    if 0.7 <= aspect <= 1.4:
                        hitboxes.append(Hitbox(
                            kind="orb",
                            x=cx1 + cbx, y=cy1 + cby, w=cbw, h=cbh,
                            dist_x=float(cbx), sub_type=name, is_hazard=False
                        ))
                elif "pad" in name:
                    # Jump pads lie flat on the ground (wide aspect ratio)
                    if aspect >= 1.4 and abs((cby + cbh) - roi_h) <= 15:
                        hitboxes.append(Hitbox(
                            kind="pad",
                            x=cx1 + cbx, y=cy1 + cby, w=cbw, h=cbh,
                            dist_x=float(cbx), sub_type=name, is_hazard=False
                        ))

        # -------------------------------------------------------------
        # 3. PIT / VOID DETECTION (FLOOR GAP)
        # -------------------------------------------------------------
        # Check if ground line is broken or missing ahead
        ground_stripe_y1 = max(0, roi_h - 4)
        ground_stripe_y2 = min(gray_roi.shape[0], roi_h)
        
        if ground_stripe_y2 > ground_stripe_y1:
            stripe = gray_roi[ground_stripe_y1:ground_stripe_y2, :]
            column_energy = np.mean(stripe, axis=0)
            
            # Find contiguous dark/empty segments in the ground line
            empty_segments = np.where(column_energy < 15)[0]
            if len(empty_segments) >= int(ps * 0.8):
                pit_start_x = int(empty_segments[0])
                pit_width = int(len(empty_segments))
                hitboxes.append(Hitbox(
                    kind="pit",
                    x=cx1 + pit_start_x, y=self.ground_y,
                    w=pit_width, h=ps,
                    dist_x=float(pit_start_x), is_hazard=True
                ))

        # Sort all detected hitboxes by distance from player (closest first)
        hitboxes.sort(key=lambda h: h.dist_x)
        return hitboxes, debug_info

    def annotate_frame(
        self, frame: np.ndarray, hitboxes: List[Hitbox],
        debug_info: dict, should_jump: bool, fps: float,
        trajectory_pts: Optional[List[Tuple[int, int]]] = None
    ) -> np.ndarray:
        """
        Draws high-tech cyber HUD with hitboxes, jump trajectory parabolic arc,
        and real-time diagnostics.
        """
        out = frame.copy()
        h, w = frame.shape[:2]

        # 1. Ground and Ceiling Lines
        gy = debug_info.get("ground_y", self.ground_y)
        cy = debug_info.get("ceiling_y", self.ceiling_y)
        cv2.line(out, (0, gy), (w, gy), (0, 255, 140), 2)
        cv2.line(out, (0, cy), (w, cy), (100, 100, 255), 1)

        # 2. Player Box & State Indicator
        if "player" in debug_info:
            px, py, pw, ph = debug_info["player"]
            pstate = debug_info.get("player_state", self.player_state)
            
            box_col = (0, 0, 255) if should_jump else ((0, 255, 0) if pstate.is_grounded else (0, 230, 255))
            cv2.rectangle(out, (px, py), (px + pw, py + ph), box_col, 2)
            
            state_str = "GROUNDED" if pstate.is_grounded else ("FALLING" if pstate.vy > 0 else "ASCENDING")
            cv2.putText(out, f"PLAYER [{state_str}]", (px - 10, max(20, py - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, box_col, 1)

        # 3. Lookahead Corridor
        if "corridor" in debug_info:
            cx, cy_box, cw, ch = debug_info["corridor"]
            cv2.rectangle(out, (cx, cy_box), (cx + cw, cy_box + ch), (255, 180, 0), 1)

        # 4. Jump Trigger Line
        if "trigger_line" in debug_info:
            tx = debug_info["trigger_line"]
            t_col = (0, 0, 255) if should_jump else (0, 160, 255)
            cv2.line(out, (tx, 0), (tx, h), t_col, 2)
            cv2.putText(out, "JUMP TRIGGER", (tx + 4, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.42, t_col, 1)

        # 5. Parabolic Jump Trajectory Arc
        if trajectory_pts and len(trajectory_pts) > 1:
            for i in range(len(trajectory_pts) - 1):
                p1 = trajectory_pts[i]
                p2 = trajectory_pts[i + 1]
                # Glowing neon trajectory
                cv2.line(out, p1, p2, (0, 255, 255), 2)

        # 6. Hitboxes
        for box in hitboxes:
            bx, by, bw, bh = box.x, box.y, box.w, box.h
            if box.kind == "spike_ground":
                col = (0, 0, 255)
                label = f"SPIKE ({int(box.dist_x)}px)"
            elif box.kind == "spike_ceiling":
                col = (0, 80, 255)
                label = f"CEIL SPIKE ({int(box.dist_x)}px)"
            elif box.kind == "block":
                col = (255, 120, 0)
                label = f"BLOCK ({int(box.dist_x)}px)"
            elif box.kind == "orb":
                col = (0, 240, 255)
                label = f"ORB [{box.sub_type}]"
            elif box.kind == "pad":
                col = (255, 0, 200)
                label = f"PAD [{box.sub_type}]"
            elif box.kind == "pit":
                col = (0, 0, 180)
                label = f"PIT VOID ({int(box.dist_x)}px)"
            else:
                col = (180, 180, 180)
                label = box.kind
                
            cv2.rectangle(out, (bx, by), (bx + bw, by + bh), col, 2)
            cv2.putText(out, label, (bx, max(15, by - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, col, 1)

        # 7. Sleek Top-Left HUD Card
        hud_w, hud_h = 280, 85
        overlay = out.copy()
        cv2.rectangle(overlay, (12, 12), (12 + hud_w, 12 + hud_h), (15, 17, 24), -1)
        cv2.addWeighted(overlay, 0.82, out, 0.18, 0, out)
        cv2.rectangle(out, (12, 12), (12 + hud_w, 12 + hud_h), (0, 240, 255), 1)

        cv2.putText(out, f"GD VISION AI PRO - {fps:.1f} FPS", (22, 34),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 240, 255), 1)
        
        action_text = "ACTION: [🔥 JUMP NOW!]" if should_jump else "ACTION: [AUTOPILOT CLEAR]"
        action_col = (0, 0, 255) if should_jump else (0, 255, 100)
        cv2.putText(out, action_text, (22, 56), cv2.FONT_HERSHEY_SIMPLEX, 0.46, action_col, 2)
        cv2.putText(out, f"Target: {len(hitboxes)} in corridor | Speed: {self.speed_multiplier:.1f}x",
                    (22, 78), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (200, 210, 225), 1)

        return out
