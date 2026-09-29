"""
bot_brain.py - Geometry Dash Physics and Trajectory Brain.
Features:
- Physics-based jump trajectory prediction (parabolic arc simulation)
- Hitbox intersection solver for spikes, blocks, and pits
- Jump pad detection (inhibits jumping to let pad bounce)
- Air-orb precision trigger
- Adaptive learning / Practice mode timing fine-tuner
"""

import time
from typing import List, Tuple, Optional
from detector import Hitbox, GDVisionDetector, PlayerState
from inputs import FastInputController

class GDBotBrain:
    """Intelligent reflex and trajectory solver for Geometry Dash."""

    def __init__(self, detector: GDVisionDetector, input_ctrl: FastInputController):
        self.detector = detector
        self.input = input_ctrl

        # Core State
        self.enabled = False
        self.is_jumping = False
        self.is_holding = False
        self.last_jump_time = 0.0
        self.last_orb_time = 0.0
        self.last_hold_time = 0.0

        # GD Physics constants (scaled to screen resolution)
        self.gravity = 1450.0            # px / s^2
        self.jump_velocity = -540.0      # initial jump impulse px / s
        self.speed_multiplier = 1.0
        self.horizontal_speed = 420.0    # px / s at 1.0x

        # Timing & Duration
        self.tap_duration_sec = 0.032    # micro-click duration
        self.jump_cooldown_sec = 0.36    # airborne refractory period for cube
        self.orb_cooldown_sec = 0.10

        # Adaptive auto-tuning
        self.total_jumps = 0
        self.deaths_detected = 0
        self.last_death_stamp = 0.0
        self.timing_offset_px = 0.0

        # Current computed trajectory for HUD
        self.current_trajectory: List[Tuple[int, int]] = []

    def set_speed(self, speed_mult: float):
        """Sets game speed portal multiplier (0.5x, 1x, 2x, 3x, 4x)."""
        self.speed_multiplier = max(0.5, speed_mult)
        self.detector.speed_multiplier = self.speed_multiplier
        self.horizontal_speed = 420.0 * self.speed_multiplier

    def compute_trajectory(self, pstate: PlayerState, ground_y: int) -> List[Tuple[int, int]]:
        """
        Simulates the parabolic jump arc starting from player's current position.
        Returns a list of (x, y) coordinates for rendering and collision checking.
        """
        pts = []
        cur_x = float(pstate.x + pstate.w // 2)
        cur_y = float(pstate.y + pstate.h)
        vy = self.jump_velocity
        vx = self.horizontal_speed
        
        sim_dt = 0.02
        for _ in range(25):
            pts.append((int(cur_x), int(cur_y)))
            cur_x += vx * sim_dt
            vy += self.gravity * sim_dt
            cur_y += vy * sim_dt
            if cur_y >= ground_y:
                pts.append((int(cur_x), int(ground_y)))
                break
        return pts

    def check_future_collision(self, hitboxes: List[Hitbox], pstate: PlayerState) -> Tuple[bool, Optional[Hitbox]]:
        """
        Checks if the player will collide with an obstacle if NO jump is performed.
        """
        eff_trigger = (self.detector.jump_trigger_dist + self.timing_offset_px) * self.speed_multiplier
        margin = self.detector.trigger_margin
        
        for box in hitboxes:
            if not box.is_hazard:
                continue
                
            # If hazard is approaching within trigger distance
            if box.dist_x <= eff_trigger:
                # If obstacle is a ground spike or pit or block at player level
                if box.kind in ("spike_ground", "block", "pit"):
                    return True, box
                    
        return False, None

    def should_trigger_jump(self, hitboxes: List[Hitbox], debug_info: dict) -> bool:
        """
        Core intelligence: decides whether to jump right now.
        """
        now = time.perf_counter()
        pstate = debug_info.get("player_state", self.detector.player_state)
        time_since_jump = now - self.last_jump_time
        time_since_orb = now - self.last_orb_time

        # 1. JUMP PAD CHECK:
        # If there is a jump pad right in front of us, DO NOT JUMP! Let the pad bounce us!
        for box in hitboxes:
            if box.kind == "pad" and box.dist_x <= (self.detector.player_size * 1.5):
                return False

        # 2. ORB CHECK (Yellow, Pink, Blue, Red):
        # Orbs must be clicked when player overlaps the orb hitbox
        for box in hitboxes:
            if box.kind == "orb":
                # When player front overlaps orb center
                orb_trigger_dist = self.detector.player_size * 0.45
                if box.dist_x <= orb_trigger_dist:
                    if time_since_orb >= self.orb_cooldown_sec:
                        self.last_orb_time = now
                        return True

        # 3. GROUND HAZARD COLLISION CHECK:
        # If player is grounded (or about to land), check upcoming ground spikes / blocks / pits
        if pstate.is_grounded or time_since_jump >= self.jump_cooldown_sec:
            will_collide, hazard = self.check_future_collision(hitboxes, pstate)
            if will_collide:
                # Collision detected! Trigger jump immediately
                return True

        return False

    def process_frame_decision(self, hitboxes: List[Hitbox], debug_info: dict, is_dead: bool) -> bool:
        """
        Evaluates current vision frame and issues instantaneous sub-millisecond input.
        """
        if not self.enabled:
            return False

        now = time.perf_counter()
        pstate = debug_info.get("player_state", self.detector.player_state)
        ground_y = debug_info.get("ground_y", self.detector.ground_y)

        # Update trajectory points for GUI visualization
        self.current_trajectory = self.compute_trajectory(pstate, ground_y)

        # 1. Handle Death / Auto-Retry Tuning
        if is_dead:
            if now - self.last_death_stamp > 0.8:
                self.deaths_detected += 1
                self.last_death_stamp = now
                # Adaptive offset: slight adjustment if died
                # Alternates subtle calibration to find perfect pixel
                self.timing_offset_px = ((self.timing_offset_px + 3) % 15) - 6
            self.input.release_up()
            self.is_holding = False
            return False

        # 2. Cube Mode Reflexes
        if self.detector.mode == "cube":
            jump = self.should_trigger_jump(hitboxes, debug_info)
            if jump:
                self.input.press_down()
                self.last_jump_time = now
                self.is_jumping = True
                self.total_jumps += 1
                return True
            elif self.is_jumping and (now - self.last_jump_time >= self.tap_duration_sec):
                self.input.release_up()
                self.is_jumping = False

        # 3. Ship / Wave Corridor Steering
        elif self.detector.mode in ("ship", "wave"):
            mid_y = (self.detector.ground_y + self.detector.ceiling_y) // 2
            player_y = pstate.y
            
            ground_threat = False
            ceiling_threat = False
            
            for box in hitboxes:
                if box.dist_x < 180:
                    if box.kind in ("spike_ceiling",) or box.y < mid_y:
                        ceiling_threat = True
                    elif box.kind in ("spike_ground", "pit") or box.y > mid_y:
                        ground_threat = True

            # Steering logic: avoid obstacles and maintain center corridor
            if ground_threat or (player_y > mid_y + 15 and not ceiling_threat):
                if not self.is_holding:
                    self.input.press_down()
                    self.is_holding = True
                    return True
            elif ceiling_threat or player_y < mid_y - 15:
                if self.is_holding:
                    self.input.release_up()
                    self.is_holding = False

        # 4. UFO Mode (Flap Jump)
        elif self.detector.mode == "ufo":
            # Flap when approaching ground hazard or falling too low
            if pstate.y > (ground_y - int(self.detector.player_size * 1.8)):
                if now - self.last_jump_time >= 0.22:
                    self.input.press_down()
                    self.last_jump_time = now
                    self.is_jumping = True
                    self.total_jumps += 1
                    return True
            elif self.is_jumping and (now - self.last_jump_time >= self.tap_duration_sec):
                self.input.release_up()
                self.is_jumping = False

        return False
