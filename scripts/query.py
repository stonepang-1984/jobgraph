"""CLI script for querying the knowledge graph."""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from src.retrieval.hybrid_retriever import query_engine


def main():
    parser = argparse.ArgumentParser(description="Query the knowledge graph")
    parser.add_argument("question", help="Question to ask")
    parser.add_argument("--top-k", type=int, default=10, help="Number of results")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    # Configure logging
    if args.verbose:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
    else:
        logger.remove()
        logger.add(sys.stderr, level="INFO")

    # Run query
    result = query_engine.query(args.question)

    # Print result
    print("\n" + "=" * 60)
    print(f"问题: {result['question']}")
    print("=" * 60)
    print(f"\n回答:\n{result['answer']}")

    if result['citations']:
        print(f"\n引用:")
        for cite in result['citations']:
            print(f"  - {cite['text']}")

    print(f"\n置信度: {result['confidence']:.2f}")

    if args.verbose and result['sources']:
        print(f"\n来源 ({len(result['sources'])}):")
        for src in result['sources']:
            print(f"  [{src['modality']}] {src['id']}: {src['content'][:100]}...")

    print("=" * 60)


if __name__ == "__main__":
    main()
