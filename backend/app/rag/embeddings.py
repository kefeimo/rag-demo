"""
Embedding Provider Abstraction
Supports OpenAI and sentence-transformers backends, selected via EMBEDDING_PROVIDER env var.
"""

import logging
from typing import List, Union

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingProvider:
    """
    Unified embedding interface.

    Encoding behaviour:
      - Single string input  → returns List[float]  (one embedding vector)
      - List[str] input      → returns List[List[float]]  (batch of vectors)

    This mirrors the SentenceTransformer.encode() convention so existing
    callers in ingestion.py and retrieval.py need only minimal changes.
    """

    def __init__(self):
        provider = settings.embedding_provider
        logger.info(f"Initializing embedding provider: {provider}")

        if provider == "openai":
            from openai import OpenAI
            self._openai_client = OpenAI(api_key=settings.openai_api_key)
            self._openai_model = settings.openai_embedding_model
            self._provider = "openai"
            logger.info(f"OpenAI embeddings ready (model={self._openai_model})")

        else:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError:
                raise ImportError(
                    "sentence-transformers is not installed. "
                    "Set EMBEDDING_PROVIDER=openai or run: pip install sentence-transformers"
                )
            self._st_model = SentenceTransformer(settings.embedding_model)
            self._provider = "sentence-transformers"
            logger.info(f"sentence-transformers ready (model={settings.embedding_model})")

    def encode(self, texts: Union[str, List[str]], **kwargs) -> Union[List[float], List[List[float]]]:
        """
        Encode one or more texts into embedding vectors.

        Extra kwargs (e.g. show_progress_bar, convert_to_numpy) are accepted but
        ignored for the OpenAI backend so call-sites don't need to branch.
        """
        single = isinstance(texts, str)
        if single:
            texts = [texts]

        if self._provider == "openai":
            # OpenAI limits: max 2048 inputs per request, 8191 tokens per text.
            # Truncate to ~6000 chars (~1500 tokens) as a safe proxy, and batch.
            MAX_CHARS = 6000
            BATCH_SIZE = 500
            safe_texts = [t[:MAX_CHARS] if t.strip() else "." for t in texts]

            result: List[List[float]] = []
            for i in range(0, len(safe_texts), BATCH_SIZE):
                batch = safe_texts[i : i + BATCH_SIZE]
                response = self._openai_client.embeddings.create(
                    input=batch,
                    model=self._openai_model
                )
                result.extend(item.embedding for item in response.data)
        else:
            embeddings = self._st_model.encode(texts, convert_to_numpy=True)
            result = embeddings.tolist()

        return result[0] if single else result
