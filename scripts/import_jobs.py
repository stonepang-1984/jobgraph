"""Import sample job data for JobGraph.

所有职位必须包含完整的岗位职责和任职要求。
"""

import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from src.jobgraph.models import (
    Company, Job, Review, Pitfall, UserProfile,
    CompanySize, RiskLevel, JobType, FundingStage
)
from src.jobgraph.graph_manager import job_manager


# ============================================================
# Sample Companies
# ============================================================

COMPANIES = [
    # 互联网大厂
    Company(
        id="comp_tencent", name="腾讯", name_en="Tencent",
        industry="互联网", size=CompanySize.GIANT,
        founded=1998, headquarters="深圳",
        is_listed=True, stock_code="0700.HK",
        funding_stage=FundingStage.IPO, risk_level=RiskLevel.LOW,
        risk_score=0.2, avg_salary=35000, avg_rating=3.8,
        tags=["大厂", "社交", "游戏", "稳定"]
    ),
    Company(
        id="comp_alibaba", name="阿里巴巴", name_en="Alibaba",
        industry="互联网", size=CompanySize.GIANT,
        founded=1999, headquarters="杭州",
        is_listed=True, stock_code="BABA",
        funding_stage=FundingStage.IPO, risk_level=RiskLevel.LOW,
        risk_score=0.3, avg_salary=38000, avg_rating=3.5,
        tags=["大厂", "电商", "云计算"]
    ),
    Company(
        id="comp_bytedance", name="字节跳动", name_en="ByteDance",
        industry="互联网", size=CompanySize.GIANT,
        founded=2012, headquarters="北京",
        funding_stage=FundingStage.UNKNOWN, risk_level=RiskLevel.LOW,
        risk_score=0.25, avg_salary=42000, avg_rating=3.6,
        tags=["大厂", "短视频", "高薪", "加班多"]
    ),
    Company(
        id="comp_meituan", name="美团", name_en="Meituan",
        industry="互联网", size=CompanySize.GIANT,
        founded=2010, headquarters="北京",
        is_listed=True, stock_code="3690.HK",
        funding_stage=FundingStage.IPO, risk_level=RiskLevel.LOW,
        risk_score=0.3, avg_salary=32000, avg_rating=3.4,
        tags=["大厂", "本地生活", "外卖"]
    ),
    Company(
        id="comp_xiaomi", name="小米", name_en="Xiaomi",
        industry="智能硬件", size=CompanySize.GIANT,
        founded=2010, headquarters="北京",
        is_listed=True, stock_code="1810.HK",
        funding_stage=FundingStage.IPO, risk_level=RiskLevel.LOW,
        risk_score=0.25, avg_salary=30000, avg_rating=3.6,
        tags=["大厂", "智能硬件", "IoT", "手机"]
    ),
    
    # 中型公司
    Company(
        id="comp_xiaohongshu", name="小红书", name_en="Xiaohongshu",
        industry="互联网", size=CompanySize.LARGE,
        founded=2013, headquarters="上海",
        funding_stage=FundingStage.D, risk_level=RiskLevel.MEDIUM,
        risk_score=0.4, avg_salary=30000, avg_rating=3.7,
        tags=["社区", "电商", "年轻"]
    ),
    Company(
        id="comp_didi", name="滴滴出行", name_en="Didi",
        industry="互联网", size=CompanySize.GIANT,
        founded=2012, headquarters="北京",
        is_listed=True, stock_code="DIDI",
        funding_stage=FundingStage.IPO, risk_level=RiskLevel.MEDIUM,
        risk_score=0.5, avg_salary=35000, avg_rating=3.2,
        tags=["出行", "监管风险", "裁员"]
    ),
    Company(
        id="comp_pingduoduo", name="拼多多", name_en="Pinduoduo",
        industry="电商", size=CompanySize.GIANT,
        founded=2015, headquarters="上海",
        is_listed=True, stock_code="PDD",
        funding_stage=FundingStage.IPO, risk_level=RiskLevel.MEDIUM,
        risk_score=0.4, avg_salary=40000, avg_rating=3.3,
        tags=["电商", "高薪", "加班多", "快节奏"]
    ),
    
    # AI 公司
    Company(
        id="comp_sensetime", name="商汤科技", name_en="SenseTime",
        industry="人工智能", size=CompanySize.LARGE,
        founded=2014, headquarters="香港",
        is_listed=True, stock_code="0020.HK",
        funding_stage=FundingStage.IPO, risk_level=RiskLevel.MEDIUM,
        risk_score=0.45, avg_salary=38000, avg_rating=3.5,
        tags=["AI", "计算机视觉", "技术驱动"]
    ),
    
    # 创业公司 (有风险)
    Company(
        id="comp_startup_a", name="某创业公司A", name_en="Startup A",
        industry="SaaS", size=CompanySize.SMALL,
        founded=2022, headquarters="北京",
        funding_stage=FundingStage.A, risk_level=RiskLevel.HIGH,
        risk_score=0.7, avg_salary=25000, avg_rating=2.8,
        tags=["创业", "不稳定", "加班多"]
    ),
    
    # 黑心公司 (避坑示例)
    Company(
        id="comp_blacklist_a", name="黑心公司A", name_en="Bad Company A",
        industry="电商", size=CompanySize.MEDIUM,
        founded=2018, headquarters="深圳",
        funding_stage=FundingStage.B, risk_level=RiskLevel.BLACKLIST,
        risk_score=0.95, avg_salary=15000, avg_rating=1.5,
        risk_factors=["欠薪", "PUA", "996", "裁员"],
        tags=["黑名单", "避坑"]
    ),
]


