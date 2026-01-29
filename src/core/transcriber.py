import json
import os
from typing import List, Dict

import whisper
import numpy as np


class Transcriber:
    """
    Wrapper de Whisper para transcribir audio con timestamps.
    """

    def __init__(self, model_size: str = "base", device: str | None = None):
        """
        model_size: tiny, base, small, medium, large
        device: 'cpu' o 'cuda' (None -> autodetect)
        """
        self.model_size = model_size
        self.device = device

        self.model = whisper.load_model(model_size, device=device)

    def transcribe_audio(self, audio_path: str) -> List[Dict]:
        """
        Ejecuta Whisper sobre un archivo de audio.

        Retorna una lista de segmentos:
        [
            {
                "text": str,
                "start": float,
                "end": float,
                "confidence": float | None
            },
            ...
        ]
        """

        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Archivo no encontrado: {audio_path}")

        result = self.model.transcribe(
            audio_path,
            verbose=False,
            language="zh",     # chino explícito
            task="transcribe"
        )

        segments = []

        for seg in result.get("segments", []):
            text = seg["text"].strip()

            # Whisper NO da una "confianza" directa por segmento.
            # Aproximación razonable: media de logprobs si existen.
            confidence = None
            if "tokens" in seg and "avg_logprob" in seg:
                # Convertimos log-probabilidad a pseudo-confianza [0,1]
                confidence = float(np.exp(seg["avg_logprob"]))

            segments.append({
                "text": text,
                "start": float(seg["start"]),
                "end": float(seg["end"]),
                "confidence": confidence
            })

        return segments

    @staticmethod
    def format_transcription(segments: List[Dict]) -> str:
        """
        Une segmentos en texto continuo con marcas de tiempo.

        Ejemplo:
        [00:01.20 - 00:04.50] 你好，欢迎来到这个视频
        """

        lines = []

        for seg in segments:
            start = Transcriber._format_time(seg["start"])
            end = Transcriber._format_time(seg["end"])
            text = seg["text"]

            lines.append(f"[{start} - {end}] {text}")

        return "\n".join(lines)

    @staticmethod
    def save_transcription_to_file(
        transcription: Dict,
        video_id: str,
        output_dir: str = "data/transcriptions"
    ):
        """
        Guarda la transcripción completa en JSON para reutilizarla.

        transcription debe incluir:
        {
            "video_id": str,
            "language": str,
            "segments": [...]
        }
        """

        os.makedirs(output_dir, exist_ok=True)
        path = os.path.join(output_dir, f"{video_id}.json")

        with open(path, "w", encoding="utf-8") as f:
            json.dump(transcription, f, ensure_ascii=False, indent=2)

    @staticmethod
    def _format_time(seconds: float) -> str:
        """
        Convierte segundos a MM:SS.xx
        """
        m = int(seconds // 60)
        s = seconds % 60
        return f"{m:02d}:{s:05.2f}"

