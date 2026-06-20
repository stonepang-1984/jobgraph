"""Graph traversal retrieval."""

from config.settings import settings
from src.graph.neo4j_client import neo4j_client
from src.retrieval.vector_retriever import RetrievalResult


class GraphRetriever:
    """Retrieve using graph traversal."""

    def retrieve_by_entity(self, entity_names: list[str], hop: int = None) -> list[RetrievalResult]:
        """Retrieve by entity name and expand subgraph."""
        hop = hop or settings.retrieval.graph_hop

        cypher = f"""
        MATCH (e:Entity)
        WHERE e.name IN $entity_names
        MATCH path = (e)-[*1..{hop}]-(connected)
        WHERE connected:Entity OR connected:TextChunk
        WITH e, connected, length(path) AS distance,
             [r IN relationships(path) | type(r)] AS rel_types
        RETURN DISTINCT
               CASE WHEN connected:Entity THEN connected.name
                    WHEN connected:TextChunk THEN connected.id
               END AS id,
               CASE WHEN connected:Entity THEN connected.description
                    WHEN connected:TextChunk THEN connected.content
               END AS content,
               CASE WHEN connected:Entity THEN 'entity'
                    WHEN connected:TextChunk THEN 'text'
               END AS modality,
               distance,
               rel_types,
               e.name AS source_entity
        ORDER BY distance
        LIMIT 50
        """

        results = neo4j_client.execute_query(cypher, {"entity_names": entity_names})

        return [
            RetrievalResult(
                id=r["id"],
                content=r["content"],
                modality=r["modality"],
                score=1.0 / (1 + r["distance"]),
                metadata={
                    "distance": r["distance"],
                    "relation_types": r["rel_types"],
                    "source_entity": r["source_entity"],
                },
            )
            for r in results
        ]

    def retrieve_by_relation_path(self, source: str, target: str, max_hops: int = 5) -> list[RetrievalResult]:
        """Find relation path between two entities."""
        cypher = f"""
        MATCH path = shortestPath(
            (source:Entity)-[*..{max_hops}]-(target:Entity)
        )
        WHERE source.name = $source AND target.name = $target
        RETURN [n IN nodes(path) | {{
            name: n.name,
            type: labels(n)[0],
            description: n.description
        }}] AS path_nodes,
        [r IN relationships(path) | {{
            type: type(r),
            description: r.description,
            evidence: r.evidence
        }}] AS path_relations,
        length(path) AS hops
        ORDER BY hops
        LIMIT 5
        """

        results = neo4j_client.execute_query(cypher, {"source": source, "target": target})

        if not results:
            return []

        # Format path as content
        r = results[0]
        path_text = self._format_path(r["path_nodes"], r["path_relations"])

        return [
            RetrievalResult(
                id=f"path_{source}_{target}",
                content=path_text,
                modality="graph_path",
                score=1.0 / (1 + r["hops"]),
                metadata={
                    "hops": r["hops"],
                    "nodes": r["path_nodes"],
                    "relations": r["path_relations"],
                },
            )
        ]

    def retrieve_entity_neighbors(self, entity_name: str, limit: int = 10) -> list[RetrievalResult]:
        """Get direct neighbors of an entity."""
        cypher = """
        MATCH (e:Entity {name: $name})-[r:RELATES_TO]-(neighbor:Entity)
        RETURN neighbor.name AS name,
               neighbor.type AS type,
               neighbor.description AS description,
               r.type AS relation_type,
               r.description AS relation_desc
        LIMIT $limit
        """

        results = neo4j_client.execute_query(cypher, {"name": entity_name, "limit": limit})

        return [
            RetrievalResult(
                id=r["name"],
                content=f"[{r['type']}] {r['name']}: {r['description']}",
                modality="entity",
                score=0.8,
                metadata={
                    "relation_type": r["relation_type"],
                    "relation_desc": r["relation_desc"],
                },
            )
            for r in results
        ]

    def _format_path(self, nodes: list[dict], relations: list[dict]) -> str:
        """Format path as readable text."""
        parts = []
        for i, node in enumerate(nodes):
            parts.append(f"{node['name']} ({node['type']})")
            if i < len(relations):
                rel = relations[i]
                parts.append(f"--[{rel['type']}]-->")
        return " ".join(parts)


# Singleton instance
graph_retriever = GraphRetriever()
