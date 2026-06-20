"""Hybrid retriever combining vector and graph retrieval."""

from loguru import logger

from config.settings import settings
from src.retrieval.fusion import deduplicate_results, reciprocal_rank_fusion
from src.retrieval.graph_retriever import GraphRetriever
from src.retrieval.vector_retriever import RetrievalResult, VectorRetriever


class HybridRetriever:
    """Hybrid retriever combining vector and graph retrieval."""

    def __init__(
        self,
        vector_retriever: VectorRetriever = None,
        graph_retriever: GraphRetriever = None,
    ):
        self.vector_retriever = vector_retriever or vector_retriever
        self.graph_retriever = graph_retriever or graph_retriever

    def retrieve(
        self,
        query: str,
        top_k: int = None,
        use_vector: bool = True,
        use_graph: bool = True,
    ) -> list[RetrievalResult]:
        """Retrieve using hybrid approach."""
        top_k = top_k or settings.retrieval.vector_top_k

        all_results = []

        # Vector retrieval
        if use_vector:
            vector_results = self.vector_retriever.retrieve(query, top_k=top_k)
            all_results.append(vector_results)
            logger.debug(f"Vector retrieval: {len(vector_results)} results")

        # Graph retrieval (entity-based)
        if use_graph:
            # Extract entities from query using simple NER
            entities = self._extract_entities(query)
            if entities:
                graph_results = self.graph_retriever.retrieve_by_entity(entities)
                all_results.append(graph_results)
                logger.debug(f"Graph retrieval: {len(graph_results)} results for entities {entities}")

        # Fuse results
        if len(all_results) > 1:
            fused = reciprocal_rank_fusion(all_results)
        elif all_results:
            fused = all_results[0]
        else:
            fused = []

        # Deduplicate and limit
        results = deduplicate_results(fused)[:top_k]

        logger.info(f"Hybrid retrieval: {len(results)} final results")
        return results

    def _extract_entities(self, query: str) -> list[str]:
        """Extract entities from query using simple heuristics."""
        # Simple approach: query Neo4j for matching entity names
        from src.graph.neo4j_client import neo4j_client

        cypher = """
        MATCH (e:Entity)
        WHERE $query CONTAINS e.name
           OR any(alias IN e.aliases WHERE $query CONTAINS alias)
        RETURN e.name AS name
        LIMIT 10
        """

        try:
            results = neo4j_client.execute_query(cypher, {"query": query})
            return [r["name"] for r in results]
        except Exception:
            return []


class QueryEngine:
    """High-level query engine combining retrieval and generation."""

    def __init__(
        self,
        retriever: HybridRetriever = None,
        generator=None,
    ):
        self.retriever = retriever or HybridRetriever()
        from src.generation.answer_generator import answer_generator

        self.generator = generator or answer_generator

    def query(self, question: str) -> dict:
        """Answer a question using hybrid retrieval and generation."""
        logger.info(f"Processing query: {question}")

        # Retrieve relevant context
        context = self.retriever.retrieve(question)

        # Generate answer
        answer = self.generator.generate(question, context)

        return {
            "question": question,
            "answer": answer.text,
            "citations": answer.citations,
            "confidence": answer.confidence,
            "sources": [
                {
                    "id": s.id,
                    "content": s.content[:200],
                    "modality": s.modality,
                    "score": s.score,
                }
                for s in answer.sources[:10]
            ],
        }


# Singleton instances
hybrid_retriever = HybridRetriever()
query_engine = QueryEngine()
