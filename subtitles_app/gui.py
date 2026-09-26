import os
import sys
import subprocess
import time
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QCheckBox, QProgressBar,
    QTextEdit, QFileDialog, QFrame, QMessageBox, QGroupBox, QSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QRadioButton, QButtonGroup,
    QSlider, QSplitter
)
from PySide6.QtCore import Qt, QThread, Signal, QUrl, QTime
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QColor, QFont
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

# Ensure D: drive cache is configured before importing transcriber
if os.path.exists("D:\\"):
    os.environ["HF_HOME"] = "D:\\huggingface_cache"

try:
    from transcriber import SubtitleEngine, is_cuda_usable, format_timestamp_srt, format_timestamp_ass
except ImportError:
    from subtitles_app.transcriber import SubtitleEngine, is_cuda_usable, format_timestamp_srt, format_timestamp_ass

SUPPORTED_EXTENSIONS = {
    ".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".wmv", ".m4v",
    ".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac", ".wma", ".opus"
}

STUDIO_STYLE = """
QMainWindow {
    background-color: #0b0f19;
}
QWidget {
    color: #e6edf3;
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    font-size: 13px;
}
QGroupBox {
    border: 1px solid #30363d;
    border-radius: 10px;
    margin-top: 14px;
    padding-top: 12px;
    font-weight: 600;
    color: #58a6ff;
    background-color: #161b22;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 6px;
    background-color: #161b22;
    border-radius: 4px;
}
QComboBox, QSpinBox {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 6px 12px;
    color: #f0f6fc;
    min-height: 26px;
}
QComboBox:hover, QSpinBox:hover {
    border: 1px solid #58a6ff;
}
QCheckBox {
    spacing: 8px;
    font-weight: 500;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #484f58;
    background-color: #0d1117;
}
QCheckBox::indicator:checked {
    background-color: #238636;
    border-color: #2ea043;
}
QRadioButton {
    spacing: 8px;
    font-weight: 600;
    color: #c9d1d9;
}
QRadioButton::indicator {
    width: 16px;
    height: 16px;
    border-radius: 8px;
    border: 1px solid #484f58;
    background-color: #0d1117;
}
QRadioButton::indicator:checked {
    background-color: #58a6ff;
    border-color: #58a6ff;
}
QProgressBar {
    border: 1px solid #30363d;
    border-radius: 8px;
    text-align: center;
    background-color: #0d1117;
    color: #f0f6fc;
    font-weight: bold;
    height: 24px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1f6feb, stop:0.5 #8a63d2, stop:1 #d29922);
    border-radius: 7px;
}
QTableWidget {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 8px;
    color: #c9d1d9;
    font-family: 'Consolas', monospace;
    font-size: 13px;
    gridline-color: #21262d;
}
QHeaderView::section {
    background-color: #161b22;
    color: #8b949e;
    padding: 8px;
    border: none;
    border-bottom: 2px solid #30363d;
    font-weight: bold;
}
QPushButton {
    background-color: #21262d;
    color: #c9d1d9;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #30363d;
    border-color: #8b949e;
    color: white;
}
QPushButton:pressed {
    background-color: #161b22;
}
QPushButton:disabled {
    background-color: #161b22;
    color: #484f58;
    border-color: #21262d;
}
QSlider::groove:horizontal {
    border: 1px solid #30363d;
    height: 6px;
    background: #0d1117;
    border-radius: 3px;
}
QSlider::sub-page:horizontal {
    background: #58a6ff;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #ffffff;
    border: 1px solid #58a6ff;
    width: 14px;
    margin-top: -4px;
    margin-bottom: -4px;
    border-radius: 7px;
}
"""

