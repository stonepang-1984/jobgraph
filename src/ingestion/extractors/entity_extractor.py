"""Entity and relation extraction using LLM."""

from typing import Optional

from pydantic import BaseModel, Field
from loguru import logger

from config.settings import settings


class Entity(BaseModel):
    """Extracted entity."""

    name: str = Field(description="Entity name (normalized)")
    type: str = Field(description="Entity type: PERSON/ORG/LOCATION/EVENT/CONCEPT/PRODUCT/TECH/METRIC")
    description: str = Field(description="Brief description of the entity")
    aliases: list[str] = Field(default_factory=list, description="Entity aliases")


class Relation(BaseModel):
    """Extracted relation."""

    source: str = Field(description="Source entity name")
    target: str = Field(description="Target entity name")
    type: str = Field(description="Relation type")
    description: str = Field(description="Relation description")
    evidence: str = Field(description="Evidence from original text")


class ExtractionResult(BaseModel):
    """Result of entity and relation extraction."""

    entities: list[Entity] = Field(default_factory=list)
    relations: list[Relation] = Field(default_factory=list)


ENTITY_EXTRACTION_PROMPT = """你是一个专业的知识图谱构建专家。请从给定文本中提取所有实体和关系。

实体类型包括:
- PERSON: 人物
- ORG: 组织机构
- LOCATION: 地点
- EVENT: 事件
- CONCEPT: 概念/理论
- PRODUCT: 产品
- TECH: 技术/工具
- METRIC: 指标/数据

关系类型包括:
- WORKS_FOR: 工作于
- LOCATED_IN: 位于
- PART_OF: 属于/包含
- CAUSES: 导致
- USES: 使用
- PRODUCES: 生产
- RELATED_TO: 相关
- COMPETES_WITH: 竞争
- DEPENDS_ON: 依赖
- INCLUDES: 包括

请确保:
1. 实体名称使用规范形式（统一别名）
2. 关系要有原文证据支持
3. 不要遗漏重要实体和关系

请以JSON格式返回结果。"""


class EntityRelationExtractor:
    """Extract entities and relations from text using LLM."""

    def __init__(self, llm=None):
        self._llm = llm

    @property
    def llm(self):
        if self._llm is None:
            self._load_llm()
        return self._llm

    def _load_llm(self) -> None:
        """Load LLM model."""
        from langchain_openai import ChatOpenAI

        self._llm = ChatOpenAI(
            model=settings.llm.openai_model,
            api_key=settings.llm.openai_api_key,
            base_url=settings.llm.openai_api_base,
            temperature=0,
        )

    def extract(self, text: str) -> ExtractionResult:
        """Extract entities and relations from text."""
        from langchain_core.prompts import ChatPromptTemplate

        prompt = ChatPromptTemplate.from_messages([
            ("system", ENTITY_EXTRACTION_PROMPT),
            ("human", "请从以下文本中提取实体和关系:\n\n{text}"),
        ])

        chain = prompt | self.llm.with_structured_output(ExtractionResult)

        try:
            result = chain.invoke({"text": text})
            return result
        except Exception as e:
            logger.warning(f"Extraction failed: {e}")
            return ExtractionResult(entities=[], relations=[])

    def extract_batch(self, texts: list[str]) -> list[ExtractionResult]:
        """Extract from multiple texts."""
        results = []
        for i, text in enumerate(texts):
            logger.debug(f"Extracting from text {i + 1}/{len(texts)}")
            result = self.extract(text)
            results.append(result)
        return results


# Singleton instance
entity_extractor = EntityRelationExtractor()
