"""
bot_brain.py - Real-time decision making engine and reflex controller for Geometry Dash.
Analyzes obstacles from the vision detector and triggers low-latency inputs.
"""

import time
from typing import List
from detector import Obstacle, GDVisionDetector
from inputs import FastInputController

class GDBotBrain:
    """Intelligent reflex controller that decides when to jump, hold, or release."""
    
    def __init__(self, detector: GDVisionDetector, input_ctrl: FastInputController):
        self.detector = detector
        self.input = input_ctrl
        
        # State
        self.enabled = False
        self.last_jump_time = 0.0
        self.last_hold_time = 0.0
        self.is_jumping = False
        self.is_holding = False
        
        # Physics & Reflex parameters
        self.jump_cooldown_sec = 0.38    # Minimum time cube is in air before next ground jump
        self.tap_duration_sec = 0.035    # Duration of a click in seconds
        self.speed_multiplier = 1.0     # 0.5x, 1x, 2x, 3x, 4x
        
        # Adaptive tuning
        self.auto_retry_active = True
        self.total_jumps = 0
        self.deaths_detected = 0

    def set_speed(self, speed_mult: float):
        """Adjusts timing parameters based on level speed portal."""
        self.speed_multiplier = max(0.5, speed_mult)

    def should_trigger_jump(self, obstacles: List[Obstacle], debug_info: dict) -> bool:
        """
        Determines if an immediate jump is needed based on obstacles and trigger zone.
        """
        if not obstacles:
            return False
            
        now = time.perf_counter()
        time_since_jump = now - self.last_jump_time
        
        # Current trigger threshold distance (adjusted for speed)
        effective_trigger = self.detector.jump_trigger_dist * self.speed_multiplier
        margin = self.detector.trigger_margin
        
        for obs in obstacles:
            # 1. Ground Spikes & Blocks
            if obs.kind in ("spike", "block"):
                # If obstacle is within trigger zone [effective_trigger - margin, effective_trigger + margin]
                if obs.distance <= effective_trigger:
                    # If we are already mid-jump, don't spam jump unless cooldown passed
                    if time_since_jump >= self.jump_cooldown_sec:
                        return True
                        
            # 2. Orbs (Yellow, Pink, Blue, Red)
            elif obs.kind == "orb":
                # Orbs require clicking when the player is directly on top of the orb
                orb_trigger = self.detector.player_size * 0.4
                if obs.distance <= orb_trigger:
                    # Orbs can be clicked in mid-air
                    if time_since_jump >= 0.12:
                        return True

        return False

    def process_frame_decision(self, obstacles: List[Obstacle], debug_info: dict, is_dead: bool) -> bool:
        """
        Processes one vision frame, decides actions, and dispatches direct input.
        Returns whether a jump action was dispatched.
        """
        if not self.enabled:
            return False
            
        now = time.perf_counter()
        
        # Check death / respawn
        if is_dead:
            self.deaths_detected += 1
            self.input.release_up()
            self.is_holding = False
            return False

        # Mode-specific handling
        if self.detector.mode == "cube":
            must_jump = self.should_trigger_jump(obstacles, debug_info)
            if must_jump:
                self.input.press_down()
                self.last_jump_time = now
                self.is_jumping = True
                self.total_jumps += 1
                return True
            elif self.is_jumping and (now - self.last_jump_time >= self.tap_duration_sec):
                self.input.release_up()
                self.is_jumping = False
                
        elif self.detector.mode in ("ship", "wave"):
            # Corridor following: hold to go up, release to go down
            target_y = (self.detector.ground_y + self.detector.ceiling_y) // 2
            player_y = debug_info["player"][1] if "player" in debug_info else target_y
            
            # Look ahead for closest block to steer away
            ceiling_threat = False
            floor_threat = False
            
            for obs in obstacles:
                if obs.distance < 150:
                    if obs.y < target_y:
                        ceiling_threat = True
                    else:
                        floor_threat = True
                        
            if floor_threat or player_y > target_y + 20:
                if not self.is_holding:
                    self.input.press_down()
                    self.is_holding = True
                    return True
            elif ceiling_threat or player_y < target_y - 20:
                if self.is_holding:
                    self.input.release_up()
                    self.is_holding = False
                    
        return False
