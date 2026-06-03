"""JobGraph - 求职图谱可视化界面

聚焦场景: 求职 - 帮你找到靠谱的工作，避开坑人的公司
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
from loguru import logger

from src.jobgraph.graph_manager import job_manager
from src.jobgraph.models import CompanySize
from src.jobgraph.license.manager import license_manager
from src.jobgraph.config import get_edition_info, get_upgrade_info


# ============================================================
# Page Config
# ============================================================

is_pro = license_manager.is_pro
edition_info = get_edition_info(is_pro)
edition_name = edition_info["edition"]

st.set_page_config(
    page_title=f"JobGraph {edition_name} - 私密求职图谱",
    page_icon="🔒",
    layout="wide",
)

st.title(f"🔒 JobGraph {edition_name} - 私密求职图谱")
st.markdown("**你的求职，你做主** — 在私有环境中安全求职，不留痕迹")


# ============================================================
# Sidebar
# ============================================================

with st.sidebar:
    st.header("🔍 功能导航")
    
    page = st.radio(
        "选择功能",
        [
            "🏠 首页",
            "🔍 岗位搜索",
            "🏢 公司画像",
            "⚠️ 避坑指南",
            "📊 薪资行情",
            "🎯 智能匹配",
            "🔄 数据同步",
            "🔑 License",
        ],
    )
    
    st.divider()
    
    # Edition badge
    license_info = license_manager.get_license_info()
    
    if is_pro:
        if license_info.get("is_trial"):
            days_left = license_info.get("days_remaining", 0)
            st.warning(f"🎁 **试用版** 还剩 {days_left} 天")
            st.caption("试用期满后需购买 License")
        else:
            st.success(f"⭐ **{edition_name}** v{edition_info['version']}")
            st.caption("全功能解锁")
    else:
        st.info(f"🔒 **免费版** v{edition_info['version']}")
        st.caption("部分功能受限")
    
    st.divider()
    
    # Privacy badge
    st.success("🔒 **私密模式**\n\n数据仅存在本地")
    
    st.divider()
    
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
    
    # Privacy highlight
    st.success("""
    🔒 **隐私保护** — 你的求职数据只存在你自己的电脑上
    - ✅ 无需注册，不留痕迹
    - ✅ 本地运行，数据不上传
    - ✅ 在职看机会，不会被发现
    """)
    
    # Free version limitations
    if not is_pro:
        upgrade_info = get_upgrade_info()
        st.warning(f"""
        ⚠️ **免费版功能受限**
        - 每日搜索限制: {edition_info['limits']['max_search_per_day']} 次
        - 岗位匹配结果: {edition_info['limits']['max_matching_results']} 个
        - 无数据导出功能
        
        👉 升级到 **专业版** 解锁全部功能
        """)
    
    st.markdown("""
    **JobGraph** 是一款基于知识图谱的**私密**求职工具，帮你：
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
        - 不想安装额外软件
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
        - 需要实时同步数据
        
        **前置条件**:
        1. 安装 Tailscale: https://tailscale.com/download
        2. 加入数据中心的 Tailscale 网络
        3. 获取数据中心的 Tailscale IP
        """)
        
        tailscale_url = st.text_input(
            "数据中心地址",
            placeholder="http://100.x.x.1:8000",
            help="输入数据中心的 Tailscale IP 和端口",
        )
        
        token = st.text_input("认证 Token (可选)", type="password", help="付费用户请输入 Token")
        
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
                                st.json(response.json())
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
                            stats = data_sync.sync_via_tailscale(tailscale_url, token or None)
                            st.success("✅ 同步完成！")
                            st.json(stats)
                        except Exception as e:
                            st.error(f"同步失败: {e}")
                else:
                    st.warning("请输入数据中心地址")
    
    # 场景C: 云服务器
    elif sync_mode == "☁️ 云服务器":
        st.subheader("☁️ 云服务器同步")
        
        st.markdown("""
        **使用场景**: 
        - 数据中心已迁移到云服务器
        - 标准 API 接口
        """)
        
        cloud_url = st.text_input("云服务器地址", placeholder="https://api.jobgraph.com")
        token = st.text_input("认证 Token", type="password", help="付费用户请输入 Token")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("测试连接", key="test_cloud"):
                if cloud_url:
                    with st.spinner("测试中..."):
                        try:
                            import httpx
                            response = httpx.get(f"{cloud_url}/api/v1/status", timeout=5)
                            if response.status_code == 200:
                                st.success("✅ 连接成功！")
                                st.json(response.json())
                            else:
                                st.error(f"连接失败: {response.status_code}")
                        except Exception as e:
                            st.error(f"连接失败: {e}")
                else:
                    st.warning("请输入云服务器地址")
        
        with col2:
            if st.button("立即同步", type="primary", key="sync_cloud"):
                if cloud_url:
                    with st.spinner("同步中..."):
                        try:
                            from src.jobgraph.sync.data_sync import data_sync
                            stats = data_sync.sync_via_cloud(cloud_url, token or None)
                            st.success("✅ 同步完成！")
                            st.json(stats)
                        except Exception as e:
                            st.error(f"同步失败: {e}")
                else:
                    st.warning("请输入云服务器地址")
    
    st.divider()
    
    # 同步状态
    st.subheader("📊 同步状态")
    
    try:
        from src.jobgraph.sync.data_sync import data_sync
        status = data_sync.get_status()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("同步模式", status.get("mode", "未设置"))
        
        with col2:
            st.metric("数据版本", status.get("version", "未知"))
        
        with col3:
            last_sync = status.get("last_sync", "从未同步")
            if last_sync and last_sync != "从未同步":
                last_sync = last_sync[:19]  # 截取日期时间
            st.metric("最后同步", last_sync)
        
        # 数据量
        counts = status.get("counts", {})
        if counts:
            st.write("**数据量**:")
            cols = st.columns(len(counts))
            for i, (key, value) in enumerate(counts.items()):
                with cols[i]:
                    st.metric(key, value)
                    
    except Exception as e:
        st.warning(f"获取同步状态失败: {e}")


# ============================================================
# License Page
# ============================================================

elif page == "🔑 License":
    st.header("🔑 License 管理")
    
    # Current status
    st.subheader("当前状态")
    
    license_info = license_manager.get_license_info()
    
    col1, col2 = st.columns(2)
    
    with col1:
        if is_pro:
            if license_info.get("is_trial"):
                # 试用版
                st.warning("🎁 **试用版**")
                days_remaining = license_info.get("days_remaining", 0)
                st.write(f"剩余天数: **{days_remaining} 天**")
                st.write(f"过期时间: {license_info.get('expire_at', 'N/A')[:10]}")
                
                if days_remaining <= 2:
                    st.error("⚠️ 试用即将结束，请购买 License 继续使用")
            else:
                # 正式版
                st.success("✅ **已激活专业版**")
                st.write(f"License Key: {license_info.get('key', 'N/A')}")
                
                expire_at = license_info.get('expire_at')
                if expire_at:
                    st.write(f"过期时间: {expire_at[:10]}")
                
                days_remaining = license_info.get('days_remaining', 0)
                if days_remaining > 30:
                    st.success(f"剩余 {days_remaining} 天")
                elif days_remaining > 7:
                    st.warning(f"剩余 {days_remaining} 天，即将过期")
                else:
                    st.error(f"剩余 {days_remaining} 天，请尽快续费")
        else:
            st.info("🔒 **免费版**")
            st.write("部分功能受限")
    
    with col2:
        if is_pro:
            st.write("**已解锁功能:**")
            for feature in ["高级匹配", "数据导出", "自动更新", "无限搜索"]:
                st.write(f"✅ {feature}")
            
            if license_info.get("is_trial"):
                st.write("**试用说明:**")
                st.write("🎁 7天免费试用")
                st.write("📦 包含全部功能")
                st.write("⏰ 试用结束后需购买")
            else:
                st.write("**安全机制:**")
                st.write("🔄 每小时自动验证")
                st.write("📱 设备绑定保护")
        else:
            st.write("**受限功能:**")
            for feature in ["高级匹配", "数据导出", "自动更新"]:
                st.write(f"❌ {feature}")
    
    st.divider()
    
    # Activate license
    if not is_pro:
        st.subheader("激活 License")
        
        license_key = st.text_input(
            "输入 License Key",
            placeholder="JGP-XXXX-XXXX-XXXX-XXXX"
        )
        
        if st.button("激活", type="primary"):
            if license_key:
                success, message = license_manager.activate(license_key)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.warning("请输入 License Key")
        
        st.divider()
        
        # Upgrade info
        st.subheader("升级到专业版")
        
        upgrade_info = get_upgrade_info()
        
        st.write("**专业版功能:**")
        for benefit in upgrade_info["benefits"]:
            st.write(f"✅ {benefit}")
        
        st.write("**定价:**")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("月度", upgrade_info["pricing"]["monthly"])
        
        with col2:
            st.metric("年度", upgrade_info["pricing"]["yearly"])
        
        with col3:
            st.metric("终身版", upgrade_info["pricing"]["lifetime"])
        
        with col4:
            st.metric("早鸟价", upgrade_info["pricing"]["early_bird"])
        
        st.info(f"🎁 新用户可享 **{upgrade_info['trial']['days']}天免费试用**")
    
    else:
        # Deactivate
        st.subheader("停用 License")
        
        if st.button("停用", type="secondary"):
            license_manager.deactivate()
            st.success("已停用 License")
            st.rerun()


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
                limit=50 if not is_pro else 200
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
                max_reviews = 10 if not is_pro else 20
                reviews = job_manager.get_company_reviews(c.get("id", ""), limit=max_reviews)
                if reviews:
                    st.subheader("💬 员工评价")
                    for rev in reviews[:max_reviews]:
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
    
    if not is_pro:
        st.warning("⚠️ 免费版限制: 最多显示 10 个匹配结果")
    
    st.info("填写你的信息，系统会为你推荐匹配的岗位")
    
    with st.form("user_profile"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("姓名")
            current_title = st.text_input("当前职位")
            experience_years = st.number_input("工作年限", 0, 30, 3)
            education = st.selectbox("学历", ["大专", "本科", "硕士", "博士"])
        
        with col2:
            skills = st.text_input("技能 (逗号分隔)", placeholder="Python, Java, Go")
            desired_salary = st.slider("期望薪资 (K)", 0, 100, 30)
            location = st.text_input("期望地点", placeholder="北京")
            prefer_remote = st.checkbox("接受远程办公")
        
        if st.form_submit_button("开始匹配", type="primary"):
            from src.jobgraph.models import UserProfile
            import hashlib
            
            user = UserProfile(
                id=hashlib.md5(name.encode()).hexdigest()[:16],
                name=name,
                current_title=current_title,
                experience_years=experience_years,
                education=education,
                skills=[s.strip() for s in skills.split(",") if s.strip()],
                desired_salary_min=desired_salary * 1000 * 0.8,
                desired_salary_max=desired_salary * 1000 * 1.2,
                desired_locations=[location] if location else [],
                prefer_remote=prefer_remote,
            )
            
            job_manager.create_user_profile(user)
            
            max_results = 10 if not is_pro else 50
            matches = job_manager.find_matching_jobs(user.id, limit=max_results)
            
            if matches:
                st.subheader(f"为你推荐 {len(matches)} 个岗位")
                
                for match in matches:
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
                            st.write(f"**薪资**: {match.get('salary_min', 0)/1000:.0f}-{match.get('salary_max', 0)/1000:.0f}K")
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


# ============================================================
# Footer
# ============================================================

st.divider()
st.caption(f"🔒 JobGraph {edition_name} v{edition_info['version']} | 你的求职，你做主 — 数据仅存在本地，不留任何痕迹")
