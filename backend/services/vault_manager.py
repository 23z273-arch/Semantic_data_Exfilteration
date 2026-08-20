"""
services/vault_manager.py — Reference Data Vault management.

Handles document ingestion, semantic chunking (sentence-boundary-aware,
tiktoken-based), embedding computation, and FAISS index population.
"""
import hashlib
import logging
import time
from typing import List, Optional

import tiktoken
from sqlalchemy.orm import Session

from config import settings
from database import SessionLocal
from models import VaultChunk, VaultDocument
from services.embedding_service import get_embedding_service
from services.pre_filter import get_pre_filter
from vector_store import get_vector_store

logger = logging.getLogger(__name__)

_TOKENIZER = tiktoken.get_encoding("cl100k_base")


# ── Chunker ───────────────────────────────────────────────────────────────────

def _chunk_text(text: str, chunk_size: int = 256, overlap: int = 64) -> List[str]:
    """
    Sentence-boundary-aware, token-counted chunker.

    Strategy:
      1. Split text into sentences (on '.', '!', '?', '\\n').
      2. Accumulate sentences into a chunk until it would exceed chunk_size tokens.
      3. When a chunk is full, save it and start the next chunk at the overlap
         boundary (last `overlap` tokens worth of sentences).
    """
    import re

    # Split into sentences, preserving delimiters
    raw_sentences = re.split(r"(?<=[.!?\n])\s+", text.strip())
    sentences = [s.strip() for s in raw_sentences if s.strip()]

    chunks: List[str] = []
    current_sentences: List[str] = []
    current_tokens = 0

    for sentence in sentences:
        s_tokens = len(_TOKENIZER.encode(sentence))
        if current_tokens + s_tokens > chunk_size and current_sentences:
            chunks.append(" ".join(current_sentences))
            # Overlap: keep sentences from the end whose total tokens ≤ overlap
            overlap_sentences: List[str] = []
            overlap_tokens = 0
            for s in reversed(current_sentences):
                t = len(_TOKENIZER.encode(s))
                if overlap_tokens + t > overlap:
                    break
                overlap_sentences.insert(0, s)
                overlap_tokens += t
            current_sentences = overlap_sentences
            current_tokens = overlap_tokens

        current_sentences.append(sentence)
        current_tokens += s_tokens

    if current_sentences:
        chunks.append(" ".join(current_sentences))

    return chunks


# ── VaultManager ──────────────────────────────────────────────────────────────

