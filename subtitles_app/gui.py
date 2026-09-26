import os
import sys
import subprocess
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QCheckBox, QProgressBar,
    QTextEdit, QFileDialog, QFrame, QMessageBox, QGroupBox, QSpinBox
)
from PySide6.QtCore import Qt, QThread, Signal, QMimeData, QUrl
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QFont, QIcon, QColor

try:
    from transcriber import SubtitleEngine, is_cuda_usable
except ImportError:
    from subtitles_app.transcriber import SubtitleEngine, is_cuda_usable

SUPPORTED_EXTENSIONS = {
    ".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".wmv", ".m4v",
    ".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac", ".wma", ".opus"
}

DARK_STYLE = """
QMainWindow {
    background-color: #12141a;
}
QWidget {
    color: #e2e8f0;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}
QGroupBox {
    border: 1px solid #2d3748;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 10px;
    font-weight: bold;
    color: #63b3ed;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}
QComboBox, QSpinBox {
    background-color: #1a202c;
    border: 1px solid #4a5568;
    border-radius: 6px;
    padding: 6px 10px;
    color: #edf2f7;
    min-height: 24px;
}
QComboBox:hover, QSpinBox:hover {
    border: 1px solid #63b3ed;
}
QComboBox::drop-down {
    border: none;
}
QCheckBox {
    spacing: 8px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #4a5568;
    background-color: #1a202c;
}
QCheckBox::indicator:checked {
    background-color: #3182ce;
    border-color: #63b3ed;
}
QProgressBar {
    border: 1px solid #2d3748;
    border-radius: 6px;
    text-align: center;
    background-color: #1a202c;
    color: #edf2f7;
    font-weight: bold;
    height: 22px;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3182ce, stop:1 #805ad5);
    border-radius: 5px;
}
QTextEdit {
    background-color: #1a202c;
    border: 1px solid #2d3748;
    border-radius: 8px;
    color: #cbd5e0;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 12px;
    padding: 8px;
}
QPushButton {
    background-color: #2b6cb0;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #3182ce;
}
QPushButton:pressed {
    background-color: #2c5282;
}
QPushButton:disabled {
    background-color: #2d3748;
    color: #718096;
}
"""