class TranscriptionWorker(QThread):
    progress_signal = Signal(float, str)
    segment_signal = Signal(dict)
    finished_signal = Signal(dict)
    error_signal = Signal(str)

    def __init__(self, file_path: str, model_name: str, language: str, device: str, 
                 preset: str, vocal_boost: bool, burn_video: bool, words_per_chunk: int):
        super().__init__()
        self.file_path = file_path
        self.model_name = model_name
        self.language = language
        self.device = device
        self.preset = preset
        self.vocal_boost = vocal_boost
        self.burn_video = burn_video
        self.words_per_chunk = words_per_chunk

    def run(self):
        try:
            self.progress_signal.emit(0.02, "Инициализация движка нейросети...")
            engine = SubtitleEngine(model_name=self.model_name, device=self.device)

            def on_seg(seg):
                self.segment_signal.emit(seg)

            def on_prog(ratio, msg):
                self.progress_signal.emit(ratio, msg)

            segments = engine.transcribe(
                self.file_path,
                language=self.language,
                preset=self.preset,
                vocal_boost=self.vocal_boost,
                on_segment=on_seg,
                on_progress=on_prog
            )

            # Export files
            base_dir = os.path.dirname(self.file_path)
            base_name = os.path.splitext(os.path.basename(self.file_path))[0]
            created_files = {}

            # 1. Standard readable SRT
            srt_path = os.path.join(base_dir, f"{base_name}_phrases.srt")
            engine.export_srt_standard(segments, srt_path)
            created_files["srt_standard"] = srt_path

            # 2. Word-by-word SRT (TikTok / Reels style)
            word_srt_path = os.path.join(base_dir, f"{base_name}_words.srt")
            engine.export_srt_word_by_word(segments, word_srt_path, words_per_chunk=self.words_per_chunk)
            created_files["srt_words"] = word_srt_path

            # 3. Dynamic Glow TikTok/Karaoke ASS
            ass_path = os.path.join(base_dir, f"{base_name}_tiktok_glow.ass")
            engine.export_ass_tiktok_karaoke(segments, ass_path, title=base_name)
            created_files["ass_karaoke"] = ass_path

            # 4. Clean lyrics / text
            txt_path = os.path.join(base_dir, f"{base_name}_lyrics.txt")
            engine.export_txt(segments, txt_path)
            created_files["txt"] = txt_path

            # 5. Burn subtitles directly onto video if requested
            ext = os.path.splitext(self.file_path)[1].lower()
            if self.burn_video and ext in {".mp4", ".mkv", ".avi", ".mov", ".webm", ".m4v"}:
                self.progress_signal.emit(0.96, "Вшивание стильных субтитров в видео (FFmpeg)...")
                sub_to_burn = ass_path if os.path.exists(ass_path) else word_srt_path
                burned_video_path = os.path.join(base_dir, f"{base_name}_subtitled{ext}")
                ok = engine.burn_subtitles_to_video(self.file_path, sub_to_burn, burned_video_path)
                if ok:
                    created_files["burned_video"] = burned_video_path

            self.progress_signal.emit(1.0, "Генерация завершена на 100%!")
            self.finished_signal.emit({
                "segments": segments,
                "created_files": created_files,
                "folder": base_dir
            })
        except Exception as e:
            self.error_signal.emit(str(e))

