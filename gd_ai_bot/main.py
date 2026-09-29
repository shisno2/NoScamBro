"""
main.py - Entry point for Geometry Dash Real-Time Vision AI.
Supports both modern PySide6 GUI and ultra-fast Headless CLI mode.
"""

import sys
import argparse
import time
from capture import WindowCapture
from inputs import FastInputController
from bot_worker import BotWorkerThread

def run_headless_cli(input_mode="mouse", speed=1.0):
    print("=" * 60)
    print("  GEOMETRY DASH VISION AI - ULTRA REFLEX 240+ FPS CLI MODE")
    print("=" * 60)
    print(f"[*] Input Mode: {input_mode.upper()}")
    print(f"[*] Level Speed: {speed}x")
    print("[*] Controls: Press Ctrl+C in this terminal to STOP.")
    print("=" * 60)

    cap = WindowCapture("Geometry Dash")
    inp = FastInputController(input_mode)
    worker = BotWorkerThread(cap, inp)
    worker.set_speed(speed)
    worker.set_active(True)
    worker.start()

    print("[+] AUTOPILOT ACTIVE! Running reflex loop at 240+ FPS...")
    try:
        while True:
            time.sleep(0.5)
            state = worker.get_shared_state()
            fps = state["fps"]
            lat = state["latency_ms"]
            jumps = state["jumps"]
            action = state["action"]
            print(f"[STATUS] Bot FPS: {fps:.0f} | Latency: {lat:.2f} ms | Jumps: {jumps} | {action}")
    except KeyboardInterrupt:
        print("\n[*] Stopping AI autopilot...")
        worker.stop()
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
