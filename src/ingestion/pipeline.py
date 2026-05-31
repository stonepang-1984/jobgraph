"""Text ingestion pipeline with incremental update support."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from loguru import logger

from src.ingestion.document_loader import Document, DocumentLoader
from src.ingestion.extractors.chunk_splitter import SemanticChunkSplitter, TextChunk
from src.ingestion.extractors.entity_extractor import (
    EntityRelationExtractor,
    ExtractionResult,
    Entity,
    Relation,
)
from src.embeddings.text_embedder import TextEmbedder
from src.graph.neo4j_client import neo4j_client
from src.ingestion.incremental import incremental_manager, DocumentStatus


@dataclass
class IngestionResult:
    """Result of document ingestion."""

    document_id: str
    chunk_count: int
    entity_count: int
    relation_count: int
    status: str = "success"
    is_update: bool = False
    errors: list[str] = field(default_factory=list)


class TextIngestionPipeline:
    """Pipeline for ingesting text documents into the knowledge graph."""

    def __init__(
        self,
        loader: DocumentLoader = None,
        chunker: SemanticChunkSplitter = None,
        extractor: EntityRelationExtractor = None,
        embedder: TextEmbedder = None,
    ):
        self.loader = loader or DocumentLoader()
        self.chunker = chunker or SemanticChunkSplitter()
        self.extractor = extractor or EntityRelationExtractor()
        self.embedder = embedder or TextEmbedder()

    def ingest(self, file_path: str, force: bool = False) -> IngestionResult:
        """Ingest a document with incremental update support.

        Args:
            file_path: Path to document
            force: Force re-ingestion even if unchanged

        Returns:
            IngestionResult with status and statistics
        """
        logger.info(f"Starting ingestion: {file_path}")

        # Step 1: Check incremental status
        doc_status = incremental_manager.register_document(file_path)
        is_update = doc_status.status != "pending" or doc_status.chunk_count > 0

        if not force and doc_status.status == "completed":
            logger.info(f"Document already ingested and unchanged: {file_path}")
            return IngestionResult(
                document_id=doc_status.doc_id,
                chunk_count=doc_status.chunk_count,
                entity_count=doc_status.entity_count,
                relation_count=0,
                status="skipped",
                is_update=False,
            )

        # Mark as processing
        incremental_manager._update_status(doc_status.doc_id, "processing")

        try:
            # Step 2: If updating, delete old data first
            if is_update:
                logger.info(f"Updating document, removing old data: {doc_status.doc_id}")
                self._delete_document_data(doc_status.doc_id)

            # Step 3: Load document
            document = self.loader.load(file_path)
            logger.info(f"Loaded document: {document.title} ({len(document.content)} chars)")

            # Step 4: Split into chunks
            chunks = self.chunker.split(document.content, doc_status.doc_id)
            logger.info(f"Created {len(chunks)} chunks")

            # Step 5: Extract entities and relations from chunks
            chunk_texts = [c.content for c in chunks]
            extraction_results = self.extractor.extract_batch(chunk_texts)

            # Merge extraction results
            all_entities = []
            all_relations = []
            for result in extraction_results:
                all_entities.extend(result.entities)
                all_relations.extend(result.relations)

            # Deduplicate entities
            unique_entities = self._deduplicate_entities(all_entities)
            logger.info(f"Extracted {len(unique_entities)} unique entities, {len(all_relations)} relations")

            # Step 6: Generate embeddings
            chunk_embeddings = self.embedder.embed_batch(chunk_texts)
            entity_descriptions = [e.description for e in unique_entities]
            entity_embeddings = self.embedder.embed_batch(entity_descriptions) if entity_descriptions else []

            # Step 7: Write to Neo4j
            self._write_to_neo4j(
                doc_id=doc_status.doc_id,
                document=document,
                chunks=chunks,
                chunk_embeddings=chunk_embeddings,
                entities=unique_entities,
                entity_embeddings=entity_embeddings,
                relations=all_relations,
            )

            # Step 8: Update incremental status
            incremental_manager.update_ingestion_result(
                doc_status.doc_id,
                chunk_count=len(chunks),
                entity_count=len(unique_entities),
                status="completed",
            )

            logger.info(f"Ingestion complete: {document.title}")

            return IngestionResult(
                document_id=doc_status.doc_id,
                chunk_count=len(chunks),
                entity_count=len(unique_entities),
                relation_count=len(all_relations),
                status="success",
                is_update=is_update,
            )

        except Exception as e:
            logger.error(f"Ingestion failed: {e}")
            incremental_manager.mark_failed(doc_status.doc_id, str(e))
            return IngestionResult(
                document_id=doc_status.doc_id,
                chunk_count=0,
                entity_count=0,
                relation_count=0,
                status="failed",
                is_update=is_update,
                errors=[str(e)],
            )

    def ingest_batch(self, file_paths: list[str], force: bool = False) -> list[IngestionResult]:
        """Ingest multiple documents with incremental update support."""
        results = []

        for file_path in file_paths:
            try:
                result = self.ingest(file_path, force=force)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to ingest {file_path}: {e}")
                results.append(
                    IngestionResult(
                        document_id="",
                        chunk_count=0,
                        entity_count=0,
                        relation_count=0,
                        status="failed",
                        errors=[str(e)],
                    )
                )

        return results

    def ingest_directory(self, directory: str, force: bool = False) -> list[IngestionResult]:
        """Ingest all documents in a directory."""
        path = Path(directory)
        if not path.is_dir():
            raise ValueError(f"Not a directory: {directory}")

        # Find all supported files
        supported_extensions = {".pdf", ".docx", ".txt", ".md", ".markdown"}
        files = [
            f for f in path.rglob("*")
            if f.suffix.lower() in supported_extensions
        ]

        logger.info(f"Found {len(files)} documents in {directory}")

        # Check which files need update
        if not force:
            files_to_process = [
                f for f in files
                if incremental_manager.needs_update(f)
            ]
            logger.info(f"{len(files_to_process)} documents need update")
        else:
            files_to_process = files

        return self.ingest_batch([str(f) for f in files_to_process], force=force)

    def delete_document(self, doc_id: str) -> None:
        """Delete a document and all related data."""
        self._delete_document_data(doc_id)
        incremental_manager.delete_document(doc_id)
        logger.info(f"Deleted document: {doc_id}")

    def _delete_document_data(self, doc_id: str) -> None:
        """Delete document chunks and related data."""
        logger.info(f"Deleting old data for document: {doc_id}")

        # Delete chunks and their relationships
        neo4j_client.execute_write(
            """
            MATCH (d:Document {id: $doc_id})-[:CONTAINS]->(c:TextChunk)
            DETACH DELETE c
            """,
            {"doc_id": doc_id},
        )

        # Delete document node
        neo4j_client.execute_write(
            """
            MATCH (d:Document {id: $doc_id})
            DETACH DELETE d
            """,
            {"doc_id": doc_id},
        )

    def _deduplicate_entities(self, entities: list[Entity]) -> list[Entity]:
        """Deduplicate entities by name."""
        seen = {}
        for entity in entities:
            key = entity.name.lower()
            if key not in seen:
                seen[key] = entity
            else:
                # Merge descriptions
                existing = seen[key]
                if entity.description and entity.description not in existing.description:
                    existing.description += f"; {entity.description}"
                # Merge aliases
                for alias in entity.aliases:
                    if alias not in existing.aliases:
                        existing.aliases.append(alias)
        return list(seen.values())

    def _write_to_neo4j(
        self,
        doc_id: str,
        document: Document,
        chunks: list[TextChunk],
        chunk_embeddings: list[list[float]],
        entities: list[Entity],
        entity_embeddings: list[list[float]],
        relations: list[Relation],
    ) -> None:
        """Write all data to Neo4j."""
        logger.info("Writing to Neo4j...")

        # Write document node
        neo4j_client.execute_write(
            """
            MERGE (d:Document {id: $id})
            SET d.title = $title,
                d.source_path = $source_path,
                d.file_type = $file_type,
                d.status = 'completed',
                d.ingested_at = datetime()
            """,
            {
                "id": doc_id,
                "title": document.title,
                "source_path": document.source_path,
                "file_type": document.file_type,
            },
        )

        # Write chunk nodes
        for i, (chunk, embedding) in enumerate(zip(chunks, chunk_embeddings)):
            neo4j_client.execute_write(
                """
                MERGE (c:TextChunk {id: $id})
                SET c.content = $content,
                    c.chunk_index = $chunk_index,
                    c.document_id = $document_id,
                    c.token_count = $token_count,
                    c.embedding = $embedding
                WITH c
                MATCH (d:Document {id: $document_id})
                MERGE (d)-[:CONTAINS]->(c)
                """,
                {
                    "id": f"{doc_id}_chunk_{i}",
                    "content": chunk.content,
                    "chunk_index": i,
                    "document_id": doc_id,
                    "token_count": chunk.token_count,
                    "embedding": embedding,
                },
            )

        # Write entity nodes
        for i, (entity, embedding) in enumerate(zip(entities, entity_embeddings)):
            neo4j_client.execute_write(
                """
                MERGE (e:Entity {name: $name})
                SET e.type = $type,
                    e.description = $description,
                    e.aliases = $aliases,
                    e.embedding = $embedding
                """,
                {
                    "name": entity.name,
                    "type": entity.type,
                    "description": entity.description,
                    "aliases": entity.aliases,
                    "embedding": embedding,
                },
            )

        # Write relations and link to chunks
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc_id}_chunk_{i}"

            # Link entities mentioned in this chunk
            extraction = self.extractor.extract(chunk.content)
            for entity in extraction.entities:
                neo4j_client.execute_write(
                    """
                    MATCH (e:Entity {name: $entity_name})
                    MATCH (c:TextChunk {id: $chunk_id})
                    MERGE (e)-[:MENTIONED_IN]->(c)
                    """,
                    {"entity_name": entity.name, "chunk_id": chunk_id},
                )

        # Write entity relations
        for relation in relations:
            neo4j_client.execute_write(
                """
                MATCH (source:Entity {name: $source})
                MATCH (target:Entity {name: $target})
                MERGE (source)-[r:RELATES_TO {type: $type}]->(target)
                SET r.description = $description,
                    r.evidence = $evidence
                """,
                {
                    "source": relation.source,
                    "target": relation.target,
                    "type": relation.type,
                    "description": relation.description,
                    "evidence": relation.evidence,
                },
            )

        logger.info("Neo4j write complete")


# Singleton instance
text_pipeline = TextIngestionPipeline()
