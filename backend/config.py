"""
config.py — Central configuration using pydantic-settings.
All values can be overridden via environment variables or .env file.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Settings(BaseSettings):
    """Application configuration settings, loaded from environment variables or .env file."""
    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL: str = f"sqlite:///{os.path.join(_BASE_DIR, 'data', 'sdlp.db')}"

    # ── Embedding ─────────────────────────────────────────────────────────────
    EMBEDDING_PROVIDER: str = "local"        # "gemini" | "openai" | "local"
    OPENAI_API_KEY: Optional[str] = None
    EMBEDDING_DIM: int = 768                 # Gemini output dim (768/1536/3072)

    # ── LLM for factual verification ──────────────────────────────────────────
    LLM_PROVIDER: str = "openai"             # "openai" | "anthropic" | "groq" | "gemini" | "mock"
    ANTHROPIC_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # ── Detection Thresholds ──────────────────────────────────────────────────
    STAGE2_TRIGGER_THRESHOLD: float = 0.55
    BLOCK_THRESHOLD: float = 0.75
    WARN_THRESHOLD: float = 0.50

    # ── Scoring Weights ───────────────────────────────────────────────────────
    EMBEDDING_WEIGHT: float = 0.30
    FACTUAL_WEIGHT: float = 0.70

    # ── Session Risk Aggregation ──────────────────────────────────────────────
    SESSION_WINDOW_SIZE: int = 10
    SESSION_BLOCK_THRESHOLD: float = 0.65
    SESSION_ESCALATION_MULTIPLIER: float = 1.25

    # ── FAISS Vector Store ────────────────────────────────────────────────────
    VECTOR_INDEX_PATH: str = os.path.join(_BASE_DIR, "data", "vault_index.faiss")
    VECTOR_MAP_PATH: str = os.path.join(_BASE_DIR, "data", "vault_index_map.json")
    VECTOR_DIM: int = 1536                   # OpenAI text-embedding-3-small
    LOCAL_VECTOR_DIM: int = 384              # all-MiniLM-L6-v2

    # ── Text Chunking ─────────────────────────────────────────────────────────
    CHUNK_SIZE: int = 256                    # tokens
    CHUNK_OVERLAP: int = 64                  # tokens

    # ── CORS / Frontend ───────────────────────────────────────────────────────
    FRONTEND_URL: str = "http://localhost:3000"

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def effective_vector_dim(self) -> int:
        """Return the correct vector dimension for the active embedding provider."""
        provider = self.effective_embedding_provider
        if provider == "local":
            return self.LOCAL_VECTOR_DIM
        if provider == "gemini":
            return self.EMBEDDING_DIM
        return self.VECTOR_DIM

    @property
    def openai_available(self) -> bool:
        """Return whether OpenAI API key is configured."""
        return bool(self.OPENAI_API_KEY)

    @property
    def anthropic_available(self) -> bool:
        """Return whether Anthropic API key is configured."""
        return bool(self.ANTHROPIC_API_KEY)

    @property
    def groq_available(self) -> bool:
        """Return whether Groq API key is configured."""
        return bool(self.GROQ_API_KEY)

    @property
    def gemini_available(self) -> bool:
        """Return whether Gemini API key is configured."""
        return bool(self.GEMINI_API_KEY)

    @property
    def effective_embedding_provider(self) -> str:
        """Get the resolved embedding provider, falling back to local if the chosen provider is unavailable."""
        if self.EMBEDDING_PROVIDER == "openai" and not self.openai_available:
            return "local"
        if self.EMBEDDING_PROVIDER == "gemini" and not self.gemini_available:
            return "local"
        return self.EMBEDDING_PROVIDER

    @property
    def effective_llm_provider(self) -> str:
        """Get the resolved LLM provider, falling back to anthropic/groq/gemini or mock if unavailable."""
        if self.LLM_PROVIDER == "openai" and not self.openai_available:
            if self.anthropic_available:
                return "anthropic"
            if self.groq_available:
                return "groq"
            if self.gemini_available:
                return "gemini"
            return "mock"
        if self.LLM_PROVIDER == "anthropic" and not self.anthropic_available:
            return "mock"
        if self.LLM_PROVIDER == "groq" and not self.groq_available:
            return "mock"
        if self.LLM_PROVIDER == "gemini" and not self.gemini_available:
            return "mock"
        return self.LLM_PROVIDER


settings = Settings()


def ensure_data_dir() -> None:
    """Create the data directory if it does not exist."""
    os.makedirs(os.path.join(_BASE_DIR, "data"), exist_ok=True)