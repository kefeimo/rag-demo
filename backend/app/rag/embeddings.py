"""
Embedding Provider Abstraction
Supports OpenAI, AWS Bedrock, and sentence-transformers backends via LiteLLM.
"""

import logging
from typing import List, Union
import os

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingProvider:
    """
    Unified embedding interface using LiteLLM.

    Encoding behaviour:
      - Single string input  → returns List[float]  (one embedding vector)
      - List[str] input      → returns List[List[float]]  (batch of vectors)

    Backend is selected via the EMBEDDING_PROVIDER env var:
      - ``openai``               — uses OpenAI text-embedding-3-small via LiteLLM
      - ``bedrock``              — uses AWS Bedrock embeddings via LiteLLM
      - anything else (default)  — uses sentence-transformers locally
    """

    def __init__(self):
        provider = settings.embedding_provider
        logger.info(f"Initializing embedding provider: {provider}")

        if provider == "openai":
            # Set environment variables for LiteLLM
            if settings.openai_api_key:
                os.environ["OPENAI_API_KEY"] = settings.openai_api_key
            self._model = f"openai/{settings.openai_embedding_model}"
            self._provider = "openai"
            logger.info(f"LiteLLM OpenAI embeddings ready (model={settings.openai_embedding_model})")

        elif provider == "bedrock":
            # Set AWS configuration for LiteLLM
            # Priority: 1) Profile (SSO), 2) Access keys, 3) Default credentials chain
            if settings.aws_profile:
                os.environ["AWS_PROFILE"] = settings.aws_profile
                logger.info(f"Using AWS profile: {settings.aws_profile}")
            elif settings.aws_access_key_id and settings.aws_secret_access_key:
                os.environ["AWS_ACCESS_KEY_ID"] = settings.aws_access_key_id
                os.environ["AWS_SECRET_ACCESS_KEY"] = settings.aws_secret_access_key
                logger.info("Using AWS access keys from environment")
            else:
                logger.info("Using AWS default credentials chain (IAM role, SSO, or default profile)")

            if settings.aws_region:
                os.environ["AWS_REGION_NAME"] = settings.aws_region

            self._model = f"bedrock/{settings.bedrock_embedding_model}"
            self._provider = "bedrock"
            logger.info(f"LiteLLM Bedrock embeddings ready (model={settings.bedrock_embedding_model}, region={settings.aws_region})")

        else:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError:
                raise ImportError(
                    "sentence-transformers is not installed. "
                    "Set EMBEDDING_PROVIDER=openai/bedrock or run: pip install sentence-transformers"
                )
            self._st_model = SentenceTransformer(settings.embedding_model)
            self._provider = "sentence-transformers"
            logger.info(f"sentence-transformers ready (model={settings.embedding_model})")

    def encode(self, texts: Union[str, List[str]], **kwargs) -> Union[List[float], List[List[float]]]:
        """
        Encode one or more texts into embedding vectors.

        Extra kwargs (e.g. show_progress_bar, convert_to_numpy) are accepted but
        ignored for the OpenAI/Bedrock backends so call-sites don't need to branch.
        """
        single = isinstance(texts, str)
        if single:
            texts = [texts]

        if self._provider in ["openai", "bedrock"]:
            # Use LiteLLM for OpenAI and Bedrock
            from litellm import embedding

            # Truncate to safe length and batch
            MAX_CHARS = 6000
            # Bedrock Cohere has max 96 texts per batch, Titan has no batching (1 per request)
            # OpenAI supports up to 2048 per batch
            BATCH_SIZE = 96 if self._provider == "bedrock" else 500
            safe_texts = [t[:MAX_CHARS] if t.strip() else "." for t in texts]

            result: List[List[float]] = []
            for i in range(0, len(safe_texts), BATCH_SIZE):
                batch = safe_texts[i : i + BATCH_SIZE]
                response = embedding(
                    model=self._model,
                    input=batch
                )
                result.extend(item["embedding"] for item in response.data)
        else:
            # Use sentence-transformers locally
            embeddings = self._st_model.encode(texts, convert_to_numpy=True)
            result = embeddings.tolist()

        return result[0] if single else result