# ============================================================
# Sample Jobs (必须包含完整职位描述)
# ============================================================

JOBS = [
    # ============================================================
    # 腾讯岗位
    # ============================================================
    Job(
        id="job_tencent_1", title="高级后端工程师",
        company_id="comp_tencent", company_name="腾讯",
        department="微信事业部", job_type=JobType.FULL_TIME,
        location="广州", salary_min=30000, salary_max=50000,
        salary_months=16, experience_years=3,
        education="本科",
        skills=["Java", "Go", "MySQL", "Redis", "微服务", "分布式", "Kafka"],
        description="""【岗位职责】
1. 负责微信核心系统的后端架构设计和开发，支撑亿级用户的消息、支付等核心功能
2. 参与高并发、高可用系统的架构优化，确保系统在峰值流量下的稳定性
3. 负责技术难点攻关，解决分布式系统中的数据一致性、性能瓶颈等问题
4. 参与代码评审，制定技术规范，指导初中级工程师成长
5. 与产品、设计、前端团队紧密协作，推动项目高质量交付

【技术栈】
- 语言：Java、Go
- 框架：Spring Boot、gRPC
- 数据库：MySQL、Redis、TiDB
- 中间件：Kafka、RocketMQ、ZooKeeper
- 基础设施：Kubernetes、Docker、Prometheus""",
        requirements="""1. 本科及以上学历，计算机相关专业
2. 3年以上 Java/Go 后端开发经验
3. 精通 Spring Boot 框架，熟悉微服务架构设计
4. 熟悉 MySQL、Redis 等数据库的使用和优化
5. 有分布式系统开发经验，了解 CAP 理论
6. 熟悉 Kafka、RocketMQ 等消息队列
7. 良好的沟通能力和团队协作精神
8. 有大厂经验或开源项目贡献者优先""",
        benefits=["年终奖", "股票", "五险一金", "弹性工作", "免费班车"],
        source="boss", is_active=True
    ),
    Job(
        id="job_tencent_2", title="前端开发工程师",
        company_id="comp_tencent", company_name="腾讯",
        department="QQ事业部", job_type=JobType.FULL_TIME,
        location="深圳", salary_min=25000, salary_max=40000,
        salary_months=16, experience_years=2,
        education="本科",
        skills=["React", "TypeScript", "Node.js", "Webpack", "CSS", "Git"],
        description="""【岗位职责】
1. 负责 QQ 产品的前端开发，包括 Web 端和移动端 H5 页面
2. 参与前端架构设计，优化前端工程化体系，提升开发效率
3. 负责前端性能优化，包括首屏加载、渲染性能、包体积优化等
4. 参与组件库建设，沉淀通用业务组件和技术方案
5. 关注前端技术前沿，引入新技术提升团队技术水平

【技术栈】
- 框架：React 18、Next.js
- 语言：TypeScript、JavaScript
- 构建：Webpack 5、Vite、Rollup
- 样式：CSS Modules、Styled-components、Tailwind CSS
- 工具：ESLint、Prettier、Jest、Cypress""",
        requirements="""1. 本科及以上学历，计算机相关专业
2. 2年以上前端开发经验
3. 精通 React 框架，熟悉 React Hooks 和状态管理
4. 精通 TypeScript，有大型 TypeScript 项目经验
5. 熟悉 Webpack/Vite 等构建工具
6. 了解 Node.js，有服务端渲染(SSR)经验优先
7. 有组件库开发经验优先
8. 良好的代码风格和文档习惯""",
        benefits=["年终奖", "股票", "五险一金", "免费三餐"],
        source="boss", is_active=True
    ),
    Job(
        id="job_tencent_3", title="数据工程师",
        company_id="comp_tencent", company_name="腾讯",
        department="云与智慧产业事业部", job_type=JobType.FULL_TIME,
        location="深圳", salary_min=28000, salary_max=45000,
        salary_months=16, experience_years=3,
        education="本科",
        skills=["Python", "Spark", "Hive", "Hadoop", "SQL", "Flink", "数据仓库"],
        description="""【岗位职责】
1. 负责腾讯云数据平台的架构设计和开发
2. 设计和构建数据仓库，制定数据建模规范
3. 开发 ETL 流程，确保数据质量和时效性
4. 优化大数据处理性能，降低计算和存储成本
5. 与数据分析师、算法工程师协作，支撑业务数据分析需求

【技术栈】
- 语言：Python、Scala、SQL
- 大数据：Spark、Hive、Hadoop、Flink
- 调度：Airflow、DolphinScheduler
- 存储：HDFS、S3、HBase、ClickHouse
- BI 工具：Superset、Metabase""",
        requirements="""1. 本科及以上学历，计算机、数学、统计相关专业
2. 3年以上大数据开发经验
3. 精通 SQL，熟悉 Hive/Spark SQL
4. 熟悉 Python/Scala 编程语言
5. 有数据仓库建设经验，了解维度建模方法
6. 熟悉 Hadoop/Spark/Flink 等大数据技术栈
7. 有实时数据处理经验优先
8. 良好的数据敏感度和业务理解能力""",
        benefits=["年终奖", "股票", "五险一金", "弹性工作"],
        source="boss", is_active=True
    ),

    # ============================================================
    # 字节跳动岗位
    # ============================================================
    Job(
        id="job_bytedance_1", title="算法工程师-推荐系统",
        company_id="comp_bytedance", company_name="字节跳动",
        department="抖音", job_type=JobType.FULL_TIME,
        location="北京", salary_min=35000, salary_max=60000,
        salary_months=15, experience_years=2,
        education="硕士",
        skills=["Python", "PyTorch", "TensorFlow", "推荐系统", "NLP", "Spark", "SQL"],
        description="""【岗位职责】
1. 负责抖音推荐系统的算法研发和优化，提升用户留存和活跃度
2. 设计和优化推荐模型，包括召回、粗排、精排、重排等环节
3. 分析用户行为数据，挖掘用户兴趣，优化推荐策略
4. 跟踪业界最新技术，推动算法创新和落地
5. 与产品、工程团队紧密协作，推动算法效果持续提升

【技术方向】
- 推荐系统：召回、排序、重排
- 深度学习：DNN、Transformer、GNN
- 特征工程：用户画像、物品特征、交叉特征
- 优化目标：CTR、CVR、时长、互动""",
        requirements="""1. 硕士及以上学历，计算机、数学、统计相关专业
2. 2年以上推荐系统或搜索算法经验
3. 扎实的机器学习/深度学习基础
4. 精通 Python，熟悉 PyTorch/TensorFlow
5. 有大规模数据处理经验，熟悉 Spark/SQL
6. 有推荐系统、搜索、广告相关经验优先
7. 有顶会论文发表者优先
8. 优秀的问题分析和解决能力""",
        benefits=["年终奖", "期权", "免费三餐", "租房补贴", "健身房"],
        source="boss", is_active=True
    ),
    Job(
        id="job_bytedance_2", title="产品经理-飞书",
        company_id="comp_bytedance", company_name="字节跳动",
        department="飞书", job_type=JobType.FULL_TIME,
        location="北京", salary_min=25000, salary_max=45000,
        salary_months=15, experience_years=3,
        education="本科",
        skills=["产品设计", "数据分析", "用户研究", "Figma", "SQL", "项目管理"],
        description="""【岗位职责】
1. 负责飞书协作产品的规划和设计，提升企业协作效率
2. 深入了解用户需求，进行用户调研和竞品分析
3. 撰写产品需求文档，协调研发、设计团队推进项目落地
4. 关注产品数据，通过数据分析驱动产品优化
5. 与国际化团队协作，推动产品全球化

【产品方向】
- 文档协作：在线文档、表格、思维导图
- 项目管理：任务、看板、甘特图
- 知识库：企业 wiki、知识管理""",
        requirements="""1. 本科及以上学历
2. 3年以上 B 端产品经验
3. 有 SaaS、企业服务、协作工具相关经验优先
4. 优秀的需求分析和产品设计能力
5. 熟悉数据分析方法，能用数据驱动决策
6. 良好的沟通协调能力和项目管理能力
7. 有国际化产品经验优先
8. 逻辑清晰，执行力强""",
        benefits=["年终奖", "期权", "免费三餐", "租房补贴"],
        source="boss", is_active=True
    ),
    Job(
        id="job_bytedance_3", title="Go 后端工程师-飞书",
        company_id="comp_bytedance", company_name="字节跳动",
        department="飞书", job_type=JobType.FULL_TIME,
        location="北京", salary_min=30000, salary_max=55000,
        salary_months=15, experience_years=2,
        education="本科",
        skills=["Go", "MySQL", "Redis", "微服务", "gRPC", "Kubernetes", "Docker"],
        description="""【岗位职责】
1. 负责飞书后端服务的架构设计和开发
2. 设计高可用、高性能的微服务架构
3. 优化系统性能，提升服务稳定性和可扩展性
4. 参与技术选型和技术方案设计
5. 与前端、产品团队协作，高质量交付项目

【技术栈】
- 语言：Go
- 框架：自研 RPC 框架、gRPC
- 数据库：MySQL、Redis、TiDB
- 中间件：Kafka、RocketMQ
- 基础设施：Kubernetes、Docker""",
        requirements="""1. 本科及以上学历，计算机相关专业
2. 2年以上 Go 后端开发经验
3. 精通 Go 语言，熟悉其并发编程模型
4. 熟悉 MySQL、Redis 等数据库
5. 了解微服务架构，有分布式系统经验
6. 熟悉 Linux 系统和常用调试工具
7. 有即时通讯(IM)系统经验优先
8. 有开源项目贡献经验优先""",
        benefits=["年终奖", "期权", "免费三餐", "租房补贴"],
        source="boss", is_active=True
    ),

    # ============================================================
    # 阿里巴巴岗位
    # ============================================================
    Job(
        id="job_alibaba_1", title="Java 开发工程师-电商",
        company_id="comp_alibaba", company_name="阿里巴巴",
        department="淘天集团", job_type=JobType.FULL_TIME,
        location="杭州", salary_min=25000, salary_max=45000,
        salary_months=16, experience_years=2,
        education="本科",
        skills=["Java", "Spring Boot", "MySQL", "Redis", "分布式", "高并发"],
        description="""【岗位职责】
1. 负责淘宝核心交易系统的开发和维护
2. 参与双11等大促活动的技术保障
3. 设计高并发、高可用的系统架构
4. 优化系统性能，提升用户体验
5. 参与技术方案评审和代码审查

【技术挑战】
- 支撑亿级用户的日常交易
- 双11 期间百万级 QPS 的系统保障
- 分布式事务的一致性保障""",
        requirements="""1. 本科及以上学历，计算机相关专业
2. 2年以上 Java 开发经验
3. 精通 Java 和 Spring Boot 框架
4. 熟悉 MySQL、Redis、消息队列
5. 有高并发系统开发经验
6. 了解分布式系统原理
7. 有电商系统经验优先
8. 良好的学习能力和抗压能力""",
        benefits=["年终奖", "股票", "五险一金", "弹性工作"],
        source="boss", is_active=True
    ),
    Job(
        id="job_alibaba_2", title="前端技术专家-钉钉",
        company_id="comp_alibaba", company_name="阿里巴巴",
        department="钉钉", job_type=JobType.FULL_TIME,
        location="杭州", salary_min=35000, salary_max=55000,
        salary_months=16, experience_years=5,
        education="本科",
        skills=["React", "TypeScript", "Node.js", "微前端", "Webpack", "性能优化"],
        description="""【岗位职责】
1. 负责钉钉 Web 端的架构设计和技术演进
2. 主导前端工程化体系建设，提升研发效率
3. 解决复杂业务场景下的技术难题
4. 负责前端团队的技术培训和代码审查
5. 跟踪前沿技术，推动技术创新

【技术挑战】
- 支撑千万级企业用户的协作需求
- 复杂表单和编辑器的技术实现
- 跨平台（Web、桌面端、移动端）的统一架构""",
        requirements="""1. 本科及以上学历，计算机相关专业
2. 5年以上前端开发经验
3. 精通 React 和 TypeScript
4. 有大型前端项目架构经验
5. 熟悉前端工程化和性能优化
6. 有微前端、Monorepo 等经验优先
7. 有团队管理经验优先
8. 有开源项目或技术博客者优先""",
        benefits=["年终奖", "股票", "五险一金", "弹性工作"],
        source="boss", is_active=True
    ),

    # ============================================================
    # 美团岗位
    # ============================================================
    Job(
        id="job_meituan_1", title="后端工程师-配送",
        company_id="comp_meituan", company_name="美团",
        department="配送事业部", job_type=JobType.FULL_TIME,
        location="北京", salary_min=25000, salary_max=40000,
        salary_months=15, experience_years=2,
        education="本科",
        skills=["Java", "Spring Boot", "MySQL", "Redis", "MQ", "微服务"],
        description="""【岗位职责】
1. 负责美团配送系统的后端开发
2. 设计和优化配送调度算法的工程实现
3. 保障高峰期系统的稳定性和性能
4. 参与系统架构升级和技术改造
5. 与算法、产品团队紧密协作

【技术挑战】
- 日均千万级订单的配送系统
- 实时调度算法的工程化
- 高并发场景下的系统稳定性""",
        requirements="""1. 本科及以上学历，计算机相关专业
2. 2年以上 Java 后端开发经验
3. 熟悉 Spring Boot 和微服务架构
4. 熟悉 MySQL、Redis、消息队列
5. 有高并发系统开发经验
6. 有物流、调度系统经验优先
7. 良好的问题分析和解决能力
8. 良好的团队协作精神""",
        benefits=["年终奖", "股票", "五险一金", "免费三餐"],
        source="boss", is_active=True
    ),

    # ============================================================
    # 小米岗位
    # ============================================================
    Job(
        id="job_xiaomi_1", title="嵌入式工程师-IoT",
        company_id="comp_xiaomi", company_name="小米",
        department="IoT 平台部", job_type=JobType.FULL_TIME,
        location="北京", salary_min=20000, salary_max=35000,
        salary_months=14, experience_years=3,
        education="本科",
        skills=["C", "C++", "嵌入式Linux", "RTOS", "WiFi", "蓝牙", "MQTT"],
        description="""【岗位职责】
1. 负责小米 IoT 设备的嵌入式软件开发
2. 设计和实现设备端通信协议
3. 优化设备功耗和性能
4. 参与 IoT 平台协议标准的制定
5. 与硬件、云端团队协作，完成产品落地

【技术方向】
- 设备端：嵌入式 Linux、RTOS
- 通信：WiFi、蓝牙、Zigbee
- 协议：MQTT、CoAP、HTTP""",
        requirements="""1. 本科及以上学历，电子、通信、计算机相关专业
2. 3年以上嵌入式开发经验
3. 精通 C/C++ 语言
4. 熟悉嵌入式 Linux 或 RTOS
5. 了解 WiFi、蓝牙等无线通信协议
6. 有 IoT 设备开发经验优先
7. 有通信协议设计经验优先
8. 良好的动手能力和问题排查能力""",
        benefits=["年终奖", "股票", "五险一金", "员工折扣"],
        source="boss", is_active=True
    ),

    # ============================================================
    # 拼多多岗位
    # ============================================================
    Job(
        id="job_pinduoduo_1", title="Java 高级工程师-营销",
        company_id="comp_pingduoduo", company_name="拼多多",
        department="营销平台", job_type=JobType.FULL_TIME,
        location="上海", salary_min=30000, salary_max=50000,
        salary_months=16, experience_years=3,
        education="本科",
        skills=["Java", "Spring Boot", "MySQL", "Redis", "分布式", "高并发", "Kafka"],
        description="""【岗位职责】
1. 负责拼多多营销平台的架构设计和开发
2. 设计高并发的营销活动系统，支撑百亿级补贴活动
3. 优化系统性能，保障大促期间系统稳定
4. 设计分布式锁、分布式事务等技术方案
5. 与业务团队紧密协作，快速响应业务需求

【技术挑战】
- 百亿补贴等高并发营销活动
- 优惠券、红包等复杂业务逻辑
- 秒杀场景下的库存一致性""",
        requirements="""1. 本科及以上学历，计算机相关专业
2. 3年以上 Java 开发经验
3. 精通 Java 和 Spring Boot
4. 熟悉高并发、分布式系统设计
5. 熟悉 MySQL、Redis、Kafka
6. 有电商、营销系统经验优先
7. 有大流量系统经验优先
8. 能适应快节奏工作环境""",
        benefits=["年终奖", "期权", "五险一金"],
        source="boss", is_active=True
    ),

    # ============================================================
    # 商汤科技岗位
    # ============================================================
    Job(
        id="job_sensetime_1", title="计算机视觉算法工程师",
        company_id="comp_sensetime", company_name="商汤科技",
        department="研究院", job_type=JobType.FULL_TIME,
        location="北京", salary_min=35000, salary_max=55000,
        salary_months=14, experience_years=2,
        education="硕士",
        skills=["Python", "PyTorch", "计算机视觉", "深度学习", "C++", "CUDA"],
        description="""【岗位职责】
1. 负责计算机视觉算法的研究和开发
2. 跟踪前沿技术，推动算法创新
3. 将算法落地到实际产品中
4. 优化算法性能，提升推理速度
5. 撰写技术文档和专利

【研究方向】
- 目标检测与分割
- 人脸识别与活体检测
- 视频理解与分析
- 3D 视觉""",
        requirements="""1. 硕士及以上学历，计算机、人工智能相关专业
2. 2年以上计算机视觉算法经验
3. 扎实的深度学习基础
4. 精通 Python 和 PyTorch
5. 有顶会论文发表者优先
6. 有 C++/CUDA 工程化经验优先
7. 有大规模数据处理经验优先
8. 优秀的研究能力和创新思维""",
        benefits=["年终奖", "期权", "五险一金", "弹性工作"],
        source="boss", is_active=True
    ),

    # ============================================================
    # 小红书岗位
    # ============================================================
    Job(
        id="job_xiaohongshu_1", title="内容推荐算法工程师",
        company_id="comp_xiaohongshu", company_name="小红书",
        department="推荐技术", job_type=JobType.FULL_TIME,
        location="上海", salary_min=30000, salary_max=50000,
        salary_months=15, experience_years=2,
        education="硕士",
        skills=["Python", "PyTorch", "推荐系统", "Spark", "SQL", "特征工程"],
        description="""【岗位职责】
1. 负责小红书内容推荐系统的算法优化
2. 优化笔记召回和排序策略
3. 挖掘用户兴趣，提升推荐精准度
4. 分析推荐效果，持续迭代优化
5. 与产品团队协作，提升用户体验

【技术挑战】
- 图文、视频等多模态内容理解
- 新用户冷启动问题
- 推荐多样性和时效性平衡""",
        requirements="""1. 硕士及以上学历，计算机相关专业
2. 2年以上推荐系统经验
3. 扎实的机器学习基础
4. 精通 Python 和 PyTorch
5. 熟悉 Spark/SQL 数据处理
6. 有内容推荐经验优先
7. 有 NLP/CV 相关经验优先
8. 良好的数据分析能力""",
        benefits=["年终奖", "期权", "免费三餐", "弹性工作"],
        source="boss", is_active=True
    ),

    # ============================================================
    # 创业公司岗位
    # ============================================================
    Job(
        id="job_startup_1", title="全栈工程师",
        company_id="comp_startup_a", company_name="某创业公司A",
        job_type=JobType.FULL_TIME,
        location="北京", salary_min=20000, salary_max=30000,
        salary_months=13, experience_years=2,
        education="本科",
        skills=["React", "Node.js", "TypeScript", "MongoDB", "Docker", "AWS"],
        description="""【岗位职责】
1. 负责公司 SaaS 产品的全栈开发
2. 参与产品需求讨论和技术方案设计
3. 开发前端页面和后端 API
4. 部署和维护云端服务
5. 快速迭代，响应业务需求变化

【技术栈】
- 前端：React、TypeScript、Tailwind CSS
- 后端：Node.js、Express、MongoDB
- 部署：Docker、AWS""",
        requirements="""1. 本科及以上学历，计算机相关专业
2. 2年以上全栈开发经验
3. 熟悉 React 和 Node.js
4. 了解 MongoDB 或其他 NoSQL 数据库
5. 有 SaaS 产品开发经验优先
6. 能独立完成从设计到上线的全流程
7. 有创业公司工作经验优先
8. 自驱力强，能适应快节奏""",
        benefits=["期权", "弹性工作", "扁平管理"],
        source="boss", is_active=True
    ),

    # ============================================================
    # 黑心公司岗位 (避坑示例)
    # ============================================================
    Job(
        id="job_bad_1", title="全栈开发工程师",
        company_id="comp_blacklist_a", company_name="黑心公司A",
        job_type=JobType.FULL_TIME,
        location="深圳", salary_min=8000, salary_max=15000,
        salary_months=12, experience_years=1,
        education="大专",
        skills=["JavaScript", "PHP", "MySQL", "HTML", "CSS"],
        description="""【岗位职责】
1. 负责公司官网和后台管理系统的开发
2. 根据需求完成页面设计和功能开发
3. 维护现有系统，修复 bug
4. 能接受加班，抗压能力强

【任职要求】
1. 大专及以上学历
2. 1年以上 Web 开发经验
3. 熟悉 JavaScript、PHP、MySQL
4. 能接受加班和出差""",
        requirements="大专学历，1年经验，能接受加班",
        source="拉勾", is_active=True
    ),
]