class VaultManager:

    def ingest_document(
        self,
        db: Session,
        name: str,
        category: str,
        classification: str,
        lineage_tag: str,
        content: str,
        department: Optional[str] = None,
        data_owner: Optional[str] = None,
        meta_data: Optional[dict] = None,
        embedding_model: Optional[str] = None,
    ) -> VaultDocument:
        """
        Ingest a document into the vault:
          1. Persist document record (status = PROCESSING)
          2. Chunk and embed content
          3. Store chunks + update FAISS index
          4. Update document status to READY
        """
        emb_svc = get_embedding_service()
        vs = get_vector_store()
        pf = get_pre_filter()

        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        model_name = embedding_model or (
            "text-embedding-3-small" if settings.effective_embedding_provider == "openai"
            else "all-MiniLM-L6-v2"
        )

        # 1. Persist document record
        doc = VaultDocument(
            name=name,
            category=category,
            classification=classification,
            lineage_tag=lineage_tag,
            department=department,
            data_owner=data_owner,
            raw_content=content,
            content_hash=content_hash,
            embedding_model=model_name,
            ingest_status="PROCESSING",
            meta_data=meta_data or {},
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        try:
            # 2. Chunk text
            chunks_text = _chunk_text(content, settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)
            total = len(chunks_text)

            for idx, chunk_text in enumerate(chunks_text):
                token_count = len(_TOKENIZER.encode(chunk_text))
                position_ratio = idx / max(1, total - 1)

                # 3. Embed chunk (using normalized text to match evaluation normalization)
                normalized_chunk_text = pf.run(chunk_text).normalized_text
                vec = emb_svc.embed(normalized_chunk_text)

                # 4. Add to FAISS
                faiss_id = vs.add(chunk_uuid="__placeholder__", vector=vec)

                # 5. Persist chunk
                chunk = VaultChunk(
                    document_id=doc.id,
                    lineage_tag=lineage_tag,
                    chunk_index=idx,
                    chunk_text=chunk_text,
                    token_count=token_count,
                    char_count=len(chunk_text),
                    position_ratio=position_ratio,
                    faiss_index_id=faiss_id,
                    embedding_model=model_name,
                )
                db.add(chunk)
                db.flush()  # Get chunk.id

                # Fix FAISS map: replace placeholder with real chunk UUID
                vs.fix_map_entry(faiss_id, chunk.id)

            # 6. Update document
            doc.chunk_count = total
            doc.ingest_status = "READY"
            db.commit()
            db.refresh(doc)

            # 7. Register content hash in pre-filter for exact-match detection
            pf.register_hash(content_hash)

            # 8. Save FAISS index to disk
            vs.save()

            logger.info(
                "Vault document ingested: %s (%d chunks, tag=%s)",
                name, total, lineage_tag
            )
        except Exception as exc:
            doc.ingest_status = "FAILED"
            db.commit()
            logger.error("Vault ingestion failed for %s: %s", name, exc)
            raise

        return doc

    def delete_document(self, db: Session, document_id: str) -> bool:
        """Delete a vault document and remove its chunks from the FAISS index."""
        doc: VaultDocument | None = db.query(VaultDocument).filter(
            VaultDocument.id == document_id
        ).first()
        if doc is None:
            return False

        # Get chunk UUIDs before deletion
        chunk_uuids = {c.id for c in doc.chunks}

        # Remove from FAISS
        vs = get_vector_store()
        vs.remove_by_uuids(chunk_uuids)
        vs.save()

        # Unregister hash from pre-filter
        get_pre_filter().unregister_hash(doc.content_hash)

        # Cascade-delete from DB
        db.delete(doc)
        db.commit()

        logger.info("Vault document deleted: %s (id=%s)", doc.name, document_id)
        return True

    def rebuild_index_from_db(self, db: Session) -> None:
        """
        Rebuild the FAISS index from scratch using DB chunk records.
        Called on startup to ensure index is in sync with the database.
        """
        from vector_store import init_vector_store

        emb_svc = get_embedding_service()
        dim = emb_svc.dim

        # Re-initialise vector store with correct dimension
        vs = init_vector_store(dim=dim)

        chunks: List[VaultChunk] = db.query(VaultChunk).all()
        if not chunks:
            logger.info("No vault chunks to rebuild.")
            return

        logger.info("Rebuilding FAISS index from %d chunks…", len(chunks))
        pf = get_pre_filter()
        for chunk in chunks:
            normalized_chunk_text = pf.run(chunk.chunk_text).normalized_text
            vec = emb_svc.embed(normalized_chunk_text)
            faiss_id = vs.add(chunk_uuid=chunk.id, vector=vec)
            chunk.faiss_index_id = faiss_id

        db.commit()
        vs.save()
        logger.info("FAISS index rebuild complete — %d vectors", vs.total_vectors)

        # Re-register all content hashes
        pf = get_pre_filter()
        docs: List[VaultDocument] = db.query(VaultDocument).filter(
            VaultDocument.ingest_status == "READY"
        ).all()
        for doc in docs:
            pf.register_hash(doc.content_hash)


# ── Singleton ─────────────────────────────────────────────────────────────────
_vault_mgr: VaultManager | None = None


def get_vault_manager() -> VaultManager:
    global _vault_mgr
    if _vault_mgr is None:
        _vault_mgr = VaultManager()
    return _vault_mgr
