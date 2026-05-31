"""Table processing pipeline."""

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
from loguru import logger

from config.settings import settings
from src.embeddings.text_embedder import TextEmbedder, text_embedder


@dataclass
class TableData:
    """Processed table data."""

    id: str
    caption: str = ""
    headers: list[str] = field(default_factory=list)
    row_count: int = 0
    col_count: int = 0
    markdown_repr: str = ""
    summary: str = ""
    embedding: list[float] = field(default_factory=list)
    page_number: int | None = None
    bbox: dict | None = None
    source_path: str | None = None


class TableProcessor:
    """Process tables from various sources."""

    def __init__(self, embedder: TextEmbedder = None):
        self.embedder = embedder or text_embedder

    def process_dataframe(
        self,
        df: pd.DataFrame,
        caption: str = "",
        page_number: int | None = None,
        source_path: str | None = None,
    ) -> TableData:
        """Process a pandas DataFrame."""
        import hashlib

        table_id = hashlib.md5(f"{source_path}_{caption}".encode()).hexdigest()[:16]

        # Generate markdown
        markdown = df.to_markdown(index=False)

        # Generate summary
        summary = self._generate_summary(markdown, caption)

        # Generate embedding
        text_for_embedding = f"{caption}\n{summary}"
        embedding = self.embedder.embed(text_for_embedding)

        return TableData(
            id=table_id,
            caption=caption,
            headers=list(df.columns),
            row_count=len(df),
            col_count=len(df.columns),
            markdown_repr=markdown,
            summary=summary,
            embedding=embedding,
            page_number=page_number,
            source_path=source_path,
        )

    def process_csv(self, csv_path: str | Path, caption: str = "") -> TableData:
        """Process a CSV file."""
        path = Path(csv_path)
        df = pd.read_csv(path)
        return self.process_dataframe(df, caption=caption, source_path=str(path))

    def process_excel(self, excel_path: str | Path, sheet_name: str = None) -> list[TableData]:
        """Process an Excel file."""
        path = Path(excel_path)
        xls = pd.ExcelFile(path)

        tables = []
        for sheet in xls.sheet_names:
            if sheet_name and sheet != sheet_name:
                continue
            df = pd.read_excel(path, sheet_name=sheet)
            table = self.process_dataframe(df, caption=f"Sheet: {sheet}", source_path=str(path))
            tables.append(table)

        return tables

    def _generate_summary(self, markdown: str, caption: str) -> str:
        """Generate table summary using LLM."""
        try:
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(
                model=settings.llm.openai_model,
                api_key=settings.llm.openai_api_key,
                base_url=settings.llm.openai_api_base,
                temperature=0,
            )

            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", "你是一个数据分析专家。请分析表格内容，提取关键信息、趋势、极值。"),
                    ("human", "表格标题: {caption}\n\n表格内容:\n{markdown}\n\n请提供简洁的表格摘要。"),
                ]
            )

            chain = prompt | llm
            response = chain.invoke({"caption": caption, "markdown": markdown})

            return response.content

        except Exception as e:
            logger.warning(f"Summary generation failed: {e}")
            return f"Table with {len(markdown)} chars"


# Singleton instance
table_processor = TableProcessor()