# ============================================================
# Sample Reviews
# ============================================================

REVIEWS = [
    # 腾讯评价
    Review(
        id="rev_tencent_1", company_id="comp_tencent",
        overall_rating=4.0, salary_rating=4.5,
        work_life_rating=3.5, management_rating=4.0,
        title="大厂光环，薪资不错",
        pros="薪资福利好，平台大，能学到东西，技术氛围好",
        cons="加班较多，部分组内卷严重，晋升困难",
        reviewer_title="高级工程师", reviewer_tenure="3年",
        source="脉脉", posted_at=datetime(2025, 6, 1)
    ),
    Review(
        id="rev_tencent_2", company_id="comp_tencent",
        overall_rating=3.5, salary_rating=4.0,
        work_life_rating=3.0, management_rating=3.5,
        title="看组，有的组很卷",
        pros="福利好，年终奖丰厚，同事优秀",
        cons="部分组996，晋升困难，流程繁琐",
        reviewer_title="产品经理", reviewer_tenure="2年",
        source="脉脉", posted_at=datetime(2025, 5, 15)
    ),
    
    # 字节评价
    Review(
        id="rev_bytedance_1", company_id="comp_bytedance",
        overall_rating=4.0, salary_rating=5.0,
        work_life_rating=2.5, management_rating=3.5,
        title="钱多但是真的累",
        pros="薪资业界顶尖，免费三餐，成长快，同事优秀",
        cons="大小周，工作强度大，压力大，节奏快",
        reviewer_title="算法工程师", reviewer_tenure="1年",
        source="脉脉", posted_at=datetime(2025, 5, 20),
        pitfall_tags=["996", "内卷"]
    ),
    Review(
        id="rev_bytedance_2", company_id="comp_bytedance",
        overall_rating=3.5, salary_rating=4.5,
        work_life_rating=2.0, management_rating=3.0,
        title="高薪但牺牲生活",
        pros="薪资高，福利好，能接触到大规模系统",
        cons="加班严重，没有个人生活，管理混乱",
        reviewer_title="后端工程师", reviewer_tenure="2年",
        source="脉脉", posted_at=datetime(2025, 4, 10),
        pitfall_tags=["996", "内卷"]
    ),
    
    # 阿里评价
    Review(
        id="rev_alibaba_1", company_id="comp_alibaba",
        overall_rating=3.5, salary_rating=4.0,
        work_life_rating=3.0, management_rating=3.5,
        title="老牌大厂，体系完善",
        pros="平台大，体系完善，能学到东西",
        cons="办公室政治，晋升靠关系，P序列压力大",
        reviewer_title="技术专家", reviewer_tenure="5年",
        source="脉脉", posted_at=datetime(2025, 5, 1)
    ),
    
    # 美团评价
    Review(
        id="rev_meituan_1", company_id="comp_meituan",
        overall_rating=3.5, salary_rating=3.5,
        work_life_rating=3.5, management_rating=3.5,
        title="中规中矩，适合稳定",
        pros="业务稳定，工作节奏适中，福利还行",
        cons="薪资涨幅有限，技术深度不够",
        reviewer_title="后端工程师", reviewer_tenure="2年",
        source="脉脉", posted_at=datetime(2025, 4, 15)
    ),
    
    # 拼多多评价
    Review(
        id="rev_pinduoduo_1", company_id="comp_pingduoduo",
        overall_rating=3.0, salary_rating=4.5,
        work_life_rating=2.0, management_rating=2.5,
        title="钱多但非常累",
        pros="薪资很高，年终奖丰厚",
        cons="强制加班，管理严苛，没有个人时间",
        reviewer_title="Java 工程师", reviewer_tenure="1年",
        source="脉脉", posted_at=datetime(2025, 3, 20),
        pitfall_tags=["996", "内卷"]
    ),
    
    # 黑心公司评价
    Review(
        id="rev_bad_1", company_id="comp_blacklist_a",
        overall_rating=1.0, salary_rating=1.0,
        work_life_rating=1.0, management_rating=1.0,
        title="千万别来，欠薪三个月",
        pros="没有优点",
        cons="老板PUA，欠薪，996，不交社保，管理混乱",
        reviewer_title="开发工程师", reviewer_tenure="6个月",
        source="脉脉", posted_at=datetime(2025, 4, 1),
        pitfall_tags=["欠薪", "PUA", "996", "不交社保"]
    ),
    Review(
        id="rev_bad_2", company_id="comp_blacklist_a",
        overall_rating=1.5, salary_rating=1.0,
        work_life_rating=1.0, management_rating=1.0,
        title="黑心公司，避坑",
        pros="没有任何优点",
        cons="拖欠工资，老板天天画饼，加班没有加班费，罚款名目多",
        reviewer_title="运营", reviewer_tenure="3个月",
        source="脉脉", posted_at=datetime(2025, 3, 15),
        pitfall_tags=["欠薪", "PUA", "画饼"]
    ),
]


