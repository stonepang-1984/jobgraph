"""Relation extraction - re-exports from entity_extractor."""

from src.ingestion.extractors.entity_extractor import (
    Entity,
    Relation,
    ExtractionResult,
    EntityRelationExtractor,
    entity_extractor,
)

__all__ = [
    "Entity",
    "Relation",
    "ExtractionResult",
    "EntityRelationExtractor",
    "entity_extractor",
]
