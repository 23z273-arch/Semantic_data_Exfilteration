"""
services/embedding_service.py — Multi-provider embedding service with in-process cache.

Priority:
  1. Google Gemini gemini-embedding-2 (768-dim, configurable)  if GEMINI_API_KEY is set
  2. sentence-transformers all-MiniLM-L6-v2 (384-dim)          local fallback
"""
import hashlib
import logging
from typing import Any, List

import numpy as np

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

try:
    import google.generativeai as genai
except ImportError:
    genai = None  # type: ignore

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None  # type: ignore

from config import settings

logger = logging.getLogger(__name__)

_cache: dict[str, np.ndarray] = {}
_MAX_CACHE = 2048

GEMINI_EMBED_DIM = getattr(settings, "EMBEDDING_DIM", 768)


class EmbeddingService:
    def __init__(self):
        self._provider: str = settings.effective_embedding_provider
        self._dim: int | None = None
        self._gemini_model_name: str = "models/gemini-embedding-2"
        self._st_model: Any = None
        self._initialised: bool = False

    def _lazy_init(self) -> None:
        if self._initialised:
            return
        if self._provider == "gemini":
            try:
                if genai is None:
                    raise ImportError("google-generativeai package is not installed")
                if not getattr(settings, "GEMINI_API_KEY", None):
                    raise ValueError("GEMINI_API_KEY is not set")
                genai.configure(api_key=settings.GEMINI_API_KEY)
                
                # Verify API key by making a minimal dummy embedding request
                # This ensures we detect invalid/unauthorized keys at startup
                genai.embed_content(
                    model=self._gemini_model_name,
                    content="test",
                    task_type="retrieval_document",
                    output_dimensionality=GEMINI_EMBED_DIM,
                )
                
                self._dim = GEMINI_EMBED_DIM
                logger.info(
                    "EmbeddingService: using Gemini %s (%d-dim)",
                    self._gemini_model_name,
                    self._dim,
                )
            except Exception as exc:
                logger.warning("Gemini embedding verification failed (%s). Falling back to local.", exc)
                self._provider = "local"

        if self._provider == "local":
            try:
                if SentenceTransformer is None:
                    raise ImportError("sentence-transformers package is not installed")
                self._st_model = SentenceTransformer("all-MiniLM-L6-v2")
                self._dim = 384
                logger.info("EmbeddingService: using local all-MiniLM-L6-v2 (384-dim)")
            except Exception as exc:
                raise RuntimeError(
                    "No embedding provider available. "
                    "Set GEMINI_API_KEY or install sentence-transformers."
                ) from exc

        self._initialised = True

    @property
    def dim(self) -> int:
        self._lazy_init()
        if self._dim is None:
            raise RuntimeError(
                "EmbeddingService dimension is unknown — provider initialisation failed."
            )
        return self._dim

    def embed(self, text: str, task_type: str = "retrieval_document") -> np.ndarray:
        self._lazy_init()
        key = hashlib.sha256(f"{task_type}:{text}".encode("utf-8")).hexdigest()[:32]
        if key in _cache:
            return _cache[key]
        vec = self._compute(text, task_type)
        if len(_cache) >= _MAX_CACHE:
            oldest = next(iter(_cache))
            del _cache[oldest]
        _cache[key] = vec
        return vec

    def embed_batch(self, texts: List[str], task_type: str = "retrieval_document") -> List[np.ndarray]:
        self._lazy_init()
        return [self.embed(t, task_type) for t in texts]

    def _compute(self, text: str, task_type: str = "retrieval_document") -> np.ndarray:
        if self._provider == "gemini":
            return self._gemini_embed(text, task_type)
        return self._local_embed(text)

    def _gemini_embed(self, text: str, task_type: str = "retrieval_document") -> np.ndarray:
        text = text.replace("\n", " ")[:8000]
        result = genai.embed_content(
            model=self._gemini_model_name,
            content=text,
            task_type=task_type,
            output_dimensionality=GEMINI_EMBED_DIM,
        )
        vec = np.array(result["embedding"], dtype=np.float32)
        return vec

    def _local_embed(self, text: str) -> np.ndarray:
        if self._st_model is None:
            raise RuntimeError("SentenceTransformer model is not initialized.")
        vec = self._st_model.encode(text, convert_to_numpy=True, normalize_embeddings=False)
        return vec.astype(np.float32)


EMBEDDING_SERVICE = EmbeddingService()


def get_embedding_service() -> EmbeddingService:
    return EMBEDDING_SERVICE