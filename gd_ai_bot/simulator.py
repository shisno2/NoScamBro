"""
simulator.py - Built-in Geometry Dash level simulator for testing and demonstrating the Vision AI.
Renders moving spikes, blocks, and jump orbs at real game speeds.
"""

import numpy as np
import cv2
import time

class GDSimulator:
    """Generates synthetic Geometry Dash frames with moving obstacles and cube physics."""
    
    def __init__(self, width=960, height=540):
        self.width = width
        self.height = height
        self.ground_y = int(height * 0.80)
        self.cube_size = int(height * 0.08)
        
        # Player state
        self.player_x = int(width * 0.22)
        self.player_y = float(self.ground_y - self.cube_size)
        self.vel_y = 0.0
        self.gravity = 1450.0  # px/s^2
        self.jump_velocity = -520.0  # px/s
        self.is_grounded = True
        self.score = 0
        
        # Obstacles: list of dicts {x, y, w, h, kind, subtype}
        self.obstacles = []
        self.speed = 380.0 # px/s (1x standard GD speed)
        self.last_spawn_x = width
        self.last_update = time.perf_counter()
        
        # Generate initial track
        self._populate_track()

    def _populate_track(self):
        """Generates an initial sequence of obstacles."""
        self.obstacles.clear()
        cur_x = self.width + 100
        
        # Pattern of spikes and blocks
        patterns = [
            ("spike", 1),
            ("spike", 2),
            ("block", 1),
            ("spike", 1),
            ("orb", "yellow_orb"),
            ("spike", 3),
            ("block", 2),
            ("spike", 1),
        ]
        
        for p_type, val in patterns * 5:
            if p_type == "spike":
                count = val
                for i in range(count):
                    self.obstacles.append({
                        "kind": "spike",
                        "x": cur_x + i * self.cube_size,
                        "y": self.ground_y - self.cube_size,
                        "w": self.cube_size,
                        "h": self.cube_size,
                        "subtype": "spike"
                    })
                cur_x += count * self.cube_size + 240
            elif p_type == "block":
                self.obstacles.append({
                    "kind": "block",
                    "x": cur_x,
                    "y": self.ground_y - self.cube_size,
                    "w": self.cube_size * val,
                    "h": self.cube_size,
                    "subtype": "block"
                })
                cur_x += self.cube_size * val + 280
            elif p_type == "orb":
                self.obstacles.append({
                    "kind": "orb",
                    "x": cur_x,
                    "y": self.ground_y - int(self.cube_size * 2.2),
                    "w": int(self.cube_size * 0.9),
                    "h": int(self.cube_size * 0.9),
                    "subtype": val
                })
                cur_x += 320

    def trigger_jump(self):
        """Simulates cube jump."""
        if self.is_grounded:
            self.vel_y = self.jump_velocity
            self.is_grounded = False

    def update(self) -> np.ndarray:
        """Updates physics and renders a game frame."""
        now = time.perf_counter()
        dt = min(0.05, now - self.last_update)
        self.last_update = now
        
        # 1. Update player physics
        if not self.is_grounded:
            self.vel_y += self.gravity * dt
            self.player_y += self.vel_y * dt
            
            # Ground collision
            floor_limit = float(self.ground_y - self.cube_size)
            if self.player_y >= floor_limit:
                self.player_y = floor_limit
                self.vel_y = 0.0
                self.is_grounded = True
                
        # 2. Move obstacles leftwards
        move_dist = self.speed * dt
        for obs in self.obstacles:
            obs["x"] -= move_dist
            
        # Recycle obstacles that move off screen
        for obs in self.obstacles:
            if obs["x"] < -100:
                max_x = max([o["x"] for o in self.obstacles] or [self.width])
                obs["x"] = max_x + 260
                
        # 3. Render frame
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # Background: dark sci-fi Geometry Dash blue/purple gradient
        for y in range(self.height):
            ratio = y / self.height
            frame[y, :] = (int(35 + 20 * ratio), int(15 + 10 * ratio), int(45 + 30 * ratio))
            
        # Floor (Checker pattern style)
        cv2.rectangle(frame, (0, self.ground_y), (self.width, self.height), (20, 20, 30), -1)
        cv2.line(frame, (0, self.ground_y), (self.width, self.ground_y), (0, 240, 255), 3)
        
        # Grid lines in background
        offset = int((time.perf_counter() * self.speed * 0.4) % 60)
        for gx in range(-offset, self.width, 60):
            cv2.line(frame, (gx, 0), (gx, self.ground_y), (45, 30, 60), 1)

        # Draw Obstacles
        for obs in self.obstacles:
            ox = int(obs["x"])
            oy = int(obs["y"])
            ow = int(obs["w"])
            oh = int(obs["h"])
            
            if ox + ow < 0 or ox > self.width:
                continue
                
            if obs["kind"] == "spike":
                # Draw sharp triangular spike with white border
                pts = np.array([
                    [ox, oy + oh],
                    [ox + ow // 2, oy],
                    [ox + ow, oy + oh]
                ], np.int32)
                cv2.fillPoly(frame, [pts], (20, 20, 230)) # Red spike
                cv2.polylines(frame, [pts], True, (255, 255, 255), 2)
            elif obs["kind"] == "block":
                # Draw square block with neon outline
                cv2.rectangle(frame, (ox, oy), (ox + ow, oy + oh), (40, 40, 100), -1)
                cv2.rectangle(frame, (ox, oy), (ox + ow, oy + oh), (255, 200, 50), 2)
                # inner cross
                cv2.line(frame, (ox, oy), (ox + ow, oy + oh), (200, 150, 40), 1)
                cv2.line(frame, (ox, oy + oh), (ox + ow, oy), (200, 150, 40), 1)
            elif obs["kind"] == "orb":
                # Yellow orb
                center = (ox + ow // 2, oy + oh // 2)
                radius = ow // 2
                cv2.circle(frame, center, radius, (0, 230, 255), -1)
                cv2.circle(frame, center, radius + 3, (255, 255, 255), 2)
                cv2.circle(frame, center, int(radius * 0.5), (255, 255, 255), -1)

        # Draw Player Cube
        px = self.player_x
        py = int(self.player_y)
        ps = self.cube_size
        # Green neon cube with eye / square face
        cv2.rectangle(frame, (px, py), (px + ps, py + ps), (0, 230, 80), -1)
        cv2.rectangle(frame, (px, py), (px + ps, py + ps), (255, 255, 255), 2)
        # Face square
        eye_pad = int(ps * 0.25)
        cv2.rectangle(frame, (px + eye_pad, py + eye_pad), (px + ps - eye_pad, py + ps - eye_pad), (0, 100, 30), -1)
        
        return frame
