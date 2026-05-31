"""Result fusion strategies."""

from collections import defaultdict

from loguru import logger

from config.settings import settings
from src.retrieval.vector_retriever import RetrievalResult


def reciprocal_rank_fusion(
    result_lists: list[list[RetrievalResult]],
    k: int = None,
) -> list[RetrievalResult]:
    """Fuse results using Reciprocal Rank Fusion (RRF).

    RRF score(d) = sum(1 / (k + rank(d, Li)))

    Args:
        result_lists: List of result lists from different retrievers
        k: RRF parameter (default from settings)

    Returns:
        Fused and re-ranked results
    """
    k = k or settings.retrieval.rrf_k

    doc_scores: dict[str, float] = defaultdict(float)
    doc_map: dict[str, RetrievalResult] = {}

    for results in result_lists:
        for rank, result in enumerate(results):
            doc_id = result.id
            doc_scores[doc_id] += 1.0 / (k + rank + 1)
            doc_map[doc_id] = result

    # Sort by fused score
    sorted_ids = sorted(doc_scores.keys(), key=lambda x: doc_scores[x], reverse=True)

    # Create results with fused scores
    fused_results = []
    for doc_id in sorted_ids:
        original = doc_map[doc_id]
        fused_results.append(
            RetrievalResult(
                id=original.id,
                content=original.content,
                modality=original.modality,
                score=doc_scores[doc_id],
                metadata=original.metadata,
                source=original.source,
                page=original.page,
            )
        )

    return fused_results


def weighted_fusion(
    result_lists: list[list[RetrievalResult]],
    weights: list[float] = None,
) -> list[RetrievalResult]:
    """Fuse results using weighted sum.

    Args:
        result_lists: List of result lists from different retrievers
        weights: Weight for each result list

    Returns:
        Fused and re-ranked results
    """
    if weights is None:
        weights = [1.0] * len(result_lists)

    if len(weights) != len(result_lists):
        raise ValueError("Number of weights must match number of result lists")

    doc_scores: dict[str, float] = defaultdict(float)
    doc_map: dict[str, RetrievalResult] = {}

    for results, weight in zip(result_lists, weights):
        for result in results:
            doc_id = result.id
            doc_scores[doc_id] += result.score * weight
            doc_map[doc_id] = result

    # Sort by weighted score
    sorted_ids = sorted(doc_scores.keys(), key=lambda x: doc_scores[x], reverse=True)

    # Create results with weighted scores
    fused_results = []
    for doc_id in sorted_ids:
        original = doc_map[doc_id]
        fused_results.append(
            RetrievalResult(
                id=original.id,
                content=original.content,
                modality=original.modality,
                score=doc_scores[doc_id],
                metadata=original.metadata,
                source=original.source,
                page=original.page,
            )
        )

    return fused_results


def deduplicate_results(
    results: list[RetrievalResult],
) -> list[RetrievalResult]:
    """Remove duplicate results by ID."""
    seen = set()
    unique = []
    for result in results:
        if result.id not in seen:
            seen.add(result.id)
            unique.append(result)
    return unique
