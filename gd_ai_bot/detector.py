"""
detector.py - Real-time Computer Vision engine for Geometry Dash.
Performs ultra-fast obstacle, spike, orb, platform, and player detection.
"""

import cv2
import numpy as np
import time
from dataclasses import dataclass
from typing import List, Tuple, Optional

@dataclass
class Obstacle:
    kind: str       # 'spike', 'block', 'orb', 'pit', 'ceiling_spike'
    x: int          # X position relative to player or frame
    y: int          # Y position
    w: int
    h: int
    distance: float # Distance in pixels from player front edge
    sub_type: str = "" # e.g. 'yellow_orb', 'pink_orb'

class GDVisionDetector:
    """
    Analyzes game frames at high frequency to detect:
    1. Player position and ground level
    2. Obstacles (spikes, blocks, saws, pits) in the forward corridor
    3. Jump orbs (yellow, pink, blue, red)
    4. Safe trajectory corridors for wave/ship
    """

    def __init__(self):
        # Calibration defaults (proportions of window width/height)
        self.player_x_ratio = 0.22      # Player is usually around 20-25% from left
        self.ground_y_ratio = 0.80      # Ground is usually around 78-84% from top
        self.player_size = 48           # Estimated icon size in px (rescaled dynamically)
        
        # Lookahead configuration
        self.lookahead_px = 240         # Scan distance ahead of player
        self.jump_trigger_dist = 62     # Optimal jump trigger distance (in px)
        self.trigger_margin = 12
        
        # Detected state
        self.last_player_box = None
        self.ground_y = 0
        self.ceiling_y = 0
        self.mode = "cube"              # 'cube', 'ship', 'wave', 'ball', 'ufo'
        self.is_dead = False
        self.last_death_time = 0
        
        # Color ranges for Orbs in HSV
        self.orb_ranges = {
            "yellow_orb": ((20, 150, 150), (35, 255, 255)),
            "pink_orb": ((140, 120, 120), (170, 255, 255)),
            "blue_orb": ((95, 150, 150), (125, 255, 255)),
            "red_orb": ((0, 160, 160), (10, 255, 255)),
        }

    def calibrate(self, frame: np.ndarray):
        """Auto-calibrates ground position and player area based on frame geometry."""
        h, w = frame.shape[:2]
        self.ground_y = int(h * self.ground_y_ratio)
        self.ceiling_y = int(h * 0.15)
        
        # Dynamic player size based on resolution
        self.player_size = max(24, int(h * 0.075))
        player_x = int(w * self.player_x_ratio)
        player_y = self.ground_y - self.player_size
        self.last_player_box = (player_x, player_y, self.player_size, self.player_size)
        
        # Dynamic lookahead based on width
        self.lookahead_px = int(w * 0.30)
        self.jump_trigger_dist = int(self.player_size * 1.35)

    def detect_death(self, frame: np.ndarray) -> bool:
        """
        Detects death explosion / flash / restart screen.
        Geometry Dash flashes brightly or displays death particles on collision.
        """
        if self.last_player_box is None:
            return False
            
        px, py, pw, ph = self.last_player_box
        h, w = frame.shape[:2]
        
        # Check region around player for death burst
        margin = 30
        x1 = max(0, px - margin)
        y1 = max(0, py - margin)
        x2 = min(w, px + pw + margin)
        y2 = min(h, py + ph + margin)
        
        roi = frame[y1:y2, x1:x2]
        if roi.size == 0:
            return False
            
        # Death creates high variance / bright particles
        std_val = np.std(roi)
        mean_val = np.mean(roi)
        
        # Death burst or restart black screen
        if mean_val < 5 or mean_val > 250:
            now = time.perf_counter()
            if now - self.last_death_time > 0.5:
                self.last_death_time = now
                self.is_dead = True
                return True
        self.is_dead = False
        return False

    def scan_corridor(self, frame: np.ndarray) -> Tuple[List[Obstacle], dict]:
        """
        Scans the forward lookahead corridor for obstacles, spikes, orbs, and pits.
        Returns detected obstacles list and debug annotations for rendering.
        """
        h, w = frame.shape[:2]
        if self.last_player_box is None or self.ground_y == 0:
            self.calibrate(frame)
            
        px, py, pw, ph = self.last_player_box
        
        # Corridor bounds
        corridor_x1 = px + pw
        corridor_x2 = min(w, corridor_x1 + self.lookahead_px)
        
        # Vertical corridor: from above jump peak down to slightly below ground
        corridor_y1 = max(0, py - int(self.player_size * 2.8))
        corridor_y2 = min(h, self.ground_y + int(self.player_size * 0.5))
        
        debug_info = {
            "corridor": (corridor_x1, corridor_y1, corridor_x2 - corridor_x1, corridor_y2 - corridor_y1),
            "player": self.last_player_box,
            "trigger_line": corridor_x1 + self.jump_trigger_dist,
            "ground_y": self.ground_y
        }
        
        if corridor_x2 <= corridor_x1 or corridor_y2 <= corridor_y1:
            return [], debug_info
            
        roi = frame[corridor_y1:corridor_y2, corridor_x1:corridor_x2]
        if roi.size == 0:
            return [], debug_info
            
        obstacles = []
        
        # 1. Grayscale & Edge Detection for Spikes & Blocks
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        # Bilateral / Gaussian filter to suppress background textures
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Canny edge detector: obstacles have very sharp, high-contrast outlines
        edges = cv2.Canny(blurred, 40, 130)
        
        # Dilate slightly to connect broken edges
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        dilated = cv2.dilate(edges, kernel, iterations=1)
        
        # Find contours of foreground objects
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Ground level relative to ROI
        roi_ground_y = self.ground_y - corridor_y1
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < (self.player_size * self.player_size * 0.08):
                continue # Ignore tiny background particles
                
            bx, by, bw, bh = cv2.boundingRect(cnt)
            
            # Absolute coordinates
            abs_x = corridor_x1 + bx
            abs_y = corridor_y1 + by
            dist_from_player = float(bx) # Distance from front face of player
            
            # Approximate polygonal shape to detect spikes vs blocks
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.04 * peri, True)
            
            # Check if object intersects player's immediate jump path
            # Player is near ground level
            is_on_ground = (by + bh) >= (roi_ground_y - int(self.player_size * 0.3))
            
            kind = "block"
            if len(approx) == 3 or (bh > bw and is_on_ground):
                kind = "spike"
            elif by < roi_ground_y - int(self.player_size * 1.5):
                # High in the air
                kind = "ceiling_spike" if len(approx) == 3 else "high_block"
            elif is_on_ground:
                kind = "spike" if bh >= bw else "block"
                
            obstacles.append(Obstacle(
                kind=kind,
                x=abs_x,
                y=abs_y,
                w=bw,
                h=bh,
                distance=dist_from_player
            ))
            
        # 2. Color Detection for Jump Orbs (HSV)
        hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        for orb_name, (lower, upper) in self.orb_ranges.items():
            mask = cv2.inRange(hsv_roi, np.array(lower), np.array(upper))
            orb_contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for ocnt in orb_contours:
                if cv2.contourArea(ocnt) > (self.player_size * self.player_size * 0.12):
                    obx, oby, obw, obh = cv2.boundingRect(ocnt)
                    # Check circular aspect ratio
                    aspect = float(obw) / max(1, obh)
                    if 0.7 <= aspect <= 1.4:
                        obstacles.append(Obstacle(
                            kind="orb",
                            x=corridor_x1 + obx,
                            y=corridor_y1 + oby,
                            w=obw,
                            h=obh,
                            distance=float(obx),
                            sub_type=orb_name
                        ))
                        
        # Sort obstacles by distance from player (closest first)
        obstacles.sort(key=lambda o: o.distance)
        return obstacles, debug_info

    def annotate_frame(self, frame: np.ndarray, obstacles: List[Obstacle], debug_info: dict, should_jump: bool, fps: float) -> np.ndarray:
        """Draws visual HUD overlay on top of the frame for the user."""
        out = frame.copy()
        
        # Draw Ground Line
        gy = debug_info.get("ground_y", self.ground_y)
        cv2.line(out, (0, gy), (out.shape[1], gy), (0, 255, 100), 2)
        
        # Draw Player Box
        if "player" in debug_info and debug_info["player"]:
            px, py, pw, ph = debug_info["player"]
            p_color = (0, 0, 255) if should_jump else (0, 255, 0)
            cv2.rectangle(out, (px, py), (px + pw, py + ph), p_color, 2)
            cv2.putText(out, "PLAYER", (px, py - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.45, p_color, 1)

        # Draw Corridor
        if "corridor" in debug_info:
            cx, cy, cw, ch = debug_info["corridor"]
            cv2.rectangle(out, (cx, cy), (cx + cw, cy + ch), (255, 200, 0), 1)
            
        # Draw Trigger Line
        if "trigger_line" in debug_info:
            tx = debug_info["trigger_line"]
            t_color = (0, 0, 255) if should_jump else (0, 165, 255)
            cv2.line(out, (tx, 0), (tx, out.shape[0]), t_color, 2)
            cv2.putText(out, "JUMP TRIGGER", (tx + 5, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.45, t_color, 1)

        # Draw Obstacles
        for obs in obstacles:
            ox, oy, ow, oh = obs.x, obs.y, obs.w, obs.h
            if obs.kind == "spike":
                color = (0, 0, 255) # Red for spikes
                label = f"SPIKE ({int(obs.distance)}px)"
            elif obs.kind == "orb":
                color = (0, 255, 255) # Yellow for orbs
                label = f"ORB ({obs.sub_type})"
            elif obs.kind == "block":
                color = (255, 100, 0) # Cyan/Blue for blocks
                label = f"BLOCK ({int(obs.distance)}px)"
            else:
                color = (200, 200, 200)
                label = obs.kind
                
            cv2.rectangle(out, (ox, oy), (ox + ow, oy + oh), color, 2)
            cv2.putText(out, label, (ox, max(15, oy - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

        # Draw HUD status top-left
        status_bg = np.zeros((70, 240, 3), dtype=np.uint8)
        # alpha blend
        out[10:80, 10:250] = cv2.addWeighted(out[10:80, 10:250], 0.3, status_bg, 0.7, 0)
        
        status_text = "ACTION: JUMP!" if should_jump else "ACTION: RUNNING"
        text_color = (0, 0, 255) if should_jump else (0, 255, 0)
        cv2.putText(out, f"GD VISION AI - {fps:.1f} FPS", (20, 32), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(out, status_text, (20, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.5, text_color, 2)
        cv2.putText(out, f"Obstacles in sight: {len(obstacles)}", (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)

        return out
