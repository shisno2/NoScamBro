"""
gui.py - Modern PySide6 GUI and Live Vision HUD for Geometry Dash AI.
Displays real-time game analysis, vision overlays, calibration controls, and hotkeys.
"""

import sys
import time
import numpy as np
import cv2
import keyboard

from PySide6.QtCore import Qt, QTimer, Slot, Signal, QObject
from PySide6.QtGui import QImage, QPixmap, QFont, QColor, QIcon
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSlider, QComboBox, QGroupBox, QSpinBox,
    QCheckBox, QFrame, QGridLayout, QStatusBar, QMessageBox
)

from capture import WindowCapture
from detector import GDVisionDetector
from bot_brain import GDBotBrain
from inputs import FastInputController
from simulator import GDSimulator

class HotkeySignaler(QObject):
    toggle_signal = Signal()
    stop_signal = Signal()

class GDMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Geometry Dash Real-Time Vision AI Bot v2.0")
        self.resize(1180, 740)
        self.setMinimumSize(960, 640)

        # Core Components
        self.capture = WindowCapture("Geometry Dash")
        self.detector = GDVisionDetector()
        self.input_ctrl = FastInputController("mouse")
        self.brain = GDBotBrain(self.detector, self.input_ctrl)
        self.simulator = GDSimulator()
        
        # State
        self.use_simulator = False
        self.show_debug_overlay = True
        self.is_active = False
        self.fps = 0.0
        self.last_frame_time = time.perf_counter()
        
        # Setup Hotkeys (F6 start/toggle, F7 stop)
        self.hotkeys = HotkeySignaler()
        self.hotkeys.toggle_signal.connect(self.toggle_ai)
        self.hotkeys.stop_signal.connect(self.stop_ai)
        
        try:
            keyboard.add_hotkey("F6", lambda: self.hotkeys.toggle_signal.emit())
            keyboard.add_hotkey("F7", lambda: self.hotkeys.stop_signal.emit())
        except Exception as e:
            print("Hotkey hook notice:", e)

        # Build UI
        self._init_theme()
        self._init_ui()

        # Frame Processing Timer (60-120 FPS target)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.process_frame)
        self.timer.start(8) # ~120 Hz timer

    def _init_theme(self):
        """Applies dark cyberpunk neon style."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0F1016;
            }
            QWidget {
                color: #ECEFF4;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-size: 13px;
            }
            QGroupBox {
                background-color: #171822;
                border: 1px solid #2B2D3C;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 14px;
                font-weight: bold;
                color: #00F0FF;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding-left: 10px;
                padding-right: 10px;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1F2233, stop:1 #272B40);
                border: 1px solid #3B4261;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                color: #FFFFFF;
            }
            QPushButton:hover {
                background: #2D324A;
                border-color: #00F0FF;
            }
            QPushButton:pressed {
                background: #00ADB5;
                color: #000000;
            }
            QPushButton#btnStart {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00B074, stop:1 #00E676);
                color: #000000;
                font-size: 15px;
                border: none;
            }
            QPushButton#btnStart:hover {
                background: #00FF88;
            }
            QPushButton#btnStop {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #D32F2F, stop:1 #FF5252);
                color: #FFFFFF;
                font-size: 15px;
                border: none;
            }
            QPushButton#btnStop:hover {
                background: #FF1744;
            }
            QComboBox {
                background-color: #1E202F;
                border: 1px solid #3B4261;
                border-radius: 5px;
                padding: 5px 10px;
                color: #FFFFFF;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #222436;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: #00F0FF;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #FFFFFF;
                border: 2px solid #00F0FF;
                width: 16px;
                margin-top: -5px;
                margin-bottom: -5px;
                border-radius: 8px;
            }
            QCheckBox {
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid #3B4261;
                background: #1E202F;
            }
            QCheckBox::indicator:checked {
                background: #00F0FF;
            }
        """)

    def _init_ui(self):
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # Left Column: Video Preview & Live Vision HUD
        left_layout = QVBoxLayout()
        
        preview_header = QHBoxLayout()
        self.lbl_title = QLabel("LIVE GAME MONITOR & COMPUTER VISION HUD")
        self.lbl_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #00F0FF;")
        self.lbl_hud_stats = QLabel("FPS: 0.0 | Latency: 0.0 ms")
        self.lbl_hud_stats.setStyleSheet("color: #7AA2F7; font-weight: bold;")
        preview_header.addWidget(self.lbl_title)
        preview_header.addStretch()
        preview_header.addWidget(self.lbl_hud_stats)
        left_layout.addLayout(preview_header)

        # Video Frame Container
        self.video_label = QLabel()
        self.video_label.setMinimumSize(640, 360)
        self.video_label.setStyleSheet("background-color: #08090C; border: 2px solid #1E2235; border-radius: 8px;")
        self.video_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.video_label, stretch=1)

        # Status Bar under Video
        status_bar_layout = QHBoxLayout()
        self.lbl_status = QLabel("● STATUS: IDLE (Press F6 or Click START)")
        self.lbl_status.setStyleSheet("color: #E0AF68; font-weight: bold; font-size: 13px;")
        self.lbl_action = QLabel("ACTION: NONE")
        self.lbl_action.setStyleSheet("color: #9ECE6A; font-weight: bold; font-size: 13px;")
        status_bar_layout.addWidget(self.lbl_status)
        status_bar_layout.addStretch()
        status_bar_layout.addWidget(self.lbl_action)
        left_layout.addLayout(status_bar_layout)

        main_layout.addLayout(left_layout, stretch=3)

        # Right Column: Controls & Tuning Dashboard
        right_panel = QVBoxLayout()
        right_panel.setSpacing(12)

        # 1. Main Action Buttons
        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton("▶ START AI (F6)")
        self.btn_start.setObjectName("btnStart")
        self.btn_start.setFixedHeight(45)
        self.btn_start.clicked.connect(self.start_ai)

        self.btn_stop = QPushButton("⏹ STOP (F7)")
        self.btn_stop.setObjectName("btnStop")
        self.btn_stop.setFixedHeight(45)
        self.btn_stop.clicked.connect(self.stop_ai)

        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_stop)
        right_panel.addLayout(btn_layout)

        # 2. Source & Target Selection Group
        grp_source = QGroupBox("Capture Target")
        src_layout = QVBoxLayout(grp_source)
        
        self.cmb_source = QComboBox()
        self.cmb_source.addItem("Auto-Detect: Geometry Dash Window")
        self.cmb_source.addItem("Built-in GD Simulator (Demo / Offline Test)")
        self.cmb_source.currentIndexChanged.connect(self._on_source_changed)
        src_layout.addWidget(self.cmb_source)

        btn_refresh = QPushButton("Refresh Window Detection")
        btn_refresh.clicked.connect(self._refresh_windows)
        src_layout.addWidget(btn_refresh)
        right_panel.addWidget(grp_source)

        # 3. Mode & Controls Group
        grp_mode = QGroupBox("Game Mode & Input")
        mode_layout = QGridLayout(grp_mode)

        mode_layout.addWidget(QLabel("Mode:"), 0, 0)
        self.cmb_mode = QComboBox()
        self.cmb_mode.addItems(["Cube (Standard Jump)", "Ship / Wave (Steering)", "UFO (Flap Jump)"])
        self.cmb_mode.currentIndexChanged.connect(self._on_mode_changed)
        mode_layout.addWidget(self.cmb_mode, 0, 1)

        mode_layout.addWidget(QLabel("Input Key:"), 1, 0)
        self.cmb_input = QComboBox()
        self.cmb_input.addItems(["Left Mouse Click", "Spacebar", "Up Arrow"])
        self.cmb_input.currentIndexChanged.connect(self._on_input_changed)
        mode_layout.addWidget(self.cmb_input, 1, 1)

        mode_layout.addWidget(QLabel("Level Speed:"), 2, 0)
        self.cmb_speed = QComboBox()
        self.cmb_speed.addItems(["1.0x Normal Speed", "0.5x Slow", "2.0x Double", "3.0x Triple", "4.0x Quad"])
        self.cmb_speed.currentIndexChanged.connect(self._on_speed_changed)
        mode_layout.addWidget(self.cmb_speed, 2, 1)
        right_panel.addWidget(grp_mode)

        # 4. Computer Vision Tuning Sliders
        grp_tuning = QGroupBox("Vision & Reflex Calibration")
        tune_layout = QVBoxLayout(grp_tuning)

        # Trigger Distance
        self.lbl_trigger_val = QLabel(f"Jump Trigger Distance: {self.detector.jump_trigger_dist} px")
        self.slider_trigger = QSlider(Qt.Horizontal)
        self.slider_trigger.setRange(30, 160)
        self.slider_trigger.setValue(self.detector.jump_trigger_dist)
        self.slider_trigger.valueChanged.connect(self._on_trigger_slider)
        tune_layout.addWidget(self.lbl_trigger_val)
        tune_layout.addWidget(self.slider_trigger)

        # Lookahead Distance
        self.lbl_lookahead_val = QLabel(f"Lookahead Scan Distance: {self.detector.lookahead_px} px")
        self.slider_lookahead = QSlider(Qt.Horizontal)
        self.slider_lookahead.setRange(100, 500)
        self.slider_lookahead.setValue(self.detector.lookahead_px)
        self.slider_lookahead.valueChanged.connect(self._on_lookahead_slider)
        tune_layout.addWidget(self.lbl_lookahead_val)
        tune_layout.addWidget(self.slider_lookahead)

        # Floor Position
        self.lbl_floor_val = QLabel(f"Ground Level: {int(self.detector.ground_y_ratio * 100)}%")
        self.slider_floor = QSlider(Qt.Horizontal)
        self.slider_floor.setRange(60, 95)
        self.slider_floor.setValue(int(self.detector.ground_y_ratio * 100))
        self.slider_floor.valueChanged.connect(self._on_floor_slider)
        tune_layout.addWidget(self.lbl_floor_val)
        tune_layout.addWidget(self.slider_floor)

        # Player X Position
        self.lbl_player_x_val = QLabel(f"Player X Position: {int(self.detector.player_x_ratio * 100)}%")
        self.slider_player_x = QSlider(Qt.Horizontal)
        self.slider_player_x.setRange(10, 45)
        self.slider_player_x.setValue(int(self.detector.player_x_ratio * 100))
        self.slider_player_x.valueChanged.connect(self._on_player_x_slider)
        tune_layout.addWidget(self.lbl_player_x_val)
        tune_layout.addWidget(self.slider_player_x)

        # Debug Overlay Checkbox
        self.chk_overlay = QCheckBox("Show AI Vision Overlay (Rays, Boxes, Triggers)")
        self.chk_overlay.setChecked(True)
        self.chk_overlay.toggled.connect(lambda v: setattr(self, "show_debug_overlay", v))
        tune_layout.addWidget(self.chk_overlay)

        right_panel.addWidget(grp_tuning)

        # Statistics Label
        self.lbl_stats = QLabel("Total Jumps: 0 | Deaths: 0")
        self.lbl_stats.setStyleSheet("color: #7AA2F7; padding: 4px;")
        right_panel.addWidget(self.lbl_stats)

        right_panel.addStretch()
        main_layout.addLayout(right_panel, stretch=2)

        self.setCentralWidget(main_widget)
        self._refresh_windows()

    def _refresh_windows(self):
        found = self.capture.find_target_window()
        if found:
            self.lbl_status.setText("● STATUS: Geometry Dash window detected! Ready.")
            self.lbl_status.setStyleSheet("color: #00E676; font-weight: bold;")
        else:
            if not self.use_simulator:
                self.lbl_status.setText("● STATUS: GD window not found. Using Simulator or Desktop.")
                self.lbl_status.setStyleSheet("color: #E0AF68; font-weight: bold;")

    def _on_source_changed(self, idx):
        self.use_simulator = (idx == 1)
        if self.use_simulator:
            self.lbl_status.setText("● STATUS: Running built-in GD Simulator mode.")
            self.lbl_status.setStyleSheet("color: #00F0FF; font-weight: bold;")

    def _on_mode_changed(self, idx):
        modes = ["cube", "ship", "ufo"]
        self.detector.mode = modes[idx]

    def _on_input_changed(self, idx):
        inputs = ["mouse", "space", "up"]
        self.input_ctrl.set_mode(inputs[idx])

    def _on_speed_changed(self, idx):
        speeds = [1.0, 0.5, 2.0, 3.0, 4.0]
        self.brain.set_speed(speeds[idx])

    def _on_trigger_slider(self, val):
        self.detector.jump_trigger_dist = val
        self.lbl_trigger_val.setText(f"Jump Trigger Distance: {val} px")

    def _on_lookahead_slider(self, val):
        self.detector.lookahead_px = val
        self.lbl_lookahead_val.setText(f"Lookahead Scan Distance: {val} px")

    def _on_floor_slider(self, val):
        self.detector.ground_y_ratio = val / 100.0
        self.lbl_floor_val.setText(f"Ground Level: {val}%")
        self.detector.last_player_box = None # force re-calibration

    def _on_player_x_slider(self, val):
        self.detector.player_x_ratio = val / 100.0
        self.lbl_player_x_val.setText(f"Player X Position: {val}%")
        self.detector.last_player_box = None

    @Slot()
    def toggle_ai(self):
        if self.is_active:
            self.stop_ai()
        else:
            self.start_ai()

    @Slot()
    def start_ai(self):
        self.is_active = True
        self.brain.enabled = True
        self.lbl_status.setText("● STATUS: AI ACTIVE - Real-Time Autopilot ENGAGED!")
        self.lbl_status.setStyleSheet("color: #00FF88; font-weight: bold;")
        # Focus game window if available
        if not self.use_simulator:
            self.capture.bring_to_front()

    @Slot()
    def stop_ai(self):
        self.is_active = False
        self.brain.enabled = False
        self.input_ctrl.release_up()
        self.lbl_status.setText("● STATUS: AI STOPPED (Paused)")
        self.lbl_status.setStyleSheet("color: #FF5252; font-weight: bold;")

    def process_frame(self):
        """Main real-time computer vision and reflex loop."""
        t_start = time.perf_counter()
        
        # 1. Grab Frame
        frame = None
        if self.use_simulator:
            frame = self.simulator.update()
        else:
            try:
                frame = self.capture.grab_frame()
            except Exception:
                # If capture fails (e.g. window minimized or display access error), fallback to simulator
                frame = self.simulator.update()

        if frame is None or frame.size == 0:
            return

        # 2. Vision Processing
        obstacles, debug_info = self.detector.scan_corridor(frame)
        is_dead = self.detector.detect_death(frame)

        # 3. Decision & Input Dispatch
        jumped = self.brain.process_frame_decision(obstacles, debug_info, is_dead)
        if jumped and self.use_simulator:
            self.simulator.trigger_jump()

        t_end = time.perf_counter()
        latency_ms = (t_end - t_start) * 1000.0
        
        # Calculate GUI FPS
        dt = t_start - self.last_frame_time
        if dt > 0:
            self.fps = 0.9 * self.fps + 0.1 * (1.0 / dt)
        self.last_frame_time = t_start

        # 4. Render Annotations if enabled
        if self.show_debug_overlay:
            display_frame = self.detector.annotate_frame(frame, obstacles, debug_info, jumped, self.fps)
        else:
            display_frame = frame

        # Update HUD Labels
        self.lbl_hud_stats.setText(f"FPS: {self.fps:.1f} | Latency: {latency_ms:.1f} ms")
        if jumped:
            self.lbl_action.setText("ACTION: 🔥 JUMP EXECUTED!")
            self.lbl_action.setStyleSheet("color: #FF1744; font-weight: bold;")
        else:
            self.lbl_action.setText("ACTION: SCANNING...")
            self.lbl_action.setStyleSheet("color: #00E676; font-weight: bold;")

        self.lbl_stats.setText(f"Total Jumps: {self.brain.total_jumps} | Deaths: {self.brain.deaths_detected}")

        # Convert OpenCV BGR image to QPixmap for display
        rgb_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        q_img = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)
        
        # Scale to fit label maintaining aspect ratio
        scaled_pixmap = pixmap.scaled(self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.video_label.setPixmap(scaled_pixmap)

    def closeEvent(self, event):
        self.stop_ai()
        try:
            keyboard.unhook_all()
        except Exception:
            pass
        super().closeEvent(event)

def launch_gui():
    app = QApplication(sys.argv)
    window = GDMainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    launch_gui()
