import os
import sys
import ssl
import subprocess
import time
from typing import List, Dict, Any, Callable, Optional

# Bypass SSL errors (e.g., self-signed certificates from antivirus, Russian root CAs, or proxy)
try:
    ssl._create_default_https_context = ssl._create_unverified_context
except AttributeError:
    pass

os.environ["PYTHONHTTPSVERIFY"] = "0"
os.environ["CURL_CA_BUNDLE"] = ""
os.environ["REQUESTS_CA_BUNDLE"] = ""
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

try:
    import urllib3
    urllib3.disable_warnings()
except Exception:
    pass

from faster_whisper import WhisperModel

def format_timestamp_srt(seconds: float) -> str:
    """Format seconds into SRT timestamp HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis >= 1000:
        secs += 1
        millis = 0
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def format_timestamp_vtt(seconds: float) -> str:
    """Format seconds into WebVTT timestamp HH:MM:SS.mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis >= 1000:
        secs += 1
        millis = 0
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"

def format_timestamp_ass(seconds: float) -> str:
    """Format seconds into ASS timestamp H:MM:SS.cc (centiseconds)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int(round((seconds - int(seconds)) * 100))
    if centis >= 100:
        secs += 1
        centis = 0
    return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"

class SubtitleEngine:
    def __init__(self, model_name: str = "small", device: str = "auto", compute_type: str = "default"):
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type
        self.model: Optional[WhisperModel] = None

    def load_model(self, on_progress: Optional[Callable[[str], None]] = None):
        if on_progress:
            on_progress(f"Загрузка модели '{self.model_name}'...")
        
        # Determine device
        device = self.device
        compute_type = self.compute_type
        if device == "auto":
            try:
                import ctranslate2
                if ctranslate2.get_cuda_device_count() > 0:
                    device = "cuda"
                    compute_type = "float16"
                else:
                    device = "cpu"
                    compute_type = "int8"
            except Exception:
                device = "cpu"
                compute_type = "int8"
        elif device == "cuda" and compute_type == "default":
            compute_type = "float16"
        elif device == "cpu" and compute_type == "default":
            compute_type = "int8"

        self.model = WhisperModel(
            self.model_name,
            device=device,
            compute_type=compute_type
        )
        if on_progress:
            on_progress(f"Модель готова ({device.upper()}, {compute_type}).")

    def transcribe(
        self,
        media_path: str,
        language: Optional[str] = None,
        on_segment: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_progress: Optional[Callable[[float, str], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        Transcribes the file with word-level timestamps.
        Returns a list of segment dicts with 'start', 'end', 'text', 'words'.
        """
        if self.model is None:
            self.load_model(lambda msg: on_progress(0.05, msg) if on_progress else None)

        if on_progress:
            on_progress(0.1, "Начало распознавания речи (слово в слово)...")

        # Run transcription with word timestamps enabled
        # vad_filter removes long silences and music-only hallucinations
        segments_gen, info = self.model.transcribe(
            media_path,
            language=language if language and language != "auto" else None,
            word_timestamps=True,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=400)
        )

        total_duration = info.duration if info and info.duration > 0 else 1.0
        results = []

        for seg in segments_gen:
            words_data = []
            if seg.words:
                for w in seg.words:
                    words_data.append({
                        "word": w.word.strip(),
                        "start": w.start,
                        "end": w.end,
                        "probability": w.probability
                    })

            seg_data = {
                "id": seg.id,
                "start": seg.start,
                "end": seg.end,
                "text": seg.text.strip(),
                "words": words_data
            }
            results.append(seg_data)

            if on_segment:
                on_segment(seg_data)

            if on_progress and total_duration > 0:
                progress = min(0.1 + 0.85 * (seg.end / total_duration), 0.95)
                on_progress(progress, f"Распознано: {seg.end:.1f} сек / {total_duration:.1f} сек")

        if on_progress:
            on_progress(0.98, "Формирование файлов субтитров...")

        return results

    @staticmethod
    def export_srt_standard(segments: List[Dict[str, Any]], output_path: str):
        """Standard SRT by phrases/sentences"""
        with open(output_path, "w", encoding="utf-8") as f:
            for idx, seg in enumerate(segments, 1):
                start = format_timestamp_srt(seg["start"])
                end = format_timestamp_srt(seg["end"])
                text = seg["text"]
                f.write(f"{idx}\n{start} --> {end}\n{text}\n\n")

    @staticmethod
    def export_srt_word_by_word(segments: List[Dict[str, Any]], output_path: str, words_per_chunk: int = 1):
        """
        Word-by-word SRT for TikTok / Shorts / Reels style.
        Each word or small group of words has exact timing.
        """
        counter = 1
        with open(output_path, "w", encoding="utf-8") as f:
            for seg in segments:
                words = seg.get("words", [])
                if not words:
                    # Fallback to segment if words empty
                    start = format_timestamp_srt(seg["start"])
                    end = format_timestamp_srt(seg["end"])
                    f.write(f"{counter}\n{start} --> {end}\n{seg['text']}\n\n")
                    counter += 1
                    continue

                for i in range(0, len(words), words_per_chunk):
                    chunk = words[i:i + words_per_chunk]
                    chunk_text = " ".join(w["word"] for w in chunk)
                    start = format_timestamp_srt(chunk[0]["start"])
                    end = format_timestamp_srt(chunk[-1]["end"])
                    f.write(f"{counter}\n{start} --> {end}\n{chunk_text}\n\n")
                    counter += 1

    @staticmethod
    def export_vtt(segments: List[Dict[str, Any]], output_path: str):
        """WebVTT format"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("WEBVTT\n\n")
            for idx, seg in enumerate(segments, 1):
                start = format_timestamp_vtt(seg["start"])
                end = format_timestamp_vtt(seg["end"])
                text = seg["text"]
                f.write(f"{idx}\n{start} --> {end}\n{text}\n\n")

    @staticmethod
    def export_ass_karaoke(segments: List[Dict[str, Any]], output_path: str, title: str = "Subtitles"):
        """
        Advanced SubStation Alpha with karaoke effect (highlights each word as it is spoken).
        Works in VLC, MPV, Aegisub, Premiere, CapCut, etc.
        """
        header = f"""[Script Info]
