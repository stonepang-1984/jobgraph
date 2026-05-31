import atexit
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

from neo4j import Driver, GraphDatabase, Session, ManagedTransaction
from loguru import logger

from config.settings import settings


class Neo4jClient:
    """Neo4j database client with connection pooling."""

    _instance: Optional["Neo4jClient"] = None
    _driver: Optional[Driver] = None

    def __new__(cls) -> "Neo4jClient":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        if self._driver is None:
            self._connect()
            atexit.register(self.close)

    def _connect(self) -> None:
        """Initialize Neo4j driver with connection pool."""
        try:
            self._driver = GraphDatabase.driver(
                settings.neo4j.uri,
                auth=(settings.neo4j.username, settings.neo4j.password),
                max_connection_pool_size=settings.neo4j.max_connection_pool_size,
                connection_acquisition_timeout=settings.neo4j.connection_acquisition_timeout,
            )
            self._driver.verify_connectivity()
            logger.info(f"Connected to Neo4j at {settings.neo4j.uri}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise

    @property
    def driver(self) -> Driver:
        if self._driver is None:
            self._connect()
        return self._driver  # type: ignore

    def close(self) -> None:
        """Close the Neo4j driver."""
        if self._driver is not None:
            self._driver.close()
            self._driver = None
            logger.info("Neo4j connection closed")

    @contextmanager
    def session(self, database: Optional[str] = None):
        """Context manager for Neo4j session."""
        db = database or settings.neo4j.database
        session = self.driver.session(database=db)
        try:
            yield session
        finally:
            session.close()

    def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Execute a Cypher query and return results as list of dicts."""
        with self.session(database) as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]

    def execute_write(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None,
    ) -> Any:
        """Execute a write transaction."""
        with self.session(database) as session:
            def _tx_func(tx: ManagedTransaction) -> Any:
                result = tx.run(query, parameters or {})
                return [record.data() for record in result]

            return session.execute_write(_tx_func)

    def execute_read(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Execute a read transaction."""
        with self.session(database) as session:
            def _tx_func(tx: ManagedTransaction) -> List[Dict[str, Any]]:
                result = tx.run(query, parameters or {})
                return [record.data() for record in result]

            return session.execute_read(_tx_func)

    def execute_batch(
        self,
        query: str,
        parameters_list: List[Dict[str, Any]],
        database: Optional[str] = None,
        batch_size: int = 1000,
    ) -> None:
        """Execute a query in batches."""
        with self.session(database) as session:
            for i in range(0, len(parameters_list), batch_size):
                batch = parameters_list[i : i + batch_size]
                session.run(
                    "UNWIND $batch AS row " + query,
                    {"batch": batch},
                )
                logger.debug(f"Executed batch {i // batch_size + 1}")

    def check_connectivity(self) -> bool:
        """Check if the connection is alive."""
        try:
            self.driver.verify_connectivity()
            return True
        except Exception:
            return False

    def get_node_count(self, label: Optional[str] = None) -> int:
        """Get count of nodes, optionally filtered by label."""
        if label:
            query = f"MATCH (n:{label}) RETURN count(n) AS count"
        else:
            query = "MATCH (n) RETURN count(n) AS count"
        result = self.execute_query(query)
        return result[0]["count"] if result else 0

    def get_relationship_count(self, rel_type: Optional[str] = None) -> int:
        """Get count of relationships, optionally filtered by type."""
        if rel_type:
            query = f"MATCH ()-[r:{rel_type}]->() RETURN count(r) AS count"
        else:
            query = "MATCH ()-[r]->() RETURN count(r) AS count"
        result = self.execute_query(query)
        return result[0]["count"] if result else 0


# Singleton instance
neo4j_client = Neo4jClient()
