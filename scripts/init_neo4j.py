"""Initialize Neo4j schema with constraints, indexes, and vector indexes."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from src.graph.neo4j_client import neo4j_client


SCHEMA_FILE = project_root / "config" / "neo4j_schema.cypher"


def read_schema_file() -> str:
    """Read the schema Cypher file."""
    if not SCHEMA_FILE.exists():
        logger.error(f"Schema file not found: {SCHEMA_FILE}")
        sys.exit(1)
    return SCHEMA_FILE.read_text(encoding="utf-8")


def split_statements(cypher_text: str) -> list[str]:
    """Split Cypher text into individual statements."""
    statements = []
    current = []

    for line in cypher_text.split("\n"):
        stripped = line.strip()

        # Skip empty lines and comments
        if not stripped or stripped.startswith("//"):
            continue

        current.append(line)

        # Check if statement ends with semicolon
        if stripped.endswith(";"):
            stmt = "\n".join(current).strip()
            if stmt:
                statements.append(stmt.rstrip(";"))
            current = []

    # Handle last statement without semicolon
    if current:
        stmt = "\n".join(current).strip()
        if stmt:
            statements.append(stmt)

    return statements


def execute_schema() -> None:
    """Execute all schema statements."""
    logger.info("Reading schema file...")
    schema_text = read_schema_file()

    statements = split_statements(schema_text)
    logger.info(f"Found {len(statements)} schema statements")

    success_count = 0
    error_count = 0

    for i, statement in enumerate(statements, 1):
        try:
            logger.debug(f"Executing statement {i}: {statement[:80]}...")
            neo4j_client.execute_query(statement)
            success_count += 1
        except Exception as e:
            error_count += 1
            logger.warning(f"Statement {i} failed (may already exist): {e}")

    logger.info(f"Schema initialization complete: {success_count} succeeded, {error_count} failed/already exist")


def verify_schema() -> None:
    """Verify the schema was created correctly."""
    logger.info("Verifying schema...")

    # Check constraints
    constraints = neo4j_client.execute_query("SHOW CONSTRAINTS")
    logger.info(f"Constraints: {len(constraints)}")

    # Check indexes
    indexes = neo4j_client.execute_query("SHOW INDEXES")
    logger.info(f"Indexes: {len(indexes)}")

    # Check vector indexes
    vector_indexes = [idx for idx in indexes if idx.get("type") == "VECTOR"]
    logger.info(f"Vector Indexes: {len(vector_indexes)}")

    # Check fulltext indexes
    fulltext_indexes = [idx for idx in indexes if idx.get("type") == "FULLTEXT"]
    logger.info(f"Fulltext Indexes: {len(fulltext_indexes)}")


def main() -> None:
    """Main entry point."""
    logger.info("=" * 60)
    logger.info("Neo4j Schema Initialization")
    logger.info("=" * 60)

    # Check connectivity
    if not neo4j_client.check_connectivity():
        logger.error("Cannot connect to Neo4j. Please ensure Neo4j is running.")
        sys.exit(1)

    logger.info("Connected to Neo4j successfully")

    # Execute schema
    execute_schema()

    # Verify
    verify_schema()

    logger.info("=" * 60)
    logger.info("Schema initialization complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
