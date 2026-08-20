import sys
from config import settings
from services.factual_verifier import FactualVerifier
from services.embedding_scorer import ChunkMatch
from database import SessionLocal
from models import VaultChunk, VaultDocument
from openai import OpenAI
import json

db = SessionLocal()
chunk = db.query(VaultChunk).filter(VaultChunk.lineage_tag == 'VAULT-MED-TRIAL-TX9082').first()
doc = db.query(VaultDocument).filter(VaultDocument.lineage_tag == 'VAULT-MED-TRIAL-TX9082').first()

match = ChunkMatch(
    chunk_id=chunk.id,
    document_id=doc.id,
    document_name=doc.name,
    lineage_tag=chunk.lineage_tag,
    classification=doc.classification,
    department=doc.department,
    chunk_text=chunk.chunk_text,
    chunk_index=chunk.chunk_index,
    similarity=0.8
)

input_text = "The patient carries a rare inherited mutation affecting endocrine cell regulation, and is currently participating in an investigational weekly oral dosing protocol at 45 milligrams, which began in early 2024 with no significant tumor progression."

client = OpenAI(api_key=settings.GEMINI_API_KEY, base_url=settings.GEMINI_BASE_URL)
from services.factual_verifier import _SYSTEM_PROMPT, _USER_PROMPT_TEMPLATE
user_msg = _USER_PROMPT_TEMPLATE.format(
    reference_text=chunk.chunk_text[:4000],
    agent_output=input_text[:2000]
)

response = client.chat.completions.create(
    model="gemini-3.6-flash",
    response_format={"type": "json_object"},
    messages=[
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
    ],
    max_tokens=1000,
    temperature=0.0,
)
print("RAW CONTENT:")
print(response.choices[0].message.content)
db.close()
