"""Import sample people data into the knowledge graph."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from src.graph.people.models import Person, Company, University, WorkExperience, Education
from src.graph.people.manager import people_manager


# ============================================================
# Sample Data - Tech Industry Leaders
# ============================================================

COMPANIES = [
    Company(id="company_tencent", name="腾讯", name_en="Tencent", industry="互联网", headquarters="深圳"),
    Company(id="company_alibaba", name="阿里巴巴", name_en="Alibaba", industry="互联网", headquarters="杭州"),
    Company(id="company_baidu", name="百度", name_en="Baidu", industry="互联网", headquarters="北京"),
    Company(id="company_bytedance", name="字节跳动", name_en="ByteDance", industry="互联网", headquarters="北京"),
    Company(id="company_huawei", name="华为", name_en="Huawei", industry="科技", headquarters="深圳"),
    Company(id="company_xiaomi", name="小米", name_en="Xiaomi", industry="科技", headquarters="北京"),
    Company(id="company_meituan", name="美团", name_en="Meituan", industry="互联网", headquarters="北京"),
    Company(id="company_jd", name="京东", name_en="JD.com", industry="电商", headquarters="北京"),
    Company(id="company_didi", name="滴滴出行", name_en="Didi", industry="出行", headquarters="北京"),
    Company(id="company_pinduoduo", name="拼多多", name_en="Pinduoduo", industry="电商", headquarters="上海"),
]

UNIVERSITIES = [
    University(id="uni_tsinghua", name="清华大学", name_en="Tsinghua University", location="北京", country="中国", ranking=1),
    University(id="uni_pku", name="北京大学", name_en="Peking University", location="北京", country="中国", ranking=2),
    University(id="uni_zju", name="浙江大学", name_en="Zhejiang University", location="杭州", country="中国", ranking=3),
    University(id="uni_sjtu", name="上海交通大学", name_en="Shanghai Jiao Tong University", location="上海", country="中国", ranking=4),
    University(id="uni_fudan", name="复旦大学", name_en="Fudan University", location="上海", country="中国", ranking=5),
    University(id="uni_nju", name="南京大学", name_en="Nanjing University", location="南京", country="中国", ranking=6),
    University(id="uni_ustc", name="中国科学技术大学", name_en="USTC", location="合肥", country="中国", ranking=7),
    University(id="uni_harvard", name="哈佛大学", name_en="Harvard University", location="Cambridge", country="美国", ranking=1),
    University(id="uni_stanford", name="斯坦福大学", name_en="Stanford University", location="Stanford", country="美国", ranking=2),
    University(id="uni_mit", name="麻省理工学院", name_en="MIT", location="Cambridge", country="美国", ranking=3),
]

PERSONS = [
    # 腾讯系
    Person(id="person_mahuateng", name="马化腾", name_en="Pony Ma", gender="男", 
           bio="腾讯公司主要创始人之一，现任腾讯公司董事会主席兼首席执行官"),
    Person(id="person_zhangzhidong", name="张志东", name_en="Tony Zhang", gender="男",
           bio="腾讯公司主要创始人之一，原腾讯公司首席技术官"),
    Person(id="person_liuChiping", name="刘炽平", name_en="Martin Lau", gender="男",
           bio="腾讯公司总裁"),

    # 阿里系
    Person(id="person_jackma", name="马云", name_en="Jack Ma", gender="男",
           bio="阿里巴巴集团主要创始人，曾任阿里巴巴集团董事局主席"),
    Person(id="person_zhangyong", name="张勇", name_en="Daniel Zhang", gender="男",
           bio="阿里巴巴集团前董事会主席兼首席执行官"),
    Person(id="person_caixinyi", name="蔡崇信", name_en="Joe Tsai", gender="男",
           bio="阿里巴巴集团董事会主席"),

    # 百度系
    Person(id="person_liyanhong", name="李彦宏", name_en="Robin Li", gender="男",
           bio="百度创始人、董事长兼首席执行官"),

    # 字节系
    Person(id="person_zhangyiming", name="张一鸣", name_en="Zhang Yiming", gender="男",
           bio="字节跳动创始人"),
    Person(id="person_laboru", name="梁汝波", name_en="Liang Rubo", gender="男",
           bio="字节跳动首席执行官"),

    # 华为系
    Person(id="person_rengfei", name="任正非", name_en="Ren Zhengfei", gender="男",
           bio="华为技术有限公司创始人兼总裁"),
    Person(id="person_mengwanzhou", name="孟晚舟", name_en="Meng Wanzhou", gender="女",
           bio="华为公司副董事长、轮值董事长、首席财务官"),

    # 小米系
    Person(id="person_leijun", name="雷军", name_en="Lei Jun", gender="男",
           bio="小米科技创始人、董事长兼首席执行官"),

    # 美团系
    Person(id="person_wangxing", name="王兴", name_en="Wang Xing", gender="男",
           bio="美团创始人兼首席执行官"),

    # 京东系
    Person(id="person_liuqiangdong", name="刘强东", name_en="Richard Liu", gender="男",
           bio="京东集团创始人、董事局主席"),

    # 滴滴系
    Person(id="person_chengwei", name="程维", name_en="Will Cheng", gender="男",
           bio="滴滴出行创始人兼首席执行官"),

    # 拼多多系
    Person(id="person_huangzheng", name="黄峥", name_en="Colin Huang", gender="男",
           bio="拼多多创始人"),
]

WORK_EXPERIENCES = [
    # 腾讯
    WorkExperience("person_mahuateng", "company_tencent", "创始人、董事会主席兼CEO", "1998", is_current=True),
    WorkExperience("person_zhangzhidong", "company_tencent", "联合创始人、原CTO", "1998", "2014"),
    WorkExperience("person_liuChiping", "company_tencent", "总裁", "2005", is_current=True),

    # 阿里
    WorkExperience("person_jackma", "company_alibaba", "创始人、原董事局主席", "1999", "2019"),
    WorkExperience("person_zhangyong", "company_alibaba", "前董事会主席兼CEO", "2007", "2023"),
    WorkExperience("person_caixinyi", "company_alibaba", "董事会主席", "1999", is_current=True),

    # 百度
    WorkExperience("person_liyanhong", "company_baidu", "创始人、董事长兼CEO", "2000", is_current=True),

    # 字节
    WorkExperience("person_zhangyiming", "company_bytedance", "创始人", "2012", "2021"),
    WorkExperience("person_laboru", "company_bytedance", "CEO", "2012", is_current=True),

    # 华为
    WorkExperience("person_rengfei", "company_huawei", "创始人兼总裁", "1987", is_current=True),
    WorkExperience("person_mengwanzhou", "company_huawei", "副董事长、轮值董事长、CFO", "1993", is_current=True),

    # 小米
    WorkExperience("person_leijun", "company_xiaomi", "创始人、董事长兼CEO", "2010", is_current=True),

    # 美团
    WorkExperience("person_wangxing", "company_meituan", "创始人兼CEO", "2010", is_current=True),

    # 京东
    WorkExperience("person_liuqiangdong", "company_jd", "创始人、董事局主席", "1998", is_current=True),

    # 滴滴
    WorkExperience("person_chengwei", "company_didi", "创始人兼CEO", "2012", is_current=True),

    # 拼多多
    WorkExperience("person_huangzheng", "company_pinduoduo", "创始人", "2015", "2021"),
]

EDUCATIONS = [
    # 马化腾
    Education("person_mahuateng", "uni_sjtu", "本科", "计算机科学"),

    # 张志东
    Education("person_zhangzhidong", "uni_sjtu", "硕士", "计算机科学"),

    # 刘炽平
    Education("person_liuChiping", "uni_mit", "MBA"),

    # 马云
    Education("person_jackma", "uni_zju", "本科", "英语"),

    # 张勇
    Education("person_zhangyong", "uni_fudan", "本科", "金融"),

    # 蔡崇信
    Education("person_caixinyi", "uni_harvard", "法学博士"),

    # 李彦宏
    Education("person_liyanhong", "uni_pku", "本科", "信息管理"),

    # 张一鸣
    Education("person_zhangyiming", "uni_nju", "本科", "软件工程"),

    # 任正非
    Education("person_rengfei", "uni_ustc", "本科", "建筑学"),

    # 雷军
    Education("person_leijun", "uni_wuhan", "本科", "计算机科学"),

    # 王兴
    Education("person_wangxing", "uni_tsinghua", "本科", "电子工程"),

    # 刘强东
    Education("person_liuqiangdong", "uni_pku", "硕士", "社会学"),

    # 程维
    Education("person_chengwei", "uni_bupt", "本科", "通信工程"),

    # 黄峥
    Education("person_huangzheng", "uni_zju", "本科", "计算机科学"),
    Education("person_huangzheng", "uni_wisconsin", "硕士", "计算机科学"),
]


def import_data():
    """Import all sample data."""
    logger.info("=" * 60)
    logger.info("Importing Sample People Data")
    logger.info("=" * 60)

    # Import companies
    logger.info(f"Importing {len(COMPANIES)} companies...")
    for company in COMPANIES:
        try:
            people_manager.create_company(company)
        except Exception as e:
            logger.error(f"Failed to import company {company.name}: {e}")

    # Import universities
    logger.info(f"Importing {len(UNIVERSITIES)} universities...")
    for university in UNIVERSITIES:
        try:
            people_manager.create_university(university)
        except Exception as e:
            logger.error(f"Failed to import university {university.name}: {e}")

    # Import persons
    logger.info(f"Importing {len(PERSONS)} persons...")
    for person in PERSONS:
        try:
            people_manager.create_person(person)
        except Exception as e:
            logger.error(f"Failed to import person {person.name}: {e}")

    # Import work experiences
    logger.info(f"Importing {len(WORK_EXPERIENCES)} work experiences...")
    for exp in WORK_EXPERIENCES:
        try:
            people_manager.add_work_experience(exp)
        except Exception as e:
            logger.error(f"Failed to import work experience: {e}")

    # Import educations
    logger.info(f"Importing {len(EDUCATIONS)} educations...")
    for edu in EDUCATIONS:
        try:
            people_manager.add_education(edu)
        except Exception as e:
            logger.error(f"Failed to import education: {e}")

    # Print statistics
    stats = people_manager.get_stats()
    logger.info("\n" + "=" * 60)
    logger.info("Import Complete!")
    logger.info("=" * 60)
    logger.info(f"Persons: {stats.get('persons', 0)}")
    logger.info(f"Companies: {stats.get('companies', 0)}")
    logger.info(f"Universities: {stats.get('universities', 0)}")
    logger.info(f"Work Relations: {stats.get('work_rels', 0)}")
    logger.info(f"Education Relations: {stats.get('edu_rels', 0)}")
    logger.info("=" * 60)


if __name__ == "__main__":
    import_data()
