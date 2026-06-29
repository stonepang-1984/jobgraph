"""SQLite 存储后端

当 Neo4j 不可用时使用的轻量级存储方案
"""

import json
import os
import re
import sqlite3
from pathlib import Path

from loguru import logger

LABEL_MAP = {
    "Company": "companies",
    "Job": "jobs",
    "Review": "reviews",
    "Pitfall": "pitfalls",
    "UserProfile": "user_profiles",
    "Person": "people",
}

_COLUMNS_BY_TABLE = {}

def _get_columns(conn, table):
    if table not in _COLUMNS_BY_TABLE:
        cursor = conn.execute(f"PRAGMA table_info({table})")
        _COLUMNS_BY_TABLE[table] = {row[1] for row in cursor.fetchall()}
    return _COLUMNS_BY_TABLE[table]


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

    # ── helpers ───────────────────────────────────────────────

    @staticmethod
    def _prepare_value(value):
        if isinstance(value, list):
            return json.dumps(value, ensure_ascii=False)
        if isinstance(value, bool):
            return 1 if value else 0
        return value

    @staticmethod
    def _label_to_table(label: str) -> str | None:
        return LABEL_MAP.get(label)

    # ── write ──────────────────────────────────────────────

    def execute_write(self, cypher: str, params: dict = None):
        try:
            statements = self._parse_write(cypher, params or {})
            if not statements:
                return

            with self._connect() as conn:
                for sql, sql_params in statements:
                    conn.execute(sql, sql_params)
                conn.commit()

        except Exception as e:
            logger.error(f"SQLite 写入失败: {e}")
            logger.debug(f"Cypher: {cypher}")
            raise

    def _parse_write(self, cypher: str, params: dict) -> list[tuple[str, list]]:
        cypher = cypher.strip()
        results = []

        clauses = re.split(r'\bWITH\b', cypher, flags=re.IGNORECASE)

        for clause in clauses:
            clause = clause.strip()
            if not clause:
                continue

            # MERGE (X:Label {id: $id}) SET col = $val, ...
            m = re.match(
                r'MERGE\s*\(\s*\w+\s*:\s*(\w+)\s*(?:\{[^}]*\})?\s*\)\s*SET\s+(.+)',
                clause, re.IGNORECASE | re.DOTALL
            )
            if m:
                label = m.group(1)
                table = self._label_to_table(label)
                if not table:
                    continue
                cols = []
                vals = []
                for key, value in params.items():
                    if key == "id":
                        continue
                    cols.append(key)
                    vals.append(self._prepare_value(value))
                cols.insert(0, "id")
                vals.insert(0, params.get("id"))
                placeholders = ", ".join("?" for _ in cols)
                cols_str = ", ".join(cols)
                results.append((
                    f"INSERT OR REPLACE INTO {table} ({cols_str}) VALUES ({placeholders})",
                    vals,
                ))
                continue

            # CREATE (X:Label {id: $id, col: $val, ...})
            m = re.match(
                r'CREATE\s*\(\s*\w+\s*:\s*(\w+)\s*\{([^}]+)\}\s*\)',
                clause, re.IGNORECASE | re.DOTALL
            )
            if m:
                label = m.group(1)
                table = self._label_to_table(label)
                if not table:
                    continue
                prop_pairs = re.findall(r'(\w+)\s*:\s*\$(\w+)', m.group(2))
                cols = []
                vals = []
                for col, param_key in prop_pairs:
                    if param_key in params:
                        cols.append(col)
                        vals.append(self._prepare_value(params[param_key]))
                if cols:
                    placeholders = ", ".join("?" for _ in cols)
                    cols_str = ", ".join(cols)
                    results.append((
                        f"INSERT INTO {table} ({cols_str}) VALUES ({placeholders})",
                        vals,
                    ))
                continue

        return results

    # ── query ──────────────────────────────────────────────

    def execute_query(self, cypher: str, params: dict = None) -> list[dict]:
        try:
            sql, sql_params = self._parse_query(cypher, params or {})
            if sql is None:
                return []

            with self._connect() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(sql, sql_params)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"SQLite 查询失败: {e}")
            logger.debug(f"Cypher: {cypher}")
            return []

    def _translate_where(self, where_clause: str, params: dict) -> tuple[str, list]:
        sql_params = []
        result = where_clause

        # 移除变量别名前缀: c.name → name, j.title → title 等
        result = re.sub(r'\w+\.(\w+)', r'\1', result)

        # any(...) 表达式 → 1=1 （忽略复杂条件）
        result = re.sub(r'any\s*\([^)]*\)', '1=1', result, flags=re.IGNORECASE | re.DOTALL)

        # 处理条件中的参数引用
        def handle_condition(m):
            col = m.group(1)
            op = m.group(2).strip()
            param_ref = m.group(3)
            val = params.get(param_ref)
            if val is not None:
                sql_params.append(val)
                return f"{col} {op} ?"
            return f"{col} {op} NULL"

        # = true / = false
        result = re.sub(r'(\w+)\s*=\s*true\b', r'\1 = 1', result, flags=re.IGNORECASE)
        result = re.sub(r'(\w+)\s*=\s*false\b', r'\1 = 0', result, flags=re.IGNORECASE)

        # IS NOT NULL / IS NULL
        # (already SQL compatible)

        # CONTAINS $param → LIKE ?
        def handle_contains(m):
            col = m.group(1)
            param_ref = m.group(2)
            val = params.get(param_ref)
            sql_params.append(f"%{val}%" if val is not None else "%")
            return f"{col} LIKE ?"

        result = re.sub(r'(\w+)\s+CONTAINS\s+\$(\w+)', handle_contains, result, flags=re.IGNORECASE)

        # 比较操作符 >= / <= / = / > / < 接 $param
        result = re.sub(
            r'(\w+)\s*([><=!]+)\s*\$(\w+)',
            lambda m: handle_condition(m),
            result, flags=re.IGNORECASE
        )

        # $param 单独出现（如 LIMIT $limit 不在这里处理）
        # 处理 MATCH (c:Company {id: $id}) 这种内联参数（已由上层处理）

        return result, sql_params

    _TABLE_TO_LABEL = {v: k for k, v in LABEL_MAP.items()}

    def _parse_query(self, cypher: str, params: dict) -> tuple[str | None, list]:
        cypher = cypher.strip()

        # CALL db.labels()
        if cypher.startswith("CALL db.labels()"):
            cases = " ".join(
                f"WHEN '{t}' THEN '{lb}'" for t, lb in self._TABLE_TO_LABEL.items()
            )
            known_tables = ", ".join(f"'{t}'" for t in self._TABLE_TO_LABEL)
            return (
                f"SELECT CASE name {cases} END AS label "
                f"FROM sqlite_master WHERE type='table' AND name IN ({known_tables})",
                [],
            )

        # MATCH (n:Label) RETURN count(n) AS cnt
        m = re.search(
            r'MATCH\s*\(\s*\w+\s*:\s*(\w+)\s*\).*?RETURN\s+count\(', cypher, re.IGNORECASE | re.DOTALL
        )
        if m:
            table = self._label_to_table(m.group(1))
            if table:
                return f"SELECT COUNT(*) AS cnt FROM {table}", []

        # 提取主 MATCH 中的标签
        m = re.match(
            r'MATCH\s*\(\s*(\w+)\s*:\s*(\w+)\s*(?:\{\s*id\s*:\s*\$(\w+)\s*\})?\s*\)',
            cypher, re.IGNORECASE | re.DOTALL
        )
        if not m:
            m = re.match(
                r'MATCH\s*\(\s*(\w+)\s*:\s*(\w+)\s*\)',
                cypher, re.IGNORECASE | re.DOTALL
            )
        if not m:
            logger.warning(f"未识别的 Cypher 查询: {cypher[:100]}...")
            return "SELECT 1", []

        label = m.group(2)
        table = self._label_to_table(label)
        if not table:
            return None, []

        id_param = m.group(3) if m.lastindex and m.lastindex >= 3 and m.group(3) else None
        sql_params = []
        where_parts = []

        if id_param and id_param in params:
            where_parts.append("id = ?")
            sql_params.append(params[id_param])

        # WHERE 子句
        where_m = re.search(
            r'WHERE\s+(.+?)(?:\s+RETURN|\s+ORDER\s+BY|\s+LIMIT|\s*$)',
            cypher, re.IGNORECASE | re.DOTALL
        )
        if where_m:
            translated, extra_params = self._translate_where(where_m.group(1), params)
            sql_params.extend(extra_params)
            where_parts.append(translated)

        # 检查是否有聚合函数
        ret_m = re.search(
            r'RETURN\s+(.*?)(?:\s+ORDER\s+BY|\s+LIMIT|\s*$)',
            cypher, re.IGNORECASE | re.DOTALL
        )
        has_aggregates = False
        ret_expr_str = ""
        if ret_m:
            ret_expr_str = ret_m.group(1).strip()
            has_aggregates = bool(re.search(
                r'\b(collect|avg|count|sum|min|max|percentileDisc)\s*\(',
                ret_expr_str, re.IGNORECASE
            ))

        if has_aggregates:
            return self._build_aggregate_query(
                table, label, ret_expr_str, where_parts, sql_params, cypher
            )

        # 非聚合查询
        sql = f"SELECT * FROM {table}"
        if where_parts:
            sql += " WHERE " + " AND ".join(where_parts)

        # ORDER BY
        order_m = re.search(r'ORDER\s+BY\s+(.+?)(?:\s+LIMIT|\s*$)', cypher, re.IGNORECASE | re.DOTALL)
        if order_m:
            order_by = re.sub(r'\w+\.', '', order_m.group(1).strip())
            sql += f" ORDER BY {order_by}"

        # LIMIT
        limit_m = re.search(r'LIMIT\s+(\$?\w+)', cypher, re.IGNORECASE)
        if limit_m:
            limit_val = limit_m.group(1)
            if limit_val.startswith("$"):
                param_key = limit_val[1:]
                if param_key in params:
                    sql += " LIMIT ?"
                    sql_params.append(params[param_key])
            else:
                sql += f" LIMIT {limit_val}"

        return sql, sql_params

    def _build_aggregate_query(
        self, table: str, label: str, ret_expr_str: str,
        where_parts: list, where_params: list, cypher: str
    ) -> tuple[str, list]:
        # 解析 RETURN 表达式（用逗号分割，考虑嵌套括号）
        exprs = self._split_return_exprs(ret_expr_str)
        select_parts = []
        select_params = list(where_params)

        for expr in exprs:
            expr = expr.strip()
            if not expr:
                continue

            # 单独变量 (RETURN c) → SELECT *
            if re.match(r'^\w{1,3}$', expr) and expr.lower() != "as":
                continue

            # collect(DISTINCT { ... }) AS alias
            m = re.match(
                r'collect\s*\(\s*DISTINCT\s*\{(.+)\}\s*\)(?:\s+AS\s+(\w+))?',
                expr, re.IGNORECASE | re.DOTALL
            )
            if m:
                alias = m.group(2) or "collection"
                select_parts.append(f"'[]' AS {alias}")
                continue

            # avg(c.xxx) AS alias
            m = re.match(r'avg\s*\(\s*\w+\.(\w+)\s*\)(?:\s+AS\s+(\w+))?', expr, re.IGNORECASE)
            if m:
                alias = m.group(2) or f"avg_{m.group(1)}"
                select_parts.append(f"avg({m.group(1)}) AS {alias}")
                continue

            # count(DISTINCT x) AS alias
            m = re.match(r'count\s*\(\s*DISTINCT\s+\w+\s*\)(?:\s+AS\s+(\w+))?', expr, re.IGNORECASE)
            if m:
                alias = m.group(1) or "cnt"
                select_parts.append(f"COUNT(*) AS {alias}")
                continue

            # count(*) AS alias
            m = re.match(r'count\s*\(\s*\*\s*\)(?:\s+AS\s+(\w+))?', expr, re.IGNORECASE)
            if m:
                alias = m.group(1) or "cnt"
                select_parts.append(f"COUNT(*) AS {alias}")
                continue

            # percentileDisc(x, p) AS alias → avg 替代
            m = re.match(
                r'percentileDisc\s*\(\s*\w+\.(\w+)\s*,\s*[\d.]+\s*\)(?:\s+AS\s+(\w+))?',
                expr, re.IGNORECASE
            )
            if m:
                alias = m.group(2) or m.group(1)
                select_parts.append(f"avg({m.group(1)}) AS {alias}")
                continue

            # avg((x + y) / 2) AS mean
            m = re.match(r'avg\s*\(\s*\(([^)]+)\)\s*\)(?:\s+AS\s+(\w+))?', expr, re.IGNORECASE)
            if m:
                alias = m.group(2) or "mean"
                inner = re.sub(r'\w+\.', '', m.group(1))
                select_parts.append(f"avg({inner}) AS {alias}")
                continue

            # c.xxx AS alias
            m = re.match(r'\w+\.(\w+)(?:\s+AS\s+(\w+))?', expr, re.IGNORECASE)
            if m:
                alias = m.group(2) or m.group(1)
                select_parts.append(f"{m.group(1)} AS {alias}")
                continue

        where_sql = ""
        if where_parts:
            where_sql = " WHERE " + " AND ".join(where_parts)

        if not select_parts:
            return f"SELECT * FROM {table}{where_sql}", select_params

        order_m = re.search(r'ORDER\s+BY\s+(.+?)(?:\s+LIMIT|\s*$)', cypher, re.IGNORECASE | re.DOTALL)
        order_sql = ""
        if order_m:
            order_by = re.sub(r'\w+\.', '', order_m.group(1).strip())
            order_sql = f" ORDER BY {order_by}"

        select_clause = ", ".join(select_parts)
        sql = f"SELECT {select_clause} FROM {table}{where_sql}{order_sql}"
        return sql, select_params

    @staticmethod
    def _split_return_exprs(expr_str: str) -> list[str]:
        exprs = []
        depth = 0
        current = []
        for ch in expr_str:
            if ch in '({':
                depth += 1
                current.append(ch)
            elif ch in ')}':
                depth -= 1
                current.append(ch)
            elif ch == ',' and depth == 0:
                exprs.append(''.join(current).strip())
                current = []
            else:
                current.append(ch)
        if current:
            exprs.append(''.join(current).strip())
        return exprs

    def close(self):
        pass
