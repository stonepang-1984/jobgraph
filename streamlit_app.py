"""Streamlit Cloud 入口文件

使用 SQLite 存储，无需 Neo4j 和 PyTorch
"""

import os
import sys
from pathlib import Path

# 设置环境变量（必须在导入其他模块之前）
os.environ["STORAGE_BACKEND"] = "sqlite"
os.environ["USE_TORCH"] = "false"
os.environ["DEMO_MODE"] = "true"
os.environ["TORCH_DISABLE_CUSTOM_CLASS_CHECK"] = "1"

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 确保数据目录存在
(project_root / "data").mkdir(exist_ok=True)

# 初始化数据库（如果需要）
import os
db_path = project_root / "data" / "jobgraph.db"
if not db_path.exists():
    from scripts.init_sqlite import import_initial_data
    import_initial_data()

# Streamlit 应用代码直接写在这里
# （因为 Streamlit Cloud 只能运行单个文件）

import streamlit as st
from datetime import datetime
from loguru import logger

# 导入项目模块
from src.jobgraph.graph_manager import job_manager
from src.jobgraph.models import CompanySize, UserProfile
from src.jobgraph.user.manager import user_manager
from src.jobgraph.resume import resume_parser, resume_extractor, privacy_filter
from src.jobgraph.resume.extractor import SKILL_STANDARD_MAP
from src.jobgraph.matching import job_matcher
from src.jobgraph.user_data_manager import user_data_manager
from src.jobgraph.notify import subscription_manager, notifier

# ============================================================
# Page Config
# ============================================================

st.set_page_config(
    page_title="JobGraph - 私密求职图谱",
    page_icon="🔒",
    layout="wide",
)

st.title("🔒 JobGraph - 私密求职图谱")
st.markdown("**你的求职，你做主** — 完全免费，数据仅存在本地")


# ============================================================
# Navigation
# ============================================================

pages = [
    "🏠 首页",
    "📄 简历管理",
    "🎯 智能匹配",
    "🔍 岗位搜索",
    "🔔 订阅提醒",
    "⚠️ 避坑指南",
    "📊 薪资行情",
]

current_page = st.session_state.get("page", pages[0])

with st.sidebar:
    st.markdown("### 🔍 功能导航")
    st.divider()
    
    for p in pages:
        if p == current_page:
            st.button(f"▶ {p}", key=f"nav_{p}", use_container_width=True, type="primary")
        else:
            if st.button(p, key=f"nav_{p}", use_container_width=True):
                st.session_state["page"] = p
                st.rerun()
    
    st.divider()
    st.success("🎁 **完全免费**")
    st.info("🔒 **私密模式**\\n\\n数据仅存在本地")

page = st.session_state.get("page", pages[0])


# ============================================================
# 首页
# ============================================================

if page == "🏠 首页":
    st.header("欢迎使用 JobGraph")
    
    st.markdown("""
    ### 🎯 核心功能
    
    | 功能 | 说明 |
    |------|------|
    | 📄 **简历管理** | 上传、预览、下载简历 |
    | 🎯 **智能匹配** | 两层匹配：字段初筛 + 语义匹配 |
    | 🔍 **岗位搜索** | 按薪资、地点、技能筛选 |
    | 🔔 **订阅提醒** | 订阅关键词，新职位提醒 |
    | ⚠️ **避坑指南** | 公司画像、风险评估 |
    """)
    
    # 数据统计
    try:
        stats = job_manager.get_stats()
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🏢 公司", stats.get("companies", 0))
        with col2:
            st.metric("💼 职位", stats.get("jobs", 0))
        with col3:
            st.metric("💬 评价", stats.get("reviews", 0))
    except Exception as e:
        st.info("💡 数据加载中...")


# ============================================================
# 简历管理
# ============================================================

