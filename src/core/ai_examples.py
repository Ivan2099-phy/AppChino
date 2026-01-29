"""
AI Example Generator
- Generación de ejemplos
- Sinónimos basados en embeddings
TOTALMENTE desacoplado del vocabulario global
"""

import logging
from typing import List
import math

logger = logging.getLogger(__name__)


class AIExampleGenerator:
    def __init__(self):
        """
        Los modelos se cargan bajo demanda.
        """
        self.embedding_model = None
        self.generation_model = None

    # ==================================================
    # Lazy loading
    # ==================================================

    def _load_embedding_model(self):
        if self.embedding_model is None:
            from transformers import BertModel, BertTokenizer
            import torch

            logger.info("Cargando BERT-base-chinese para embeddings")

            self.tokenizer = BertTokenizer.from_pretrained(
                "bert-base-chinese"
            )
            self.embedding_model = BertModel.from_pretrained(
                "bert-base-chinese"
            )
            self.embedding_model.eval()
            self.torch = torch

    def _load_generation_model(self):
        if self.generation_model is None:
            from transformers import GPT2LMHeadModel, GPT2Tokenizer

            logger.info("Cargando GPT-2 Chinese para generación")

            self.gen_tokenizer = GPT2Tokenizer.from_pretrained(
                "uer/gpt2-chinese-cluecorpussmall"
            )
            self.generation_model = GPT2LMHeadModel.from_pretrained(
                "uer/gpt2-chinese-cluecorpussmall"
            )
            self.generation_model.eval()

    # ==================================================
    # Utilidades
    # ==================================================

    def _embed_word(self, word: str):
        self._load_embedding_model()

        tokens = self.tokenizer(word, return_tensors="pt")
        with self.torch.no_grad():
            output = self.embedding_model(**tokens)

        # CLS embedding
        return output.last_hidden_state[0][0]

    def _cosine_similarity(self, a, b) -> float:
        return self.torch.nn.functional.cosine_similarity(a, b, dim=0).item()

    # ==================================================
    # API pública
    # ==================================================

    def get_word_synonyms(
        self,
        word: str,
        vocabulary: List[str],
        top_k: int = 5
    ) -> List[str]:
        """
        Encuentra sinónimos SOLO dentro del vocabulario del video actual.
        """
        if not vocabulary or word not in vocabulary:
            return []

        self._load_embedding_model()

        target_vec = self._embed_word(word)

        similarities = []
        for other in vocabulary:
            if other == word:
                continue

            vec = self._embed_word(other)
            sim = self._cosine_similarity(target_vec, vec)
            similarities.append((other, sim))

        similarities.sort(key=lambda x: x[1], reverse=True)
        return [w for w, _ in similarities[:top_k]]

    def generate_example_sentences(
        self,
        word: str,
        count: int = 3,
        max_length: int = 30
    ) -> List[str]:
        """
        Genera oraciones simples usando GPT-2 Chinese.
        """
        self._load_generation_model()

        prompt = f"{word}是一个词。{word}"

        input_ids = self.gen_tokenizer.encode(
            prompt, return_tensors="pt"
        )

        outputs = self.generation_model.generate(
            input_ids,
            max_length=max_length,
            num_return_sequences=count,
            do_sample=True,
            top_p=0.95,
            top_k=50
        )

        sentences = []
        for out in outputs:
            text = self.gen_tokenizer.decode(
                out, skip_special_tokens=True
            )
            if word in text:
                sentences.append(text.strip())

        return sentences[:count]

    def estimate_word_difficulty(
        self,
        word: str,
        frequency: int,
        max_frequency: int
    ) -> int:
        """
        Dificultad aproximada (1–5) basada SOLO en frecuencia relativa.
        """
        if max_frequency <= 0:
            return 3

        ratio = frequency / max_frequency

        if ratio > 0.2:
            return 1
        elif ratio > 0.1:
            return 2
        elif ratio > 0.05:
            return 3
        elif ratio > 0.02:
            return 4
        else:
            return 5

