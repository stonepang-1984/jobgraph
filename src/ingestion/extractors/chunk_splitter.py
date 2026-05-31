"""Text chunking with semantic awareness."""

from dataclasses import dataclass, field

import tiktoken
from loguru import logger

from config.settings import settings


@dataclass
class TextChunk:
    """Represents a text chunk."""

    id: str
    content: str
    document_id: str
    chunk_index: int
    metadata: dict = field(default_factory=dict)
    token_count: int = 0
    page_number: int | None = None


class SemanticChunkSplitter:
    """Split text into semantic chunks with header awareness."""

    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
    ):
        self.chunk_size = chunk_size or settings.processing.chunk_size
        self.chunk_overlap = chunk_overlap or settings.processing.chunk_overlap
        self.tokenizer = tiktoken.get_encoding("cl100k_base")

    def split(self, text: str, document_id: str) -> list[TextChunk]:
        """Split text into chunks with semantic awareness."""
        logger.info(f"Splitting document {document_id} into chunks")

        # Try markdown header splitting first
        if self._is_markdown(text):
            chunks = self._split_markdown(text, document_id)
        else:
            chunks = self._split_recursive(text, document_id)

        logger.info(f"Created {len(chunks)} chunks")
        return chunks

    def _is_markdown(self, text: str) -> bool:
        """Check if text is markdown format."""
        import re

        return bool(re.search(r"^#{1,6}\s", text, re.MULTILINE))

    def _split_markdown(self, text: str, document_id: str) -> list[TextChunk]:
        """Split markdown by headers then by size."""
        import re

        # Split by headers
        sections = re.split(r"(?=^#{1,6}\s)", text, flags=re.MULTILINE)
        sections = [s.strip() for s in sections if s.strip()]

        chunks = []
        chunk_index = 0

        for section in sections:
            # Extract header
            header_match = re.match(r"^(#{1,6})\s+(.+)$", section, re.MULTILINE)
            header = header_match.group(2) if header_match else ""

            # If section is small enough, keep as one chunk
            token_count = self._token_count(section)
            if token_count <= self.chunk_size:
                chunks.append(
                    TextChunk(
                        id=f"{document_id}_chunk_{chunk_index}",
                        content=section,
                        document_id=document_id,
                        chunk_index=chunk_index,
                        token_count=token_count,
                        metadata={"header": header},
                    )
                )
                chunk_index += 1
            else:
                # Split large section recursively
                sub_chunks = self._split_recursive(section, document_id, start_index=chunk_index)
                for chunk in sub_chunks:
                    chunk.metadata["header"] = header
                chunks.extend(sub_chunks)
                chunk_index += len(sub_chunks)

        return chunks

    def _split_recursive(self, text: str, document_id: str, start_index: int = 0) -> list[TextChunk]:
        """Split text recursively by separators."""
        separators = ["\n\n", "\n", "。", "！", "？", "；", "，", ".", "!", "?", ";", ",", " "]

        chunks = []
        parts = self._split_by_separators(text, separators)

        current_chunk = ""
        current_tokens = 0
        chunk_index = start_index

        for part in parts:
            part_tokens = self._token_count(part)

            if current_tokens + part_tokens > self.chunk_size:
                if current_chunk:
                    chunks.append(
                        TextChunk(
                            id=f"{document_id}_chunk_{chunk_index}",
                            content=current_chunk.strip(),
                            document_id=document_id,
                            chunk_index=chunk_index,
                            token_count=current_tokens,
                        )
                    )
                    chunk_index += 1

                    # Handle overlap
                    overlap_text = self._get_overlap_text(current_chunk)
                    current_chunk = overlap_text + part
                    current_tokens = self._token_count(current_chunk)
                else:
                    current_chunk = part
                    current_tokens = part_tokens
            else:
                current_chunk += part
                current_tokens += part_tokens

        # Add remaining chunk
        if current_chunk.strip():
            chunks.append(
                TextChunk(
                    id=f"{document_id}_chunk_{chunk_index}",
                    content=current_chunk.strip(),
                    document_id=document_id,
                    chunk_index=chunk_index,
                    token_count=current_tokens,
                )
            )

        return chunks

    def _split_by_separators(self, text: str, separators: list[str]) -> list[str]:
        """Split text by separators recursively."""
        if not separators:
            return [text]

        sep = separators[0]
        remaining_separators = separators[1:]

        parts = text.split(sep)

        if len(parts) == 1:
            return self._split_by_separators(text, remaining_separators)

        result = []
        for i, part in enumerate(parts):
            if not part.strip():
                continue

            if self._token_count(part) > self.chunk_size and remaining_separators:
                result.extend(self._split_by_separators(part, remaining_separators))
            else:
                if i > 0:
                    result.append(sep + part)
                else:
                    result.append(part)

        return result

    def _get_overlap_text(self, text: str) -> str:
        """Get overlap text from the end of current chunk."""
        tokens = self.tokenizer.encode(text)
        if len(tokens) <= self.chunk_overlap:
            return text
        overlap_tokens = tokens[-self.chunk_overlap :]
        return self.tokenizer.decode(overlap_tokens)

    def _token_count(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.tokenizer.encode(text))
