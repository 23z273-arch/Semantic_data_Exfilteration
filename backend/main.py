"""
main.py — FastAPI application entry point.

Startup sequence:
  1. Create all database tables
  2. Initialise embedding service (triggers lazy provider detection)
  3. Initialise FAISS vector store (loads from disk or creates fresh)
  4. Check if vault is empty → if so, seed with synthetic documents
  5. Rebuild FAISS index from DB if dimension mismatch detected
  6. Seed test cases into the DB
"""
import logging
import os
import sys
from contextlib import asynccontextmanager

# Ensure we can import from backend root
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings, ensure_data_dir
from database import create_tables, SessionLocal

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


# ── Startup lifespan ─────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app):
    """Executed once at startup (before yield) and once at shutdown (after yield)."""
    ensure_data_dir()
    logger.info("═══ Semantic Data Exfiltration Detector starting up ═══")

    # 1. Create DB tables
    logger.info("Creating database tables…")
    create_tables()

    # 2. Initialise embedding service
    logger.info("Initialising embedding service…")
    from services.embedding_service import get_embedding_service
    emb_svc = get_embedding_service()
    dim = emb_svc.dim
    logger.info("Embedding service ready (provider=%s, dim=%d)", emb_svc._provider, dim)

    # 3. Initialise vector store
    logger.info("Initialising FAISS vector store…")
    from vector_store import init_vector_store
    vs = init_vector_store(dim=dim)

    db = SessionLocal()
    try:
        from models import VaultDocument, VaultChunk

        db_chunk_count = db.query(VaultChunk).count()
        vs_count = vs.total_vectors

        # 4. Rebuild index if mismatch
        if db_chunk_count > 0 and vs_count == 0:
            logger.info(
                "DB has %d chunks but vector store is empty — rebuilding index…",
                db_chunk_count,
            )
            from services.vault_manager import get_vault_manager
            get_vault_manager().rebuild_index_from_db(db)

        elif db_chunk_count > 0 and vs_count > 0 and vs_count != db_chunk_count:
            logger.warning(
                "Chunk count mismatch (DB=%d, VS=%d) — rebuilding index…",
                db_chunk_count, vs_count,
            )
            from services.vault_manager import get_vault_manager
            get_vault_manager().rebuild_index_from_db(db)
        else:
            # Register existing hashes in pre-filter
            from services.pre_filter import get_pre_filter
            docs = db.query(VaultDocument).filter(VaultDocument.ingest_status == "READY").all()
            pf = get_pre_filter()
            for doc in docs:
                pf.register_hash(doc.content_hash)
            logger.info("Pre-filter loaded %d content hashes", len(docs))

        # 5. Seed vault documents if empty
        ready_docs = db.query(VaultDocument).filter(VaultDocument.ingest_status == "READY").count()
        if ready_docs == 0:
            logger.info("Vault is empty — seeding synthetic documents…")
            _seed_vault(db)
        else:
            logger.info("Vault already has %d ready documents — skipping seed.", ready_docs)

        # 6. Seed test cases if empty
        from models import TestCase
        if db.query(TestCase).count() == 0:
            logger.info("Seeding test cases…")
            _seed_test_cases(db)
        else:
            logger.info("Test cases already seeded.")

    finally:
        db.close()

    logger.info("═══ Startup complete — API is ready ═══")
    yield
    # Shutdown: nothing to teardown in this implementation


# ── Application factory ───────────────────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        title="Semantic Data Exfiltration Detector",
        description=(
            "PS-5.3 — AI Governance Engine that detects when AI agents exfiltrate "
            "sensitive information semantically (paraphrase, obfuscation, translation, code-form)."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.FRONTEND_URL, "http://localhost:3000", "http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ───────────────────────────────────────────────────────────────
    from routers.health import router as health_router
    from routers.vault import router as vault_router
    from routers.governance import router as governance_router

    app.include_router(health_router, prefix="/v1")
    app.include_router(vault_router, prefix="/v1")
    app.include_router(governance_router, prefix="/v1")

    # ── Root redirect ──────────────────────────────────────────────────────────
    @app.get("/", include_in_schema=False)
    def root():
        return {"service": "Semantic Data Exfiltration Detector", "version": "1.0.0", "docs": "/docs"}

    return app


app = create_app()



def _seed_vault(db):
    from data.synthetic_documents import VAULT_DOCUMENTS
    from services.vault_manager import get_vault_manager
    vm = get_vault_manager()
    for doc_data in VAULT_DOCUMENTS:
        try:
            vm.ingest_document(
                db=db,
                name=doc_data["name"],
                category=doc_data["category"],
                classification=doc_data["classification"],
                lineage_tag=doc_data["lineage_tag"],
                content=doc_data["content"],
                department=doc_data.get("department"),
                data_owner=doc_data.get("data_owner"),
                meta_data=doc_data.get("meta_data"),
            )
            logger.info("Seeded: %s", doc_data["name"])
        except Exception as exc:
            logger.error("Failed to seed %s: %s", doc_data["name"], exc)


def _seed_test_cases(db):
    from data.test_cases import TEST_CASES
    from models import TestCase
    for tc in TEST_CASES:
        case = TestCase(
            case_id=tc["case_id"],
            category=tc["category"],
            attack_type=tc.get("attack_type"),
            input_text=tc["input_text"],
            vault_source_tag=tc.get("vault_source_tag"),
            expected_decision=tc["expected_decision"],
            expected_min_score=tc.get("expected_min_score"),
            expected_max_score=tc.get("expected_max_score"),
            description=tc.get("description"),
        )
        db.add(case)
    db.commit()
    logger.info("Seeded %d test cases.", len(TEST_CASES))


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False, log_level="info")
