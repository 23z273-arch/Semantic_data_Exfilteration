"""
routers/health.py — Health check and metrics endpoints.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from services.embedding_service import get_embedding_service
from vector_store import get_vector_store
from models import VaultDocument, VaultChunk, AuditLog

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
def health_check(db: Session = Depends(get_db)):
    """Comprehensive health check reporting status of all subsystems."""
    now = datetime.now(timezone.utc).isoformat()
    components = {}

    # Database
    try:
        db.query(VaultDocument).count()
        components["database"] = "healthy"
    except Exception as exc:
        components["database"] = f"unhealthy: {exc}"

    # Vector store
    try:
        vs = get_vector_store()
        components["vector_store"] = "healthy"
        vector_count = vs.total_vectors
    except Exception as exc:
        components["vector_store"] = f"unhealthy: {exc}"
        vector_count = 0

    # Embedding service
    try:
        emb_svc = get_embedding_service()
        _ = emb_svc.dim  # Triggers lazy init
        components["embedding_service"] = f"healthy ({emb_svc._provider})"
    except Exception as exc:
        components["embedding_service"] = f"unhealthy: {exc}"

    # Document counts
    doc_count = db.query(VaultDocument).filter(VaultDocument.ingest_status == "READY").count()
    chunk_count = db.query(VaultChunk).count()
    eval_count = db.query(AuditLog).count()

    overall = "healthy" if all("healthy" in v for v in components.values()) else "degraded"

    return {
        "status": overall,
        "timestamp": now,
        "version": "1.0.0",
        "components": components,
        "vault_document_count": doc_count,
        "vault_chunk_count": chunk_count,
        "vector_index_size": vector_count,
        "total_evaluations": eval_count,
    }
