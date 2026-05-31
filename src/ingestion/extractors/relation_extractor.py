"""Relation extraction - re-exports from entity_extractor."""

from src.ingestion.extractors.entity_extractor import (
    Entity,
    EntityRelationExtractor,
    ExtractionResult,
    Relation,
    entity_extractor,
)

__all__ = [
    "Entity",
    "Relation",
    "ExtractionResult",
    "EntityRelationExtractor",
    "entity_extractor",
]
