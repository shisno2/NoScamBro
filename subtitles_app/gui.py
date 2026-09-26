import os
import sys
import subprocess
import time
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QCheckBox, QProgressBar,
    QTextEdit, QFileDialog, QFrame, QMessageBox, QGroupBox, QSpinBox,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView, QRadioButton, QButtonGroup
)
from PySide6.QtCore import Qt, QThread, Signal, QMimeData, QUrl, QTimer
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QFont, QColor, QPalette

try:
    from transcriber import SubtitleEngine, is_cuda_usable
except ImportError:
    from subtitles_app.transcriber import SubtitleEngine, is_cuda_usable

SUPPORTED_EXTENSIONS = {
    ".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".wmv", ".m4v",
    ".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac", ".wma", ".opus"
}

PREMIUM_STYLE = """
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
QComboBox QAbstractItemView {
    background-color: #161b22;
    border: 1px solid #30363d;
    selection-background-color: #1f6feb;
    selection-color: white;
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
QTextEdit, QTableWidget {
    background-color: #0d1117;
    border: 1px solid #30363d;
    border-radius: 8px;
    color: #c9d1d9;
    font-family: 'Consolas', monospace;
    font-size: 13px;
    padding: 8px;
}
QHeaderView::section {
    background-color: #161b22;
    color: #8b949e;
    padding: 6px;
    border: none;
    border-bottom: 1px solid #30363d;
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
"""

