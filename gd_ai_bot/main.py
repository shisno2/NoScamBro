"""
main.py - Entry point for Geometry Dash Real-Time Vision AI.
Supports both modern PySide6 GUI and ultra-fast Headless CLI mode.
"""

import sys
import argparse
import time
from capture import WindowCapture
from detector import GDVisionDetector
from bot_brain import GDBotBrain
from inputs import FastInputController

def run_headless_cli(input_mode="mouse", speed=1.0):
    print("=" * 60)
    print("  GEOMETRY DASH VISION AI - ULTRA REFLEX HEADLESS MODE")
    print("=" * 60)
    print(f"[*] Input Mode: {input_mode.upper()}")
    print(f"[*] Level Speed: {speed}x")
    print("[*] Controls: Press Ctrl+C in this terminal to STOP.")
    print("=" * 60)

    cap = WindowCapture("Geometry Dash")
    det = GDVisionDetector()
    inp = FastInputController(input_mode)
    brain = GDBotBrain(det, inp)
    brain.set_speed(speed)
    brain.enabled = True

    print("[+] Searching for Geometry Dash window...")
    while not cap.hwnd:
        if cap.find_target_window():
            print("[+] Geometry Dash window found and hooked!")
            break
        print("[-] Geometry Dash not detected yet. Retrying in 2 seconds... (Open GD!)")
        time.sleep(2)

    print("[+] AUTOPILOT ACTIVE! Monitoring screen in real time...")
    frame_count = 0
    t0 = time.perf_counter()

    try:
        while True:
            frame = cap.grab_frame()
            if frame is None or frame.size == 0:
                time.sleep(0.005)
                continue

            obstacles, debug_info = det.scan_corridor(frame)
            is_dead = det.detect_death(frame)
            jumped = brain.process_frame_decision(obstacles, debug_info, is_dead)

            frame_count += 1
            if frame_count % 120 == 0:
                elapsed = time.perf_counter() - t0
                fps = frame_count / elapsed
                print(f"[HUD] FPS: {fps:.1f} | Jumps: {brain.total_jumps} | Deaths: {brain.deaths_detected} | Sight: {len(obstacles)} objects")
                t0 = time.perf_counter()
                frame_count = 0

    except KeyboardInterrupt:
        print("\n[*] Stopping AI autopilot. Releasing inputs...")
        inp.release_up()
        print("[*] AI stopped safely.")

def main():
    parser = argparse.ArgumentParser(description="Geometry Dash Real-Time Vision AI")
    parser.add_argument("--cli", action="store_true", help="Run in headless terminal mode for ultra-high FPS")
    parser.add_argument("--input", choices=["mouse", "space", "up"], default="mouse", help="Input device to trigger")
    parser.add_argument("--speed", type=float, default=1.0, help="Game speed multiplier (0.5 to 4.0)")
    args = parser.parse_args()

    if args.cli:
        run_headless_cli(args.input, args.speed)
    else:
        from gui import launch_gui
        launch_gui()

if __name__ == "__main__":
    main()
