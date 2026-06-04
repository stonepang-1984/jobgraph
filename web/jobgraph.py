"""JobGraph - 私密求职图谱

聚焦场景: 求职 - 帮你找到靠谱的工作，避开坑人的公司
完全免费，所有功能均可使用
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
from loguru import logger

from src.jobgraph.graph_manager import job_manager
from src.jobgraph.models import CompanySize, UserProfile
from src.jobgraph.user.manager import user_manager
from src.jobgraph.resume import resume_parser, resume_extractor, privacy_filter, resume_optimizer
from src.jobgraph.matching import job_matcher
from src.jobgraph.config_manager import config_manager


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
# Sidebar
# ============================================================

with st.sidebar:
    st.header("🔍 功能导航")
    
    page = st.radio(
        "选择功能",
        [
            "🏠 首页",
            "📄 简历上传",
            "🎯 智能匹配",
            "📝 手动匹配",
            "🔍 岗位搜索",
            "🏢 公司画像",
            "⚠️ 避坑指南",
            "📊 薪资行情",
            "✏️ 贡献数据",
            "🔄 数据同步",
            "👤 用户中心",
            "⚙️ LLM 配置",
        ],
    )
    
    st.divider()
    
    # 免费标识
    st.success("🎁 **完全免费** - 所有功能均可使用")
    
    # Privacy badge
    st.info("🔒 **私密模式**\n\n数据仅存在本地，不留痕迹")
    
    st.divider()
    
    # User info
    user_stats = user_manager.get_user_stats()
    st.markdown(f"👤 **{user_stats['nickname']}**")
    st.caption(f"等级: Lv.{user_stats['level']} | 积分: {user_stats['points']}")
    
    # Statistics
    st.header("📊 数据统计")
    try:
        stats = job_manager.get_stats()
        st.metric("🏢 公司", stats.get("companies", 0))
        st.metric("💼 岗位", stats.get("jobs", 0))
        st.metric("💬 评价", stats.get("reviews", 0))
        st.metric("⚠️ 坑点", stats.get("pitfalls", 0))
    except Exception as e:
        st.error(f"获取统计失败: {e}")


# ============================================================
# Homepage
# ============================================================

if page == "🏠 首页":
    st.header("欢迎使用 JobGraph")
    
    # 隐私保护
    st.success("""
    🔒 **隐私保护** — 你的求职数据只存在你自己的电脑上
    - ✅ 无需注册，不留痕迹
    - ✅ 本地运行，数据不上传
    - ✅ 在职看机会，不会被发现
    """)
    
    # 免费标识
    st.info("""
    🎁 **完全免费** — 所有功能均可免费使用
    - ✅ 无搜索次数限制
    - ✅ 无功能限制
    - ✅ 无广告
    """)
    
    st.markdown("""
    **JobGraph** 是一款基于知识图谱的**私密求职工具**，帮你：
    - 🔍 **精准匹配** - 根据技能、薪资、地点匹配合适岗位
    - 🏢 **了解公司** - 真实员工评价，全面了解公司情况
    - ⚠️ **避坑预警** - 识别欠薪、PUA、996等坑点特征
    - 📊 **薪资分析** - 市场行情，合理定价
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("### 🔍 岗位搜索\n聚合多平台岗位信息，智能筛选匹配")
    
    with col2:
        st.warning("### 🏢 公司画像\n真实员工评价，全面了解公司情况")
    
    with col3:
        st.error("### ⚠️ 避坑指南\n识别坑点特征，远离黑心公司")


# ============================================================
# Resume Upload
# ============================================================

