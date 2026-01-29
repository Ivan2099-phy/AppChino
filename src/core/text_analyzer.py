import json
import re
from collections import defaultdict, Counter
from typing import List, Dict, Any

import jieba


CHINESE_CHAR_PATTERN = re.compile(r"[\u4e00-\u9fff]+")


class TextAnalyzer:
    def __init__(
        self,
        hsk_path: str = "src/data/hsk_data.json",
        cedict_path: str = "src/data/cedict.txt"
    ):
        self.jieba = jieba
        self.hsk_data = self.load_hsk_data(hsk_path)
        self.cedict = self.load_cedict(cedict_path)

    # ---------- CARGA DE DATOS ----------

    @staticmethod
    def load_hsk_data(path: str) -> Dict[str, int]:
        """
        Retorna:
        {
            "我": 1,
            "喜欢": 1,
            ...
        }
        """
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def load_cedict(path: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Retorna:
        {
            "学习": [
                {
                    "traditional": "學習",
                    "pinyin": "xué xí",
                    "definitions": ["to study", "to learn"]
                }
            ]
        }
        """
        cedict = defaultdict(list)

        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # Ejemplo:
                # 學習 学习 [xue2 xi2] /to study/to learn/
                match = re.match(
                    r"(\S+)\s(\S+)\s\[(.+?)\]\s/(.+)/",
                    line
                )
                if not match:
                    continue

                traditional, simplified, pinyin, defs = match.groups()
                definitions = defs.split("/")

                cedict[simplified].append({
                    "traditional": traditional,
                    "pinyin": pinyin,
                    "definitions": definitions
                })

        return cedict

    # ---------- PROCESAMIENTO DE TEXTO ----------

    def segment_text(self, text: str) -> List[str]:
        """
        Usa Jieba para segmentar texto chino.
        """
        tokens = list(self.jieba.cut(text, cut_all=False))
        return tokens

    @staticmethod
    def filter_non_chinese(tokens: List[str]) -> List[str]:
        """
        Elimina:
        - puntuación
        - números
        - tokens sin caracteres chinos
        """
        filtered = []
        for token in tokens:
            if CHINESE_CHAR_PATTERN.search(token):
                filtered.append(token)
        return filtered

    # ---------- CONTEXTO Y TIMESTAMPS ----------

    def extract_words_with_context(self, segments: List[Dict]) -> List[Dict]:
        """
        segments viene del Transcriber:
        [
            {
                "text": "...",
                "start": float,
                "end": float
            }
        ]

        Retorna lista de ocurrencias:
        [
            {
                "word": str,
                "sentence": str,
                "start": float,
                "end": float,
                "position": int
            }
        ]
        """

        results = []

        for seg in segments:
            sentence = seg["text"]
            tokens = self.segment_text(sentence)
            tokens = self.filter_non_chinese(tokens)

            for idx, token in enumerate(tokens):
                results.append({
                    "word": token,
                    "sentence": sentence,
                    "start": seg["start"],
                    "end": seg["end"],
                    "position": idx
                })

        return results

    # ---------- FRECUENCIAS ----------

    @staticmethod
    def calculate_word_frequencies(words: List[str]) -> Dict[str, int]:
        """
        Retorna diccionario ordenado por frecuencia descendente.
        """
        counter = Counter(words)
        return dict(counter.most_common())

    # ---------- CLASIFICACIÓN HSK ----------

    def classify_by_hsk(self, words: List[str]) -> Dict[str, Dict]:
        """
        Retorna:
        {
            "学习": {"hsk": 1},
            "量子": {"hsk": None}
        }
        """
        classification = {}

        for word in set(words):
            level = self.hsk_data.get(word)
            classification[word] = {
                "hsk": level if level is not None else "Fuera de HSK"
            }

        return classification

    # ---------- DICCIONARIO ----------

    def get_pinyin_and_translation(self, word: str) -> Dict[str, Any]:
        """
        Retorna:
        {
            "pinyin": "xué xí",
            "definitions": [...]
        }
        """
        entries = self.cedict.get(word)

        if not entries:
            return {
                "pinyin": None,
                "definitions": []
            }

        # Puede haber múltiples entradas
        all_definitions = []
        pinyin = entries[0]["pinyin"]

        for e in entries:
            all_definitions.extend(e["definitions"])

        return {
            "pinyin": pinyin,
            "definitions": all_definitions
        }

    # ---------- PIPELINE COMPLETO ----------

    def analyze(self, segments: List[Dict]) -> Dict[str, Any]:
        """
        Pipeline completo de análisis.
        """

        occurrences = self.extract_words_with_context(segments)
        words = [o["word"] for o in occurrences]

        frequencies = self.calculate_word_frequencies(words)
        hsk_info = self.classify_by_hsk(words)

        analysis = {}

        for word, freq in frequencies.items():
            dict_info = self.get_pinyin_and_translation(word)
            contexts = [o for o in occurrences if o["word"] == word]

            analysis[word] = {
                "frequency": freq,
                "hsk": hsk_info[word]["hsk"],
                "pinyin": dict_info["pinyin"],
                "definitions": dict_info["definitions"],
                "contexts": contexts
            }

        return analysis

