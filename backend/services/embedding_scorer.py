"""
services/embedding_scorer.py — Stage-1 semantic similarity engine.

Embeds agent output and queries the FAISS vault index for top-K similar chunks.
Returns a SimilarityResult with max cosine, mean-top-3, and ranked matches.
"""
import logging
import time
from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np
from sqlalchemy.orm import Session

from config import settings
from models import VaultChunk, VaultDocument
from services.embedding_service import get_embedding_service
from vector_store import get_vector_store

logger = logging.getLogger(__name__)


@dataclass
class ChunkMatch:
    """Represents a matched chunk from the vector vault with similarity and lineage information."""
    chunk_id: str
    document_id: str
    document_name: str
    lineage_tag: str
    classification: str
    department: Optional[str]
    chunk_text: str
    chunk_index: int
    similarity: float


@dataclass
class SimilarityResult:
    """Holds similarity calculation results and matches for Stage-1 search."""
    max_similarity: float
    mean_top3: float
    triggered_stage2: bool
    top_matches: List[ChunkMatch] = field(default_factory=list)
    latency_ms: float = 0.0

    @property
    def top_match(self) -> Optional[ChunkMatch]:
        """Return the highest similarity chunk match or None if empty."""
        return self.top_matches[0] if self.top_matches else None


class EmbeddingScorer:
    """
    Stage-1: Computes output embedding then retrieves top-K vault chunks
    by cosine similarity via the FAISS index.
    """

    def score(self, normalized_text: str, db: Session, top_k: int = 10) -> SimilarityResult:
        """Compute the semantic similarity of normalized_text against vault index."""
        t0 = time.perf_counter()

        emb_svc = get_embedding_service()
        vs = get_vector_store()

        if vs.total_vectors == 0:
            logger.debug("Vector store is empty — returning zero similarity.")
            return SimilarityResult(
                max_similarity=0.0,
                mean_top3=0.0,
                triggered_stage2=False,
                latency_ms=(time.perf_counter() - t0) * 1000,
            )

        # Compute output embedding
        output_vec = emb_svc.embed(normalized_text)

        # Query FAISS
        raw_results = vs.search(output_vec, top_k=top_k)

        if not raw_results:
            return SimilarityResult(
                max_similarity=0.0,
                mean_top3=0.0,
                triggered_stage2=False,
                latency_ms=(time.perf_counter() - t0) * 1000,
            )

        # Enrich with DB metadata
        chunk_uuids = [uid for uid, _ in raw_results]
        chunks_db: List[VaultChunk] = (
            db.query(VaultChunk)
            .filter(VaultChunk.id.in_(chunk_uuids))
            .all()
        )
        chunk_map = {c.id: c for c in chunks_db}

        # Build doc cache to avoid repeated queries
        doc_ids = {c.document_id for c in chunks_db}
        docs_db: List[VaultDocument] = (
            db.query(VaultDocument)
            .filter(VaultDocument.id.in_(doc_ids))
            .all()
        )
        doc_map = {d.id: d for d in docs_db}

        matches: List[ChunkMatch] = []
        for chunk_uuid, sim in raw_results:
            chunk = chunk_map.get(chunk_uuid)
            if chunk is None:
                continue
            doc = doc_map.get(chunk.document_id)
            if doc is None:
                continue
            matches.append(
                ChunkMatch(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    document_name=doc.name,
                    lineage_tag=chunk.lineage_tag,
                    classification=doc.classification,
                    department=doc.department,
                    chunk_text=chunk.chunk_text,
                    chunk_index=chunk.chunk_index,
                    similarity=sim,
                )
            )

        # Sort descending by similarity
        matches.sort(key=lambda m: m.similarity, reverse=True)

        max_sim = matches[0].similarity if matches else 0.0
        top3_sims = [m.similarity for m in matches[:3]]
        mean_top3 = float(np.mean(top3_sims)) if top3_sims else 0.0

        return SimilarityResult(
            max_similarity=max_sim,
            mean_top3=mean_top3,
            triggered_stage2=max_sim >= settings.STAGE2_TRIGGER_THRESHOLD,
            top_matches=matches,
            latency_ms=(time.perf_counter() - t0) * 1000,
        )


# ── Singleton ─────────────────────────────────────────────────────────────────
EMBEDDING_SCORER = EmbeddingScorer()


def get_embedding_scorer() -> EmbeddingScorer:
    """Retrieve the module-level singleton instance of EmbeddingScorer."""
    return EMBEDDING_SCORER