elif page == "📄 简历管理":
    st.header("📄 简历管理")
    
    st.success("""
    🔒 **简历 100% 本地处理，绝不上传服务器**
    - 💾 简历文件仅保存在你的电脑
    - 🔐 解析过程在本地完成
    - 🛡️ 自动过滤隐私信息
    """)
    
    uploaded_file = st.file_uploader("选择简历文件", type=["pdf", "docx"])
    
    if uploaded_file:
        st.success(f"✅ 已选择文件: {uploaded_file.name}")
        
        with st.spinner("正在解析..."):
            try:
                text = resume_parser.parse_uploaded_file(uploaded_file)
                filtered_text = privacy_filter.filter(text)
                profile = resume_extractor.extract(filtered_text)
                
                st.subheader("📋 解析结果")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**当前职位**: {profile.current_title or '未识别'}")
                    st.write(f"**工作年限**: {profile.experience_years} 年")
                    st.write(f"**最高学历**: {profile.education or '未识别'}")
                
                with col2:
                    if profile.skills:
                        st.write(f"**技能** ({len(profile.skills)} 项):")
                        st.markdown(" ".join([f"`{s}`" for s in profile.skills[:15]]))
                
                # 保存到本地
                import hashlib
                user_id = hashlib.md5(user_manager.device_id.encode()).hexdigest()[:16]
                
                resume_data = {
                    "current_title": profile.current_title,
                    "experience_years": profile.experience_years,
                    "education": profile.education,
                    "skills": profile.skills,
                    "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
                user_data_manager.save_resume_profile(user_id, resume_data)
                st.session_state["resume_profile"] = resume_data
                
            except Exception as e:
                st.error(f"❌ 解析失败: {e}")


# ============================================================
# 智能匹配
# ============================================================

elif page == "🎯 智能匹配":
    st.header("🎯 智能匹配")
    
    st.info("填写期望职位信息，系统自动匹配")
    
    with st.form("match_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            job_title = st.text_input("期望职位", placeholder="如：后端工程师")
            skills = st.text_input("技能 (逗号分隔)", placeholder="Python, Java, Go")
            experience_years = st.number_input("工作年限", 0, 30, 3)
        
        with col2:
            location = st.text_input("期望地点", placeholder="北京")
            salary_min = st.slider("最低薪资 (K)", 0, 100, 20)
            education = st.selectbox("学历", ["不限", "大专", "本科", "硕士", "博士"])
        
        st.text_area("个人简介 (可选)", placeholder="简单介绍自己的经验...", height=80)
        
        if st.form_submit_button("🎯 开始匹配", type="primary"):
            if not job_title and not skills:
                st.warning("请至少填写期望职位或技能")
            else:
                import hashlib
                user_id = hashlib.md5(user_manager.device_id.encode()).hexdigest()[:16]
                
                user = UserProfile(
                    id=user_id,
                    current_title=job_title,
                    experience_years=experience_years,
                    education=education if education != "不限" else None,
                    skills=[SKILL_STANDARD_MAP.get(s.strip().lower(), s.strip().title()) for s in skills.replace("，", ",").split(",") if s.strip()],
                    desired_salary_min=salary_min * 1000 if salary_min > 0 else None,
                    desired_locations=[loc.strip() for loc in location.replace("，", ",").split(",") if loc.strip()] if location else [],
                )
                
                job_manager.create_user_profile(user)
                
                with st.spinner("正在匹配..."):
                    result = job_matcher.match_by_profile(user_id, limit=10)
                
                if result.matches:
                    st.success(f"✅ 找到 {len(result.matches)} 个匹配岗位")
                    
                    for match in result.matches:
                        score = match.get("total_score", 0)
                        color = "green" if score >= 0.7 else "orange" if score >= 0.5 else "red"
                        
                        with st.expander(f"{match.get('job_title', '')} @ {match.get('company_name', '')}"):
                            st.markdown(f"**匹配度**: :{color}[{score:.0%}]")
                            salary_min = match.get('salary_min', 0) or 0
                            salary_max = match.get('salary_max', 0) or 0
                            st.write(f"**薪资**: {salary_min/1000:.0f}-{salary_max/1000:.0f}K")
                            st.write(f"**地点**: {match.get('location', '')}")
                            
                            if match.get('skills'):
                                st.write(f"**技能**: {', '.join(match['skills'][:10])}")
                            
                            desc = match.get('description', '')
                            if desc:
                                st.write(f"**描述**: {desc[:200]}...")
                else:
                    st.warning("未找到匹配的岗位")


# ============================================================
# 岗位搜索
# ============================================================

elif page == "🔍 岗位搜索":
    st.header("🔍 岗位搜索")
    
    search_query = st.text_input("搜索职位或公司", placeholder="输入关键词...")
    
    if search_query:
        with st.spinner("搜索中..."):
            results = job_manager.search_jobs(search_query)
        
        if results:
            st.write(f"找到 {len(results)} 个结果")
            for job in results[:20]:
                with st.expander(f"{job.get('title', '')} @ {job.get('company_name', '')}"):
                    salary_min = job.get('salary_min', 0) or 0
                    salary_max = job.get('salary_max', 0) or 0
                    st.write(f"**薪资**: {salary_min/1000:.0f}-{salary_max/1000:.0f}K")
                    st.write(f"**地点**: {job.get('location', '')}")
                    st.write(f"**经验**: {job.get('experience_years', '不限')}年")
        else:
            st.info("未找到相关职位")


# ============================================================
# 订阅提醒
# ============================================================

elif page == "🔔 订阅提醒":
    st.header("🔔 订阅提醒")
    
    st.info("订阅关键词，有新职位时自动提醒")
    
    with st.form("sub_form"):
        keywords = st.text_input("关键词 (逗号分隔)", placeholder="Java, Python")
        city = st.text_input("城市", value="武汉")
        
        if st.form_submit_button("添加订阅"):
            if keywords:
                import hashlib
                user_id = hashlib.md5(user_manager.device_id.encode()).hexdigest()[:16]
                
                sub = subscription_manager.add_subscription(
                    user_id=user_id,
                    keywords=[k.strip() for k in keywords.split(",") if k.strip()],
                    city=city,
                )
                st.success(f"✅ 订阅成功: {', '.join(sub['keywords'])}")


# ============================================================
# 避坑指南
# ============================================================

elif page == "⚠️ 避坑指南":
    st.header("⚠️ 公司画像 & 避坑指南")
    
    st.subheader("常见坑点")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.error("### 💰 欠薪\\n拖欠工资")
    with col2:
        st.error("### 🎭 PUA\\n精神控制")
    with col3:
        st.error("### ⏰ 996\\n强制加班")
    with col4:
        st.error("### 📉 裁员\\n频繁裁员")


# ============================================================
# 薪资行情
# ============================================================

elif page == "📊 薪资行情":
    st.header("📊 薪资行情")
    
    st.info("薪资数据仅供参考")
    
    # 按行业统计
    st.subheader("行业薪资分布")
    st.write("数据加载中...")


# ============================================================
# Footer
# ============================================================

st.divider()
st.caption("🔒 JobGraph - 完全免费 | 你的求职，你做主 | 数据仅存在本地")
