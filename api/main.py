"""FastAPI application."""

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from loguru import logger

from config.settings import settings

# Import routes
from api.routes.resume import router as resume_router

app = FastAPI(
    title="Multimodal Graph RAG API",
    description="API for multimodal knowledge graph construction and querying",
    version="0.1.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(resume_router)


class QueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = 10


class QueryResponse(BaseModel):
    answer: str
    citations: list[dict]
    confidence: float
    sources: list[dict]


class IngestResponse(BaseModel):
    document_id: str
    chunk_count: int
    entity_count: int
    relation_count: int
    status: str


@app.get("/")
async def root():
    return {"message": "Multimodal Graph RAG API"}


@app.get("/health")
async def health():
    from src.graph.neo4j_client import neo4j_client

    return {
        "status": "healthy" if neo4j_client.check_connectivity() else "unhealthy",
        "neo4j": neo4j_client.check_connectivity(),
    }


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Query the knowledge graph."""
    try:
        from src.retrieval.hybrid_retriever import query_engine

        result = query_engine.query(request.question)

        return QueryResponse(
            answer=result["answer"],
            citations=result["citations"],
            confidence=result["confidence"],
            sources=result["sources"],
        )
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest", response_model=IngestResponse)
async def ingest_file(file: UploadFile = File(...)):
    """Ingest a document file."""
    try:
        # Save uploaded file
        upload_dir = Path(settings.raw_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)

        file_path = upload_dir / file.filename
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Process file
        ext = file_path.suffix.lower()

        if ext in (".pdf", ".docx", ".txt", ".md"):
            from src.ingestion.pipeline import text_pipeline

            result = text_pipeline.ingest(str(file_path))

            return IngestResponse(
                document_id=result.document_id,
                chunk_count=result.chunk_count,
                entity_count=result.entity_count,
                relation_count=result.relation_count,
                status=result.status,
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format: {ext}",
            )

    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def stats():
    """Get knowledge graph statistics."""
    from src.graph.neo4j_client import neo4j_client

    return {
        "documents": neo4j_client.get_node_count("Document"),
        "chunks": neo4j_client.get_node_count("TextChunk"),
        "entities": neo4j_client.get_node_count("Entity"),
        "communities": neo4j_client.get_node_count("Community"),
        "relationships": neo4j_client.get_relationship_count(),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_debug,
    )
