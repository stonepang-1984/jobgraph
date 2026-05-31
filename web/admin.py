"""People Graph Admin - Backend Management Interface."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
import pandas as pd
from loguru import logger

from src.graph.people.manager import people_manager
from src.graph.people.models import Person, Company, University, WorkExperience, Education
from src.graph.people.crawlers.wikipedia import wikipedia_crawler


# ============================================================
# Page Config
# ============================================================

st.set_page_config(
    page_title="人物图谱管理后台",
    page_icon="⚙️",
    layout="wide",
)

st.title("⚙️ 人物图谱管理后台")
st.markdown("管理人物、企业、高校数据及其关系")


# ============================================================
# Sidebar Navigation
# ============================================================

with st.sidebar:
    st.header("📋 功能菜单")

    page = st.radio(
        "选择功能",
        [
            "📊 数据概览",
            "👤 人物管理",
            "🏢 企业管理",
            "🎓 高校管理",
            "🔗 关系管理",
            "📥 数据导入",
            "🔄 数据同步",
        ],
    )

    st.divider()

    # Quick stats
    st.header("📈 快速统计")
    try:
        stats = people_manager.get_stats()
        st.metric("人物", stats.get("persons", 0))
        st.metric("企业", stats.get("companies", 0))
        st.metric("高校", stats.get("universities", 0))
    except Exception as e:
        st.error(f"统计失败: {e}")


# ============================================================
# Data Overview
# ============================================================

if page == "📊 数据概览":
    st.header("📊 数据概览")

    try:
        stats = people_manager.get_stats()

        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("👤 人物总数", stats.get("persons", 0))
        col2.metric("🏢 企业总数", stats.get("companies", 0))
        col3.metric("🎓 高校总数", stats.get("universities", 0))
        col4.metric("🔗 关系总数", 
                    stats.get("work_rels", 0) + 
                    stats.get("edu_rels", 0) + 
                    stats.get("know_rels", 0))

        st.divider()

        # Relationship breakdown
        col1, col2, col3 = st.columns(3)
        col1.metric("💼 任职关系", stats.get("work_rels", 0))
        col2.metric("📚 教育关系", stats.get("edu_rels", 0))
        col3.metric("🤝 人际关系", stats.get("know_rels", 0))

        st.divider()

        # Recent data
        st.subheader("📋 最近添加的人物")
        from src.graph.neo4j_client import neo4j_client
        recent = neo4j_client.execute_query(
            "MATCH (p:Person) RETURN p.name AS name, p.created_at AS created ORDER BY p.created_at DESC LIMIT 10"
        )
        if recent:
            df = pd.DataFrame(recent)
            st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error(f"获取数据概览失败: {e}")


# ============================================================
# Person Management
# ============================================================

elif page == "👤 人物管理":
    st.header("👤 人物管理")

    tab1, tab2, tab3 = st.tabs(["查看列表", "添加人物", "编辑人物"])

    with tab1:
        st.subheader("人物列表")
        try:
            from src.graph.neo4j_client import neo4j_client
            persons = neo4j_client.execute_query(
                "MATCH (p:Person) RETURN p.id AS id, p.name AS name, p.name_en AS name_en, p.bio AS bio ORDER BY p.name"
            )
            if persons:
                df = pd.DataFrame(persons)
                st.dataframe(df, use_container_width=True)

                # Delete person
                st.divider()
                st.subheader("删除人物")
                person_to_delete = st.selectbox(
                    "选择要删除的人物",
                    options=[p["name"] for p in persons],
                )
                if st.button("确认删除", type="primary"):
                    person_id = next(p["id"] for p in persons if p["name"] == person_to_delete)
                    neo4j_client.execute_write(
                        "MATCH (p:Person {id: $id}) DETACH DELETE p",
                        {"id": person_id},
                    )
                    st.success(f"已删除: {person_to_delete}")
                    st.rerun()
            else:
                st.info("暂无数据")
        except Exception as e:
            st.error(f"获取人物列表失败: {e}")

    with tab2:
        st.subheader("添加人物")
        with st.form("add_person_form"):
            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input("姓名 *", placeholder="张三")
                name_en = st.text_input("英文名", placeholder="Zhang San")
                gender = st.selectbox("性别", ["男", "女", "其他"])
                birth_date = st.text_input("出生日期", placeholder="1990-01-01")

            with col2:
                nationality = st.text_input("国籍", placeholder="中国")
                bio = st.text_area("简介", placeholder="个人简介...")
                tags = st.text_input("标签", placeholder="CEO, 创始人 (逗号分隔)")

            if st.form_submit_button("添加"):
                if name:
                    import hashlib
                    person_id = hashlib.md5(name.encode()).hexdigest()[:16]

                    person = Person(
                        id=person_id,
                        name=name,
                        name_en=name_en,
                        gender=gender,
                        birth_date=birth_date,
                        nationality=nationality,
                        bio=bio,
                        tags=[t.strip() for t in tags.split(",") if t.strip()],
                        source="manual",
                    )

                    try:
                        people_manager.create_person(person)
                        st.success(f"已添加: {name}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"添加失败: {e}")
                else:
                    st.error("请输入姓名")

    with tab3:
        st.subheader("编辑人物")
        try:
            from src.graph.neo4j_client import neo4j_client
            persons = neo4j_client.execute_query(
                "MATCH (p:Person) RETURN p.id AS id, p.name AS name"
            )

            if persons:
                selected = st.selectbox("选择人物", [p["name"] for p in persons])
                person_id = next(p["id"] for p in persons if p["name"] == selected)

                # Get current data
                current = neo4j_client.execute_query(
                    "MATCH (p:Person {id: $id}) RETURN p",
                    {"id": person_id},
                )

                if current:
                    p = current[0]["p"]

                    with st.form("edit_person_form"):
                        col1, col2 = st.columns(2)

                        with col1:
                            name = st.text_input("姓名", value=p.get("name", ""))
                            name_en = st.text_input("英文名", value=p.get("name_en", ""))
                            gender = st.selectbox("性别", ["男", "女", "其他"], 
                                                index=["男", "女", "其他"].index(p.get("gender", "男")))

                        with col2:
                            bio = st.text_area("简介", value=p.get("bio", ""))
                            tags = st.text_input("标签", value=", ".join(p.get("tags", [])))

                        if st.form_submit_button("保存"):
                            neo4j_client.execute_write(
                                """
                                MATCH (p:Person {id: $id})
                                SET p.name = $name,
                                    p.name_en = $name_en,
                                    p.gender = $gender,
                                    p.bio = $bio,
                                    p.tags = $tags,
                                    p.updated_at = datetime()
                                """,
                                {
                                    "id": person_id,
                                    "name": name,
                                    "name_en": name_en,
                                    "gender": gender,
                                    "bio": bio,
                                    "tags": [t.strip() for t in tags.split(",") if t.strip()],
                                },
                            )
                            st.success(f"已更新: {name}")
                            st.rerun()
        except Exception as e:
            st.error(f"获取人物数据失败: {e}")


# ============================================================
# Company Management
# ============================================================

elif page == "🏢 企业管理":
    st.header("🏢 企业管理")

    tab1, tab2 = st.tabs(["查看列表", "添加企业"])

    with tab1:
        try:
            from src.graph.neo4j_client import neo4j_client
            companies = neo4j_client.execute_query(
                "MATCH (c:Company) RETURN c.id AS id, c.name AS name, c.industry AS industry, c.headquarters AS headquarters ORDER BY c.name"
            )
            if companies:
                df = pd.DataFrame(companies)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("暂无企业数据")
        except Exception as e:
            st.error(f"获取企业列表失败: {e}")

    with tab2:
        with st.form("add_company_form"):
            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input("企业名称 *", placeholder="腾讯")
                name_en = st.text_input("英文名", placeholder="Tencent")
                industry = st.text_input("行业", placeholder="互联网")

            with col2:
                headquarters = st.text_input("总部", placeholder="深圳")
                website = st.text_input("官网", placeholder="https://www.tencent.com")
                description = st.text_area("简介")

            if st.form_submit_button("添加"):
                if name:
                    import hashlib
                    company_id = hashlib.md5(name.encode()).hexdigest()[:16]

                    company = Company(
                        id=company_id,
                        name=name,
                        name_en=name_en,
                        industry=industry,
                        headquarters=headquarters,
                        website=website,
                        description=description,
                        source="manual",
                    )

                    try:
                        people_manager.create_company(company)
                        st.success(f"已添加: {name}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"添加失败: {e}")
                else:
                    st.error("请输入企业名称")


# ============================================================
# University Management
# ============================================================

elif page == "🎓 高校管理":
    st.header("🎓 高校管理")

    tab1, tab2 = st.tabs(["查看列表", "添加高校"])

    with tab1:
        try:
            from src.graph.neo4j_client import neo4j_client
            universities = neo4j_client.execute_query(
                "MATCH (u:University) RETURN u.id AS id, u.name AS name, u.location AS location, u.country AS country ORDER BY u.name"
            )
            if universities:
                df = pd.DataFrame(universities)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("暂无高校数据")
        except Exception as e:
            st.error(f"获取高校列表失败: {e}")

    with tab2:
        with st.form("add_university_form"):
            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input("高校名称 *", placeholder="清华大学")
                name_en = st.text_input("英文名", placeholder="Tsinghua University")
                country = st.text_input("国家", placeholder="中国")

            with col2:
                location = st.text_input("城市", placeholder="北京")
                website = st.text_input("官网", placeholder="https://www.tsinghua.edu.cn")
                description = st.text_area("简介")

            if st.form_submit_button("添加"):
                if name:
                    import hashlib
                    uni_id = hashlib.md5(name.encode()).hexdigest()[:16]

                    university = University(
                        id=uni_id,
                        name=name,
                        name_en=name_en,
                        country=country,
                        location=location,
                        website=website,
                        description=description,
                        source="manual",
                    )

                    try:
                        people_manager.create_university(university)
                        st.success(f"已添加: {name}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"添加失败: {e}")
                else:
                    st.error("请输入高校名称")


# ============================================================
# Relationship Management
# ============================================================

elif page == "🔗 关系管理":
    st.header("🔗 关系管理")

    tab1, tab2 = st.tabs(["添加任职关系", "添加教育关系"])

    with tab1:
        st.subheader("添加任职关系")
        try:
            from src.graph.neo4j_client import neo4j_client

            persons = neo4j_client.execute_query("MATCH (p:Person) RETURN p.id AS id, p.name AS name ORDER BY p.name")
            companies = neo4j_client.execute_query("MATCH (c:Company) RETURN c.id AS id, c.name AS name ORDER BY c.name")

            if persons and companies:
                with st.form("add_work_form"):
                    col1, col2 = st.columns(2)

                    with col1:
                        person_name = st.selectbox("选择人物", [p["name"] for p in persons])
                        company_name = st.selectbox("选择企业", [c["name"] for c in companies])

                    with col2:
                        position = st.text_input("职位", placeholder="CEO")
                        is_current = st.checkbox("在职", True)

                    start_date = st.text_input("入职时间", placeholder="2020-01")

                    if st.form_submit_button("添加"):
                        person_id = next(p["id"] for p in persons if p["name"] == person_name)
                        company_id = next(c["id"] for c in companies if c["name"] == company_name)

                        exp = WorkExperience(
                            person_id=person_id,
                            company_id=company_id,
                            position=position,
                            start_date=start_date,
                            is_current=is_current,
                            source="manual",
                        )

                        try:
                            people_manager.add_work_experience(exp)
                            st.success(f"已添加: {person_name} -> {company_name}")
                        except Exception as e:
                            st.error(f"添加失败: {e}")
            else:
                st.warning("请先添加人物和企业数据")

        except Exception as e:
            st.error(f"获取数据失败: {e}")

    with tab2:
        st.subheader("添加教育关系")
        try:
            from src.graph.neo4j_client import neo4j_client

            persons = neo4j_client.execute_query("MATCH (p:Person) RETURN p.id AS id, p.name AS name ORDER BY p.name")
            universities = neo4j_client.execute_query("MATCH (u:University) RETURN u.id AS id, u.name AS name ORDER BY u.name")

            if persons and universities:
                with st.form("add_education_form"):
                    col1, col2 = st.columns(2)

                    with col1:
                        person_name = st.selectbox("选择人物", [p["name"] for p in persons])
                        uni_name = st.selectbox("选择高校", [u["name"] for u in universities])

                    with col2:
                        degree = st.selectbox("学位", ["本科", "硕士", "博士", "MBA", "其他"])
                        major = st.text_input("专业", placeholder="计算机科学")

                    if st.form_submit_button("添加"):
                        person_id = next(p["id"] for p in persons if p["name"] == person_name)
                        uni_id = next(u["id"] for u in universities if u["name"] == uni_name)

                        edu = Education(
                            person_id=person_id,
                            university_id=uni_id,
                            degree=degree,
                            major=major,
                            source="manual",
                        )

                        try:
                            people_manager.add_education(edu)
                            st.success(f"已添加: {person_name} -> {uni_name}")
                        except Exception as e:
                            st.error(f"添加失败: {e}")
            else:
                st.warning("请先添加人物和高校数据")

        except Exception as e:
            st.error(f"获取数据失败: {e}")


# ============================================================
# Data Import
# ============================================================

elif page == "📥 数据导入":
    st.header("📥 数据导入")

    tab1, tab2 = st.tabs(["导入示例数据", "从文件导入"])

    with tab1:
        st.subheader("导入示例数据")
        st.markdown("导入预置的中国科技行业领袖数据（腾讯、阿里、百度、字节、华为等）")

        if st.button("导入示例数据", type="primary"):
            with st.spinner("正在导入..."):
                try:
                    # Import sample data
                    from scripts.import_people import import_data
                    import_data()
                    st.success("示例数据导入成功！")
                    st.rerun()
                except Exception as e:
                    st.error(f"导入失败: {e}")

    with tab2:
        st.subheader("从文件导入")
        st.markdown("支持 CSV、JSON 格式文件")

        uploaded_file = st.file_uploader("选择文件", type=["csv", "json"])

        if uploaded_file:
            st.info("文件导入功能开发中...")


# ============================================================
# Data Sync
# ============================================================

elif page == "🔄 数据同步":
    st.header("🔄 数据同步")

    st.subheader("从 Wikipedia 同步")
    st.markdown("从 Wikipedia 抓取人物信息并更新到图谱")

    with st.form("wiki_sync_form"):
        wiki_name = st.text_input("Wikipedia 页面标题", placeholder="马化腾")

        if st.form_submit_button("开始同步"):
            if wiki_name:
                with st.spinner(f"正在从 Wikipedia 获取 {wiki_name} 的数据..."):
                    try:
                        result = wikipedia_crawler.crawl_person(wiki_name)

                        if result.persons:
                            st.success(f"获取到 {len(result.persons)} 个人物")

                            # Import to graph
                            for person_data in result.persons:
                                person = Person(**person_data)
                                people_manager.create_person(person)

                            # Import companies
                            for company_data in result.companies:
                                company = Company(**company_data)
                                people_manager.create_company(company)

                            # Import universities
                            for uni_data in result.universities:
                                university = University(**uni_data)
                                people_manager.create_university(university)

                            # Import work experiences
                            for exp_data in result.work_experiences:
                                exp = WorkExperience(**exp_data)
                                people_manager.add_work_experience(exp)

                            # Import educations
                            for edu_data in result.educations:
                                edu = Education(**edu_data)
                                people_manager.add_education(edu)

                            st.success("数据同步完成！")
                        else:
                            st.warning("未找到相关数据")

                        if result.errors:
                            st.warning(f"警告: {result.errors}")

                    except Exception as e:
                        st.error(f"同步失败: {e}")
            else:
                st.error("请输入 Wikipedia 页面标题")


# ============================================================
# Footer
# ============================================================

st.divider()
st.caption("人物图谱管理后台 v1.0")
