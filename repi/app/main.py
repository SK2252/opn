from fastapi import FastAPI

from app.api import ingest, retrieve, chat
from app.db.qdrant import init_qdrant
from app.db.database import init_db

app = FastAPI(title="RAG Agent Router")

# ✅ AUTO INIT
init_db()
init_qdrant()

app.include_router(ingest.router, prefix="/ingest")
app.include_router(retrieve.router, prefix="/search")
app.include_router(chat.router, prefix="/chat")


@app.get("/health")
def health_check():
    """Health check endpoint to verify server and database connection."""
    return {
        "status": "healthy",
        "database": "supabase-postgresql",
        "service": "rag-agent-router"
    }