elif page == "📄 简历上传":
    st.header("📄 简历上传 - 智能匹配")
    
    # 🔒 隐私保护核心提示
    st.success("""
    🔒 **简历 100% 本地处理，绝不上传服务器**
    
    - 💾 简历文件仅保存在你的电脑
    - 🔐 解析过程在本地完成，内容不会传出
    - 👤 匹配只用技能、经验，不用姓名手机号
    - 🛡️ 即使包含隐私信息，也绝不会被传出去
    """)
    
    # LLM 配置状态提示
    if not config_manager.is_llm_configured():
        st.warning("""
        ⚠️ **AI 智能解析未启用**
        
        当前使用规则模式解析简历，精度有限。
        配置 LLM 后可大幅提升解析精度。
        """)
        if st.button("⚙️ 前往配置 LLM"):
            st.session_state["page"] = "⚙️ LLM 配置"
            st.rerun()
    
    # 补充建议
    st.info("""
    💡 **建议**：虽然系统会自动过滤隐私信息，但为更安全起见，建议使用只包含技能、经验、教育背景的简历版本
    """)
    
    st.divider()
    
    # 上传区域
    uploaded_file = st.file_uploader(
        "选择简历文件",
        type=["pdf", "docx"],
        help="支持 PDF、DOCX 格式",
    )
    
    if uploaded_file:
        st.success(f"✅ 已选择文件: {uploaded_file.name}")
        
        # 解析简历
        with st.spinner("正在解析简历..."):
            try:
                # 解析文件
                text = resume_parser.parse_uploaded_file(uploaded_file)
                
                # 隐私过滤
                filtered_text = privacy_filter.filter(text)
                
                # 扫描隐私信息
                privacy_scan = privacy_filter.scan(text)
                if privacy_scan:
                    st.warning(f"⚠️ 检测到隐私信息已自动过滤: {', '.join(privacy_scan.keys())}")
                
                # 提取信息
                profile = resume_extractor.extract(filtered_text)
                
                st.success("✅ 简历解析完成！")
                
            except Exception as e:
                st.error(f"❌ 简历解析失败: {e}")
                profile = None
        
        if profile:
            st.divider()
            
            # 预览提取结果
            st.subheader("📋 提取结果预览")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**当前职位**: {profile.current_title or '未识别'}")
                st.write(f"**工作年限**: {profile.experience_years} 年")
                st.write(f"**最高学历**: {profile.education or '未识别'}")
            
            with col2:
                skills = profile.skills or []
                if skills:
                    st.write(f"**技能** ({len(skills)} 项):")
                    # 显示技能标签
                    skills_text = " ".join([f"`{s}`" for s in skills[:15]])
                    st.markdown(skills_text)
                    if len(skills) > 15:
                        st.caption(f"...还有 {len(skills) - 15} 项技能")
                else:
                    st.write("**技能**: 未识别")
            
            # 证书
            if profile.certifications:
                st.write(f"**证书**: {', '.join(profile.certifications)}")
            
            st.divider()
            
            # 用户确认/修改
            st.subheader("✏️ 确认/修改信息")
            
            with st.form("confirm_profile"):
                col1, col2 = st.columns(2)
                
                with col1:
                    current_title = st.text_input(
                        "当前职位",
                        value=profile.current_title or "",
                        placeholder="如：后端工程师"
                    )
                    experience_years = st.number_input(
                        "工作年限",
                        min_value=0,
                        max_value=50,
                        value=profile.experience_years,
                    )
                    education = st.selectbox(
                        "最高学历",
                        ["大专", "本科", "硕士", "博士"],
                        index=["大专", "本科", "硕士", "博士"].index(profile.education) if profile.education in ["大专", "本科", "硕士", "博士"] else 1,
                    )
                
                with col2:
                    skills_input = st.text_input(
                        "技能 (逗号分隔)",
                        value=", ".join(profile.skills) if profile.skills else "",
                        placeholder="Python, Java, Go"
                    )
                    desired_salary = st.slider("期望薪资 (K)", 0, 100, 30)
                    location = st.text_input("期望地点", placeholder="北京")
                    prefer_remote = st.checkbox("接受远程办公")
                
                st.info("💡 请确认以上信息是否准确，您可以在此修改")
                
                if st.form_submit_button("🎯 开始匹配", type="primary"):
                    # 创建用户档案
                    import hashlib
                    
                    user_id = hashlib.md5(
                        f"{user_manager.device_id}_resume".encode()
                    ).hexdigest()[:16]
                    
                    user = UserProfile(
                        id=user_id,
                        current_title=current_title,
                        experience_years=experience_years,
                        education=education,
                        skills=[s.strip() for s in skills_input.split(",") if s.strip()],
                        desired_salary_min=desired_salary * 1000 * 0.8 if desired_salary > 0 else None,
                        desired_salary_max=desired_salary * 1000 * 1.2 if desired_salary > 0 else None,
                        desired_locations=[location] if location else [],
                        prefer_remote=prefer_remote,
                    )
                    
                    # 保存用户档案
                    job_manager.create_user_profile(user)
                    
                    # 保存当前简历信息到 session
                    st.session_state["current_profile"] = {
                        "user_id": user_id,
                        "current_title": current_title,
                        "experience_years": experience_years,
                        "education": education,
                        "skills": [s.strip() for s in skills_input.split(",") if s.strip()],
                        "work_history": profile.work_history if profile else [],
                        "projects": profile.projects if profile else [],
                    }
                    
                    # 执行匹配
                    with st.spinner("正在匹配岗位..."):
                        result = job_matcher.match_by_profile(user_id, limit=20)
                    
                    if result.matches:
                        st.success(f"✅ 为你找到 {len(result.matches)} 个匹配岗位")
                        
                        # 显示匹配结果
                        for match in result.matches:
                            score = match.get("total_score", 0)
                            risk = match.get("company_risk", "medium")
                            
                            if score >= 0.7:
                                score_color = "green"
                            elif score >= 0.5:
                                score_color = "orange"
                            else:
                                score_color = "red"
                            
                            risk_color = "green" if risk == "low" else "orange" if risk == "medium" else "red"
                            
                            with st.expander(f"{match.get('job_title', '')} @ {match.get('company_name', '')}"):
                                col1, col2, col3 = st.columns(3)
                                
                                with col1:
                                    salary_min = match.get('salary_min', 0) or 0
                                    salary_max = match.get('salary_max', 0) or 0
                                    st.write(f"**薪资**: {salary_min/1000:.0f}-{salary_max/1000:.0f}K")
                                    st.write(f"**地点**: {match.get('location', '')}")
                                
                                with col2:
                                    st.markdown(f"**匹配度**: :{score_color}[{score:.0%}]")
                                    st.markdown(f"**公司风险**: :{risk_color}[{risk}]")
                                
                                with col3:
                                    matched_skills = match.get("matched_skills", 0)
                                    st.write(f"**技能匹配**: {matched_skills}项")
                                
                                if risk in ["high", "blacklist"]:
                                    st.warning("⚠️ 该公司存在风险，请谨慎考虑！")
                        
                        # 检查是否有低匹配度的岗位，提供优化建议
                        low_match_jobs = [m for m in result.matches if m.get("total_score", 0) < 0.5]
                        
                        if low_match_jobs:
                            st.divider()
                            st.subheader("📝 简历优化建议")
                            st.info("💡 发现部分岗位匹配度较低，以下是针对性的简历优化建议")
                            
                            # 选择要分析的岗位
                            job_options = [
                                f"{m.get('job_title', '')} @ {m.get('company_name', '')} ({m.get('total_score', 0):.0%})"
                                for m in low_match_jobs[:5]
                            ]
                            selected_job = st.selectbox("选择要分析的岗位", job_options)
                            
                            if selected_job:
                                # 获取选中的岗位
                                job_idx = job_options.index(selected_job)
                                target_job = low_match_jobs[job_idx]
                                
                                # 生成优化建议
                                current_profile = st.session_state.get("current_profile", {})
                                suggestion = resume_optimizer.analyze_and_suggest(
                                    current_profile=current_profile,
                                    match_result=target_job,
                                    target_job=target_job,
                                )
                                
                                # 显示优化建议
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.metric("当前匹配度", f"{suggestion.overall_score:.0%}")
                                
                                with col2:
                                    st.metric("目标匹配度", f"{suggestion.target_score:.0%}")
                                
                                # 显示差距分析
                                if suggestion.gaps:
                                    st.write("**📊 匹配差距分析:**")
                                    for gap in suggestion.gaps:
                                        severity_icon = "🔴" if gap.severity >= 4 else "🟡" if gap.severity >= 2 else "🟢"
                                        st.write(f"{severity_icon} **{gap.gap_type.upper()}**: {gap.description}")
                                        for s in gap.suggestions:
                                            st.write(f"  - {s}")
                                
                                # 显示技能建议
                                if suggestion.skill_suggestions:
                                    st.write("**🔑 技能优化建议:**")
                                    for s in suggestion.skill_suggestions:
                                        st.write(f"  - {s}")
                                
                                # 显示经验建议
                                if suggestion.experience_suggestions:
                                    st.write("**📋 经验优化建议:**")
                                    for s in suggestion.experience_suggestions:
                                        st.write(f"  - {s}")
                                
                                # 显示通用建议
                                if suggestion.general_tips:
                                    st.write("**💡 通用建议:**")
                                    for s in suggestion.general_tips:
                                        st.write(f"  - {s}")
                                
                                st.divider()
                                
                                # 生成修改建议
                                modifications = resume_optimizer.generate_modifications(
                                    current_profile, suggestion
                                )
                                
                                if modifications:
                                    st.write("**✏️ 简历修改建议:**")
                                    
                                    # 显示修改建议
                                    accepted_fields = []
                                    for i, mod in enumerate(modifications):
                                        col1, col2 = st.columns([3, 1])
                                        
                                        with col1:
                                            st.write(f"**{mod.field_name}**: {mod.reason}")
                                            if mod.old_value:
                                                st.caption(f"当前: {mod.old_value[:50]}...")
                                            if mod.new_value:
                                                st.caption(f"建议: {mod.new_value[:50]}...")
                                        
                                        with col2:
                                            if st.checkbox("接受", key=f"mod_{i}", value=True):
                                                accepted_fields.append(mod.field_name)
                                    
                                    # 应用修改
                                    if st.button("🎯 应用修改并重新匹配", type="primary"):
                                        # 应用修改
                                        updated_profile = resume_optimizer.apply_modifications(
                                            current_profile, modifications, accepted_fields
                                        )
                                        
                                        # 更新用户档案
                                        user = UserProfile(
                                            id=updated_profile["user_id"],
                                            current_title=updated_profile.get("current_title"),
                                            experience_years=updated_profile.get("experience_years", 0),
                                            education=updated_profile.get("education"),
                                            skills=updated_profile.get("skills", []),
                                        )
                                        job_manager.create_user_profile(user)
                                        
                                        # 更新 session
                                        st.session_state["current_profile"] = updated_profile
                                        
                                        st.success("✅ 简历已优化，正在重新匹配...")
                                        st.rerun()
                        
                        # 如果匹配结果较少，提示手动输入
                        if result.need_manual_input:
                            st.divider()
                            st.info("💡 匹配结果较少？可以尝试手动输入职位信息获取更多匹配")
                            if st.button("📝 手动输入职位信息"):
                                st.session_state["page"] = "📝 手动匹配"
                                st.rerun()
                    else:
                        st.warning("暂未找到匹配的岗位")
                        st.info("💡 建议尝试手动输入职位信息进行匹配")
                        if st.button("📝 手动输入职位信息", key="manual_btn"):
                            st.session_state["page"] = "📝 手动匹配"
                            st.rerun()
    
    else:
        # 未上传文件时显示说明
        st.info("""
        **使用说明**：
        1. 上传您的简历文件（PDF 或 DOCX 格式）
        2. 系统自动解析简历内容
        3. 确认提取的信息是否准确
        4. 点击"开始匹配"获取推荐岗位
        """)
        
        st.markdown("""
        **支持的信息提取**：
        - 🔧 技能（编程语言、框架、工具等）
        - 📅 工作年限
        - 🎓 教育背景
        - 💼 当前职位
        - 📜 专业证书
        """)


