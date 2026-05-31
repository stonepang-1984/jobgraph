"""Vector similarity retrieval."""

from dataclasses import dataclass, field

from config.settings import settings
from src.embeddings.text_embedder import text_embedder
from src.graph.neo4j_client import neo4j_client


@dataclass
class RetrievalResult:
    """Result from retrieval."""

    id: str
    content: str
    modality: str  # text, image, table, audio, video, entity, community
    score: float
    metadata: dict = field(default_factory=dict)
    source: str | None = None
    page: int | None = None


class VectorRetriever:
    """Retrieve using vector similarity search."""

    def __init__(self, embedder=None):
        self.embedder = embedder or text_embedder

    def retrieve(
        self,
        query: str,
        top_k: int = None,
        modalities: list[str] = None,
    ) -> list[RetrievalResult]:
        """Retrieve similar content using vector search."""
        top_k = top_k or settings.retrieval.vector_top_k
        query_embedding = self.embedder.embed(query)

        if modalities is None:
            modalities = ["text", "entity", "community"]

        results = []
        per_modality_k = max(top_k // len(modalities), 5)

        for modality in modalities:
            if modality == "text":
                results.extend(self._search_text_chunks(query_embedding, per_modality_k))
            elif modality == "entity":
                results.extend(self._search_entities(query_embedding, per_modality_k))
            elif modality == "community":
                results.extend(self._search_communities(query_embedding, per_modality_k))

        # Sort by score
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    def _search_text_chunks(self, embedding: list[float], top_k: int) -> list[RetrievalResult]:
        """Search text chunks by vector similarity."""
        cypher = """
        CALL db.index.vector.queryNodes('text_chunk_embedding', $top_k, $embedding)
        YIELD node AS chunk, score
        MATCH (doc:Document)-[:CONTAINS]->(chunk)
        RETURN chunk.id AS id,
               chunk.content AS content,
               score,
               doc.title AS document_title,
               doc.id AS document_id
        ORDER BY score DESC
        """

        results = neo4j_client.execute_query(cypher, {"top_k": top_k, "embedding": embedding})

        return [
            RetrievalResult(
                id=r["id"],
                content=r["content"],
                modality="text",
                score=r["score"],
                source=r["document_title"],
                metadata={"document_id": r["document_id"]},
            )
            for r in results
        ]

    def _search_entities(self, embedding: list[float], top_k: int) -> list[RetrievalResult]:
        """Search entities by vector similarity."""
        cypher = """
        CALL db.index.vector.queryNodes('entity_embedding', $top_k, $embedding)
        YIELD node AS entity, score
        RETURN entity.name AS name,
               entity.type AS type,
               entity.description AS description,
               score
        ORDER BY score DESC
        """

        results = neo4j_client.execute_query(cypher, {"top_k": top_k, "embedding": embedding})

        return [
            RetrievalResult(
                id=r["name"],
                content=f"[{r['type']}] {r['name']}: {r['description']}",
                modality="entity",
                score=r["score"],
                metadata={"entity_type": r["type"]},
            )
            for r in results
        ]

    def _search_communities(self, embedding: list[float], top_k: int) -> list[RetrievalResult]:
        """Search communities by vector similarity."""
        cypher = """
        CALL db.index.vector.queryNodes('community_embedding', $top_k, $embedding)
        YIELD node AS community, score
        RETURN community.id AS id,
               community.title AS title,
               community.summary AS summary,
               score
        ORDER BY score DESC
        """

        results = neo4j_client.execute_query(cypher, {"top_k": top_k, "embedding": embedding})

        return [
            RetrievalResult(
                id=r["id"],
                content=f"[社区] {r['title']}: {r['summary']}",
                modality="community",
                score=r["score"],
            )
            for r in results
        ]


# Singleton instance
vector_retriever = VectorRetriever()
