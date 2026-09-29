"""
capture.py - Ultra-fast window grabber for Geometry Dash using Win32 API and MSS.
Captures screen frames at 120-200+ FPS with zero unnecessary copies.
"""

import time
import win32gui
import win32con
import numpy as np
import mss

class WindowCapture:
    """Fast screen capture for a targeted game window or custom bounding box."""
    
    def __init__(self, window_title="Geometry Dash"):
        self.target_title = window_title
        self.hwnd = None
        self.sct = mss.mss()
        self.monitor = None
        self.last_update_time = 0
        self.fps = 0.0
        self.frame_count = 0
        self._fps_timer = time.perf_counter()
        
        # Try to find window immediately
        self.find_target_window()
        
    def find_target_window(self) -> bool:
        """Find the Geometry Dash window handle."""
        found_hwnds = []
        
        def enum_cb(hwnd, extra):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if self.target_title.lower() in title.lower():
                    found_hwnds.append(hwnd)
            return True
            
        win32gui.EnumWindows(enum_cb, None)
        
        if found_hwnds:
            self.hwnd = found_hwnds[0]
            self.update_geometry()
            return True
        else:
            self.hwnd = None
            # Fallback to primary monitor
            self.monitor = self.sct.monitors[1]
            return False

    def list_game_windows(self):
        """Returns a list of visible window titles."""
        windows = []
        def enum_cb(hwnd, extra):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title.strip():
                    windows.append((hwnd, title))
            return True
        win32gui.EnumWindows(enum_cb, None)
        return windows

    def set_window_by_hwnd(self, hwnd: int):
        """Manually select a window by handle."""
        if win32gui.IsWindow(hwnd):
            self.hwnd = hwnd
            self.update_geometry()
            return True
        return False

    def update_geometry(self):
        """Calculate client area (removes titlebar and window borders)."""
        if not self.hwnd or not win32gui.IsWindow(self.hwnd):
            return
            
        # Get client area dimensions
        client_rect = win32gui.GetClientRect(self.hwnd)
        left, top = win32gui.ClientToScreen(self.hwnd, (0, 0))
        right, bottom = win32gui.ClientToScreen(self.hwnd, (client_rect[2], client_rect[3]))
        
        width = right - left
        height = bottom - top
        
        if width > 50 and height > 50:
            self.monitor = {
                "left": left,
                "top": top,
                "width": width,
                "height": height
            }

    def bring_to_front(self):
        """Focus the game window."""
        if self.hwnd and win32gui.IsWindow(self.hwnd):
            try:
                win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)
                win32gui.SetForegroundWindow(self.hwnd)
            except Exception:
                pass

    def grab_frame(self) -> np.ndarray:
        """
        Captures the current frame as a BGR numpy array (OpenCV compatible).
        Runs at ultra-high FPS.
        """
        # Periodic geometry refresh every 2 seconds in case window was moved
        now = time.perf_counter()
        if now - self.last_update_time > 2.0:
            if self.hwnd:
                self.update_geometry()
            else:
                self.find_target_window()
            self.last_update_time = now

        # Grab raw image
        raw = self.sct.grab(self.monitor)
        
        # Convert to BGR array (discard alpha channel)
        # raw.raw has BGRA bytes
        frame = np.frombuffer(raw.raw, dtype=np.uint8).reshape((raw.height, raw.width, 4))[:, :, :3]
        
        # Measure FPS
        self.frame_count += 1
        elapsed = now - self._fps_timer
        if elapsed >= 0.5:
            self.fps = self.frame_count / elapsed
            self.frame_count = 0
            self._fps_timer = now
            
        return frame

if __name__ == "__main__":
    cap = WindowCapture("Geometry Dash")
    print(f"Target found: {cap.hwnd is not None}")
    print(f"Capture region: {cap.monitor}")
    
    print("Testing capture speed (100 frames)...")
    t0 = time.perf_counter()
    for _ in range(100):
        img = cap.grab_frame()
    total_time = time.perf_counter() - t0
    print(f"Captured 100 frames in {total_time:.3f}s -> {100 / total_time:.1f} FPS! Image shape: {img.shape}")
