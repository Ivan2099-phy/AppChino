"""
Video Processor
Responsabilidad:
- Descargar videos (YouTube)
- Extraer audio normalizado (WAV, mono, 16kHz)
NO realiza transcripción
"""

import os
import subprocess
import uuid
import logging
import json
from typing import Dict

logger = logging.getLogger(__name__)


class VideoProcessor:
    def __init__(self, temp_dir: str = "temp"):
        self.temp_dir = temp_dir
        os.makedirs(self.temp_dir, exist_ok=True)

    # =====================================================
    # YouTube
    # =====================================================

    def process_youtube_video(self, url: str) -> Dict:
        """
        Descarga audio de YouTube y devuelve metadata.
        """
        video_uuid = str(uuid.uuid4())
        output_template = os.path.join(self.temp_dir, f"{video_uuid}.%(ext)s")

        logger.info("Descargando audio desde YouTube")

        cmd = [
            "yt-dlp",
            "-f", "bestaudio/best",
            "--extract-audio",
            "--audio-format", "wav",
            "--audio-quality", "0",
            "-o", output_template,
            "--print-json",
            url
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )

        metadata = self._parse_yt_metadata(result.stdout)
        audio_path = os.path.join(self.temp_dir, f"{video_uuid}.wav")

        if not os.path.exists(audio_path):
            raise RuntimeError("No se pudo generar el archivo de audio")

        return {
            "video_id": video_uuid,
            "title": metadata.get("title", "Unknown title"),
            "duration": metadata.get("duration"),
            "source_url": url,
            "audio_path": audio_path
        }

    # =====================================================
    # Video local
    # =====================================================

    def process_local_video(self, file_path: str) -> Dict:
        """
        Extrae audio de un archivo de video local.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(file_path)

        video_uuid = str(uuid.uuid4())
        audio_path = os.path.join(self.temp_dir, f"{video_uuid}.wav")

        logger.info("Extrayendo audio de video local")

        cmd = [
            "ffmpeg",
            "-y",
            "-i", file_path,
            "-vn",
            "-ac", "1",
            "-ar", "16000",
            audio_path
        ]

        subprocess.run(cmd, check=True)

        if not os.path.exists(audio_path):
            raise RuntimeError("FFmpeg no generó el audio")

        return {
            "video_id": video_uuid,
            "title": os.path.basename(file_path),
            "file_path": file_path,
            "audio_path": audio_path
        }

    # =====================================================
    # Utilidades
    # =====================================================

    def _parse_yt_metadata(self, stdout: str) -> Dict:
        """
        yt-dlp puede imprimir múltiples JSON;
        usamos el último válido.
        """
        for line in reversed(stdout.splitlines()):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                continue
        return {}