# ============================================================
# Manual Match
# ============================================================

elif page == "📝 手动匹配":
    st.header("🎯 手动职位匹配")
    st.info("当简历匹配结果不理想时，可以手动输入期望职位信息进行匹配")
    
    st.divider()
    
    with st.form("manual_match_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            job_title = st.text_input("期望职位", placeholder="如：后端工程师")
            skills = st.text_input("技能 (逗号分隔)", placeholder="Python, Java, Go")
            experience_years = st.number_input("工作年限", 0, 30, 3)
        
        with col2:
            location = st.text_input("期望地点", placeholder="北京")
            salary_min = st.slider("最低薪资 (K)", 0, 100, 20)
            education = st.selectbox("学历", ["不限", "大专", "本科", "硕士", "博士"])
        
        submitted = st.form_submit_button("🎯 开始匹配", type="primary")
    
    if submitted:
        if not job_title and not skills:
            st.warning("请至少填写期望职位或技能")
        else:
            with st.spinner("正在匹配岗位..."):
                result = job_matcher.match_by_manual_input(
                    job_title=job_title if job_title else None,
                    skills=[s.strip() for s in skills.split(",") if s.strip()] if skills else None,
                    experience_years=experience_years,
                    education=education if education != "不限" else None,
                    location=location if location else None,
                    salary_min=salary_min * 1000 if salary_min > 0 else None,
                    limit=20,
                )
            
            if result.matches:
                st.success(f"✅ 为你找到 {len(result.matches)} 个匹配岗位")
                
                # 显示匹配结果
                for match in result.matches:
                    score = match.get("total_score", 0)
                    risk = match.get("company_risk", "medium")
                    
                    if score >= 0.7:
                        score_color = "green"
                    elif score >= 0.5:
                        score_color = "orange"
                    else:
                        score_color = "red"
                    
                    risk_color = "green" if risk == "low" else "orange" if risk == "medium" else "red"
                    
                    with st.expander(f"{match.get('job_title', '')} @ {match.get('company_name', '')}"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            salary_min_val = match.get('salary_min', 0) or 0
                            salary_max_val = match.get('salary_max', 0) or 0
                            st.write(f"**薪资**: {salary_min_val/1000:.0f}-{salary_max_val/1000:.0f}K")
                            st.write(f"**地点**: {match.get('location', '')}")
                        
                        with col2:
                            st.markdown(f"**匹配度**: :{score_color}[{score:.0%}]")
                            st.markdown(f"**公司风险**: :{risk_color}[{risk}]")
                        
                        with col3:
                            matched_skills = match.get("matched_skills", 0)
                            st.write(f"**技能匹配**: {matched_skills}项")
                        
                        if risk in ["high", "blacklist"]:
                            st.warning("⚠️ 该公司存在风险，请谨慎考虑！")
            else:
                st.warning("暂未找到匹配的岗位")
                st.info("💡 建议尝试：")
                st.markdown("""
                - 调整期望职位关键词
                - 减少筛选条件
                - 扩大地点范围
                - 降低薪资要求
                """)


# ============================================================
# Job Search
# ============================================================

elif page == "🔍 岗位搜索":
    st.header("🔍 岗位搜索")
    
    # Search filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        query = st.text_input("搜索关键词", placeholder="职位名称/公司")
    
    with col2:
        location = st.selectbox("工作地点", ["不限", "北京", "上海", "广州", "深圳", "杭州", "成都"])
    
    with col3:
        salary_min = st.slider("最低薪资 (K)", 0, 100, 0)
    
    # Search
    if st.button("搜索", type="primary") or query:
        try:
            jobs = job_manager.search_jobs(
                query=query if query else None,
                location=location if location != "不限" else None,
                salary_min=salary_min * 1000 if salary_min > 0 else None,
                limit=50
            )
            
            if jobs:
                st.subheader(f"找到 {len(jobs)} 个岗位")
                
                for job in jobs:
                    j = job.get("j", {})
                    risk = job.get("company_risk", "medium")
                    risk_color = "green" if risk == "low" else "orange" if risk == "medium" else "red"
                    risk_text = {"low": "低风险", "medium": "中风险", "high": "高风险", "blacklist": "黑名单"}.get(risk, "未知")
                    
                    with st.expander(f"{j.get('title', '')} @ {j.get('company_name', '')}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write(f"**薪资**: {j.get('salary_min', 0)/1000:.0f}-{j.get('salary_max', 0)/1000:.0f}K × {j.get('salary_months', 12)}薪")
                            st.write(f"**地点**: {j.get('location', '')}")
                            st.write(f"**经验**: {j.get('experience_years', 0)}年+")
                            st.write(f"**学历**: {j.get('education', '不限')}")
                        
                        with col2:
                            st.markdown(f"**公司风险**: :{risk_color}[{risk_text}]")
                            skills = j.get("skills", [])
                            if skills:
                                st.write(f"**技能要求**: {', '.join(skills)}")
                        
                        benefits = j.get("benefits", [])
                        if benefits:
                            st.write(f"**福利待遇**: {', '.join(benefits)}")
                        
                        if risk in ["high", "blacklist"]:
                            st.warning("⚠️ 该公司存在风险，请谨慎考虑！")
            else:
                st.info("未找到匹配的岗位")
        except Exception as e:
            st.error(f"搜索失败: {e}")


# ============================================================
# Company Profile
# ============================================================

elif page == "🏢 公司画像":
    st.header("🏢 公司画像")
    
    company_query = st.text_input("搜索公司", placeholder="输入公司名称")
    
    if company_query:
        companies = job_manager.search_companies(company_query)
        
        if companies:
            for comp in companies:
                c = comp.get("c", {})
                risk = c.get("risk_level", "medium")
                risk_icon = "🟢" if risk == "low" else "🟡" if risk == "medium" else "🔴"
                
                st.subheader(f"{risk_icon} {c.get('name', '')}")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**行业**: {c.get('industry', '')}")
                    st.write(f"**规模**: {c.get('size', '')}")
                    st.write(f"**成立**: {c.get('founded', '')}")
                    st.write(f"**总部**: {c.get('headquarters', '')}")
                
                with col2:
                    st.write(f"**融资**: {c.get('funding_stage', '')}")
                    st.write(f"**上市**: {'是' if c.get('is_listed') else '否'}")
                    st.write(f"**平均薪资**: ¥{c.get('avg_salary', 0):,.0f}/月")
                    st.write(f"**评分**: {'⭐' * int(c.get('avg_rating', 0))} ({c.get('avg_rating', 0):.1f})")
                
                with col3:
                    st.markdown(f"**风险等级**: {risk.upper()}")
                    st.write(f"**风险分数**: {c.get('risk_score', 0):.2f}")
                    
                    tags = c.get("tags", [])
                    if tags:
                        st.write(f"**标签**: {', '.join(tags)}")
                
                # Reviews
                reviews = job_manager.get_company_reviews(c.get("id", ""))
                if reviews:
                    st.subheader("💬 员工评价")
                    for rev in reviews[:5]:
                        r = rev.get("r", {})
                        st.write(f"**{r.get('title', '')}** - {r.get('reviewer_title', '')}")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.success(f"✅ {r.get('pros', '')}")
                        with col2:
                            st.error(f"❌ {r.get('cons', '')}")
                
                # Pitfalls
                pitfalls = job_manager.get_company_pitfalls(c.get("id", ""))
                if pitfalls:
                    st.subheader("⚠️ 坑点预警")
                    for pit in pitfalls:
                        p = pit.get("p", {})
                        severity = p.get("severity", 3)
                        st.error(f"**{p.get('pitfall_type', '')}** ({'🔴' * severity})")
                
                st.divider()
        else:
            st.info("未找到匹配的公司")


# ============================================================
# Pitfall Guide
# ============================================================

elif page == "⚠️ 避坑指南":
    st.header("⚠️ 避坑指南")
    
    st.subheader("常见坑点类型")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.error("### 💰 欠薪\n拖欠工资，不按时发放")
    
    with col2:
        st.error("### 🎭 PUA\n精神控制，贬低员工")
    
    with col3:
        st.error("### ⏰ 996\n强制加班，没有加班费")
    
    with col4:
        st.error("### 📉 裁员\n频繁裁员，不稳定")
    
    st.divider()
    
    st.subheader("避坑技巧")
    
    st.info("""
    1. **查看员工评价**: 脉脉、Glassdoor 等平台的真实评价
    2. **查询企业信息**: 天眼查、企查查了解公司背景
    3. **注意面试信号**: 面试中是否尊重候选人
    4. **问清楚薪资结构**: 底薪、绩效、年终奖比例
    5. **了解加班情况**: 是否强制加班，有无加班费
    """)
    
    st.divider()
    
    st.subheader("黑名单公司查询")
    
    blacklist_query = st.text_input("查询公司", placeholder="输入公司名称")
    
    if blacklist_query:
        companies = job_manager.search_companies(blacklist_query)
        
        for comp in companies:
            c = comp.get("c", {})
            risk = c.get("risk_level", "medium")
            
            if risk in ["high", "blacklist"]:
                st.error(f"⚠️ **{c.get('name', '')}** 存在高风险！")
                st.write(f"风险等级: {risk.upper()}")
                st.write(f"风险分数: {c.get('risk_score', 0):.2f}")
            else:
                st.success(f"✅ **{c.get('name', '')}** 暂未发现明显风险")


# ============================================================
# Salary Analysis
# ============================================================

elif page == "📊 薪资行情":
    st.header("📊 薪资行情")
    
    st.subheader("薪资查询")
    
    job_title = st.text_input("输入职位名称", placeholder="如: 后端工程师")
    
    if job_title:
        salary_data = job_manager.get_job_salary_range(job_title)
        
        if salary_data and salary_data.get("sample_count", 0) > 0:
            st.subheader(f"「{job_title}」薪资分布")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("25分位", f"¥{salary_data.get('p25_min', 0)/1000:.0f}K")
            
            with col2:
                st.metric("中位数", f"¥{salary_data.get('p50_min', 0)/1000:.0f}K")
            
            with col3:
                st.metric("75分位", f"¥{salary_data.get('p75_min', 0)/1000:.0f}K")
            
            st.write(f"样本数量: {salary_data.get('sample_count', 0)}")
        else:
            st.info(f"暂无「{job_title}」的薪资数据")


# ============================================================
# Smart Matching
# ============================================================

elif page == "🎯 智能匹配":
    st.header("🎯 智能匹配")
    
    st.info("填写你的信息，系统会为你推荐匹配的岗位")
    
    # 隐私提示
    st.warning("🔒 **隐私保护**：无需填写姓名、手机号等隐私信息")
    
    with st.form("user_profile"):
        col1, col2 = st.columns(2)
        
        with col1:
            current_title = st.text_input("当前职位")
            experience_years = st.number_input("工作年限", 0, 30, 3)
            education = st.selectbox("学历", ["大专", "本科", "硕士", "博士"])
        
        with col2:
            skills = st.text_input("技能 (逗号分隔)", placeholder="Python, Java, Go")
            desired_salary = st.slider("期望薪资 (K)", 0, 100, 30)
            location = st.text_input("期望地点", placeholder="北京")
            prefer_remote = st.checkbox("接受远程办公")
        
        if st.form_submit_button("开始匹配", type="primary"):
            import hashlib
            
            user_id = hashlib.md5(
                f"{user_manager.device_id}_smart".encode()
            ).hexdigest()[:16]
            
            user = UserProfile(
                id=user_id,
                current_title=current_title,
                experience_years=experience_years,
                education=education,
                skills=[s.strip() for s in skills.split(",") if s.strip()],
                desired_salary_min=desired_salary * 1000 * 0.8 if desired_salary > 0 else None,
                desired_salary_max=desired_salary * 1000 * 1.2 if desired_salary > 0 else None,
                desired_locations=[location] if location else [],
                prefer_remote=prefer_remote,
            )
            
            job_manager.create_user_profile(user)
            
            with st.spinner("正在匹配岗位..."):
                result = job_matcher.match_by_profile(user_id, limit=20)
            
            if result.matches:
                st.subheader(f"为你推荐 {len(result.matches)} 个岗位")
                
                for match in result.matches:
                    score = match.get("total_score", 0)
                    risk = match.get("company_risk", "medium")
                    
                    if score >= 0.7:
                        score_color = "green"
                    elif score >= 0.5:
                        score_color = "orange"
                    else:
                        score_color = "red"
                    
                    risk_color = "green" if risk == "low" else "orange" if risk == "medium" else "red"
                    
                    with st.expander(f"{match.get('job_title', '')} @ {match.get('company_name', '')}"):
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            salary_min = match.get('salary_min', 0) or 0
                            salary_max = match.get('salary_max', 0) or 0
                            st.write(f"**薪资**: {salary_min/1000:.0f}-{salary_max/1000:.0f}K")
                            st.write(f"**地点**: {match.get('location', '')}")
                        
                        with col2:
                            st.markdown(f"**匹配度**: :{score_color}[{score:.0%}]")
                            st.markdown(f"**公司风险**: :{risk_color}[{risk}]")
                        
                        with col3:
                            matched_skills = match.get("matched_skills", 0)
                            st.write(f"**技能匹配**: {matched_skills}项")
                        
                        if risk in ["high", "blacklist"]:
                            st.warning("⚠️ 该公司存在风险，请谨慎考虑！")
                
                # 如果匹配结果较少，提示手动输入
                if result.need_manual_input:
                    st.divider()
                    st.info("💡 匹配结果较少？可以尝试手动输入职位信息获取更多匹配")
                    if st.button("📝 手动输入职位信息"):
                        st.session_state["page"] = "📝 手动匹配"
                        st.rerun()
            else:
                st.warning("暂未找到匹配的岗位")
                st.info("💡 建议尝试手动输入职位信息进行匹配")
                if st.button("📝 手动输入职位信息", key="smart_manual_btn"):
                    st.session_state["page"] = "📝 手动匹配"
                    st.rerun()


# ============================================================
# Contribution Page
# ============================================================

elif page == "✏️ 贡献数据":
    st.header("✏️ 贡献数据")
    
    st.info("帮助其他求职者了解公司真实情况，提交你的评价和坑点")
    
    # 用户贡献统计
    user_stats = user_manager.get_user_stats()
    contributions = user_stats.get("contributions", {})
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("等级", f"Lv.{user_stats['level']}")
    with col2:
        st.metric("积分", user_stats['points'])
    with col3:
        st.metric("评价", contributions.get('reviews', 0))
    with col4:
        st.metric("坑点", contributions.get('pitfalls', 0))
    
    st.divider()
    
    tab1, tab2, tab3, tab4 = st.tabs(["提交评价", "提交坑点", "提交薪资", "提交职位"])
    
    with tab1:
        st.subheader("提交员工评价")
        
        company_query = st.text_input("搜索公司", placeholder="输入公司名称", key="review_company")
        
        if company_query:
            companies = job_manager.search_companies(company_query)
            if companies:
                company_options = [c.get("c", {}).get("name", "") for c in companies]
                selected_company = st.selectbox("选择公司", company_options)
                
                company_id = None
                for c in companies:
                    if c.get("c", {}).get("name") == selected_company:
                        company_id = c.get("c", {}).get("id")
                        break
                
                if company_id:
                    with st.form("review_form"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            overall_rating = st.slider("综合评分", 1.0, 5.0, 3.0, 0.1)
                            salary_rating = st.slider("薪资评分", 1.0, 5.0, 3.0, 0.1)
                            work_life_rating = st.slider("工作生活平衡", 1.0, 5.0, 3.0, 0.1)
                        
                        with col2:
                            management_rating = st.slider("管理评分", 1.0, 5.0, 3.0, 0.1)
                            reviewer_title = st.text_input("你的职位", placeholder="工程师")
                            reviewer_tenure = st.selectbox("在职时长", ["不到1年", "1-2年", "2-3年", "3-5年", "5年以上"])
                        
                        title = st.text_input("评价标题", placeholder="一句话总结")
                        pros = st.text_area("优点", placeholder="公司有什么好的地方？")
                        cons = st.text_area("缺点", placeholder="公司有什么不好的地方？")
                        
                        pitfall_options = ["996", "PUA", "内卷", "欠薪", "裁员", "画饼", "克扣"]
                        selected_pitfalls = st.multiselect("坑点标签（可选）", pitfall_options)
                        
                        if st.form_submit_button("提交评价", type="primary"):
                            if pros and cons:
                                from src.jobgraph.user.contribution import contribution_manager
                                
                                result = contribution_manager.submit_review(
                                    company_id=company_id,
                                    overall_rating=overall_rating,
                                    pros=pros,
                                    cons=cons,
                                    title=title,
                                    salary_rating=salary_rating,
                                    work_life_rating=work_life_rating,
                                    management_rating=management_rating,
                                    reviewer_title=reviewer_title,
                                    reviewer_tenure=reviewer_tenure,
                                    pitfall_tags=selected_pitfalls,
                                )
                                
                                if result["success"]:
                                    st.success(f"✅ 评价已提交！获得 10 积分")
                                else:
                                    st.error(f"提交失败: {result['error']}")
                            else:
                                st.warning("请填写优点和缺点")
    
    with tab2:
        st.subheader("提交坑点")
        
        company_query_pitfall = st.text_input("搜索公司", placeholder="输入公司名称", key="pitfall_company")
        
        if company_query_pitfall:
            companies = job_manager.search_companies(company_query_pitfall)
            if companies:
                company_options = [c.get("c", {}).get("name", "") for c in companies]
                selected_company = st.selectbox("选择公司", company_options, key="pitfall_select")
                
                company_id = None
                for c in companies:
                    if c.get("c", {}).get("name") == selected_company:
                        company_id = c.get("c", {}).get("id")
                        break
                
                if company_id:
                    with st.form("pitfall_form"):
                        pitfall_type = st.selectbox("坑点类型", ["欠薪", "PUA", "996", "内卷", "裁员", "画饼", "克扣", "其他"])
                        severity = st.slider("严重程度", 1, 5, 3)
                        description = st.text_area("详细描述", placeholder="请详细描述坑点情况")
                        evidence = st.text_area("证据来源（可选）", placeholder="如：脉脉评价、劳动仲裁等")
                        
                        if st.form_submit_button("提交坑点", type="primary"):
                            if description:
                                from src.jobgraph.user.contribution import contribution_manager
                                
                                result = contribution_manager.submit_pitfall(
                                    company_id=company_id,
                                    pitfall_type=pitfall_type,
                                    description=description,
                                    severity=severity,
                                    evidence=evidence,
                                )
                                
                                if result["success"]:
                                    st.success(f"✅ 坑点已提交！获得 15 积分")
                                else:
                                    st.error(f"提交失败: {result['error']}")
                            else:
                                st.warning("请填写详细描述")
    
    with tab3:
        st.subheader("提交薪资信息")
        
        company_query_salary = st.text_input("搜索公司", placeholder="输入公司名称", key="salary_company")
        
        if company_query_salary:
            companies = job_manager.search_companies(company_query_salary)
            if companies:
                company_options = [c.get("c", {}).get("name", "") for c in companies]
                selected_company = st.selectbox("选择公司", company_options, key="salary_select")
                
                company_id = None
                for c in companies:
                    if c.get("c", {}).get("name") == selected_company:
                        company_id = c.get("c", {}).get("id")
                        break
                
                if company_id:
                    with st.form("salary_form"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            job_title = st.text_input("职位名称", placeholder="后端工程师")
                            salary_min = st.number_input("最低薪资 (K)", 0, 200, 20)
                        
                        with col2:
                            experience_years = st.number_input("工作年限", 0, 30, 3)
                            salary_max = st.number_input("最高薪资 (K)", 0, 200, 40)
                        
                        education = st.selectbox("学历", ["大专", "本科", "硕士", "博士"])
                        
                        if st.form_submit_button("提交薪资", type="primary"):
                            if job_title:
                                from src.jobgraph.user.contribution import contribution_manager
                                
                                result = contribution_manager.submit_salary(
                                    company_id=company_id,
                                    job_title=job_title,
                                    salary_min=salary_min * 1000,
                                    salary_max=salary_max * 1000,
                                    experience_years=experience_years,
                                    education=education,
                                )
                                
                                if result["success"]:
                                    st.success(f"✅ 薪资信息已提交！获得 5 积分")
                                else:
                                    st.error(f"提交失败: {result['error']}")
                            else:
                                st.warning("请填写职位名称")
    
    with tab4:
        st.subheader("提交职位信息")
        
        company_query_job = st.text_input("搜索公司", placeholder="输入公司名称", key="job_company")
        
        if company_query_job:
            companies = job_manager.search_companies(company_query_job)
            if companies:
                company_options = [c.get("c", {}).get("name", "") for c in companies]
                selected_company = st.selectbox("选择公司", company_options, key="job_select")
                
                company_id = None
                for c in companies:
                    if c.get("c", {}).get("name") == selected_company:
                        company_id = c.get("c", {}).get("id")
                        break
                
                if company_id:
                    with st.form("job_form"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            job_title = st.text_input("职位名称 *", placeholder="后端工程师")
                            location = st.text_input("工作地点", placeholder="北京")
                            salary_min = st.number_input("最低薪资 (K)", 0, 200, 20)
                            salary_max = st.number_input("最高薪资 (K)", 0, 200, 40)
                        
                        with col2:
                            experience_years = st.number_input("工作年限要求", 0, 30, 3)
                            education = st.selectbox("学历要求", ["不限", "大专", "本科", "硕士", "博士"])
                            skills = st.text_input("技能要求 (逗号分隔)", placeholder="Java, Python, MySQL")
                            benefits = st.text_input("福利待遇 (逗号分隔)", placeholder="五险一金, 年终奖")
                        
                        description = st.text_area("职位描述", placeholder="请描述职位职责和要求...")
                        
                        if st.form_submit_button("提交职位", type="primary"):
                            if job_title:
                                from src.jobgraph.user.contribution import contribution_manager
                                
                                result = contribution_manager.submit_job(
                                    company_id=company_id,
                                    company_name=selected_company,
                                    title=job_title,
                                    location=location,
                                    salary_min=salary_min * 1000 if salary_min > 0 else None,
                                    salary_max=salary_max * 1000 if salary_max > 0 else None,
                                    experience_years=experience_years,
                                    education=education if education != "不限" else None,
                                    skills=[s.strip() for s in skills.split(",") if s.strip()],
                                    description=description,
                                    benefits=[b.strip() for b in benefits.split(",") if b.strip()],
                                )
                                
                                if result["success"]:
                                    st.success(f"✅ 职位已提交！获得 8 积分")
                                else:
                                    st.error(f"提交失败: {result['error']}")
                            else:
                                st.warning("请填写职位名称")


# ============================================================
# User Center Page
# ============================================================

elif page == "👤 用户中心":
    st.header("👤 用户中心")
    
    user_stats = user_manager.get_user_stats()
    
    # 用户信息卡片
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("基本信息")
        st.write(f"**昵称**: {user_stats['nickname']}")
        st.write(f"**设备ID**: {user_stats['device_id']}")
        st.write(f"**等级**: Lv.{user_stats['level']}")
        st.write(f"**积分**: {user_stats['points']}")
    
    with col2:
        st.subheader("贡献统计")
        contributions = user_stats.get("contributions", {})
        st.write(f"**评价**: {contributions.get('reviews', 0)} 条")
        st.write(f"**坑点**: {contributions.get('pitfalls', 0)} 条")
        st.write(f"**薪资**: {contributions.get('salaries', 0)} 条")
    
    st.divider()
    
    # 设置
    st.subheader("设置")
    
    new_nickname = st.text_input("修改昵称", value=user_stats['nickname'])
    if st.button("保存昵称"):
        user_manager.set_nickname(new_nickname)
        st.success("昵称已更新")
        st.rerun()


# ============================================================
# Data Sync Page
# ============================================================

elif page == "🔄 数据同步":
    st.header("🔄 数据同步")
    
    st.info("从数据中心同步最新的公司、岗位、评价数据")
    
    # 同步模式选择
    sync_mode = st.radio(
        "选择同步模式",
        ["📦 离线数据包", "🌐 Tailscale 直连", "☁️ 云服务器"],
        horizontal=True,
    )
    
    st.divider()
    
    # 场景A: 离线数据包
    if sync_mode == "📦 离线数据包":
        st.subheader("📦 离线数据包导入")
        
        st.markdown("""
        **使用场景**: 
        - 从数据管理员处获取数据包
        
        **操作步骤**:
        1. 从数据管理员获取 `.zip` 数据包
        2. 上传数据包
        3. 点击导入
        """)
        
        uploaded_file = st.file_uploader("上传数据包", type=["zip"])
        
        if uploaded_file and st.button("导入数据包", type="primary"):
            with st.spinner("正在导入..."):
                try:
                    import tempfile
                    import os
                    
                    # 保存上传文件
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
                        tmp.write(uploaded_file.getbuffer())
                        tmp_path = tmp.name
                    
                    # 导入
                    from src.jobgraph.sync.data_sync import data_sync
                    stats = data_sync.import_package(tmp_path)
                    
                    # 清理
                    os.unlink(tmp_path)
                    
                    st.success("✅ 数据包导入成功！")
                    st.json(stats)
                    
                except Exception as e:
                    st.error(f"导入失败: {e}")
    
    # 场景B: Tailscale 直连
    elif sync_mode == "🌐 Tailscale 直连":
        st.subheader("🌐 Tailscale 直连同步")
        
        st.markdown("""
        **使用场景**: 
        - 数据中心已部署 Tailscale
        
        **前置条件**:
        1. 安装 Tailscale: https://tailscale.com/download
        2. 加入数据中心的 Tailscale 网络
        """)
        
        tailscale_url = st.text_input(
            "数据中心地址",
            placeholder="http://100.x.x.1:8000",
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("测试连接"):
                if tailscale_url:
                    with st.spinner("测试中..."):
                        try:
                            import httpx
                            response = httpx.get(f"{tailscale_url}/api/v1/status", timeout=5)
                            if response.status_code == 200:
                                st.success("✅ 连接成功！")
                            else:
                                st.error(f"连接失败: {response.status_code}")
                        except Exception as e:
                            st.error(f"连接失败: {e}")
                else:
                    st.warning("请输入数据中心地址")
        
        with col2:
            if st.button("立即同步", type="primary"):
                if tailscale_url:
                    with st.spinner("同步中..."):
                        try:
                            from src.jobgraph.sync.data_sync import data_sync
                            stats = data_sync.sync_via_tailscale(tailscale_url)
                            st.success("✅ 同步完成！")
                            st.json(stats)
                        except Exception as e:
                            st.error(f"同步失败: {e}")
                else:
                    st.warning("请输入数据中心地址")
    
    # 场景C: 云服务器
    elif sync_mode == "☁️ 云服务器":
        st.subheader("☁️ 云服务器同步")
        
        cloud_url = st.text_input("云服务器地址", placeholder="https://api.example.com")
        
        if st.button("立即同步", type="primary"):
            if cloud_url:
                with st.spinner("同步中..."):
                    try:
                        from src.jobgraph.sync.data_sync import data_sync
                        stats = data_sync.sync_via_cloud(cloud_url)
                        st.success("✅ 同步完成！")
                        st.json(stats)
                    except Exception as e:
                        st.error(f"同步失败: {e}")
            else:
                st.warning("请输入云服务器地址")


# ============================================================
# LLM Configuration
# ============================================================

elif page == "⚙️ LLM 配置":
    st.header("⚙️ LLM 配置")
    
    # 当前状态
    is_configured = config_manager.is_llm_configured()
    
    if is_configured:
        st.success("✅ LLM 已配置 - 简历解析将使用 AI 智能提取")
    else:
        st.warning("⚠️ LLM 未配置 - 简历解析使用规则模式（精度有限）")
    
    st.divider()
    
    # 获取当前配置
    llm_config = config_manager.get_llm_config()
    
    # 选择提供商
    provider = st.radio(
        "选择 LLM 提供商",
        ["OpenAI API", "本地 Ollama"],
        horizontal=True,
    )
    
    if provider == "OpenAI API":
        st.subheader("OpenAI API 配置")
        
        st.info("""
        **获取 API Key**：
        1. 访问 https://platform.openai.com/api-keys
        2. 创建新的 API Key
        3. 复制并粘贴到下方
        
        **兼容 API**：
        - 支持 OpenAI 兼容的第三方 API（如 DeepSeek、Moonshot 等）
        - 只需修改 API Base URL 和 Model 名称
        """)
        
        with st.form("openai_config"):
            openai_key = st.text_input(
                "API Key *",
                value=llm_config.get("openai_api_key", ""),
                type="password",
                placeholder="sk-xxxxxxxxxxxxxxxx",
                help="OpenAI API Key 或兼容 API 的 Key"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                openai_base = st.text_input(
                    "API Base URL",
                    value=llm_config.get("openai_api_base", "https://api.openai.com/v1"),
                    help="OpenAI 或兼容 API 的地址"
                )
            
            with col2:
                openai_model = st.text_input(
                    "模型名称",
                    value=llm_config.get("openai_model", "gpt-4o"),
                    help="如 gpt-4o, gpt-3.5-turbo, deepseek-chat 等"
                )
            
            if st.form_submit_button("💾 保存配置", type="primary"):
                if openai_key and openai_key != "sk-your-openai-api-key":
                    success = config_manager.save_llm_config(
                        provider="openai",
                        openai_api_key=openai_key,
                        openai_api_base=openai_base,
                        openai_model=openai_model,
                    )
                    if success:
                        st.success("✅ 配置已保存！重启服务后生效")
                        st.rerun()
                    else:
                        st.error("❌ 保存失败")
                else:
                    st.warning("请输入有效的 API Key")
        
        # 常用 API 预设（在表单外面）
        st.write("**快速设置**：")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("OpenAI 官方"):
                config_manager.save_llm_config(
                    provider="openai",
                    openai_api_base="https://api.openai.com/v1",
                    openai_model="gpt-4o",
                )
                st.rerun()
        
        with col2:
            if st.button("DeepSeek"):
                config_manager.save_llm_config(
                    provider="openai",
                    openai_api_base="https://api.deepseek.com/v1",
                    openai_model="deepseek-chat",
                )
                st.rerun()
        
        with col3:
            if st.button("Moonshot"):
                config_manager.save_llm_config(
                    provider="openai",
                    openai_api_base="https://api.moonshot.cn/v1",
                    openai_model="moonshot-v1-8k",
                )
                st.rerun()
    
    else:  # Ollama
        st.subheader("本地 Ollama 配置")
        
        st.info("""
        **安装 Ollama**：
        ```bash
        # Linux/macOS
        curl -fsSL https://ollama.com/install.sh | sh
        
        # 下载模型
        ollama pull qwen2.5:14b
        ```
        
        **推荐模型**：
        - `qwen2.5:14b` - 中文效果好，需要 16GB 内存
        - `qwen2.5:7b` - 轻量版，需要 8GB 内存
        - `llama3:8b` - 英文效果好
        """)
        
        with st.form("ollama_config"):
            col1, col2 = st.columns(2)
            
            with col1:
                ollama_url = st.text_input(
                    "Ollama 服务地址",
                    value=llm_config.get("ollama_base_url", "http://localhost:11434"),
                    help="Ollama 服务的地址"
                )
            
            with col2:
                ollama_model = st.text_input(
                    "模型名称",
                    value=llm_config.get("ollama_model", "qwen2.5:14b"),
                    help="已下载的模型名称"
                )
            
            if st.form_submit_button("💾 保存配置", type="primary"):
                success = config_manager.save_llm_config(
                    provider="ollama",
                    ollama_base_url=ollama_url,
                    ollama_model=ollama_model,
                )
                if success:
                    st.success("✅ 配置已保存！重启服务后生效")
                    st.rerun()
                else:
                    st.error("❌ 保存失败")
    
    st.divider()
    
    # 测试连接
    st.subheader("🧪 测试连接")
    
    # 显示当前激活的提供商
    if config_manager.is_llm_configured():
        active_provider = config_manager.get_active_provider()
        st.info(f"当前激活的 LLM 提供商: **{active_provider.upper()}**")
    
    if st.button("测试 LLM 连接"):
        if not config_manager.is_llm_configured():
            st.warning("请先配置 LLM（输入 OpenAI API Key 或配置 Ollama 地址）")
        else:
            with st.spinner("正在测试连接..."):
                try:
                    from src.jobgraph.resume.extractor import resume_extractor
                    
                    # 重置 LLM 可用性缓存
                    resume_extractor._llm_available = None
                    
                    # 测试提取
                    test_text = "5年Java开发经验，熟悉Spring Boot、MySQL、Redis"
                    result = resume_extractor.extract(test_text)
                    
                    st.success("✅ LLM 连接成功！")
                    st.write(f"测试结果：识别到 {len(result.skills)} 个技能")
                    st.write(f"技能: {result.skills}")
                except Exception as e:
                    st.error(f"❌ 连接失败: {e}")
                    st.info("请检查：\n- API Key 是否正确\n- Ollama 服务是否启动\n- 网络连接是否正常")
    
    st.divider()
    
    # 隐私说明
    st.info("""
    🔒 **隐私说明**：
    - API Key 仅保存在本地 `.env` 文件中
    - 简历内容通过 API 发送到 LLM 服务进行解析
    - 如果担心隐私，建议使用本地 Ollama
    """)


# ============================================================
# Footer
# ============================================================

st.divider()
st.caption("🔒 JobGraph - 完全免费 | 你的求职，你做主 | 数据仅存在本地，不留任何痕迹")
