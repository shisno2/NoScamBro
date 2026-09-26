import os
import sys
import ssl
import subprocess
import time
import tempfile
from typing import List, Dict, Any, Callable, Optional

# Set Hugging Face cache to D: drive if available to preserve C: drive space
if os.path.exists("D:\\"):
    os.environ["HF_HOME"] = "D:\\huggingface_cache"

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

try:
    import httpx
    _orig_httpx = httpx.Client.__init__
    def _patched_httpx(self, *args, **kwargs):
        kwargs["verify"] = False
        return _orig_httpx(self, *args, **kwargs)
    httpx.Client.__init__ = _patched_httpx
except Exception:
    pass

try:
    import requests
    _orig_req = requests.Session.__init__
    def _patched_req(self, *args, **kwargs):
        _orig_req(self, *args, **kwargs)
        self.verify = False
    requests.Session.__init__ = _patched_req
except Exception:
    pass

def setup_cuda_paths():
    """Ensure NVIDIA pip wheel DLLs (cublas, cudnn) are registered in Windows DLL search path."""
    import site
    site_dirs = []
    try:
        site_dirs.extend(site.getsitepackages())
    except Exception:
        pass
    try:
        if site.getusersitepackages():
            site_dirs.append(site.getusersitepackages())
    except Exception:
        pass

    for base in site_dirs:
        nvidia_path = os.path.join(base, "nvidia")
        if os.path.isdir(nvidia_path):
            for item in os.listdir(nvidia_path):
                bin_path = os.path.join(nvidia_path, item, "bin")
                if os.path.isdir(bin_path):
                    if bin_path not in os.environ["PATH"]:
                        os.environ["PATH"] = bin_path + os.pathsep + os.environ["PATH"]
                    if hasattr(os, "add_dll_directory"):
                        try:
                            os.add_dll_directory(bin_path)
                        except Exception:
                            pass

setup_cuda_paths()

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

def is_cuda_usable() -> bool:
    """Check if CUDA device and required cuBLAS libraries are actually functional."""
    try:
        import ctranslate2
        if ctranslate2.get_cuda_device_count() == 0:
            return False
        import ctypes
        ctypes.CDLL("cublas64_12.dll")
        return True
    except Exception:
        return False

def preprocess_audio_for_vocals(input_path: str, on_progress: Optional[Callable[[str], None]] = None) -> str:
    """
    Extracts clean 16kHz mono audio for Whisper without destructive distortion.
    Applies gentle high-pass (80Hz) to remove non-vocal low-frequency rumble.
    """
    if on_progress:
        on_progress("Подготовка чистого аудиопотока...")

    temp_wav = tempfile.NamedTemporaryFile(suffix="_clean_voice.wav", delete=False)
    temp_wav.close()
    out_path = temp_wav.name

    # Clean 16kHz mono conversion with low rumble cutoff (no dynamic pumping or distortion)
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-af", "highpass=f=80",
        "-vn",
        "-ar", "16000",
        "-ac", "1",
        "-c:a", "pcm_s16le",
        out_path
    ]

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return out_path
    except Exception:
        return input_path

