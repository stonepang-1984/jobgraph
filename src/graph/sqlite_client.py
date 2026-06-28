"""SQLite 存储后端

当 Neo4j 不可用时使用的轻量级存储方案
"""

import os
import sqlite3
from pathlib import Path

from loguru import logger


class SQLiteClient:
    """SQLite 图数据库客户端"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.getenv("SQLITE_DB_PATH", "data/jobgraph.db")

        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        logger.info(f"SQLite 数据库已连接: {db_path}")

    def _connect(self):
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """初始化数据库表"""
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS companies (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    name_en TEXT,
                    industry TEXT,
                    size TEXT,
                    founded INTEGER,
                    headquarters TEXT,
                    website TEXT,
                    description TEXT,
                    funding_stage TEXT,
                    valuation REAL,
                    is_listed BOOLEAN DEFAULT 0,
                    stock_code TEXT,
                    employees INTEGER,
                    avg_salary REAL,
                    avg_rating REAL,
                    review_count INTEGER DEFAULT 0,
                    risk_level TEXT DEFAULT 'medium',
                    risk_score REAL DEFAULT 0.5,
                    risk_factors TEXT,
                    tags TEXT,
                    source TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    company_id TEXT,
                    company_name TEXT,
                    department TEXT,
                    job_type TEXT DEFAULT 'full_time',
                    location TEXT,
                    is_remote BOOLEAN DEFAULT 0,
                    salary_min REAL,
                    salary_max REAL,
                    salary_months INTEGER DEFAULT 12,
                    experience_years INTEGER,
                    education TEXT,
                    skills TEXT,
                    description TEXT,
                    requirements TEXT,
                    benefits TEXT,
                    source TEXT,
                    source_url TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS reviews (
                    id TEXT PRIMARY KEY,
                    company_id TEXT,
                    overall_rating REAL,
                    salary_rating REAL,
                    work_life_rating REAL,
                    management_rating REAL,
                    culture_rating REAL,
                    growth_rating REAL,
                    title TEXT,
                    pros TEXT,
                    cons TEXT,
                    reviewer_title TEXT,
                    reviewer_tenure TEXT,
                    is_current_employee BOOLEAN,
                    source TEXT,
                    posted_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS pitfalls (
                    id TEXT PRIMARY KEY,
                    company_id TEXT,
                    pitfall_type TEXT,
                    severity INTEGER DEFAULT 3,
                    description TEXT,
                    evidence TEXT,
                    report_count INTEGER DEFAULT 0,
                    confirmed_count INTEGER DEFAULT 0,
                    source TEXT,
                    is_verified BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS user_profiles (
                    id TEXT PRIMARY KEY,
                    name TEXT,
                    current_title TEXT,
                    current_company TEXT,
                    experience_years INTEGER DEFAULT 0,
                    education TEXT,
                    location TEXT,
                    skills TEXT,
                    certifications TEXT,
                    desired_titles TEXT,
                    desired_locations TEXT,
                    desired_salary_min REAL,
                    desired_salary_max REAL,
                    prefer_remote BOOLEAN DEFAULT 0,
                    resume_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company_id);
                CREATE INDEX IF NOT EXISTS idx_jobs_location ON jobs(location);
                CREATE INDEX IF NOT EXISTS idx_reviews_company ON reviews(company_id);
                CREATE INDEX IF NOT EXISTS idx_pitfalls_company ON pitfalls(company_id);
            """)

    def execute_query(self, cypher: str, params: dict = None) -> list[dict]:
        """执行查询（Cypher -> SQL 转换）"""
        try:
            # 简单的 Cypher 到 SQL 转换
            sql, sql_params = self._cypher_to_sql(cypher, params or {})

            with self._connect() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(sql, sql_params)
                rows = cursor.fetchall()

                # 转换为字典列表
                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"SQLite 查询失败: {e}")
            logger.debug(f"Cypher: {cypher}")
            logger.debug(f"Params: {params}")
            return []

    def execute_write(self, cypher: str, params: dict = None):
        """执行写入"""
        try:
            sql, sql_params = self._cypher_to_sql(cypher, params or {})

            with self._connect() as conn:
                conn.execute(sql, sql_params)
                conn.commit()

        except Exception as e:
            logger.error(f"SQLite 写入失败: {e}")
            logger.debug(f"Cypher: {cypher}")
            raise

    def _cypher_to_sql(self, cypher: str, params: dict) -> tuple[str, dict]:
        """将简单 Cypher 查询转换为 SQL"""
        cypher = cypher.strip()

        # 处理 MATCH (c:Company) RETURN c
        if "MATCH (c:Company)" in cypher and "RETURN c" in cypher:
            sql = "SELECT * FROM companies"
            return sql, {}

        # 处理 MATCH (c:Company {id: $id}) RETURN c
        if "MATCH (c:Company {id: $id})" in cypher:
            return "SELECT * FROM companies WHERE id = ?", [params.get("id")]

        # 处理 MATCH (j:Job) RETURN j
        if "MATCH (j:Job)" in cypher and "RETURN j" in cypher:
            return "SELECT * FROM jobs WHERE is_active = 1", {}

        # 处理 MATCH (r:Review) RETURN r
        if "MATCH (r:Review)" in cypher and "RETURN r" in cypher:
            return "SELECT * FROM reviews", {}

        # 通用处理：尝试解析
        logger.warning(f"未识别的 Cypher 查询: {cypher[:100]}...")
        return "SELECT 1", {}

    def close(self):
        """关闭连接"""
        # SQLite 连接是短暂的，不需要显式关闭
        pass
