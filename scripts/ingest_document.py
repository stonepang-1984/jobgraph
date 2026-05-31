"""CLI script for ingesting documents."""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from src.ingestion.pipeline import TextIngestionPipeline


def main():
    parser = argparse.ArgumentParser(description="Ingest a document into the knowledge graph")
    parser.add_argument("file_path", help="Path to the document file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    # Configure logging
    if args.verbose:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
    else:
        logger.remove()
        logger.add(sys.stderr, level="INFO")

    # Check file exists
    file_path = Path(args.file_path)
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        sys.exit(1)

    # Run ingestion
    pipeline = TextIngestionPipeline()
    result = pipeline.ingest(str(file_path))

    # Print result
    logger.info("=" * 60)
    logger.info(f"Document: {file_path.name}")
    logger.info(f"Status: {result.status}")
    logger.info(f"Chunks: {result.chunk_count}")
    logger.info(f"Entities: {result.entity_count}")
    logger.info(f"Relations: {result.relation_count}")
    if result.errors:
        logger.warning(f"Errors: {result.errors}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
