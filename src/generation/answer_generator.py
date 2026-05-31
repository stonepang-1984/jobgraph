"""Answer generation with citations."""

from dataclasses import dataclass, field

from loguru import logger

from config.settings import settings
from src.retrieval.vector_retriever import RetrievalResult


@dataclass
class Answer:
    """Generated answer with citations."""

    text: str
    citations: list[dict] = field(default_factory=list)
    sources: list[RetrievalResult] = field(default_factory=list)
    confidence: float = 0.0


SYSTEM_PROMPT = """你是一个多模态知识问答助手。基于提供的上下文信息回答用户问题。

规则：
1. 只基于提供的上下文回答，不要编造信息
2. 如果上下文信息不足，明确说明
3. 在回答中标注信息来源，格式: [来源: 文档名/页码]
4. 对于图片、表格等非文本信息，在回答中说明引用
5. 如果是对比/分析类问题，结构化呈现
6. 使用中文回答"""


class AnswerGenerator:
    """Generate answers from retrieved context."""

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

    def generate(self, query: str, context: list[RetrievalResult]) -> Answer:
        """Generate answer from query and context."""
        # Build context text
        context_text = self._build_context(context)

        # Generate answer
        from langchain_core.prompts import ChatPromptTemplate

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT),
                (
                    "human",
                    "上下文信息:\n{context}\n\n用户问题: {query}\n\n请基于上述上下文信息，提供详细、准确的回答，并标注信息来源。",
                ),
            ]
        )

        chain = prompt | self.llm

        try:
            response = chain.invoke(
                {
                    "context": context_text,
                    "query": query,
                }
            )
            answer_text = response.content
        except Exception as e:
            logger.error(f"Answer generation failed: {e}")
            answer_text = "抱歉，生成回答时出现错误。"

        # Extract citations
        citations = self._extract_citations(answer_text, context)

        return Answer(
            text=answer_text,
            citations=citations,
            sources=context,
            confidence=self._estimate_confidence(context),
        )

    def _build_context(self, results: list[RetrievalResult]) -> str:
        """Build context text from retrieval results."""
        parts = []

        for i, result in enumerate(results, 1):
            if result.modality == "text":
                source = result.source or "未知来源"
                parts.append(f"[{i}] [来源: {source}] {result.content}")
            elif result.modality == "entity":
                parts.append(f"[{i}] [实体] {result.content}")
            elif result.modality == "community":
                parts.append(f"[{i}] [社区] {result.content}")
            elif result.modality == "graph_path":
                parts.append(f"[{i}] [关系路径] {result.content}")
            else:
                parts.append(f"[{i}] {result.content}")

        return "\n\n".join(parts)

    def _extract_citations(self, answer: str, context: list[RetrievalResult]) -> list[dict]:
        """Extract citations from answer."""
        import re

        citations = []
        # Find [来源: ...] patterns
        pattern = r"\[来源:\s*(.+?)\]"
        matches = re.findall(pattern, answer)

        for match in matches:
            citations.append({"text": match, "type": "inline"})

        return citations

    def _estimate_confidence(self, context: list[RetrievalResult]) -> float:
        """Estimate answer confidence based on context quality."""
        if not context:
            return 0.0

        # Average score of top results
        top_scores = [r.score for r in context[:5]]
        avg_score = sum(top_scores) / len(top_scores) if top_scores else 0.0

        # Normalize to 0-1
        return min(avg_score, 1.0)


# Singleton instance
answer_generator = AnswerGenerator()
