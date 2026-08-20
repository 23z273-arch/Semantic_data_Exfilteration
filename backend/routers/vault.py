"""
routers/vault.py — Reference Data Vault CRUD endpoints.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from models import VaultDocument, VaultChunk
from services.vault_manager import get_vault_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/vault", tags=["Vault"])


# ── Request / Response schemas ────────────────────────────────────────────────

class IngestDocumentRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    category: str = Field(..., description="HR_RECORD | FINANCIAL | MEDICAL | INFRASTRUCTURE")
    classification: str = Field(..., description="RESTRICTED | CONFIDENTIAL | TOP_SECRET")
    lineage_tag: str = Field(..., min_length=1, max_length=200)
    department: Optional[str] = None
    data_owner: Optional[str] = None
    content: str = Field(..., min_length=10)
    meta_data: Optional[dict] = None


class ChunkOut(BaseModel):
    id: str
    chunk_index: int
    chunk_text: str
    token_count: int
    position_ratio: float

    model_config = {"from_attributes": True}


class DocumentOut(BaseModel):
    id: str
    name: str
    category: str
    classification: str
    lineage_tag: str
    department: Optional[str]
    data_owner: Optional[str]
    chunk_count: int
    ingest_status: str
    embedding_model: str
    created_at: str
    meta_data: Optional[dict]

    model_config = {"from_attributes": True}


class DocumentDetailOut(DocumentOut):
    chunks: List[ChunkOut] = []


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/documents", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
def ingest_document(req: IngestDocumentRequest, db: Session = Depends(get_db)):
    """Ingest a document into the protected vault (synchronous — chunking + embedding happens inline)."""
    # Check for duplicate lineage tag
    existing = db.query(VaultDocument).filter(
        VaultDocument.lineage_tag == req.lineage_tag
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A document with lineage_tag '{req.lineage_tag}' already exists. "
                   f"Delete the existing document first.",
        )

    try:
        doc = get_vault_manager().ingest_document(
            db=db,
            name=req.name,
            category=req.category,
            classification=req.classification,
            lineage_tag=req.lineage_tag,
            content=req.content,
            department=req.department,
            data_owner=req.data_owner,
            meta_data=req.meta_data,
        )
    except Exception as exc:
        logger.exception("Document ingestion failed")
        raise HTTPException(status_code=500, detail=str(exc))

    return _doc_to_out(doc)


@router.get("/documents", response_model=List[DocumentOut])
def list_documents(
    category: Optional[str] = None,
    classification: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List all vault documents, optionally filtered by category or classification."""
    query = db.query(VaultDocument)
    if category:
        query = query.filter(VaultDocument.category == category)
    if classification:
        query = query.filter(VaultDocument.classification == classification)
    docs = query.order_by(VaultDocument.created_at.desc()).all()
    return [_doc_to_out(d) for d in docs]


@router.get("/documents/{document_id}", response_model=DocumentDetailOut)
def get_document(document_id: str, db: Session = Depends(get_db)):
    """Retrieve a single vault document with its chunks."""
    doc = db.query(VaultDocument).filter(VaultDocument.id == document_id).first()
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found.")
    out = _doc_to_out(doc)
    chunks = [
        ChunkOut(
            id=c.id,
            chunk_index=c.chunk_index,
            chunk_text=c.chunk_text,
            token_count=c.token_count,
            position_ratio=c.position_ratio,
        )
        for c in sorted(doc.chunks, key=lambda x: x.chunk_index)
    ]
    return DocumentDetailOut(**out.__dict__, chunks=chunks)


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: str, db: Session = Depends(get_db)):
    """Delete a vault document and remove its embeddings from the vector index."""
    deleted = get_vault_manager().delete_document(db, document_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found.")


# ── Helper ────────────────────────────────────────────────────────────────────

def _doc_to_out(doc: VaultDocument) -> DocumentOut:
    return DocumentOut(
        id=doc.id,
        name=doc.name,
        category=doc.category,
        classification=doc.classification,
        lineage_tag=doc.lineage_tag,
        department=doc.department,
        data_owner=doc.data_owner,
        chunk_count=doc.chunk_count,
        ingest_status=doc.ingest_status,
        embedding_model=doc.embedding_model,
        created_at=doc.created_at.isoformat() if doc.created_at else "",
        meta_data=doc.meta_data,
    )
