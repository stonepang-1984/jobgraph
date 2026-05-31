"""People Graph Visualization - Streamlit App with interactive graph."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import json
from loguru import logger

from src.graph.people.manager import people_manager


# ============================================================
# Page Config
# ============================================================

st.set_page_config(
    page_title="人物关系图谱",
    page_icon="👥",
    layout="wide",
)

st.title("👥 人物关系图谱")
st.markdown("探索人物、企业、学校之间的关系网络")


# ============================================================
# Helper Functions
# ============================================================

def get_person_network_data(person_id: str, depth: int = 2) -> dict:
    """Get person network data for visualization."""
    cypher = """
    MATCH path = (p:Person {id: $person_id})-[*1..""" + str(depth) + """]-(connected)
    WHERE connected:Person OR connected:Company OR connected:University
    WITH nodes(path) AS path_nodes, relationships(path) AS path_rels
    UNWIND path_nodes AS node
    UNWIND path_rels AS rel
    RETURN DISTINCT
           labels(node)[0] AS node_type,
           node.id AS node_id,
           node.name AS node_name,
           node.name_en AS node_name_en,
           type(rel) AS rel_type,
           startNode(rel).id AS rel_start,
           endNode(rel).id AS rel_end,
           properties(rel) AS rel_props
    LIMIT 200
    """
    from src.graph.neo4j_client import neo4j_client
    return neo4j_client.execute_query(cypher, {"person_id": person_id})


def build_vis_graph(data: list[dict], center_id: str) -> dict:
    """Build vis.js compatible graph data."""
    nodes = {}
    edges = []

    # Color mapping
    colors = {
        "Person": "#4F46E5",  # Indigo
        "Company": "#059669",  # Emerald
        "University": "#D97706",  # Amber
    }

    # Shape mapping
    shapes = {
        "Person": "circularImage",
        "Company": "box",
        "University": "diamond",
    }

    for item in data:
        # Add nodes
        node_id = item["node_id"]
        if node_id not in nodes:
            node_type = item["node_type"]
            is_center = node_id == center_id

            nodes[node_id] = {
                "id": node_id,
                "label": item["node_name"],
                "title": f"{item['node_name']} ({node_type})",
                "color": {
                    "background": "#FF6B6B" if is_center else colors.get(node_type, "#999"),
                    "border": "#FF0000" if is_center else colors.get(node_type, "#666"),
                },
                "shape": shapes.get(node_type, "dot"),
                "size": 40 if is_center else 25,
                "font": {"size": 14, "color": "#333"},
                "borderWidth": 3 if is_center else 1,
                "nodeType": node_type,
            }

        # Add edges
        rel_start = item["rel_start"]
        rel_end = item["rel_end"]
        rel_type = item["rel_type"]

        edge_id = f"{rel_start}_{rel_end}_{rel_type}"
        edge = {
            "id": edge_id,
            "from": rel_start,
            "to": rel_end,
            "label": rel_type,
            "arrows": "to",
            "font": {"size": 10, "align": "middle"},
            "color": {"color": "#666", "highlight": "#333"},
            "smooth": {"type": "curvedCW", "roundness": 0.2},
        }

        # Add edge properties
        props = item.get("rel_props", {})
        if props.get("position"):
            edge["label"] = props["position"]
        elif props.get("degree"):
            edge["label"] = props["degree"]

        edges.append(edge)

    return {
        "nodes": list(nodes.values()),
        "edges": edges,
    }


# ============================================================
# Sidebar
# ============================================================

with st.sidebar:
    st.header("🔍 搜索")

    # Search box
    search_query = st.text_input("搜索人物", placeholder="输入姓名...")

    if search_query:
        results = people_manager.search_persons(search_query)
        if results:
            st.subheader("搜索结果")
            for r in results:
                person = r.get("p", {})
                if st.button(
                    f"{person.get('name', '')}",
                    key=f"search_{person.get('id', '')}",
                ):
                    st.session_state.selected_person = person.get("id", "")
                    st.rerun()
        else:
            st.info("未找到匹配的人物")

    st.divider()

    # Statistics
    st.header("📊 统计")
    try:
        stats = people_manager.get_stats()
        col1, col2 = st.columns(2)
        col1.metric("人物", stats.get("persons", 0))
        col2.metric("企业", stats.get("companies", 0))
        col1.metric("高校", stats.get("universities", 0))
        col2.metric("任职关系", stats.get("work_rels", 0))
    except Exception as e:
        st.error(f"获取统计失败: {e}")

    st.divider()

    # Quick select
    st.header("⚡ 快速选择")
    quick_persons = [
        ("person_mahuateng", "马化腾"),
        ("person_jackma", "马云"),
        ("person_liyanhong", "李彦宏"),
        ("person_zhangyiming", "张一鸣"),
        ("person_rengfei", "任正非"),
        ("person_leijun", "雷军"),
        ("person_wangxing", "王兴"),
        ("person_liuqiangdong", "刘强东"),
    ]

    for pid, name in quick_persons:
        if st.button(name, key=f"quick_{pid}"):
            st.session_state.selected_person = pid
            st.rerun()


# ============================================================
# Main Content
# ============================================================

# Initialize session state
if "selected_person" not in st.session_state:
    st.session_state.selected_person = "person_mahuateng"

selected_id = st.session_state.selected_person

# Get person info
person_info = people_manager.get_person(selected_id)

if not person_info:
    st.error("未找到该人物信息")
    st.stop()

person = person_info.get("p", {})
work_history = person_info.get("work_history", [])
education = person_info.get("education", [])

# ============================================================
# Person Info Card
# ============================================================

col1, col2 = st.columns([1, 3])

with col1:
    # Avatar placeholder
    st.markdown(
        f"""
        <div style="text-align: center; padding: 20px;">
            <div style="width: 120px; height: 120px; border-radius: 50%; background: #4F46E5; 
                        display: flex; align-items: center; justify-content: center; margin: 0 auto;">
                <span style="color: white; font-size: 48px;">{person.get('name', '?')[0]}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.subheader(person.get("name", ""))

    if person.get("name_en"):
        st.caption(person["name_en"])

    if person.get("bio"):
        st.write(person["bio"])

    # Tags
    tags = person.get("tags", [])
    if tags:
        tag_html = " ".join([f'<span class="tag">{t}</span>' for t in tags])
        st.markdown(tag_html, unsafe_allow_html=True)

    # Work history
    if work_history:
        st.markdown("**🏢 工作经历**")
        for work in work_history:
            if work.get("company"):
                current = "🟢" if work.get("is_current") else "⚪"
                st.markdown(f"{current} **{work['company']}** - {work.get('position', '')}")

    # Education
    if education:
        st.markdown("**🎓 教育背景**")
        for edu in education:
            if edu.get("university"):
                degree = edu.get("degree", "")
                major = edu.get("major", "")
                st.markdown(f"📚 **{edu['university']}** {degree} {major}")


