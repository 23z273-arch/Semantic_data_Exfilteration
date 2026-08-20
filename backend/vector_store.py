"""
vector_store.py — Thread-safe FAISS wrapper with disk persistence.

Vectors are L2-normalised before storage so that inner product (IndexFlatIP)
equals cosine similarity. This lets us do fast ANN search with cosine semantics.
"""
import json
import logging
import os
import threading
from typing import List, Tuple

import faiss
import numpy as np

from config import settings

logger = logging.getLogger(__name__)


class VectorStore:
    """Thread-safe, disk-persisted FAISS flat inner-product index."""

    def __init__(self, dim: int, index_path: str, map_path: str):
        self.dim = dim
        self.index_path = index_path
        self.map_path = map_path
        self._lock = threading.Lock()

        # chunk_uuid_map[i] = chunk_uuid for FAISS index position i
        self._chunk_uuid_map: List[str] = []

        self._index: faiss.IndexFlatIP = self._load_or_create()

    # ── Public API ────────────────────────────────────────────────────────────

    def add(self, chunk_uuid: str, vector: np.ndarray) -> int:
        """Add a single L2-normalised vector; return its FAISS index position."""
        vec = self._normalise(vector).reshape(1, -1).astype(np.float32)
        with self._lock:
            faiss_id = len(self._chunk_uuid_map)
            self._index.add(vec)
            self._chunk_uuid_map.append(chunk_uuid)
        return faiss_id

    def search(self, query_vector: np.ndarray, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Return top-k (chunk_uuid, cosine_similarity) tuples.
        Similarity is in [-1, 1]; higher = more similar.
        """
        if self._index.ntotal == 0:
            return []

        top_k = min(top_k, self._index.ntotal)
        vec = self._normalise(query_vector).reshape(1, -1).astype(np.float32)

        with self._lock:
            distances, indices = self._index.search(vec, top_k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue
            chunk_uuid = self._chunk_uuid_map[idx]
            results.append((chunk_uuid, float(dist)))

        return results

    def remove_by_uuids(self, chunk_uuids: set) -> None:
        """
        Remove chunks by UUID. FAISS FlatIP does not support selective removal
        so we rebuild the index from retained vectors.
        """
        with self._lock:
            keep_positions = [
                i for i, uid in enumerate(self._chunk_uuid_map) if uid not in chunk_uuids
            ]
            if not keep_positions:
                self._index = faiss.IndexFlatIP(self.dim)
                self._chunk_uuid_map = []
                return

            all_vecs = faiss.rev_swig_ptr(self._index.get_xb(), self._index.ntotal * self.dim)
            all_vecs = np.array(all_vecs).reshape(self._index.ntotal, self.dim)

            kept_vecs = all_vecs[keep_positions]
            kept_uuids = [self._chunk_uuid_map[i] for i in keep_positions]

            new_index = faiss.IndexFlatIP(self.dim)
            new_index.add(kept_vecs.astype(np.float32))

            self._index = new_index
            self._chunk_uuid_map = kept_uuids

    def save(self) -> None:
        """Persist index and UUID map to disk."""
        with self._lock:
            os.makedirs(os.path.dirname(self.index_path) or ".", exist_ok=True)
            faiss.write_index(self._index, self.index_path)
            with open(self.map_path, "w", encoding="utf-8") as f:
                json.dump(self._chunk_uuid_map, f)
        logger.info("VectorStore saved — %d vectors", self._index.ntotal)

    @property
    def total_vectors(self) -> int:
        return self._index.ntotal

    def fix_map_entry(self, faiss_id: int, chunk_uuid: str) -> None:
        """Replace a placeholder UUID at faiss_id with the real chunk UUID.

        Called after flushing a new chunk to the DB to swap the temporary
        '__placeholder__' entry that was inserted during add().
        """
        with self._lock:
            if faiss_id < len(self._chunk_uuid_map):
                self._chunk_uuid_map[faiss_id] = chunk_uuid

    # ── Internals ─────────────────────────────────────────────────────────────

    def _load_or_create(self) -> faiss.IndexFlatIP:
        if os.path.exists(self.index_path) and os.path.exists(self.map_path):
            try:
                index = faiss.read_index(self.index_path)
                with open(self.map_path, "r", encoding="utf-8") as f:
                    self._chunk_uuid_map = json.load(f)
                logger.info("VectorStore loaded — %d vectors (dim=%d)", index.ntotal, self.dim)

                # Sanity check: dimension must match
                if index.d != self.dim:
                    logger.warning(
                        "Index dimension mismatch (index=%d, config=%d). Rebuilding.",
                        index.d, self.dim
                    )
                    return self._fresh_index()

                return index
            except Exception as exc:
                logger.error("Failed to load FAISS index: %s. Starting fresh.", exc)

        return self._fresh_index()

    def _fresh_index(self) -> faiss.IndexFlatIP:
        self._chunk_uuid_map = []
        logger.info("VectorStore created fresh (dim=%d)", self.dim)
        return faiss.IndexFlatIP(self.dim)

    @staticmethod
    def _normalise(vec: np.ndarray) -> np.ndarray:
        norm = np.linalg.norm(vec)
        if norm == 0:
            return vec
        return vec / norm


# ── Singleton instance (created in main.py after settings are known) ──────────
_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _store
    if _store is None:
        raise RuntimeError("VectorStore has not been initialised. Call init_vector_store() first.")
    return _store


def init_vector_store(dim: int | None = None) -> VectorStore:
    global _store
    _dim = dim or settings.effective_vector_dim
    _store = VectorStore(
        dim=_dim,
        index_path=settings.VECTOR_INDEX_PATH,
        map_path=settings.VECTOR_MAP_PATH,
    )
    return _store
