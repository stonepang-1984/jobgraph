"""Incremental update manager for document ingestion."""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from loguru import logger

from src.graph.neo4j_client import neo4j_client


@dataclass
class DocumentStatus:
    """Document status for incremental update."""

    doc_id: str
    file_path: str
    file_hash: str
    file_size: int
    last_modified: float
    status: str  # pending, processing, completed, failed, deleted
    chunk_count: int = 0
    entity_count: int = 0
    error_message: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class IncrementalManager:
    """Manage incremental document updates."""

    def __init__(self):
        self._init_schema()

    def _init_schema(self) -> None:
        """Initialize document status schema."""
        cypher = """
        CREATE CONSTRAINT doc_status_id IF NOT EXISTS
        FOR (d:DocumentStatus) REQUIRE d.doc_id IS UNIQUE
        """
        try:
            neo4j_client.execute_query(cypher)
        except Exception:
            pass  # Constraint may already exist

    def compute_file_hash(self, file_path: str | Path) -> str:
        """Compute MD5 hash of file content."""
        path = Path(file_path)
        hasher = hashlib.md5()

        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)

        return hasher.hexdigest()

    def get_document_status(self, doc_id: str) -> Optional[DocumentStatus]:
        """Get document status by ID."""
        cypher = """
        MATCH (d:DocumentStatus {doc_id: $doc_id})
        RETURN d
        """
        results = neo4j_client.execute_query(cypher, {"doc_id": doc_id})
        if results:
            data = results[0]["d"]
            return DocumentStatus(**data)
        return None

    def get_document_by_path(self, file_path: str) -> Optional[DocumentStatus]:
        """Get document status by file path."""
        cypher = """
        MATCH (d:DocumentStatus {file_path: $file_path})
        RETURN d
        """
        results = neo4j_client.execute_query(cypher, {"file_path": file_path})
        if results:
            data = results[0]["d"]
            return DocumentStatus(**data)
        return None

    def register_document(self, file_path: str | Path) -> DocumentStatus:
        """Register a new document or update existing status."""
        path = Path(file_path)
        file_hash = self.compute_file_hash(path)
        file_size = path.stat().st_size
        last_modified = path.stat().st_mtime

        # Check if document exists
        existing = self.get_document_by_path(str(path))

        if existing:
            # Check if file has changed
            if existing.file_hash == file_hash:
                logger.info(f"Document unchanged: {path.name}")
                return existing
            else:
                # File has changed, update status
                logger.info(f"Document changed: {path.name}")
                self._update_status(existing.doc_id, "pending", file_hash, file_size, last_modified)
                existing.file_hash = file_hash
                existing.file_size = file_size
                existing.last_modified = last_modified
                existing.status = "pending"
                return existing
        else:
            # New document
            doc_id = hashlib.md5(str(path).encode()).hexdigest()[:16]
            now = datetime.now().isoformat()

            status = DocumentStatus(
                doc_id=doc_id,
                file_path=str(path),
                file_hash=file_hash,
                file_size=file_size,
                last_modified=last_modified,
                status="pending",
                created_at=now,
                updated_at=now,
            )

            cypher = """
            CREATE (d:DocumentStatus {
                doc_id: $doc_id,
                file_path: $file_path,
                file_hash: $file_hash,
                file_size: $file_size,
                last_modified: $last_modified,
                status: $status,
                chunk_count: 0,
                entity_count: 0,
                created_at: $created_at,
                updated_at: $updated_at
            })
            """
            neo4j_client.execute_write(
                cypher,
                {
                    "doc_id": status.doc_id,
                    "file_path": status.file_path,
                    "file_hash": status.file_hash,
                    "file_size": status.file_size,
                    "last_modified": status.last_modified,
                    "status": status.status,
                    "created_at": status.created_at,
                    "updated_at": status.updated_at,
                },
            )

            logger.info(f"Registered new document: {path.name} (ID: {doc_id})")
            return status

    def update_ingestion_result(
        self,
        doc_id: str,
        chunk_count: int,
        entity_count: int,
        status: str = "completed",
    ) -> None:
        """Update document ingestion result."""
        self._update_status(doc_id, status)
        self._update_counts(doc_id, chunk_count, entity_count)

    def mark_failed(self, doc_id: str, error_message: str) -> None:
        """Mark document as failed."""
        self._update_status(doc_id, "failed")
        self._set_error(doc_id, error_message)

    def needs_update(self, file_path: str | Path) -> bool:
        """Check if document needs update."""
        path = Path(file_path)
        existing = self.get_document_by_path(str(path))

        if not existing:
            return True  # New document

        current_hash = self.compute_file_hash(path)
        return existing.file_hash != current_hash

    def get_pending_documents(self) -> list[DocumentStatus]:
        """Get all documents that need processing."""
        cypher = """
        MATCH (d:DocumentStatus)
        WHERE d.status IN ['pending', 'failed']
        RETURN d
        ORDER BY d.updated_at
        """
        results = neo4j_client.execute_query(cypher)
        return [DocumentStatus(**r["d"]) for r in results]

    def get_all_documents(self) -> list[DocumentStatus]:
        """Get all document statuses."""
        cypher = """
        MATCH (d:DocumentStatus)
        RETURN d
        ORDER BY d.updated_at DESC
        """
        results = neo4j_client.execute_query(cypher)
        return [DocumentStatus(**r["d"]) for r in results]

    def delete_document(self, doc_id: str) -> None:
        """Delete document and all related data."""
        logger.info(f"Deleting document: {doc_id}")

        # Delete document and related nodes
        cypher = """
        MATCH (d:Document {id: $doc_id})
        OPTIONAL MATCH (d)-[:CONTAINS]->(c:TextChunk)
        OPTIONAL MATCH (c)<-[:MENTIONED_IN]-(e:Entity)
        DETACH DELETE d, c
        """
        neo4j_client.execute_write(cypher, {"doc_id": doc_id})

        # Delete status record
        cypher_status = """
        MATCH (d:DocumentStatus {doc_id: $doc_id})
        DELETE d
        """
        neo4j_client.execute_write(cypher_status, {"doc_id": doc_id})

        logger.info(f"Deleted document: {doc_id}")

    def cleanup_orphaned_entities(self) -> int:
        """Clean up entities that are not connected to any chunks."""
        cypher = """
        MATCH (e:Entity)
        WHERE NOT (e)-[:MENTIONED_IN]->(:TextChunk)
           AND NOT (e)-[:MENTIONED_IN]->(:Image)
           AND NOT (e)-[:MENTIONED_IN]->(:Table)
        DETACH DELETE e
        RETURN count(e) AS deleted_count
        """
        results = neo4j_client.execute_write(cypher)
        count = results[0]["deleted_count"] if results else 0
        logger.info(f"Cleaned up {count} orphaned entities")
        return count

    def get_statistics(self) -> dict:
        """Get ingestion statistics."""
        cypher = """
        MATCH (d:DocumentStatus)
        WITH count(d) AS total,
             sum(CASE WHEN d.status = 'completed' THEN 1 ELSE 0 END) AS completed,
             sum(CASE WHEN d.status = 'pending' THEN 1 ELSE 0 END) AS pending,
             sum(CASE WHEN d.status = 'failed' THEN 1 ELSE 0 END) AS failed,
             sum(d.chunk_count) AS total_chunks,
             sum(d.entity_count) AS total_entities
        RETURN total, completed, pending, failed, total_chunks, total_entities
        """
        results = neo4j_client.execute_query(cypher)
        return results[0] if results else {}

    def _update_status(
        self,
        doc_id: str,
        status: str,
        file_hash: Optional[str] = None,
        file_size: Optional[int] = None,
        last_modified: Optional[float] = None,
    ) -> None:
        """Update document status."""
        params = {"doc_id": doc_id, "status": status, "updated_at": datetime.now().isoformat()}

        set_clauses = ["d.status = $status", "d.updated_at = $updated_at"]

        if file_hash:
            set_clauses.append("d.file_hash = $file_hash")
            params["file_hash"] = file_hash
        if file_size:
            set_clauses.append("d.file_size = $file_size")
            params["file_size"] = file_size
        if last_modified:
            set_clauses.append("d.last_modified = $last_modified")
            params["last_modified"] = last_modified

        cypher = f"""
        MATCH (d:DocumentStatus {{doc_id: $doc_id}})
        SET {', '.join(set_clauses)}
        """
        neo4j_client.execute_write(cypher, params)

    def _update_counts(self, doc_id: str, chunk_count: int, entity_count: int) -> None:
        """Update chunk and entity counts."""
        cypher = """
        MATCH (d:DocumentStatus {doc_id: $doc_id})
        SET d.chunk_count = $chunk_count,
            d.entity_count = $entity_count
        """
        neo4j_client.execute_write(
            cypher,
            {"doc_id": doc_id, "chunk_count": chunk_count, "entity_count": entity_count},
        )

    def _set_error(self, doc_id: str, error_message: str) -> None:
        """Set error message."""
        cypher = """
        MATCH (d:DocumentStatus {doc_id: $doc_id})
        SET d.error_message = $error_message
        """
        neo4j_client.execute_write(cypher, {"doc_id": doc_id, "error_message": error_message})


# Singleton instance
incremental_manager = IncrementalManager()
