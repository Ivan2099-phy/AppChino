"""
Application Controller - Coordinates all modules
"""

import os
import json
import logging
from typing import Dict, List, Optional, Callable

from .video_processor import VideoProcessor
from .transcriber import Transcriber
from .text_analyzer import TextAnalyzer
from .database import Database
from .ai_examples import AIExampleGenerator


logger = logging.getLogger(__name__)


class ChineseVideoAnalyzer:
    """
    Controlador principal de la aplicación.
    Orquesta:
    - Video processing
    - Transcripción
    - Análisis lingüístico
    - Persistencia
    - IA opcional
    """

    # ==========================
    # Inicialización
    # ==========================

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)

        self.video_processor = VideoProcessor()
        self.transcriber = Transcriber(
            model_size=self.config["whisper_model"]
        )
        self.text_analyzer = TextAnalyzer()
        self.database = Database()

        self.ai_generator: Optional[AIExampleGenerator] = None
        if self.config["enable_ai"]:
            self.ai_generator = AIExampleGenerator()

        logger.info("ChineseVideoAnalyzer inicializado")

    # ==========================
    # Configuración
    # ==========================

    def _load_config(self, config_path: Optional[str]) -> Dict:
        default_config = {
            "whisper_model": "base",
            "enable_ai": False,
            "max_video_duration": 3600,
            "min_word_length": 1,
            "data_dir": "data",
        }

        if not config_path or not os.path.exists(config_path):
            return default_config

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                user_config = json.load(f)
            default_config.update(user_config)
        except Exception as e:
            logger.warning(f"No se pudo cargar config: {e}")

        return default_config

    # ==========================
    # Procesamiento de video
    # ==========================

    def process_youtube_video(
        self,
        url: str,
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> Dict:
        try:
            if progress_callback:
                progress_callback("Descargando video…", 10)

            video_info = self.video_processor.process_youtube_video(url)

            if progress_callback:
                progress_callback("Transcribiendo audio…", 40)

            segments = self.transcriber.transcribe_audio(
                video_info["audio_path"]
            )

            if progress_callback:
                progress_callback("Analizando texto…", 70)

            analysis = self.text_analyzer.analyze(segments)

            if progress_callback:
                progress_callback("Guardando resultados…", 90)

            video_id = self._save_to_database(video_info, analysis)

            stats = self._calculate_video_stats(analysis)
            self.database.save_video_stats(video_id, stats)

            return {
                "success": True,
                "video_id": video_id,
                "title": video_info["title"],
                "stats": stats,
            }

        except Exception as e:
            logger.exception("Error procesando video")
            return {"success": False, "error": str(e)}

    def process_local_video(
        self,
        file_path: str,
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> Dict:
        try:
            if progress_callback:
                progress_callback("Procesando archivo local…", 10)

            video_info = self.video_processor.process_local_video(file_path)

            if progress_callback:
                progress_callback("Transcribiendo audio…", 40)

            segments = self.transcriber.transcribe_audio(
                video_info["audio_path"]
            )

            if progress_callback:
                progress_callback("Analizando texto…", 70)

            analysis = self.text_analyzer.analyze(segments)

            if progress_callback:
                progress_callback("Guardando resultados…", 90)

            video_id = self._save_to_database(video_info, analysis)

            stats = self._calculate_video_stats(analysis)
            self.database.save_video_stats(video_id, stats)

            return {
                "success": True,
                "video_id": video_id,
                "title": video_info["title"],
                "stats": stats,
            }

        except Exception as e:
            logger.exception("Error procesando video local")
            return {"success": False, "error": str(e)}

    # ==========================
    # Persistencia
    # ==========================

    def _save_to_database(self, video_data: Dict, analysis: Dict) -> int:
        video_id = self.database.add_video(
            title=video_data["title"],
            source_url=video_data.get("source_url"),
            file_path=video_data.get("file_path"),
            duration=video_data.get("duration"),
        )

        for word, data in analysis.items():
            if len(word) < self.config["min_word_length"]:
                continue

            word_id = self.database.add_word(
                chinese=word,
                pinyin=data.get("pinyin"),
                translation="; ".join(data.get("definitions", [])[:3]),
                hsk_level=data["hsk"] if isinstance(data["hsk"], int) else None,
            )

            for ctx in data.get("contexts", []):
                self.database.add_word_occurrence(
                    word_id=word_id,
                    video_id=video_id,
                    sentence=ctx["sentence"],
                    start_time=ctx["start"],
                    end_time=ctx["end"],
                )

        return video_id

    # ==========================
    # Estadísticas
    # ==========================

    def _calculate_video_stats(self, analysis: Dict) -> Dict:
        total_words = sum(d["frequency"] for d in analysis.values())
        unique_words = len(analysis)

        hsk_counts = {i: 0 for i in range(1, 7)}
        non_hsk = 0

        for d in analysis.values():
            hsk = d.get("hsk")
            if isinstance(hsk, int) and 1 <= hsk <= 6:
                hsk_counts[hsk] += 1
            else:
                non_hsk += 1

        return {
            "total_words": total_words,
            "unique_words": unique_words,
            **{f"hsk{i}_count": hsk_counts[i] for i in range(1, 7)},
            "non_hsk_count": non_hsk,
        }

    # ==========================
    # Consultas para UI
    # ==========================

    def get_video_words(
        self, video_id: int, sort_by: str = "frequency"
    ) -> List[Dict]:
        words = self.database.get_video_words(video_id)

        if sort_by == "frequency":
            words.sort(key=lambda x: x["frequency"], reverse=True)
        elif sort_by == "hsk":
            words.sort(
                key=lambda x: (
                    x["hsk_level"] if x["hsk_level"] is not None else 99,
                    -x["frequency"],
                )
            )
        elif sort_by == "alphabetical":
            words.sort(key=lambda x: x["chinese"])

        return words

    def get_word_details(
        self, word_id: int, video_id: Optional[int] = None
    ) -> Dict:
        word = self.database.get_word(word_id)
        occurrences = self.database.get_word_occurrences(word_id, video_id)

        user_id = self.database.get_default_user_id()
        status = self.database.get_word_status(user_id, word_id)

        examples = []
        if self.ai_generator:
            examples = self.ai_generator.generate_example_sentences(
                word["chinese"]
            )

        return {
            "id": word_id,
            "hanzi": word["chinese"],
            "pinyin": word["pinyin"],
            "meaning": word["translation"],
            "hsk_level": word["hsk_level"],
            "frequency": word.get("frequency", 0),
            'occurrences': occurrences,
            "examples": examples,
            "user_status": status,
            "review_count": self.database.get_review_count(user_id, word_id),
        }

    def update_word_status(self, word_id: int, status: str):
        user_id = self.database.get_default_user_id()
        self.database.set_word_status(user_id, word_id, status)

    def get_video_stats(self, video_id: int) -> Dict:
        return self.database.get_video_stats(video_id)

    def get_all_videos(self) -> List[Dict]:
        return self.database.get_all_videos()

    # ==========================
    # Limpieza
    # ==========================

    def close(self):
        self.database.close()
        logger.info("Aplicación cerrada correctamente")

