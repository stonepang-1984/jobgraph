from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class Neo4jSettings(BaseSettings):
    uri: str = Field(default="bolt://localhost:7687", alias="NEO4J_URI")
    username: str = Field(default="neo4j", alias="NEO4J_USERNAME")
    password: str = Field(default="password123", alias="NEO4J_PASSWORD")
    database: str = Field(default="neo4j", alias="NEO4J_DATABASE")
    max_connection_pool_size: int = 50
    connection_acquisition_timeout: int = 60

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


class RedisSettings(BaseSettings):
    host: str = Field(default="localhost", alias="REDIS_HOST")
    port: int = Field(default=6379, alias="REDIS_PORT")
    db: int = Field(default=0, alias="REDIS_DB")
    password: str = Field(default="", alias="REDIS_PASSWORD")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    @property
    def url(self) -> str:
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class LLMSettings(BaseSettings):
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_api_base: str = Field(default="https://api.openai.com/v1", alias="OPENAI_API_BASE")
    openai_model: str = Field(default="gpt-4o", alias="OPENAI_MODEL")
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    ollama_model: str = Field(default="qwen2.5:14b", alias="OLLAMA_MODEL")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


class EmbeddingSettings(BaseSettings):
    text_model: str = Field(default="BAAI/bge-m3", alias="TEXT_EMBEDDING_MODEL")
    text_dimension: int = Field(default=1024, alias="TEXT_EMBEDDING_DIMENSION")
    clip_model: str = Field(default="openai/clip-vit-large-patch14-336", alias="CLIP_MODEL")
    clip_dimension: int = Field(default=768, alias="CLIP_EMBEDDING_DIMENSION")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


class ProcessingSettings(BaseSettings):
    chunk_size: int = Field(default=512, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=64, alias="CHUNK_OVERLAP")
    max_entities_per_chunk: int = Field(default=20, alias="MAX_ENTITIES_PER_CHUNK")
    max_relations_per_chunk: int = Field(default=30, alias="MAX_RELATIONS_PER_CHUNK")


class RetrievalSettings(BaseSettings):
    vector_top_k: int = Field(default=20, alias="VECTOR_TOP_K")
    graph_hop: int = Field(default=2, alias="GRAPH_HOP")
    rrf_k: int = Field(default=60, alias="RRF_K")
    rerank_top_k: int = Field(default=15, alias="RERANK_TOP_K")
    mmr_lambda: float = Field(default=0.7, alias="MMR_LAMBDA")


class Settings(BaseSettings):
    neo4j: Neo4jSettings = Neo4jSettings()
    redis: RedisSettings = RedisSettings()
    llm: LLMSettings = LLMSettings()
    embedding: EmbeddingSettings = EmbeddingSettings()
    processing: ProcessingSettings = ProcessingSettings()
    retrieval: RetrievalSettings = RetrievalSettings()

    data_dir: str = Field(default="./data", alias="DATA_DIR")
    raw_dir: str = Field(default="./data/raw", alias="RAW_DIR")
    processed_dir: str = Field(default="./data/processed", alias="PROCESSED_DIR")
    embeddings_dir: str = Field(default="./data/embeddings", alias="EMBEDDINGS_DIR")

    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_debug: bool = Field(default=True, alias="API_DEBUG")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_file: str = Field(default="./logs/app.log", alias="LOG_FILE")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