class TranscriptionWorker(QThread):
    progress_signal = Signal(float, str)
    segment_signal = Signal(dict)
    finished_signal = Signal(dict)
    error_signal = Signal(str)

    def __init__(self, file_path: str, model_name: str, language: str, device: str, 
                 preset: str, vocal_boost: bool, mode: str, burn_video: bool, words_per_chunk: int):
        super().__init__()
        self.file_path = file_path
        self.model_name = model_name
        self.language = language
        self.device = device
        self.preset = preset
        self.vocal_boost = vocal_boost
        self.mode = mode
        self.burn_video = burn_video
        self.words_per_chunk = words_per_chunk

    def run(self):
        try:
            self.progress_signal.emit(0.02, "Запуск движка искусственного интеллекта...")
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
                burned_video_path = os.path.join(base_dir, f"{base_name}_with_subs{ext}")
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
        layout.setContentsMargins(25, 30, 25, 30)
        layout.setAlignment(Qt.AlignCenter)

        self.icon_label = QLabel("🎵")
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setStyleSheet("font-size: 48px; background: transparent; border: none;")
        layout.addWidget(self.icon_label)

        self.text_label = QLabel("Перетащите любую песню, музыку или видео сюда")
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #f0f6fc; background: transparent; border: none;")
        layout.addWidget(self.text_label)

        self.sub_label = QLabel("Сверхточное распознавание текста слово в слово | Поддерживает MP3, WAV, MP4, MKV, FLAC...")
        self.sub_label.setAlignment(Qt.AlignCenter)
        self.sub_label.setStyleSheet("font-size: 12px; color: #8b949e; background: transparent; border: none; margin-top: 4px;")
        layout.addWidget(self.sub_label)

        self.btn_browse = QPushButton("📁 Выбрать файл на компьютере")
        self.btn_browse.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1f6feb, stop:1 #388bfd);
                color: white;
                padding: 8px 24px;
                font-size: 13px;
                font-weight: bold;
                border-radius: 8px;
                margin-top: 12px;
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
        self.text_label.setText(f"Загружен: {base_name}")
        self.sub_label.setText(f"Размер: {size_mb:.1f} МБ | Готов к идеальному распознаванию")
        self.file_selected.emit(path)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎯 WordSync AI — Сверхточные субтитры слово в слово")
        self.resize(920, 800)
        self.setStyleSheet(PREMIUM_STYLE)

        self.current_file = None
        self.created_folder = None
        self.worker = None

        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(20, 18, 20, 18)

        # Header
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("🎯 WordSync AI: Субтитры слово в слово")
        title.setStyleSheet("font-size: 22px; font-weight: 800; color: #58a6ff;")
        subtitle = QLabel("Профессиональное распознавание песен и видео | Без глюков, повторов и пропусков")
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

        # Drop Zone
        self.drop_zone = DropZone()
        self.drop_zone.file_selected.connect(self.on_file_selected)
        main_layout.addWidget(self.drop_zone)

        # Presets Bar
        presets_group = QGroupBox("✨ Режим обработки (выберите подходящий сценарий)")
        presets_layout = QHBoxLayout(presets_group)
        presets_layout.setContentsMargins(16, 12, 16, 12)

        self.rb_music = QRadioButton("🎵 Песня / Музыка (Усиление вокала + Караоке)")
        self.rb_music.setChecked(True)
        self.rb_reels = QRadioButton("📱 Reels / Shorts / TikTok (По 1-2 слова, динамично)")
        self.rb_speech = QRadioButton("🎬 Разговор / Подкаст / Кино (Классические фразы)")

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
        main_layout.addWidget(presets_group)

        # Detailed Settings
        settings_group = QGroupBox("⚙ Тонкие настройки качества")
        settings_layout = QVBoxLayout(settings_group)
        settings_layout.setSpacing(10)

        row1 = QHBoxLayout()
        # Model
        lbl_model = QLabel("AI Модель:")
        self.combo_model = QComboBox()
        self.combo_model.addItem("medium (Высочайшая точность — рекомендуется для песен)", "medium")
        self.combo_model.addItem("small (Быстро и качественно)", "small")
        self.combo_model.addItem("large-v3-turbo (Максимальное качество)", "large-v3-turbo")
        self.combo_model.addItem("base (Быстро для слабых ПК)", "base")
        self.combo_model.addItem("tiny (Сверхбыстро)", "tiny")
        row1.addWidget(lbl_model)
        row1.addWidget(self.combo_model, stretch=2)

        # Language
        lbl_lang = QLabel("Язык:")
        self.combo_lang = QComboBox()
        self.combo_lang.addItem("Автоопределение (любой язык)", "auto")
        self.combo_lang.addItem("Русский (Russian)", "ru")
        self.combo_lang.addItem("Английский (English)", "en")
        self.combo_lang.addItem("Казахский (Kazakh)", "kk")
        self.combo_lang.addItem("Украинский (Ukrainian)", "uk")
        row1.addWidget(lbl_lang)
        row1.addWidget(self.combo_lang, stretch=1)

        # Device
        lbl_dev = QLabel("Устройство:")
        self.combo_dev = QComboBox()
        if cuda_ok:
            self.combo_dev.addItem("GPU (NVIDIA RTX CUDA float16)", "cuda")
            self.combo_dev.addItem("CPU (Процессор)", "cpu")
        else:
            self.combo_dev.addItem("CPU (Многопоточный процессор)", "cpu")
            self.combo_dev.addItem("GPU (NVIDIA CUDA)", "cuda")
        row1.addWidget(lbl_dev)
        row1.addWidget(self.combo_dev, stretch=1)

        settings_layout.addLayout(row1)

        row2 = QHBoxLayout()
        # Words per chunk
        lbl_chunk = QLabel("Слов на строку (для Shorts/Reels):")
        self.spin_chunk = QSpinBox()
        self.spin_chunk.setRange(1, 10)
        self.spin_chunk.setValue(1)
        row2.addWidget(lbl_chunk)
        row2.addWidget(self.spin_chunk)

        # Vocal boost toggle
        self.chk_vocal = QCheckBox("🎤 Vocal Booster: подавление громких битов и усиление голоса")
        self.chk_vocal.setChecked(True)
        row2.addWidget(self.chk_vocal, stretch=2)

        # Hardsub checkbox
        self.chk_burn = QCheckBox("🎬 Вшить субтитры прямо в видеофайл (MP4)")
        self.chk_burn.setChecked(False)
        row2.addWidget(self.chk_burn)

        settings_layout.addLayout(row2)
        main_layout.addWidget(settings_group)

        # Start Button
        self.btn_start = QPushButton("⚡ СОЗДАТЬ СУБТИТРЫ СЛОВО В СЛОВО")
        self.btn_start.setEnabled(False)
        self.btn_start.setFixedHeight(48)
        self.btn_start.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #238636, stop:1 #2ea043);
                font-size: 15px;
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
        main_layout.addWidget(self.btn_start)

        # Progress bar & status
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Перетащите медиафайл для начала...")
        self.status_label.setStyleSheet("color: #8b949e; font-size: 13px; font-weight: 500;")
        main_layout.addWidget(self.status_label)

        # Live Results Preview Table
        preview_group = QGroupBox("📝 Распознанные слова в реальном времени с точнейшим таймингом")
        preview_layout = QVBoxLayout(preview_group)

        self.table_words = QTableWidget()
        self.table_words.setColumnCount(4)
        self.table_words.setHorizontalHeaderLabels(["Начало", "Конец", "Слово", "Точность"])
        self.table_words.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table_words.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_words.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table_words.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table_words.verticalHeader().setVisible(False)
        preview_layout.addWidget(self.table_words)

        # Bottom buttons
        btns_row = QHBoxLayout()
        self.btn_open_folder = QPushButton("📂 Открыть папку с файлами субтитров")
        self.btn_open_folder.setEnabled(False)
        self.btn_open_folder.setStyleSheet("padding: 8px 20px; font-weight: bold;")
        self.btn_open_folder.clicked.connect(self.open_result_folder)
        btns_row.addWidget(self.btn_open_folder)

        self.btn_copy_text = QPushButton("📋 Скопировать весь текст (текст песни / субтитры)")
        self.btn_copy_text.setEnabled(False)
        self.btn_copy_text.clicked.connect(self.copy_transcription)
        btns_row.addWidget(self.btn_copy_text)

        preview_layout.addLayout(btns_row)
        main_layout.addWidget(preview_group)

    def on_preset_changed(self):
        if self.rb_music.isChecked():
            self.chk_vocal.setChecked(True)
            self.spin_chunk.setValue(1)
            self.combo_model.setCurrentIndex(0)  # medium
        elif self.rb_reels.isChecked():
            self.chk_vocal.setChecked(False)
            self.spin_chunk.setValue(2)
        elif self.rb_speech.isChecked():
            self.chk_vocal.setChecked(False)
            self.spin_chunk.setValue(5)

    def on_file_selected(self, path: str):
        self.current_file = path
        self.btn_start.setEnabled(True)
        self.status_label.setText(f"Файл готов к обработке: {os.path.basename(path)}")

    def start_transcription(self):
        if not self.current_file or not os.path.exists(self.current_file):
            QMessageBox.warning(self, "Ошибка", "Файл не выбран.")
            return

        self.btn_start.setEnabled(False)
        self.drop_zone.btn_browse.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.table_words.setRowCount(0)
        self.btn_open_folder.setEnabled(False)
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
            mode="all",
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
        words = seg.get("words", [])
        if words:
            for w in words:
                row = self.table_words.rowCount()
                self.table_words.insertRow(row)

                start_item = QTableWidgetItem(f"{w['start']:.2f} с")
                end_item = QTableWidgetItem(f"{w['end']:.2f} с")
                word_item = QTableWidgetItem(w["word"])
                prob_item = QTableWidgetItem(f"{int(w['probability'] * 100)}%")

                # Style
                word_item.setForeground(QColor("#f0f6fc"))
                font = word_item.font()
                font.setBold(True)
                word_item.setFont(font)

                self.table_words.setItem(row, 0, start_item)
                self.table_words.setItem(row, 1, end_item)
                self.table_words.setItem(row, 2, word_item)
                self.table_words.setItem(row, 3, prob_item)
        else:
            row = self.table_words.rowCount()
            self.table_words.insertRow(row)
            self.table_words.setItem(row, 0, QTableWidgetItem(f"{seg['start']:.2f} с"))
            self.table_words.setItem(row, 1, QTableWidgetItem(f"{seg['end']:.2f} с"))
            self.table_words.setItem(row, 2, QTableWidgetItem(seg["text"]))
            self.table_words.setItem(row, 3, QTableWidgetItem("-"))

        self.table_words.scrollToBottom()

    def on_worker_finished(self, result: dict):
        self.btn_start.setEnabled(True)
        self.drop_zone.btn_browse.setEnabled(True)
        self.btn_open_folder.setEnabled(True)
        self.btn_copy_text.setEnabled(True)
        self.created_folder = result["folder"]

        file_list_str = "\n".join([f"• {os.path.basename(p)}" for p in result["created_files"].values()])
        self.status_label.setText("✔ Успешно завершено! Созданы все форматы субтитров.")
        QMessageBox.information(
            self,
            "Готово!",
            f"Субтитры успешно созданы с высочайшей точностью!\n\nСохранённые файлы в папке с файлом:\n{file_list_str}"
        )

    def on_worker_error(self, err_msg: str):
        self.btn_start.setEnabled(True)
        self.drop_zone.btn_browse.setEnabled(True)
        self.status_label.setText(f"❌ Ошибка: {err_msg}")
        QMessageBox.critical(self, "Ошибка выполнения", f"Произошла ошибка:\n{err_msg}")

    def open_result_folder(self):
        if self.created_folder and os.path.exists(self.created_folder):
            if sys.platform == "win32":
                os.startfile(self.created_folder)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", self.created_folder])
            else:
                subprocess.Popen(["xdg-open", self.created_folder])

    def copy_transcription(self):
        rows = self.table_words.rowCount()
        words_list = []
        for r in range(rows):
            item = self.table_words.item(r, 2)
            if item:
                words_list.append(item.text())
        full_text = " ".join(words_list)
        if full_text:
            clipboard = QApplication.clipboard()
            clipboard.setText(full_text)
            self.status_label.setText("Текст скопирован в буфер обмена!")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