# ============================================================
# Network Graph
# ============================================================

st.divider()
st.subheader("🔗 关系网络")

# Graph options
col1, col2, col3 = st.columns(3)
with col1:
    depth = st.slider("网络深度", 1, 3, 2)
with col2:
    show_companies = st.checkbox("显示企业", True)
with col3:
    show_universities = st.checkbox("显示高校", True)

# Get network data
try:
    network_data = get_person_network_data(selected_id, depth)

    if network_data:
        graph = build_vis_graph(network_data, selected_id)

        # Filter nodes
        if not show_companies:
            graph["nodes"] = [n for n in graph["nodes"] if n.get("nodeType") != "Company"]
        if not show_universities:
            graph["nodes"] = [n for n in graph["nodes"] if n.get("nodeType") != "University"]

        # Render with vis.js
        graph_json = json.dumps(graph)

        st.components.v1.html(
            f"""
            <div id="graph-container" style="width: 100%; height: 600px; border: 1px solid #ddd; border-radius: 8px;"></div>
            <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
            <script>
                var container = document.getElementById('graph-container');
                var data = {graph_json};
                
                var options = {{
                    nodes: {{
                        font: {{
                            size: 14,
                            face: 'Arial'
                        }},
                        borderWidth: 2,
                        shadow: true
                    }},
                    edges: {{
                        font: {{
                            size: 10,
                            align: 'middle'
                        }},
                        color: {{
                            color: '#666',
                            highlight: '#333',
                            hover: '#333'
                        }},
                        smooth: {{
                            type: 'curvedCW',
                            roundness: 0.2
                        }}
                    }},
                    physics: {{
                        barnesHut: {{
                            gravitationalConstant: -2000,
                            centralGravity: 0.1,
                            springLength: 150,
                            springConstant: 0.04,
                            damping: 0.09
                        }},
                        stabilization: {{
                            iterations: 100
                        }}
                    }},
                    interaction: {{
                        hover: true,
                        tooltipDelay: 200,
                        zoomView: true,
                        dragView: true
                    }}
                }};
                
                var network = new vis.Network(container, data, options);
                
                // Click event
                network.on('click', function(params) {{
                    if (params.nodes.length > 0) {{
                        var nodeId = params.nodes[0];
                        // Send to Streamlit
                        window.parent.postMessage({{
                            type: 'streamlit:setComponentValue',
                            value: nodeId
                        }}, '*');
                    }}
                }});
            </script>
            """,
            height=650,
        )

        # Legend
        st.markdown(
            """
            <div style="display: flex; gap: 20px; margin-top: 10px;">
                <div><span style="color: #4F46E5;">●</span> 人物</div>
                <div><span style="color: #059669;">■</span> 企业</div>
                <div><span style="color: #D97706;">◆</span> 高校</div>
                <div><span style="color: #FF6B6B;">●</span> 当前选择</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.info("暂无关系数据")

except Exception as e:
    st.error(f"加载图谱失败: {e}")
    logger.exception(e)


# ============================================================
# Timeline
# ============================================================

st.divider()
st.subheader("📅 时间线")

try:
    timeline = people_manager.get_person_timeline(selected_id)

    if timeline:
        for item in timeline:
            icon = "🏢" if item.get("type") == "work" else "🎓"
            name = item.get("name", "")
            start = item.get("start_date", "")
            end = item.get("end_date", "至今") if item.get("is_current") else item.get("end_date", "")

            details = []
            if item.get("position"):
                details.append(item["position"])
            if item.get("degree"):
                details.append(item["degree"])
            if item.get("major"):
                details.append(item["major"])

            detail_str = " - ".join(details) if details else ""

            st.markdown(f"{icon} **{name}** {detail_str} `({start} - {end})`")
    else:
        st.info("暂无时间线数据")

except Exception as e:
    st.error(f"加载时间线失败: {e}")


# ============================================================
# Relations
# ============================================================

st.divider()
st.subheader("🤝 关联人物")

tab1, tab2 = st.tabs(["同事", "同学"])

with tab1:
    try:
        colleagues = people_manager.get_colleagues(selected_id)
        if colleagues:
            for c in colleagues:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"👤 **{c['name']}** @ {c['company']}")
                with col2:
                    if st.button("查看", key=f"colleague_{c['id']}"):
                        st.session_state.selected_person = c["id"]
                        st.rerun()
        else:
            st.info("暂无同事数据")
    except Exception as e:
        st.error(f"获取同事数据失败: {e}")

with tab2:
    try:
        classmates = people_manager.get_classmates(selected_id)
        if classmates:
            for c in classmates:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"👤 **{c['name']}** @ {c['university']}")
                with col2:
                    if st.button("查看", key=f"classmate_{c['id']}"):
                        st.session_state.selected_person = c["id"]
                        st.rerun()
        else:
            st.info("暂无同学数据")
    except Exception as e:
        st.error(f"获取同学数据失败: {e}")


# ============================================================
# Find Connection
# ============================================================

st.divider()
st.subheader("🔍 查找关系路径")

col1, col2 = st.columns(2)

with col1:
    person1 = st.text_input("人物1", value=person.get("name", ""), key="person1_input")

with col2:
    person2 = st.text_input("人物2", placeholder="输入另一个人物姓名...", key="person2_input")

if st.button("查找路径") and person2:
    # Search for person2
    results = people_manager.search_persons(person2)
    if results:
        person2_id = results[0].get("p", {}).get("id", "")
        if person2_id:
            path = people_manager.find_connection(selected_id, person2_id)
            if path:
                st.success(f"找到关系路径 (跳数: {path[0].get('hops', 0)})")
                for p in path:
                    nodes = p.get("nodes", [])
                    rels = p.get("relationships", [])

                    # Display path
                    path_str = " → ".join([n["name"] for n in nodes])
                    st.markdown(f"**路径:** {path_str}")

                    # Display relationships
                    for i, rel in enumerate(rels):
                        st.caption(f"  ↳ {rel['type']}: {rel.get('properties', {}).get('position', '')}")
            else:
                st.warning("未找到关系路径")
    else:
        st.warning(f"未找到人物: {person2}")


# ============================================================
# Footer
# ============================================================

st.divider()
st.caption("人物关系图谱 v1.0 | 数据来源: Wikipedia / 手动录入")