class TranscriptionWorker(QThread):
    progress_signal = Signal(float, str)
    segment_signal = Signal(dict)
    finished_signal = Signal(dict)
    error_signal = Signal(str)

    def __init__(self, file_path: str, model_name: str, language: str, device: str, 
                 mode: str, burn_video: bool, words_per_chunk: int):
        super().__init__()
        self.file_path = file_path
        self.model_name = model_name
        self.language = language
        self.device = device
        self.mode = mode
        self.burn_video = burn_video
        self.words_per_chunk = words_per_chunk

    def run(self):
        try:
            self.progress_signal.emit(0.02, "Инициализация AI модели...")
            engine = SubtitleEngine(model_name=self.model_name, device=self.device)
            
            def on_seg(seg):
                self.segment_signal.emit(seg)

            def on_prog(ratio, msg):
                self.progress_signal.emit(ratio, msg)

            segments = engine.transcribe(
                self.file_path,
                language=self.language,
                on_segment=on_seg,
                on_progress=on_prog
            )

            # Export files
            base_dir = os.path.dirname(self.file_path)
            base_name = os.path.splitext(os.path.basename(self.file_path))[0]
            created_files = {}

            # 1. Standard SRT
            if self.mode in ("all", "srt_standard"):
                srt_path = os.path.join(base_dir, f"{base_name}.srt")
                engine.export_srt_standard(segments, srt_path)
                created_files["srt"] = srt_path

            # 2. Word-by-word SRT
            if self.mode in ("all", "srt_words"):
                word_srt_path = os.path.join(base_dir, f"{base_name}_words.srt")
                engine.export_srt_word_by_word(segments, word_srt_path, words_per_chunk=self.words_per_chunk)
                created_files["srt_words"] = word_srt_path

            # 3. Karaoke ASS
            if self.mode in ("all", "ass_karaoke"):
                ass_path = os.path.join(base_dir, f"{base_name}_karaoke.ass")
                engine.export_ass_karaoke(segments, ass_path, title=base_name)
                created_files["ass"] = ass_path

            # 4. Text and WebVTT
            if self.mode == "all":
                vtt_path = os.path.join(base_dir, f"{base_name}.vtt")
                engine.export_vtt(segments, vtt_path)
                created_files["vtt"] = vtt_path

                txt_path = os.path.join(base_dir, f"{base_name}.txt")
                engine.export_txt(segments, txt_path, include_timestamps=False)
                created_files["txt"] = txt_path

            # 5. Burn to video if requested and it is a video file
            ext = os.path.splitext(self.file_path)[1].lower()
            if self.burn_video and ext in {".mp4", ".mkv", ".avi", ".mov", ".webm", ".m4v"}:
                self.progress_signal.emit(0.96, "Вшивание субтитров в видео (FFmpeg)...")
                # Prefer ass if exists, else word_srt, else srt
                sub_to_burn = created_files.get("ass") or created_files.get("srt_words") or created_files.get("srt")
                if sub_to_burn:
                    burned_video_path = os.path.join(base_dir, f"{base_name}_subtitled{ext}")
                    ok = engine.burn_subtitles_to_video(self.file_path, sub_to_burn, burned_video_path)
                    if ok:
                        created_files["burned_video"] = burned_video_path

            self.progress_signal.emit(1.0, "Готово!")
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
                border: 2px dashed #4a5568;
                border-radius: 12px;
                background-color: #171923;
            }
            QFrame:hover {
                border-color: #63b3ed;
                background-color: #1a202c;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 25, 20, 25)
        layout.setAlignment(Qt.AlignCenter)

        self.icon_label = QLabel("📥")
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setStyleSheet("font-size: 40px; background: transparent; border: none;")
        layout.addWidget(self.icon_label)

        self.text_label = QLabel("Перетащите видео или музыку сюда\nили нажмите кнопку для выбора")
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #edf2f7; background: transparent; border: none;")
        layout.addWidget(self.text_label)

        self.sub_label = QLabel("Поддерживает MP4, MKV, MOV, MP3, WAV, FLAC, OGG, AAC и др.")
        self.sub_label.setAlignment(Qt.AlignCenter)
        self.sub_label.setStyleSheet("font-size: 11px; color: #a0aec0; background: transparent; border: none;")
        layout.addWidget(self.sub_label)

        self.btn_browse = QPushButton("Выбрать файл на диске")
        self.btn_browse.setStyleSheet("""
            QPushButton {
                background-color: #3182ce;
                padding: 6px 20px;
                font-size: 13px;
                margin-top: 8px;
            }
            QPushButton:hover {
                background-color: #4299e1;
            }
        """)
        self.btn_browse.clicked.connect(self.browse_file)
        layout.addWidget(self.btn_browse, alignment=Qt.AlignCenter)

    def browse_file(self):
        filter_str = "Медиафайлы (*.mp4 *.mkv *.avi *.mov *.webm *.mp3 *.wav *.ogg *.flac *.m4a *.aac);;Все файлы (*.*)"
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите видео или музыку", "", filter_str)
        if file_path:
            self.set_file(file_path)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                ext = os.path.splitext(urls[0].toLocalFile())[1].lower()
                if ext in SUPPORTED_EXTENSIONS or ext == "":
                    event.acceptProposedAction()
                    self.setStyleSheet("""
                        QFrame {
                            border: 2px dashed #48bb78;
                            border-radius: 12px;
                            background-color: #1c4532;
                        }
                    """)
                    return
        event.ignore()

    def dragLeaveEvent(self, event):
        self.setStyleSheet("""
            QFrame {
                border: 2px dashed #4a5568;
                border-radius: 12px;
                background-color: #171923;
            }
            QFrame:hover {
                border-color: #63b3ed;
                background-color: #1a202c;
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
        self.text_label.setText(f"Выбран: {base_name}")
        self.sub_label.setText(f"Размер: {size_mb:.1f} МБ | Путь: {path}")
        self.file_selected.emit(path)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI WordSync Subtitles — Субтитры слово в слово")
        self.resize(850, 750)
        self.setStyleSheet(DARK_STYLE)

        self.current_file = None
        self.created_folder = None
        self.worker = None

        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(18, 18, 18, 18)

        # Header
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("🎯 AI WordSync Subtitles")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #63b3ed;")
        subtitle = QLabel("Высокоточное распознавание речи со словесными таймингами (слово в слово)")
        subtitle.setStyleSheet("font-size: 12px; color: #a0aec0;")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        # Check CUDA
        cuda_functional = is_cuda_usable()
        if cuda_functional:
            cuda_status = "⚡ GPU CUDA (NVIDIA RTX 3060 Ti) активен"
            badge_color = "#38a169"
        else:
            cuda_status = "💻 Режим CPU (Оптимизирован)"
            badge_color = "#3182ce"

        badge = QLabel(cuda_status)
        badge.setStyleSheet(f"background-color: {badge_color}; color: white; padding: 4px 10px; border-radius: 12px; font-weight: bold;")
        header_layout.addWidget(badge)
        main_layout.addLayout(header_layout)

        # Drop Zone
        self.drop_zone = DropZone()
        self.drop_zone.file_selected.connect(self.on_file_selected)
        main_layout.addWidget(self.drop_zone)

        # Settings Group
        settings_group = QGroupBox("⚙ Настройки генерации")
        settings_layout = QVBoxLayout(settings_group)
        settings_layout.setSpacing(10)

        row1 = QHBoxLayout()
        # Mode
        lbl_mode = QLabel("Формат субтитров:")
        self.combo_mode = QComboBox()
        self.combo_mode.addItem("Все форматы сразу (SRT, Караоке ASS, TXT, VTT)", "all")
        self.combo_mode.addItem("Слово в слово (по 1 слову, TikTok/Reels)", "srt_words")
        self.combo_mode.addItem("Караоке ASS (подсветка произносимого слова)", "ass_karaoke")
        self.combo_mode.addItem("Стандартные предложения (обычный SRT)", "srt_standard")
        row1.addWidget(lbl_mode)
        row1.addWidget(self.combo_mode, stretch=2)

        # Words per chunk (for word srt)
        lbl_chunk = QLabel("Слов на строку:")
        self.spin_chunk = QSpinBox()
        self.spin_chunk.setRange(1, 10)
        self.spin_chunk.setValue(1)
        row1.addWidget(lbl_chunk)
        row1.addWidget(self.spin_chunk)

        settings_layout.addLayout(row1)

        row2 = QHBoxLayout()
        # Language
        lbl_lang = QLabel("Язык аудио:")
        self.combo_lang = QComboBox()
        self.combo_lang.addItem("Автоопределение (любой язык)", "auto")
        self.combo_lang.addItem("Русский (Russian)", "ru")
        self.combo_lang.addItem("Английский (English)", "en")
        self.combo_lang.addItem("Казахский (Kazakh)", "kk")
        self.combo_lang.addItem("Украинский (Ukrainian)", "uk")
        self.combo_lang.addItem("Немецкий (German)", "de")
        self.combo_lang.addItem("Испанский (Spanish)", "es")
        self.combo_lang.addItem("Французский (French)", "fr")
        self.combo_lang.addItem("Китайский (Chinese)", "zh")
        row2.addWidget(lbl_lang)
        row2.addWidget(self.combo_lang, stretch=1)

        # Model
        lbl_model = QLabel("AI Модель:")
        self.combo_model = QComboBox()
        self.combo_model.addItem("small (Рекомендуется — быстро и высокая точность)", "small")
        self.combo_model.addItem("medium (Высшая точность, чуть дольше)", "medium")
        self.combo_model.addItem("large-v3-turbo (Турбо-максимум)", "large-v3-turbo")
        self.combo_model.addItem("base (Очень быстро)", "base")
        self.combo_model.addItem("tiny (Сверхбыстро, для слабых ПК)", "tiny")
        row2.addWidget(lbl_model)
        row2.addWidget(self.combo_model, stretch=2)

        # Device
        lbl_dev = QLabel("Устройство:")
        self.combo_dev = QComboBox()
        if cuda_functional:
            self.combo_dev.addItem("Авто (GPU CUDA)", "auto")
            self.combo_dev.addItem("GPU (NVIDIA CUDA)", "cuda")
            self.combo_dev.addItem("CPU (Процессор)", "cpu")
        else:
            self.combo_dev.addItem("CPU (Быстрый процессорный int8)", "cpu")
            self.combo_dev.addItem("Авто", "auto")
            self.combo_dev.addItem("GPU (NVIDIA CUDA)", "cuda")
        row2.addWidget(lbl_dev)
        row2.addWidget(self.combo_dev, stretch=1)

        settings_layout.addLayout(row2)

        # Row 3 - Hardsub option
        row3 = QHBoxLayout()
        self.chk_burn = QCheckBox("Вшить субтитры прямо в видеопоток (Hardsub MP4 с помощью FFmpeg)")
        self.chk_burn.setChecked(False)
        row3.addWidget(self.chk_burn)
        settings_layout.addLayout(row3)

        main_layout.addWidget(settings_group)

        # Action Button & Progress
        self.btn_start = QPushButton("⚡ Создать субтитры слово в слово")
        self.btn_start.setEnabled(False)
        self.btn_start.setFixedHeight(45)
        self.btn_start.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3182ce, stop:1 #805ad5);
                font-size: 15px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4299e1, stop:1 #9f7aea);
            }
            QPushButton:disabled {
                background: #2d3748;
                color: #718096;
            }
        """)
        self.btn_start.clicked.connect(self.start_transcription)
        main_layout.addWidget(self.btn_start)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Ожидание файла...")
        self.status_label.setStyleSheet("color: #a0aec0; font-size: 12px;")
        main_layout.addWidget(self.status_label)

        # Results & Real-time preview
        preview_group = QGroupBox("📝 Распознанный текст в реальном времени (со словесными таймингами)")
        preview_layout = QVBoxLayout(preview_group)
        self.text_preview = QTextEdit()
        self.text_preview.setReadOnly(True)
        self.text_preview.setPlaceholderText("Здесь будут в реальном времени отображаться распознанные слова с точным таймингом...")
        preview_layout.addWidget(self.text_preview)

        # Action buttons after completion
        btns_row = QHBoxLayout()
        self.btn_open_folder = QPushButton("📂 Открыть папку с результатом")
        self.btn_open_folder.setEnabled(False)
        self.btn_open_folder.clicked.connect(self.open_result_folder)
        btns_row.addWidget(self.btn_open_folder)

        self.btn_copy_text = QPushButton("📋 Скопировать весь текст")
        self.btn_copy_text.setEnabled(False)
        self.btn_copy_text.clicked.connect(self.copy_transcription)
        btns_row.addWidget(self.btn_copy_text)

        preview_layout.addLayout(btns_row)
        main_layout.addWidget(preview_group)

    def on_file_selected(self, path: str):
        self.current_file = path
        self.btn_start.setEnabled(True)
        self.status_label.setText(f"Готов к обработке: {os.path.basename(path)}")

    def start_transcription(self):
        if not self.current_file or not os.path.exists(self.current_file):
            QMessageBox.warning(self, "Ошибка", "Файл не выбран или не существует.")
            return

        self.btn_start.setEnabled(False)
        self.drop_zone.btn_browse.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.text_preview.clear()
        self.btn_open_folder.setEnabled(False)
        self.btn_copy_text.setEnabled(False)

        model_name = self.combo_model.currentData()
        language = self.combo_lang.currentData()
        device = self.combo_dev.currentData()
        mode = self.combo_mode.currentData()
        burn_video = self.chk_burn.isChecked()
        words_per_chunk = self.spin_chunk.value()

        self.worker = TranscriptionWorker(
            file_path=self.current_file,
            model_name=model_name,
            language=language,
            device=device,
            mode=mode,
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
        # Format words cleanly
        words = seg.get("words", [])
        if words:
            lines = []
            for w in words:
                start_s = f"{w['start']:.2f}s"
                end_s = f"{w['end']:.2f}s"
                lines.append(f"[{start_s} -> {end_s}] {w['word']}")
            self.text_preview.append("\n".join(lines))
        else:
            self.text_preview.append(f"[{seg['start']:.2f}s -> {seg['end']:.2f}s] {seg['text']}")
        
        # Scroll to bottom
        cursor = self.text_preview.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.text_preview.setTextCursor(cursor)

    def on_worker_finished(self, result: dict):
        self.btn_start.setEnabled(True)
        self.drop_zone.btn_browse.setEnabled(True)
        self.btn_open_folder.setEnabled(True)
        self.btn_copy_text.setEnabled(True)
        self.created_folder = result["folder"]

        file_list_str = "\n".join([f"• {os.path.basename(p)}" for p in result["created_files"].values()])
        self.status_label.setText("✔ Успешно завершено! Файлы сохранены рядом с исходником.")
        QMessageBox.information(
            self,
            "Готово!",
            f"Субтитры успешно созданы и сохранены!\n\nСозданные файлы:\n{file_list_str}"
        )

    def on_worker_error(self, err_msg: str):
        self.btn_start.setEnabled(True)
        self.drop_zone.btn_browse.setEnabled(True)
        self.status_label.setText(f"❌ Ошибка: {err_msg}")
        QMessageBox.critical(self, "Ошибка выполнения", f"Произошла ошибка при обработке:\n{err_msg}")

    def open_result_folder(self):
        if self.created_folder and os.path.exists(self.created_folder):
            if sys.platform == "win32":
                os.startfile(self.created_folder)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", self.created_folder])
            else:
                subprocess.Popen(["xdg-open", self.created_folder])

    def copy_transcription(self):
        text = self.text_preview.toPlainText()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self.status_label.setText("Текст скопирован в буфер обмена!")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