# ============================================================
# Sample Pitfalls
# ============================================================

PITFALLS = [
    Pitfall(
        id="pit_bad_1", company_id="comp_blacklist_a",
        pitfall_type="欠薪", severity=5,
        description="多次被员工举报拖欠工资，最长拖欠3个月",
        evidence="脉脉多条评价，劳动仲裁记录",
        report_count=15, confirmed_count=10,
        source="脉脉", is_verified=True
    ),
    Pitfall(
        id="pit_bad_2", company_id="comp_blacklist_a",
        pitfall_type="PUA", severity=4,
        description="老板经常PUA员工，贬低工作成果，否定员工价值",
        evidence="多名员工匿名举报",
        report_count=8, confirmed_count=5,
        source="脉脉", is_verified=True
    ),
    Pitfall(
        id="pit_bad_3", company_id="comp_blacklist_a",
        pitfall_type="996", severity=4,
        description="强制996，没有加班费，迟到罚款",
        evidence="员工评价",
        report_count=12, confirmed_count=8,
        source="脉脉", is_verified=True
    ),
]


# ============================================================
# Import Function
# ============================================================

def import_data():
    """Import all sample data."""
    logger.info("=" * 60)
    logger.info("Importing Sample Job Data")
    logger.info("=" * 60)

    # Import companies
    logger.info(f"Importing {len(COMPANIES)} companies...")
    for company in COMPANIES:
        try:
            job_manager.create_company(company)
            logger.info(f"  ✓ {company.name}")
        except Exception as e:
            logger.error(f"  ✗ Failed to import company {company.name}: {e}")

    # Import jobs
    logger.info(f"Importing {len(JOBS)} jobs...")
    for job in JOBS:
        try:
            job_manager.create_job(job)
            logger.info(f"  ✓ {job.company_name} - {job.title}")
        except Exception as e:
            logger.error(f"  ✗ Failed to import job {job.title}: {e}")

    # Import reviews
    logger.info(f"Importing {len(REVIEWS)} reviews...")
    for review in REVIEWS:
        try:
            job_manager.create_review(review)
            logger.info(f"  ✓ {review.company_id} - {review.title}")
        except Exception as e:
            logger.error(f"  ✗ Failed to import review: {e}")

    # Import pitfalls
    logger.info(f"Importing {len(PITFALLS)} pitfalls...")
    for pitfall in PITFALLS:
        try:
            job_manager.create_pitfall(pitfall)
            logger.info(f"  ✓ {pitfall.company_id} - {pitfall.pitfall_type}")
        except Exception as e:
            logger.error(f"  ✗ Failed to import pitfall: {e}")

    # Print statistics
    stats = job_manager.get_stats()
    logger.info("\n" + "=" * 60)
    logger.info("Import Complete!")
    logger.info("=" * 60)
    logger.info(f"Companies: {stats.get('companies', 0)}")
    logger.info(f"Jobs: {stats.get('jobs', 0)}")
    logger.info(f"Reviews: {stats.get('reviews', 0)}")
    logger.info(f"Pitfalls: {stats.get('pitfalls', 0)}")
    logger.info("=" * 60)


if __name__ == "__main__":
    import_data()