class DropZone(QFrame):
    file_selected = Signal(str)

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.current_file = None
        self.init_ui()

    def init_ui(self):
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                border: 2px dashed #30363d;
                border-radius: 14px;
                background-color: #0d1117;
            }
            QFrame:hover {
                border-color: #58a6ff;
                background-color: #161b22;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 22, 20, 22)
        layout.setAlignment(Qt.AlignCenter)

        self.icon_label = QLabel("📥")
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setStyleSheet("font-size: 40px; background: transparent; border: none;")
        layout.addWidget(self.icon_label)

        self.text_label = QLabel("Перетащите видео или песню сюда")
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #f0f6fc; background: transparent; border: none;")
        layout.addWidget(self.text_label)

        self.sub_label = QLabel("MP3, WAV, MP4, MKV, FLAC, MOV, OGG | Автоматическое распознавание каждого слова")
        self.sub_label.setAlignment(Qt.AlignCenter)
        self.sub_label.setStyleSheet("font-size: 12px; color: #8b949e; background: transparent; border: none; margin-top: 3px;")
        layout.addWidget(self.sub_label)

        self.btn_browse = QPushButton("📁 Выбрать файл")
        self.btn_browse.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1f6feb, stop:1 #388bfd);
                color: white;
                padding: 6px 20px;
                font-size: 13px;
                font-weight: bold;
                border-radius: 6px;
                margin-top: 8px;
                border: none;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #388bfd, stop:1 #58a6ff);
            }
        """)
        self.btn_browse.clicked.connect(self.browse_file)
        layout.addWidget(self.btn_browse, alignment=Qt.AlignCenter)

    def browse_file(self):
        filter_str = "Медиа (*.mp3 *.wav *.flac *.m4a *.ogg *.mp4 *.mkv *.avi *.mov *.webm);;Все файлы (*.*)"
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите файл", "", filter_str)
        if file_path:
            self.set_file(file_path)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                event.acceptProposedAction()
                self.setStyleSheet("""
                    QFrame {
                        border: 2px dashed #238636;
                        border-radius: 14px;
                        background-color: #04260f;
                    }
                """)
                return
        event.ignore()

    def dragLeaveEvent(self, event):
        self.setStyleSheet("""
            QFrame {
                border: 2px dashed #30363d;
                border-radius: 14px;
                background-color: #0d1117;
            }
            QFrame:hover {
                border-color: #58a6ff;
                background-color: #161b22;
            }
        """)

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if os.path.isfile(file_path):
                self.set_file(file_path)
                event.acceptProposedAction()
        self.dragLeaveEvent(None)

    def set_file(self, path: str):
        self.current_file = path
        base_name = os.path.basename(path)
        size_mb = os.path.getsize(path) / (1024 * 1024)
        ext = os.path.splitext(path)[1].lower()
        is_video = ext in {".mp4", ".mkv", ".avi", ".mov", ".webm", ".m4v"}
        icon = "🎬" if is_video else "🎵"
        
        self.icon_label.setText(icon)
        self.text_label.setText(f"Файл: {base_name}")
        self.sub_label.setText(f"Размер: {size_mb:.1f} МБ | Готов к созданию субтитров")
        self.file_selected.emit(path)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎯 WordSync AI Studio — Субтитры слово в слово")
        self.resize(1080, 860)
        self.setStyleSheet(STUDIO_STYLE)

        self.current_file = None
        self.created_folder = None
        self.worker = None
        self.all_words = []  # List of dicts: {"word": ..., "start": ..., "end": ..., "prob": ...}
        self.all_segments = []

        # Player setup
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)

        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(18, 14, 18, 14)

        # Header
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("🎯 WordSync AI Studio")
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #58a6ff;")
        subtitle = QLabel("Автоматические субтитры слово в слово | Плеер с живым караоке-предпросмотром")
        subtitle.setStyleSheet("font-size: 13px; color: #8b949e;")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        # Check CUDA
        cuda_ok = is_cuda_usable()
        if cuda_ok:
            cuda_status = "⚡ GPU CUDA (NVIDIA RTX 3060 Ti) активен"
            badge_color = "#238636"
        else:
            cuda_status = "💻 Режим CPU (12 потоков Ryzen)"
            badge_color = "#1f6feb"

        badge = QLabel(cuda_status)
        badge.setStyleSheet(f"background-color: {badge_color}; color: white; padding: 6px 14px; border-radius: 12px; font-weight: bold; font-size: 12px;")
        header_layout.addWidget(badge)
        main_layout.addLayout(header_layout)

        # Splitter: Left panel (Settings & File), Right panel (Player & Word Table)
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background-color: #21262d; width: 3px; }")

        # LEFT PANEL
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 10, 0)
        left_layout.setSpacing(10)

        # Drop Zone
        self.drop_zone = DropZone()
        self.drop_zone.file_selected.connect(self.on_file_selected)
        left_layout.addWidget(self.drop_zone)

        # Presets Group
        presets_group = QGroupBox("✨ Режим распознавания")
        presets_layout = QVBoxLayout(presets_group)
        presets_layout.setSpacing(6)

        self.rb_music = QRadioButton("🎵 Песня / Музыка (Vocal Booster + Караоке)")
        self.rb_music.setChecked(True)
        self.rb_reels = QRadioButton("📱 Reels / Shorts / TikTok (1–2 слова на экран)")
        self.rb_speech = QRadioButton("🎬 Разговор / Подкаст (Предложениями)")

        self.btn_group_preset = QButtonGroup(self)
        self.btn_group_preset.addButton(self.rb_music, 1)
        self.btn_group_preset.addButton(self.rb_reels, 2)
        self.btn_group_preset.addButton(self.rb_speech, 3)

        self.rb_music.toggled.connect(self.on_preset_changed)
        self.rb_reels.toggled.connect(self.on_preset_changed)
        self.rb_speech.toggled.connect(self.on_preset_changed)

        presets_layout.addWidget(self.rb_music)
        presets_layout.addWidget(self.rb_reels)
        presets_layout.addWidget(self.rb_speech)
        left_layout.addWidget(presets_group)

        # Detailed Settings
        settings_group = QGroupBox("⚙ Параметры")
        settings_layout = QVBoxLayout(settings_group)
        settings_layout.setSpacing(8)

        # Model
        row_model = QHBoxLayout()
        row_model.addWidget(QLabel("Модель:"))
        self.combo_model = QComboBox()
        self.combo_model.addItem("small (Локальная, высокая точность)", "small")
        self.combo_model.addItem("base (Быстро для слабых ПК)", "base")
        self.combo_model.addItem("tiny (Мгновенно)", "tiny")
        self.combo_model.addItem("medium (Высочайшая точность)", "medium")
        row_model.addWidget(self.combo_model, stretch=1)
        settings_layout.addLayout(row_model)

        # Language
        row_lang = QHBoxLayout()
        row_lang.addWidget(QLabel("Язык:"))
        self.combo_lang = QComboBox()
        self.combo_lang.addItem("Автоопределение", "auto")
        self.combo_lang.addItem("Русский (Russian)", "ru")
        self.combo_lang.addItem("Английский (English)", "en")
        self.combo_lang.addItem("Казахский (Kazakh)", "kk")
        self.combo_lang.addItem("Украинский (Ukrainian)", "uk")
        row_lang.addWidget(self.combo_lang, stretch=1)
        settings_layout.addLayout(row_lang)

        # Device
        row_dev = QHBoxLayout()
        row_dev.addWidget(QLabel("Ускоритель:"))
        self.combo_dev = QComboBox()
        if cuda_ok:
            self.combo_dev.addItem("GPU (NVIDIA RTX CUDA)", "cuda")
            self.combo_dev.addItem("CPU (Процессор Ryzen)", "cpu")
        else:
            self.combo_dev.addItem("CPU (Многопоточный Ryzen)", "cpu")
            self.combo_dev.addItem("GPU (NVIDIA CUDA)", "cuda")
        row_dev.addWidget(self.combo_dev, stretch=1)
        settings_layout.addLayout(row_dev)

        # Words per chunk
        row_chunk = QHBoxLayout()
        row_chunk.addWidget(QLabel("Слов на строку:"))
        self.spin_chunk = QSpinBox()
        self.spin_chunk.setRange(1, 10)
        self.spin_chunk.setValue(1)
        row_chunk.addWidget(self.spin_chunk)
        settings_layout.addLayout(row_chunk)

        # Checkboxes
        self.chk_vocal = QCheckBox("🎤 Vocal Booster (очистка музыки и басов)")
        self.chk_vocal.setChecked(True)
        settings_layout.addWidget(self.chk_vocal)

        self.chk_burn = QCheckBox("🎬 Вшить субтитры в видео (MP4 Hardsub)")
        self.chk_burn.setChecked(False)
        settings_layout.addWidget(self.chk_burn)

        left_layout.addWidget(settings_group)

        # Start Button
        self.btn_start = QPushButton("⚡ СОЗДАТЬ СУБТИТРЫ СЛОВО В СЛОВО")
        self.btn_start.setEnabled(False)
        self.btn_start.setFixedHeight(48)
        self.btn_start.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #238636, stop:1 #2ea043);
                font-size: 14px;
                font-weight: 800;
                color: white;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2ea043, stop:1 #3fb950);
            }
            QPushButton:disabled {
                background: #21262d;
                color: #484f58;
            }
        """)
        self.btn_start.clicked.connect(self.start_transcription)
        left_layout.addWidget(self.btn_start)

        # Progress bar & status
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        left_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Ожидание файла...")
        self.status_label.setStyleSheet("color: #8b949e; font-size: 12px; font-weight: 500;")
        left_layout.addWidget(self.status_label)
        left_layout.addStretch()

        splitter.addWidget(left_widget)

        # RIGHT PANEL: Media Player + Karaoke Screen + Word Table
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(10, 0, 0, 0)
        right_layout.setSpacing(10)

        # Karaoke Preview Screen
        preview_box = QGroupBox("🎬 Интерактивный плеер и живое караоке-выделение")
        preview_box_layout = QVBoxLayout(preview_box)
        preview_box_layout.setSpacing(8)

        # Video Widget (or music visualizer banner)
        self.video_widget = QVideoWidget()
        self.video_widget.setFixedHeight(220)
        self.video_widget.setStyleSheet("background-color: #04060a; border-radius: 8px;")
        self.player.setVideoOutput(self.video_widget)
        preview_box_layout.addWidget(self.video_widget)

        # Live Karaoke Subtitle Display Banner
        self.lbl_karaoke_banner = QLabel("Здесь будет отображаться текст с подсветкой текущего слова...")
        self.lbl_karaoke_banner.setAlignment(Qt.AlignCenter)
        self.lbl_karaoke_banner.setFixedHeight(50)
        self.lbl_karaoke_banner.setStyleSheet("""
            QLabel {
                background-color: #0d1117;
                border: 1px solid #30363d;
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 17px;
                font-weight: bold;
                color: #f0f6fc;
            }
        """)
        preview_box_layout.addWidget(self.lbl_karaoke_banner)

        # Player Controls
        controls_layout = QHBoxLayout()
        self.btn_play = QPushButton("▶ Воспроизвести")
        self.btn_play.setEnabled(False)
        self.btn_play.clicked.connect(self.toggle_play)
        controls_layout.addWidget(self.btn_play)

        self.slider_pos = QSlider(Qt.Horizontal)
        self.slider_pos.setEnabled(False)
        self.slider_pos.sliderMoved.connect(self.on_seek)
        controls_layout.addWidget(self.slider_pos, stretch=1)

        self.lbl_time = QLabel("00:00 / 00:00")
        self.lbl_time.setStyleSheet("font-family: Consolas; color: #8b949e;")
        controls_layout.addWidget(self.lbl_time)

        preview_box_layout.addLayout(controls_layout)
        right_layout.addWidget(preview_box)

        # Player signal bindings
        self.player.positionChanged.connect(self.on_player_position_changed)
        self.player.durationChanged.connect(self.on_player_duration_changed)

        # Table of words
        table_box = QGroupBox("📝 Таблица распознанных слов (клик для перехода, двойной клик для правки)")
        table_layout = QVBoxLayout(table_box)
        table_layout.setSpacing(8)

        self.table_words = QTableWidget()
        self.table_words.setColumnCount(4)
        self.table_words.setHorizontalHeaderLabels(["Старт", "Конец", "Слово (можно править)", "Точность"])
        self.table_words.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_words.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_words.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table_words.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table_words.verticalHeader().setVisible(False)
        self.table_words.cellClicked.connect(self.on_table_cell_clicked)
        table_layout.addWidget(self.table_words)

        # Action Buttons Row
        action_row = QHBoxLayout()
        self.btn_open_folder = QPushButton("📂 Открыть папку")
        self.btn_open_folder.setEnabled(False)
        self.btn_open_folder.clicked.connect(self.open_result_folder)
        action_row.addWidget(self.btn_open_folder)

        self.btn_export_edited = QPushButton("💾 Сохранить субтитры")
        self.btn_export_edited.setEnabled(False)
        self.btn_export_edited.clicked.connect(self.save_edited_subtitles)
        action_row.addWidget(self.btn_export_edited)

        self.btn_copy_text = QPushButton("📋 Скопировать текст")
        self.btn_copy_text.setEnabled(False)
        self.btn_copy_text.clicked.connect(self.copy_transcription)
        action_row.addWidget(self.btn_copy_text)

        table_layout.addLayout(action_row)
        right_layout.addWidget(table_box)

        splitter.addWidget(right_widget)
        splitter.setSizes([380, 700])
        main_layout.addWidget(splitter)

    def on_preset_changed(self):
        if self.rb_music.isChecked():
            self.chk_vocal.setChecked(True)
            self.spin_chunk.setValue(1)
        elif self.rb_reels.isChecked():
            self.chk_vocal.setChecked(False)
            self.spin_chunk.setValue(2)
        elif self.rb_speech.isChecked():
            self.chk_vocal.setChecked(False)
            self.spin_chunk.setValue(5)

    def on_file_selected(self, path: str):
        self.current_file = path
        self.btn_start.setEnabled(True)
        self.status_label.setText(f"Файл готов: {os.path.basename(path)}")

        # Load into player
        self.player.setSource(QUrl.fromLocalFile(path))
        self.btn_play.setEnabled(True)
        self.slider_pos.setEnabled(True)

    def toggle_play(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            self.btn_play.setText("▶ Воспроизвести")
        else:
            self.player.play()
            self.btn_play.setText("⏸ Пауза")

    def on_seek(self, position: int):
        self.player.setPosition(position)

    def on_player_duration_changed(self, duration: int):
        self.slider_pos.setRange(0, duration)

    def on_player_position_changed(self, position: int):
        self.slider_pos.setValue(position)
        cur_sec = position // 1000
        dur_sec = self.player.duration() // 1000
        self.lbl_time.setText(f"{cur_sec//60:02d}:{cur_sec%60:02d} / {dur_sec//60:02d}:{dur_sec%60:02d}")

        pos_sec = position / 1000.0
        # Find active word and phrase
        active_idx = -1
        for idx, w in enumerate(self.all_words):
            if w["start"] <= pos_sec <= w["end"]:
                active_idx = idx
                break

        if active_idx != -1:
            active_word = self.all_words[active_idx]["word"]
            # Get surrounding words (phrase context)
            start_window = max(0, active_idx - 3)
            end_window = min(len(self.all_words), active_idx + 4)
            phrase_parts = []
            for i in range(start_window, end_window):
                w_text = self.all_words[i]["word"]
                if i == active_idx:
                    phrase_parts.append(f'<span style="color: #ffd700; font-size: 20px; text-decoration: underline;">{w_text}</span>')
                else:
                    phrase_parts.append(f'<span style="color: #c9d1d9;">{w_text}</span>')
            
            self.lbl_karaoke_banner.setText(" ".join(phrase_parts))
            self.table_words.selectRow(active_idx)

    def on_table_cell_clicked(self, row: int, col: int):
        if row < len(self.all_words):
            target_ms = int(self.all_words[row]["start"] * 1000)
            self.player.setPosition(target_ms)
            if self.player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
                self.player.play()
                self.btn_play.setText("⏸ Пауза")

    def start_transcription(self):
        if not self.current_file or not os.path.exists(self.current_file):
            QMessageBox.warning(self, "Ошибка", "Файл не выбран.")
            return

        self.btn_start.setEnabled(False)
        self.drop_zone.btn_browse.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.table_words.setRowCount(0)
        self.all_words.clear()
        self.all_segments.clear()
        self.btn_open_folder.setEnabled(False)
        self.btn_export_edited.setEnabled(False)
        self.btn_copy_text.setEnabled(False)

        model_name = self.combo_model.currentData()
        language = self.combo_lang.currentData()
        device = self.combo_dev.currentData()
        words_per_chunk = self.spin_chunk.value()
        vocal_boost = self.chk_vocal.isChecked()
        burn_video = self.chk_burn.isChecked()
        preset = "music" if self.rb_music.isChecked() else ("reels" if self.rb_reels.isChecked() else "speech")

        self.worker = TranscriptionWorker(
            file_path=self.current_file,
            model_name=model_name,
            language=language,
            device=device,
            preset=preset,
            vocal_boost=vocal_boost,
            burn_video=burn_video,
            words_per_chunk=words_per_chunk
        )

        self.worker.progress_signal.connect(self.on_worker_progress)
        self.worker.segment_signal.connect(self.on_worker_segment)
        self.worker.finished_signal.connect(self.on_worker_finished)
        self.worker.error_signal.connect(self.on_worker_error)
        self.worker.start()

    def on_worker_progress(self, ratio: float, message: str):
        pct = int(ratio * 100)
        self.progress_bar.setValue(pct)
        self.status_label.setText(f"{message} ({pct}%)")

    def on_worker_segment(self, seg: dict):
        self.all_segments.append(seg)
        words = seg.get("words", [])
        if words:
            for w in words:
                self.all_words.append(w)
                row = self.table_words.rowCount()
                self.table_words.insertRow(row)

                item_start = QTableWidgetItem(f"{w['start']:.2f}")
                item_start.setFlags(item_start.flags() & ~Qt.ItemIsEditable)

                item_end = QTableWidgetItem(f"{w['end']:.2f}")
                item_end.setFlags(item_end.flags() & ~Qt.ItemIsEditable)

                item_word = QTableWidgetItem(w["word"])
                item_word.setForeground(QColor("#f0f6fc"))
                f = item_word.font()
                f.setBold(True)
                item_word.setFont(f)

                item_prob = QTableWidgetItem(f"{int(w.get('probability', 1.0) * 100)}%")
                item_prob.setFlags(item_prob.flags() & ~Qt.ItemIsEditable)

                self.table_words.setItem(row, 0, item_start)
                self.table_words.setItem(row, 1, item_end)
                self.table_words.setItem(row, 2, item_word)
                self.table_words.setItem(row, 3, item_prob)
        else:
            row = self.table_words.rowCount()
            self.table_words.insertRow(row)
            self.table_words.setItem(row, 0, QTableWidgetItem(f"{seg['start']:.2f}"))
            self.table_words.setItem(row, 1, QTableWidgetItem(f"{seg['end']:.2f}"))
            self.table_words.setItem(row, 2, QTableWidgetItem(seg["text"]))
            self.table_words.setItem(row, 3, QTableWidgetItem("-"))

        self.table_words.scrollToBottom()

    def on_worker_finished(self, result: dict):
        self.btn_start.setEnabled(True)
        self.drop_zone.btn_browse.setEnabled(True)
        self.btn_open_folder.setEnabled(True)
        self.btn_export_edited.setEnabled(True)
        self.btn_copy_text.setEnabled(True)
        self.created_folder = result["folder"]

        file_list_str = "\n".join([f"• {os.path.basename(p)}" for p in result["created_files"].values()])
        self.status_label.setText("✔ Готово! Нажмите Play для проверки караоке-подсветки.")
        QMessageBox.information(
            self,
            "Субтитры успешно созданы!",
            f"Субтитры готовы и сохранены рядом с исходным файлом:\n\n{file_list_str}\n\nВы можете запустить встроенный плеер и проверить синхронизацию слов!"
        )

    def on_worker_error(self, err_msg: str):
        self.btn_start.setEnabled(True)
        self.drop_zone.btn_browse.setEnabled(True)
        self.status_label.setText(f"❌ Ошибка: {err_msg}")
        QMessageBox.critical(self, "Ошибка выполнения", f"Произошла ошибка:\n{err_msg}")

    def save_edited_subtitles(self):
        """Re-exports SRT and ASS using any edits made in the table by the user."""
        if not self.current_file or not self.all_words:
            return

        # Update word texts from table
        for r in range(min(self.table_words.rowCount(), len(self.all_words))):
            item = self.table_words.item(r, 2)
            if item:
                self.all_words[r]["word"] = item.text().strip()

        base_dir = os.path.dirname(self.current_file)
        base_name = os.path.splitext(os.path.basename(self.current_file))[0]

        # Re-save word-by-word SRT
        out_srt = os.path.join(base_dir, f"{base_name}_words_edited.srt")
        with open(out_srt, "w", encoding="utf-8") as f:
            for i, w in enumerate(self.all_words, 1):
                s = format_timestamp_srt(w["start"])
                e = format_timestamp_srt(w["end"])
                f.write(f"{i}\n{s} --> {e}\n{w['word']}\n\n")

        # Re-save ASS Karaoke
        out_ass = os.path.join(base_dir, f"{base_name}_tiktok_glow_edited.ass")
        SubtitleEngine.export_ass_tiktok_karaoke(self.all_segments, out_ass, title=base_name)

        QMessageBox.information(self, "Сохранено", f"Отредактированные субтитры успешно сохранены:\n• {os.path.basename(out_srt)}\n• {os.path.basename(out_ass)}")

    def open_result_folder(self):
        if self.created_folder and os.path.exists(self.created_folder):
            if sys.platform == "win32":
                os.startfile(self.created_folder)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", self.created_folder])
            else:
                subprocess.Popen(["xdg-open", self.created_folder])

    def copy_transcription(self):
        words = [w["word"] for w in self.all_words]
        text = " ".join(words)
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self.status_label.setText("Весь текст успешно скопирован в буфер обмена!")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