Title: {title}
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: None
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Karaoke,Montserrat,58,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,3.5,2,2,40,40,70,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(header)
            for seg in segments:
                words = seg.get("words", [])
                if not words:
                    start_str = format_timestamp_ass(seg["start"])
                    end_str = format_timestamp_ass(seg["end"])
                    f.write(f"Dialogue: 0,{start_str},{end_str},Karaoke,,0,0,0,,{seg['text']}\n")
                    continue

                start_str = format_timestamp_ass(seg["start"])
                end_str = format_timestamp_ass(seg["end"])

                karaoke_line = ""
                for w in words:
                    # Duration in centiseconds
                    duration_cs = max(1, int(round((w["end"] - w["start"]) * 100)))
                    word_clean = w["word"].replace("{", "").replace("}", "")
                    karaoke_line += f"{{\\k{duration_cs}}}{word_clean} "

                f.write(f"Dialogue: 0,{start_str},{end_str},Karaoke,,0,0,0,,{karaoke_line.strip()}\n")

    @staticmethod
    def export_txt(segments: List[Dict[str, Any]], output_path: str, include_timestamps: bool = False):
        """Plain text export"""
        with open(output_path, "w", encoding="utf-8") as f:
            for seg in segments:
                if include_timestamps:
                    time_str = f"[{format_timestamp_srt(seg['start'])} --> {format_timestamp_srt(seg['end'])}] "
                    f.write(f"{time_str}{seg['text']}\n")
                else:
                    f.write(f"{seg['text']}\n")

    @staticmethod
    def burn_subtitles_to_video(video_path: str, srt_or_ass_path: str, output_video_path: str) -> bool:
        """Uses FFmpeg to burn subtitles directly onto the video."""
        try:
            # Escape path for ffmpeg filter syntax
            escaped_sub = srt_or_ass_path.replace("\\", "/").replace(":", "\\:")
            cmd = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-vf", f"subtitles='{escaped_sub}'",
                "-c:a", "copy",
                "-c:v", "libx264",
                "-crf", "20",
                "-preset", "fast",
                output_video_path
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except Exception as e:
            print(f"Error burning subtitles: {e}")
            return False
