"""CLI script for incremental document ingestion."""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from src.ingestion.pipeline import text_pipeline
from src.ingestion.incremental import incremental_manager


def cmd_ingest(args):
    """Ingest documents incrementally."""
    if args.file:
        # Single file
        result = text_pipeline.ingest(args.file, force=args.force)
        print_result(result)
    elif args.directory:
        # Directory
        results = text_pipeline.ingest_directory(args.directory, force=args.force)
        print_batch_results(results)
    else:
        print("Please specify --file or --directory")
        sys.exit(1)


def cmd_status(args):
    """Show document status."""
    if args.doc_id:
        status = incremental_manager.get_document_status(args.doc_id)
        if status:
            print_status(status)
        else:
            print(f"Document not found: {args.doc_id}")
    else:
        statuses = incremental_manager.get_all_documents()
        if statuses:
            print_status_table(statuses)
        else:
            print("No documents found")


def cmd_delete(args):
    """Delete a document."""
    if not args.doc_id:
        print("Please specify --doc-id")
        sys.exit(1)

    confirm = input(f"Delete document {args.doc_id}? (y/N): ")
    if confirm.lower() == 'y':
        text_pipeline.delete_document(args.doc_id)
        print(f"Deleted: {args.doc_id}")
    else:
        print("Cancelled")


def cmd_cleanup(args):
    """Clean up orphaned entities."""
    count = incremental_manager.cleanup_orphaned_entities()
    print(f"Cleaned up {count} orphaned entities")


def cmd_stats(args):
    """Show ingestion statistics."""
    stats = incremental_manager.get_statistics()
    print("\n" + "=" * 40)
    print("Ingestion Statistics")
    print("=" * 40)
    print(f"  Total documents: {stats.get('total', 0)}")
    print(f"  Completed:       {stats.get('completed', 0)}")
    print(f"  Pending:         {stats.get('pending', 0)}")
    print(f"  Failed:          {stats.get('failed', 0)}")
    print(f"  Total chunks:    {stats.get('total_chunks', 0)}")
    print(f"  Total entities:  {stats.get('total_entities', 0)}")
    print("=" * 40)


def print_result(result):
    """Print single ingestion result."""
    icon = "✓" if result.status == "success" else "✗" if result.status == "failed" else "⊘"
    update = " (update)" if result.is_update else ""

    print(f"\n{icon} {result.document_id}{update}")
    print(f"  Status:    {result.status}")
    print(f"  Chunks:    {result.chunk_count}")
    print(f"  Entities:  {result.entity_count}")
    print(f"  Relations: {result.relation_count}")

    if result.errors:
        print(f"  Errors:    {result.errors}")


def print_batch_results(results):
    """Print batch ingestion results."""
    success = sum(1 for r in results if r.status == "success")
    skipped = sum(1 for r in results if r.status == "skipped")
    failed = sum(1 for r in results if r.status == "failed")

    print("\n" + "=" * 40)
    print("Batch Ingestion Results")
    print("=" * 40)

    for result in results:
        icon = "✓" if result.status == "success" else "✗" if result.status == "failed" else "⊘"
        update = " (update)" if result.is_update else ""
        print(f"  {icon} {result.document_id}{update}")

    print("-" * 40)
    print(f"  Total:   {len(results)}")
    print(f"  Success: {success}")
    print(f"  Skipped: {skipped}")
    print(f"  Failed:  {failed}")
    print("=" * 40)


def print_status(status):
    """Print document status."""
    print("\n" + "=" * 40)
    print(f"Document: {status.doc_id}")
    print("=" * 40)
    print(f"  Path:      {status.file_path}")
    print(f"  Hash:      {status.file_hash}")
    print(f"  Size:      {status.file_size} bytes")
    print(f"  Status:    {status.status}")
    print(f"  Chunks:    {status.chunk_count}")
    print(f"  Entities:  {status.entity_count}")
    print(f"  Created:   {status.created_at}")
    print(f"  Updated:   {status.updated_at}")

    if status.error_message:
        print(f"  Error:     {status.error_message}")
    print("=" * 40)


def print_status_table(statuses):
    """Print status table."""
    print("\n" + "=" * 80)
    print("Document Status")
    print("=" * 80)
    print(f"{'ID':<20} {'Status':<12} {'Chunks':<8} {'Entities':<10} {'Path'}")
    print("-" * 80)

    for s in statuses:
        icon = "✓" if s.status == "completed" else "✗" if s.status == "failed" else "○"
        print(f"{s.doc_id:<20} {icon} {s.status:<10} {s.chunk_count:<8} {s.entity_count:<10} {s.file_path}")

    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Incremental document ingestion")
    subparsers = parser.add_subparsers(dest="command", help="Command")

    # Ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Ingest documents")
    ingest_parser.add_argument("--file", "-f", help="Single file to ingest")
    ingest_parser.add_argument("--directory", "-d", help="Directory to ingest")
    ingest_parser.add_argument("--force", action="store_true", help="Force re-ingestion")

    # Status command
    status_parser = subparsers.add_parser("status", help="Show document status")
    status_parser.add_argument("--doc-id", help="Document ID")

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete document")
    delete_parser.add_argument("--doc-id", required=True, help="Document ID")

    # Cleanup command
    subparsers.add_parser("cleanup", help="Clean up orphaned entities")

    # Stats command
    subparsers.add_parser("stats", help="Show statistics")

    args = parser.parse_args()

    # Configure logging
    logger.remove()
    logger.add(sys.stderr, level="INFO")

    if args.command == "ingest":
        cmd_ingest(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "delete":
        cmd_delete(args)
    elif args.command == "cleanup":
        cmd_cleanup(args)
    elif args.command == "stats":
        cmd_stats(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
