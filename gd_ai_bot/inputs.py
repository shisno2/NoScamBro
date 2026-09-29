"""
inputs.py - Ultra-low latency direct Windows SendInput for Geometry Dash.
Provides sub-millisecond hardware-level keyboard and mouse simulation.
"""

import ctypes
import time
from ctypes import wintypes

# Win32 Constants
INPUT_MOUSE = 0
INPUT_KEYBOARD = 1

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004

KEYEVENTF_KEYDOWN = 0x0000
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008

VK_SPACE = 0x20
VK_UP = 0x26
SCAN_SPACE = 0x39
SCAN_UP = 0x48

# Win32 Structures
class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG))
    ]

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG))
    ]

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD)
    ]

class _INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT)
    ]

class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        ("u", _INPUT_UNION)
    ]

SendInput = ctypes.windll.user32.SendInput
SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
SendInput.restype = wintypes.UINT

class FastInputController:
    """Ultra-low latency controller for Geometry Dash inputs."""
    
    def __init__(self, mode="mouse"):
        """
        mode: 'mouse' (Left Click), 'space' (Spacebar), or 'up' (Up Arrow)
        """
        self.mode = mode.lower()
        self.is_pressed = False
        
    def set_mode(self, mode: str):
        self.mode = mode.lower()
        
    def press_down(self):
        """Send instant button down without releasing."""
        if self.is_pressed:
            return
        self.is_pressed = True
        
        if self.mode == "mouse":
            inp = INPUT(type=INPUT_MOUSE)
            inp.u.mi = MOUSEINPUT(0, 0, 0, MOUSEEVENTF_LEFTDOWN, 0, None)
            SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
        elif self.mode == "space":
            inp = INPUT(type=INPUT_KEYBOARD)
            inp.u.ki = KEYBDINPUT(VK_SPACE, SCAN_SPACE, KEYEVENTF_KEYDOWN, 0, None)
            SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
        elif self.mode == "up":
            inp = INPUT(type=INPUT_KEYBOARD)
            inp.u.ki = KEYBDINPUT(VK_UP, SCAN_UP, KEYEVENTF_KEYDOWN, 0, None)
            SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
            
    def release_up(self):
        """Send instant button up."""
        if not self.is_pressed:
            return
        self.is_pressed = False
        
        if self.mode == "mouse":
            inp = INPUT(type=INPUT_MOUSE)
            inp.u.mi = MOUSEINPUT(0, 0, 0, MOUSEEVENTF_LEFTUP, 0, None)
            SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
        elif self.mode == "space":
            inp = INPUT(type=INPUT_KEYBOARD)
            inp.u.ki = KEYBDINPUT(VK_SPACE, SCAN_SPACE, KEYEVENTF_KEYUP, 0, None)
            SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
        elif self.mode == "up":
            inp = INPUT(type=INPUT_KEYBOARD)
            inp.u.ki = KEYBDINPUT(VK_UP, SCAN_UP, KEYEVENTF_KEYUP, 0, None)
            SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))

    def tap_jump(self, duration_sec=0.035):
        """Performs a micro-tap jump."""
        self.press_down()
        time.sleep(duration_sec)
        self.release_up()

if __name__ == "__main__":
    controller = FastInputController("mouse")
    print("Testing input controller...")
    controller.tap_jump(0.05)
    print("Tap completed successfully!")