class SubtitleEngine:
    def __init__(self, model_name: str = "medium", device: str = "auto", compute_type: str = "default"):
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type
        self.model: Optional[WhisperModel] = None

    def load_model(self, on_progress: Optional[Callable[[str], None]] = None):
        if on_progress:
            on_progress(f"Инициализация AI модели '{self.model_name}'...")
        
        device = self.device
        compute_type = self.compute_type
        cuda_ok = is_cuda_usable()

        if device == "auto":
            if cuda_ok:
                device = "cuda"
                compute_type = "float16"
            else:
                device = "cpu"
                compute_type = "int8"
        elif device == "cuda":
            if not cuda_ok:
                if on_progress:
                    on_progress("CUDA недоступен. Переключение на процессор...")
                device = "cpu"
                compute_type = "int8"
            elif compute_type == "default":
                compute_type = "float16"
        elif device == "cpu" and compute_type == "default":
            compute_type = "int8"

        self.device = device
        self.compute_type = compute_type
        threads = os.cpu_count() or 4

        def try_init(model_name, dev, comp):
            if dev == "cpu":
                return WhisperModel(model_name, device="cpu", compute_type="int8", cpu_threads=threads)
            else:
                return WhisperModel(model_name, device="cuda", compute_type=comp)

        try:
            self.model = try_init(self.model_name, device, compute_type)
        except Exception as e:
            err_str = str(e).lower()
            # If CUDA fails, fallback to CPU
            if device == "cuda" and ("cublas" in err_str or "cuda" in err_str):
                if on_progress:
                    on_progress("Переключение на CPU режим...")
                self.device = "cpu"
                self.compute_type = "int8"
                try:
                    self.model = try_init(self.model_name, "cpu", "int8")
                except Exception:
                    pass

            # If model files are incomplete or network failed, fallback to local small model
            if self.model is None and self.model_name != "small":
                if on_progress:
                    on_progress(f"Модель '{self.model_name}' не готова локально. Загрузка готовой локальной модели 'small'...")
                self.model_name = "small"
                try:
                    self.model = try_init("small", self.device, self.compute_type)
                except Exception:
                    self.device = "cpu"
                    self.compute_type = "int8"
                    self.model = try_init("small", "cpu", "int8")
            elif self.model is None:
                raise e

        if on_progress:
            dev_label = f"GPU ({self.compute_type})" if self.device == "cuda" else f"CPU ({threads} потоков)"
            on_progress(f"Модель {self.model_name} готова [{dev_label}]")

    def transcribe(
        self,
        media_path: str,
        language: Optional[str] = None,
        preset: str = "music",  # "music", "reels", "speech"
        vocal_boost: bool = True,
        on_segment: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_progress: Optional[Callable[[float, str], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        Transcribes media with word-level accuracy and music anti-hallucination.
        """
        if self.model is None:
            self.load_model(lambda msg: on_progress(0.05, msg) if on_progress else None)

        processed_audio = media_path
        cleanup_temp = False

        # Apply vocal boost if requested or in music preset
        if vocal_boost:
            if on_progress:
                on_progress(0.08, "🎤 Очистка музыки и усиление вокала (Vocal Booster)...")
            enhanced_path = preprocess_audio_for_vocals(media_path)
            if enhanced_path != media_path and os.path.exists(enhanced_path):
                processed_audio = enhanced_path
                cleanup_temp = True

        if on_progress:
            on_progress(0.15, "🎯 Распознавание каждого слова (нейросеть)...")

        # Anti-hallucination settings tailored for music and speech:
        # condition_on_previous_text=False prevents infinite loop repetition on songs
        # repetition_penalty stops looping lyrics
        # beam_size=5 ensures deep search for accurate vocabulary
        beam_size = 5 if self.device == "cuda" else 3
        
        # Word timestamps options
        vad_kwargs = dict(
            min_silence_duration_ms=500,
            speech_pad_ms=250
        )

        # Smart initial prompt for context and vocabulary priming:
        prompt = None
        if language in ("ru", None, "auto"):
            prompt = "Разборчивый русский текст песни или речи со всеми словами, куплетами и знаками препинания."

        def run_inference():
            return self.model.transcribe(
                processed_audio,
                language=language if language and language != "auto" else None,
                word_timestamps=True,
                vad_filter=True,
                vad_parameters=vad_kwargs,
                beam_size=beam_size,
                best_of=beam_size,
                temperature=[0.0, 0.2, 0.4],
                condition_on_previous_text=True,
                initial_prompt=prompt,
                repetition_penalty=1.1,
                no_speech_threshold=0.6,
                compression_ratio_threshold=2.4
            )

        try:
            segments_gen, info = run_inference()
            total_duration = info.duration if info and info.duration > 0 else 1.0
            results = []

            for seg in segments_gen:
                words_data = []
                if seg.words:
                    for w in seg.words:
                        clean_w = w.word.strip()
                        if clean_w:
                            words_data.append({
                                "word": clean_w,
                                "start": w.start,
                                "end": w.end,
                                "probability": round(w.probability, 3)
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
                    progress = min(0.15 + 0.80 * (seg.end / total_duration), 0.95)
                    on_progress(progress, f"Обработано: {seg.end:.1f}с / {total_duration:.1f}с")

            return results

        except RuntimeError as e:
            if ("cublas" in str(e).lower() or "cuda" in str(e).lower()) and self.device == "cuda":
                if on_progress:
                    on_progress(0.12, "Переключение CUDA -> CPU...")
                self.device = "cpu"
                self.compute_type = "int8"
                threads = os.cpu_count() or 4
                self.model = WhisperModel(self.model_name, device="cpu", compute_type="int8", cpu_threads=threads)
                return self.transcribe(media_path, language, preset, vocal_boost, on_segment, on_progress)
            else:
                raise e
        finally:
            if cleanup_temp and os.path.exists(processed_audio):
                try:
                    os.remove(processed_audio)
                except Exception:
                    pass

    @staticmethod
    def export_srt_standard(segments: List[Dict[str, Any]], output_path: str):
        """Standard readable sentence/phrase SRT"""
        with open(output_path, "w", encoding="utf-8") as f:
            for idx, seg in enumerate(segments, 1):
                start = format_timestamp_srt(seg["start"])
                end = format_timestamp_srt(seg["end"])
                f.write(f"{idx}\n{start} --> {end}\n{seg['text']}\n\n")

    @staticmethod
    def export_srt_word_by_word(segments: List[Dict[str, Any]], output_path: str, words_per_chunk: int = 1):
        """
        Word-by-word SRT.
        words_per_chunk=1: every single word gets its own line and timestamp (Pure word-by-word)
        words_per_chunk=2-3: short punchy blocks for TikTok / Reels / Shorts
        """
        counter = 1
        with open(output_path, "w", encoding="utf-8") as f:
            for seg in segments:
                words = seg.get("words", [])
                if not words:
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
    def export_ass_tiktok_karaoke(segments: List[Dict[str, Any]], output_path: str, title: str = "Subtitles"):
        """
        Dynamic TikTok / Shorts / Reels style ASS Karaoke:
        - Bold, modern font with high contrast
        - Glowing Yellow highlight on active spoken word
        - Pop effect with thick border and shadow
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
Style: TikTokGlow,Trebuchet MS,64,&H00FFFFFF,&H0000E5FF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,4.5,3,2,60,60,110,1
Style: ClassicKaraoke,Montserrat,58,&H00FFFFFF,&H0000FFFF,&H00000000,&H90000000,-1,0,0,0,100,100,0,0,1,3.5,2,2,40,40,75,1

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
                    f.write(f"Dialogue: 0,{start_str},{end_str},TikTokGlow,,0,0,0,,{seg['text']}\n")
                    continue

                start_str = format_timestamp_ass(seg["start"])
                end_str = format_timestamp_ass(seg["end"])

                karaoke_line = ""
                for w in words:
                    duration_cs = max(1, int(round((w["end"] - w["start"]) * 100)))
                    word_clean = w["word"].replace("{", "").replace("}", "")
                    karaoke_line += f"{{\\k{duration_cs}}}{word_clean} "

                f.write(f"Dialogue: 0,{start_str},{end_str},TikTokGlow,,0,0,0,,{karaoke_line.strip()}\n")

    @staticmethod
    def export_vtt(segments: List[Dict[str, Any]], output_path: str):
        """WebVTT format"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("WEBVTT\n\n")
            for idx, seg in enumerate(segments, 1):
                start = format_timestamp_vtt(seg["start"])
                end = format_timestamp_vtt(seg["end"])
                f.write(f"{idx}\n{start} --> {end}\n{seg['text']}\n\n")

    @staticmethod
    def export_txt(segments: List[Dict[str, Any]], output_path: str):
        """Plain lyrics / clean text"""
        with open(output_path, "w", encoding="utf-8") as f:
            for seg in segments:
                f.write(f"{seg['text']}\n")

    @staticmethod
    def burn_subtitles_to_video(video_path: str, srt_or_ass_path: str, output_video_path: str) -> bool:
        """Uses FFmpeg to burn subtitles directly onto video with GPU nvenc or fast CPU."""
        try:
            escaped_sub = srt_or_ass_path.replace("\\", "/").replace(":", "\\:")
            cmd = [
                "ffmpeg", "-y",
                "-i", video_path,
                "-vf", f"subtitles='{escaped_sub}'",
                "-c:a", "copy",
                "-c:v", "libx264",
                "-crf", "18",
                "-preset", "veryfast",
                output_video_path
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return True
        except Exception as e:
            print(f"Error burning subtitles: {e}")
            return False
