"""Streamlit web interface for Multimodal Graph RAG."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
from loguru import logger

from config.settings import settings


st.set_page_config(
    page_title="Multimodal Graph RAG",
    page_icon="🔗",
    layout="wide",
)

st.title("🔗 Multimodal Graph RAG")
st.markdown("基于知识图谱的多模态检索增强生成系统")


# Sidebar
with st.sidebar:
    st.header("设置")

    # File upload
    st.subheader("📄 文档上传")
    uploaded_file = st.file_uploader(
        "选择文件",
        type=["pdf", "docx", "txt", "md"],
        help="支持 PDF、DOCX、TXT、Markdown 格式",
    )

    if uploaded_file and st.button("处理文档"):
        with st.spinner("正在处理文档..."):
            try:
                import tempfile
                import os

                # Save uploaded file
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=Path(uploaded_file.name).suffix
                ) as tmp:
                    tmp.write(uploaded_file.getbuffer())
                    tmp_path = tmp.name

                # Process
                from src.ingestion.pipeline import text_pipeline

                result = text_pipeline.ingest(tmp_path)

                st.success(f"处理完成!")
                st.json({
                    "chunks": result.chunk_count,
                    "entities": result.entity_count,
                    "relations": result.relation_count,
                })

                # Cleanup
                os.unlink(tmp_path)

            except Exception as e:
                st.error(f"处理失败: {e}")

    # Stats
    st.subheader("📊 知识图谱统计")
    if st.button("刷新统计"):
        try:
            from src.graph.neo4j_client import neo4j_client

            stats = {
                "文档数": neo4j_client.get_node_count("Document"),
                "文本块数": neo4j_client.get_node_count("TextChunk"),
                "实体数": neo4j_client.get_node_count("Entity"),
                "社区数": neo4j_client.get_node_count("Community"),
                "关系数": neo4j_client.get_relationship_count(),
            }
            st.json(stats)
        except Exception as e:
            st.error(f"获取统计失败: {e}")


# Main area
tab1, tab2 = st.tabs(["💬 查询", "🔍 图探索"])

with tab1:
    st.header("知识问答")

    # Query input
    question = st.text_input(
        "输入你的问题",
        placeholder="例如: 张三在哪个部门工作？",
    )

    if st.button("查询", type="primary") and question:
        with st.spinner("正在检索和生成回答..."):
            try:
                from src.retrieval.hybrid_retriever import query_engine

                result = query_engine.query(question)

                # Display answer
                st.subheader("回答")
                st.write(result["answer"])

                # Display citations
                if result["citations"]:
                    st.subheader("引用")
                    for cite in result["citations"]:
                        st.caption(f"📌 {cite['text']}")

                # Display sources
                if result["sources"]:
                    with st.expander("查看来源详情"):
                        for src in result["sources"][:10]:
                            st.markdown(
                                f"**[{src['modality']}]** {src['content'][:200]}..."
                            )

                # Confidence
                confidence = result["confidence"]
                color = (
                    "green" if confidence > 0.7
                    else "orange" if confidence > 0.4
                    else "red"
                )
                st.markdown(
                    f"置信度: :{color}[{confidence:.2f}]"
                )

            except Exception as e:
                st.error(f"查询失败: {e}")
                logger.exception(e)

with tab2:
    st.header("图谱探索")

    entity_name = st.text_input(
        "输入实体名称",
        placeholder="例如: 张三",
    )

    if st.button("探索") and entity_name:
        with st.spinner("正在查询..."):
            try:
                from src.retrieval.graph_retriever import graph_retriever

                neighbors = graph_retriever.retrieve_entity_neighbors(
                    entity_name, limit=20
                )

                if neighbors:
                    st.subheader(f"与 {entity_name} 相关的实体")

                    for n in neighbors:
                        st.markdown(f"- {n.content}")
                else:
                    st.info("未找到相关实体")

            except Exception as e:
                st.error(f"查询失败: {e}")


# Footer
st.divider()
st.caption("Multimodal Graph RAG v0.1.0 | Powered by Neo4j + LangChain")
