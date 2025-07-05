import os
import sys
from py2neo import Graph, Node, Relationship
import logging
import json
import random

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/demo_data.log", mode='a'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("Demo_Data_Generator")

# 加载Neo4j配置
def load_config():
    try:
        config_file = 'config_windows.json' if os.path.exists('config_windows.json') else 'config.json'
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
        return {
            "neo4j": {
                "uri": "bolt://127.0.0.1:7687",
                "username": "neo4j",
                "password": "12345678"
            }
        }

config = load_config()

# 连接Neo4j
try:
    graph = Graph(
        config["neo4j"]["uri"],
        auth=(config["neo4j"]["username"], config["neo4j"]["password"])
    )
    logger.info("Neo4j连接成功")
except Exception as e:
    logger.error(f"Neo4j连接失败: {e}")
    sys.exit(1)

# 清空数据库
def clear_database():
    logger.info("清空数据库")
    graph.run("MATCH (n) DETACH DELETE n")

# 行业数据
industries = [
    # 电子信息产业链
    {"name": "集成电路", "description": "集成电路设计与制造行业"},
    {"name": "电子元件", "description": "电子元器件制造行业"},
    {"name": "消费电子", "description": "消费电子产品行业"},
    {"name": "通信设备", "description": "通信设备制造行业"},
    {"name": "计算机设备", "description": "计算机及外围设备制造行业"},
    
    # 医药健康产业链
    {"name": "医药原料", "description": "医药原料生产行业"},
    {"name": "医药制造", "description": "医药制剂生产行业"},
    {"name": "医疗器械", "description": "医疗器械研发制造行业"},
    {"name": "医疗服务", "description": "医疗服务提供行业"},
    {"name": "生物技术", "description": "生物技术研发应用行业"},
    
    # 汽车产业链
    {"name": "汽车零部件", "description": "汽车零部件制造行业"},
    {"name": "整车制造", "description": "汽车整车制造行业"},
    {"name": "新能源汽车", "description": "新能源汽车制造行业"},
    {"name": "智能驾驶", "description": "智能驾驶技术行业"},
    {"name": "汽车服务", "description": "汽车后市场服务行业"},
    
    # 互联网产业链
    {"name": "互联网服务", "description": "互联网服务提供行业"},
    {"name": "电子商务", "description": "电子商务平台行业"},
    {"name": "互联网金融", "description": "互联网金融服务行业"},
    {"name": "社交媒体", "description": "社交媒体平台行业"},
    {"name": "云计算", "description": "云计算服务提供行业"}
]

# 公司数据
companies = [
    # 集成电路行业
    {"name": "中芯国际", "description": "中国领先的集成电路制造商", "industry": "集成电路"},
    {"name": "长电科技", "description": "中国领先的集成电路封测企业", "industry": "集成电路"},
    {"name": "华虹半导体", "description": "中国知名的集成电路制造商", "industry": "集成电路"},
    {"name": "紫光展锐", "description": "中国领先的集成电路设计企业", "industry": "集成电路"},
    {"name": "兆易创新", "description": "中国领先的存储器设计企业", "industry": "集成电路"},
    
    # 电子元件行业
    {"name": "歌尔股份", "description": "中国领先的电子元器件制造商", "industry": "电子元件"},
    {"name": "立讯精密", "description": "中国领先的电子连接器制造商", "industry": "电子元件"},
    {"name": "蓝思科技", "description": "中国领先的玻璃面板制造商", "industry": "电子元件"},
    {"name": "鹏鼎控股", "description": "中国领先的PCB制造商", "industry": "电子元件"},
    {"name": "顺络电子", "description": "中国领先的电子元器件制造商", "industry": "电子元件"},
    
    # 消费电子行业
    {"name": "小米集团", "description": "中国领先的智能手机制造商", "industry": "消费电子"},
    {"name": "OPPO", "description": "中国领先的智能手机制造商", "industry": "消费电子"},
    {"name": "vivo", "description": "中国领先的智能手机制造商", "industry": "消费电子"},
    {"name": "TCL科技", "description": "中国领先的电视制造商", "industry": "消费电子"},
    {"name": "海信视像", "description": "中国领先的电视制造商", "industry": "消费电子"},
    
    # 医药制造行业
    {"name": "恒瑞医药", "description": "中国领先的创新药研发企业", "industry": "医药制造"},
    {"name": "复星医药", "description": "中国领先的医药制造企业", "industry": "医药制造"},
    {"name": "云南白药", "description": "中国知名的中药制造企业", "industry": "医药制造"},
    {"name": "同仁堂", "description": "中国著名的中药制造企业", "industry": "医药制造"},
    {"name": "石药集团", "description": "中国领先的制药企业", "industry": "医药制造"},
    
    # 医疗器械行业
    {"name": "迈瑞医疗", "description": "中国领先的医疗器械制造商", "industry": "医疗器械"},
    {"name": "万东医疗", "description": "中国知名的医学影像设备制造商", "industry": "医疗器械"},
    {"name": "乐普医疗", "description": "中国领先的心血管医疗器械制造商", "industry": "医疗器械"},
    {"name": "安图生物", "description": "中国领先的体外诊断产品提供商", "industry": "医疗器械"},
    {"name": "鱼跃医疗", "description": "中国领先的家用医疗器械制造商", "industry": "医疗器械"},
    
    # 互联网服务行业
    {"name": "阿里巴巴", "description": "中国领先的电子商务公司", "industry": "互联网服务"},
    {"name": "腾讯", "description": "中国领先的互联网服务提供商", "industry": "互联网服务"},
    {"name": "百度", "description": "中国领先的搜索引擎公司", "industry": "互联网服务"},
    {"name": "京东", "description": "中国领先的电子商务平台", "industry": "电子商务"},
    {"name": "拼多多", "description": "中国领先的社交电商平台", "industry": "电子商务"},
    
    # 新能源汽车行业
    {"name": "比亚迪", "description": "中国领先的新能源汽车制造商", "industry": "新能源汽车"},
    {"name": "蔚来汽车", "description": "中国知名的高端电动车制造商", "industry": "新能源汽车"},
    {"name": "小鹏汽车", "description": "中国知名的智能电动车制造商", "industry": "新能源汽车"},
    {"name": "理想汽车", "description": "中国知名的增程式电动车制造商", "industry": "新能源汽车"},
    {"name": "宁德时代", "description": "中国领先的动力电池制造商", "industry": "新能源汽车"},
]

# 产品数据
products = [
    # 集成电路行业产品
    {"name": "CPU芯片", "description": "中央处理器芯片", "company": "中芯国际"},
    {"name": "存储芯片", "description": "存储器芯片", "company": "兆易创新"},
    {"name": "功率芯片", "description": "功率控制芯片", "company": "华虹半导体"},
    {"name": "射频芯片", "description": "无线通信射频芯片", "company": "紫光展锐"},
    {"name": "传感器芯片", "description": "传感器数据处理芯片", "company": "长电科技"},
    
    # 电子元件行业产品
    {"name": "PCB电路板", "description": "印刷电路板", "company": "鹏鼎控股"},
    {"name": "连接器", "description": "电子连接器", "company": "立讯精密"},
    {"name": "电阻", "description": "电阻元件", "company": "顺络电子"},
    {"name": "电容", "description": "电容元件", "company": "顺络电子"},
    {"name": "声学元件", "description": "声学传感器和扬声器", "company": "歌尔股份"},
    
    # 消费电子行业产品
    {"name": "智能手机", "description": "智能手机设备", "company": "小米集团"},
    {"name": "智能电视", "description": "联网智能电视", "company": "TCL科技"},
    {"name": "智能手表", "description": "智能穿戴手表", "company": "小米集团"},
    {"name": "无线耳机", "description": "无线蓝牙耳机", "company": "OPPO"},
    {"name": "平板电脑", "description": "便携平板电脑", "company": "vivo"},
    
    # 医药制造行业产品
    {"name": "抗肿瘤药", "description": "治疗癌症的药物", "company": "恒瑞医药"},
    {"name": "心血管药", "description": "治疗心血管疾病的药物", "company": "石药集团"},
    {"name": "抗生素", "description": "抗菌类药物", "company": "复星医药"},
    {"name": "中成药", "description": "传统中药制剂", "company": "同仁堂"},
    {"name": "止痛药", "description": "止痛消炎类药物", "company": "云南白药"},
    
    # 医疗器械行业产品
    {"name": "CT设备", "description": "计算机断层扫描设备", "company": "万东医疗"},
    {"name": "监护仪", "description": "病人生命体征监护仪", "company": "迈瑞医疗"},
    {"name": "血糖仪", "description": "血糖监测设备", "company": "鱼跃医疗"},
    {"name": "心脏支架", "description": "心血管支架", "company": "乐普医疗"},
    {"name": "检测试剂", "description": "体外诊断试剂", "company": "安图生物"},
    
    # 互联网服务行业产品
    {"name": "电商平台", "description": "电子商务交易平台", "company": "阿里巴巴"},
    {"name": "社交软件", "description": "社交通讯软件", "company": "腾讯"},
    {"name": "搜索引擎", "description": "互联网搜索服务", "company": "百度"},
    {"name": "直播平台", "description": "在线直播服务平台", "company": "腾讯"},
    {"name": "支付服务", "description": "电子支付服务", "company": "阿里巴巴"},
    
    # 新能源汽车行业产品
    {"name": "电动轿车", "description": "纯电动乘用车", "company": "比亚迪"},
    {"name": "电动SUV", "description": "纯电动运动型多用途车", "company": "蔚来汽车"},
    {"name": "混合动力车", "description": "混合动力汽车", "company": "比亚迪"},
    {"name": "动力电池", "description": "汽车动力电池", "company": "宁德时代"},
    {"name": "自动驾驶系统", "description": "汽车自动驾驶系统", "company": "小鹏汽车"},
]

# 行业上下游关系
industry_relations = [
    # 电子信息产业链上下游
    {"upstream": "集成电路", "downstream": "电子元件", "relation": "上游材料"},
    {"upstream": "电子元件", "downstream": "消费电子", "relation": "上游材料"},
    {"upstream": "电子元件", "downstream": "通信设备", "relation": "上游材料"},
    {"upstream": "集成电路", "downstream": "计算机设备", "relation": "上游材料"},
    {"upstream": "集成电路", "downstream": "通信设备", "relation": "上游材料"},
    
    # 医药健康产业链上下游
    {"upstream": "医药原料", "downstream": "医药制造", "relation": "上游材料"},
    {"upstream": "医药制造", "downstream": "医疗服务", "relation": "上游材料"},
    {"upstream": "医疗器械", "downstream": "医疗服务", "relation": "上游材料"},
    {"upstream": "生物技术", "downstream": "医药制造", "relation": "上游材料"},
    {"upstream": "生物技术", "downstream": "医疗器械", "relation": "上游材料"},
    
    # 汽车产业链上下游
    {"upstream": "汽车零部件", "downstream": "整车制造", "relation": "上游材料"},
    {"upstream": "汽车零部件", "downstream": "新能源汽车", "relation": "上游材料"},
    {"upstream": "智能驾驶", "downstream": "新能源汽车", "relation": "上游材料"},
    {"upstream": "整车制造", "downstream": "汽车服务", "relation": "上游材料"},
    {"upstream": "新能源汽车", "downstream": "汽车服务", "relation": "上游材料"},
    
    # 互联网产业链上下游
    {"upstream": "云计算", "downstream": "互联网服务", "relation": "上游材料"},
    {"upstream": "互联网服务", "downstream": "电子商务", "relation": "上游材料"},
    {"upstream": "互联网服务", "downstream": "社交媒体", "relation": "上游材料"},
    {"upstream": "互联网服务", "downstream": "互联网金融", "relation": "上游材料"},
    {"upstream": "电子商务", "downstream": "互联网金融", "relation": "上游材料"},
]

# 产品关联关系
product_relations = [
    # 产品之间的关联关系
    {"source": "CPU芯片", "target": "智能手机", "relation": "上游材料"},
    {"source": "存储芯片", "target": "智能手机", "relation": "上游材料"},
    {"source": "PCB电路板", "target": "智能手机", "relation": "上游材料"},
    {"source": "连接器", "target": "智能手机", "relation": "上游材料"},
    {"source": "射频芯片", "target": "智能手机", "relation": "上游材料"},
    
    {"source": "CPU芯片", "target": "智能电视", "relation": "上游材料"},
    {"source": "存储芯片", "target": "智能电视", "relation": "上游材料"},
    {"source": "PCB电路板", "target": "智能电视", "relation": "上游材料"},
    
    {"source": "动力电池", "target": "电动轿车", "relation": "上游材料"},
    {"source": "动力电池", "target": "电动SUV", "relation": "上游材料"},
    {"source": "自动驾驶系统", "target": "电动轿车", "relation": "配套系统"},
    {"source": "自动驾驶系统", "target": "电动SUV", "relation": "配套系统"},
    
    {"source": "检测试剂", "target": "CT设备", "relation": "配套产品"},
    {"source": "监护仪", "target": "CT设备", "relation": "配套设备"},
    {"source": "抗肿瘤药", "target": "CT设备", "relation": "配套药物"},
]

# 创建节点和关系
def create_data():
    # 创建行业节点
    logger.info("创建行业节点")
    for industry in industries:
        industry_node = Node("industry", name=industry["name"], description=industry["description"])
        graph.create(industry_node)
    
    # 创建公司节点并与行业建立关系
    logger.info("创建公司节点")
    for company in companies:
        company_node = Node("company", name=company["name"], description=company["description"])
        graph.create(company_node)
        
        # 公司与行业的关系
        industry_node = graph.nodes.match("industry", name=company["industry"]).first()
        if industry_node:
            graph.create(Relationship(company_node, "属于", industry_node))
    
    # 创建产品节点并与公司建立关系
    logger.info("创建产品节点")
    for product in products:
        product_node = Node("product", name=product["name"], description=product["description"])
        graph.create(product_node)
        
        # 产品与公司的关系
        company_node = graph.nodes.match("company", name=product["company"]).first()
        if company_node:
            graph.create(Relationship(company_node, "生产", product_node, 权重="主营"))
    
    # 创建行业上下游关系
    logger.info("创建行业上下游关系")
    for relation in industry_relations:
        upstream_node = graph.nodes.match("industry", name=relation["upstream"]).first()
        downstream_node = graph.nodes.match("industry", name=relation["downstream"]).first()
        if upstream_node and downstream_node:
            graph.create(Relationship(upstream_node, relation["relation"], downstream_node))
    
    # 创建产品关联关系
    logger.info("创建产品关联关系")
    for relation in product_relations:
        source_node = graph.nodes.match("product", name=relation["source"]).first()
        target_node = graph.nodes.match("product", name=relation["target"]).first()
        if source_node and target_node:
            graph.create(Relationship(source_node, relation["relation"], target_node))
    
    # 添加一些随机的竞争关系
    logger.info("创建竞争关系")
    # 同行业公司之间添加竞争关系
    for industry in industries:
        companies_in_industry = [c for c in companies if c["industry"] == industry["name"]]
        if len(companies_in_industry) > 1:
            for i in range(len(companies_in_industry)):
                for j in range(i+1, len(companies_in_industry)):
                    if random.random() < 0.7:  # 70%的概率建立竞争关系
                        company1 = graph.nodes.match("company", name=companies_in_industry[i]["name"]).first()
                        company2 = graph.nodes.match("company", name=companies_in_industry[j]["name"]).first()
                        if company1 and company2:
                            graph.create(Relationship(company1, "竞争对手", company2))
                            graph.create(Relationship(company2, "竞争对手", company1))
    
    # 添加一些合作关系
    logger.info("创建合作关系")
    for _ in range(20):  # 创建20个随机合作关系
        company1 = random.choice(companies)
        company2 = random.choice(companies)
        if company1["name"] != company2["name"]:
            c1_node = graph.nodes.match("company", name=company1["name"]).first()
            c2_node = graph.nodes.match("company", name=company2["name"]).first()
            if c1_node and c2_node:
                relation_type = random.choice(["合作伙伴", "战略合作", "技术合作", "供应商"])
                graph.create(Relationship(c1_node, relation_type, c2_node))

# 添加一些产品技术关联关系
def create_tech_relations():
    logger.info("创建产品技术关联关系")
    
    # 技术关键词
    technologies = [
        "5G技术", "人工智能", "大数据", "云计算", "物联网", 
        "区块链", "虚拟现实", "增强现实", "量子计算", "边缘计算",
        "生物识别", "神经网络", "机器学习", "深度学习", "自然语言处理"
    ]
    
    # 为每个产品添加1-3个技术关联
    for product in products:
        product_node = graph.nodes.match("product", name=product["name"]).first()
        if product_node:
            # 为每个产品随机选择1-3个技术
            selected_techs = random.sample(technologies, min(3, random.randint(1, 3)))
            for tech in selected_techs:
                # 检查技术节点是否存在，不存在则创建
                tech_node = graph.nodes.match("technology", name=tech).first()
                if not tech_node:
                    tech_node = Node("technology", name=tech, description=f"{tech}相关技术")
                    graph.create(tech_node)
                
                # 创建产品与技术的关联关系
                relation_type = random.choice(["应用", "基于", "使用"])
                graph.create(Relationship(product_node, relation_type, tech_node))

def add_additional_data():
    """在不清空数据库的情况下增加示例数据"""
    logger.info("在现有数据库中增加示例数据")
    
    # 新增行业数据 - 新材料产业链
    new_industries = [
        {"name": "新型材料", "description": "新型材料研发制造行业"},
        {"name": "半导体材料", "description": "半导体材料研发制造行业"},
        {"name": "光电材料", "description": "光电材料研发制造行业"},
        {"name": "新能源材料", "description": "新能源材料研发制造行业"},
        {"name": "高分子材料", "description": "高分子材料研发制造行业"}
    ]
    
    # 新增公司数据
    new_companies = [
        {"name": "中科三环", "description": "中国领先的磁性材料制造商", "industry": "新型材料"},
        {"name": "上海新阳", "description": "中国领先的半导体材料供应商", "industry": "半导体材料"},
        {"name": "三安光电", "description": "中国领先的光电材料供应商", "industry": "光电材料"},
        {"name": "天赐材料", "description": "中国领先的锂电池材料供应商", "industry": "新能源材料"},
        {"name": "万华化学", "description": "中国领先的化工新材料企业", "industry": "高分子材料"}
    ]
    
    # 新增产品数据
    new_products = [
        {"name": "永磁材料", "description": "高性能永磁材料", "company": "中科三环"},
        {"name": "光刻胶", "description": "半导体光刻胶材料", "company": "上海新阳"},
        {"name": "LED芯片", "description": "LED照明芯片", "company": "三安光电"},
        {"name": "电解液", "description": "锂电池电解液", "company": "天赐材料"},
        {"name": "聚氨酯", "description": "高性能聚氨酯材料", "company": "万华化学"}
    ]
    
    # 新增行业上下游关系
    new_industry_relations = [
        {"upstream": "半导体材料", "downstream": "集成电路", "relation": "上游材料"},
        {"upstream": "光电材料", "downstream": "消费电子", "relation": "上游材料"},
        {"upstream": "新能源材料", "downstream": "新能源汽车", "relation": "上游材料"},
        {"upstream": "高分子材料", "downstream": "电子元件", "relation": "上游材料"},
        {"upstream": "新型材料", "downstream": "通信设备", "relation": "上游材料"}
    ]
    
    # 新增产品关联关系
    new_product_relations = [
        {"source": "永磁材料", "target": "电动轿车", "relation": "上游材料"},
        {"source": "光刻胶", "target": "CPU芯片", "relation": "制造材料"},
        {"source": "LED芯片", "target": "智能电视", "relation": "核心组件"},
        {"source": "电解液", "target": "动力电池", "relation": "关键材料"},
        {"source": "聚氨酯", "target": "PCB电路板", "relation": "基础材料"}
    ]
    
    # 创建新增行业节点
    logger.info("创建新增行业节点")
    for industry in new_industries:
        # 检查节点是否已存在
        existing = graph.nodes.match("industry", name=industry["name"]).first()
        if not existing:
            industry_node = Node("industry", name=industry["name"], description=industry["description"])
            graph.create(industry_node)
    
    # 创建新增公司节点并与行业建立关系
    logger.info("创建新增公司节点")
    for company in new_companies:
        # 检查节点是否已存在
        existing = graph.nodes.match("company", name=company["name"]).first()
        if not existing:
            company_node = Node("company", name=company["name"], description=company["description"])
            graph.create(company_node)
            
            # 公司与行业的关系
            industry_node = graph.nodes.match("industry", name=company["industry"]).first()
            if industry_node:
                graph.create(Relationship(company_node, "属于", industry_node))
    
    # 创建新增产品节点并与公司建立关系
    logger.info("创建新增产品节点")
    for product in new_products:
        # 检查节点是否已存在
        existing = graph.nodes.match("product", name=product["name"]).first()
        if not existing:
            product_node = Node("product", name=product["name"], description=product["description"])
            graph.create(product_node)
            
            # 产品与公司的关系
            company_node = graph.nodes.match("company", name=product["company"]).first()
            if company_node:
                graph.create(Relationship(company_node, "生产", product_node, 权重="主营"))
    
    # 创建新增行业上下游关系
    logger.info("创建新增行业上下游关系")
    for relation in new_industry_relations:
        upstream_node = graph.nodes.match("industry", name=relation["upstream"]).first()
        downstream_node = graph.nodes.match("industry", name=relation["downstream"]).first()
        if upstream_node and downstream_node:
            # 检查关系是否已存在
            existing_rel = graph.match_one((upstream_node, downstream_node), r_type=relation["relation"])
            if not existing_rel:
                graph.create(Relationship(upstream_node, relation["relation"], downstream_node))
    
    # 创建新增产品关联关系
    logger.info("创建新增产品关联关系")
    for relation in new_product_relations:
        source_node = graph.nodes.match("product", name=relation["source"]).first()
        target_node = graph.nodes.match("product", name=relation["target"]).first()
        if source_node and target_node:
            # 检查关系是否已存在
            existing_rel = graph.match_one((source_node, target_node), r_type=relation["relation"])
            if not existing_rel:
                graph.create(Relationship(source_node, relation["relation"], target_node))
    
    # 添加一些交叉行业合作关系
    logger.info("创建交叉行业合作关系")
    # 寻找不同行业的公司建立合作关系
    company_pairs = []
    for new_company in new_companies:
        # 随机选择2个老公司与新公司建立合作关系
        old_company_selection = random.sample(companies, min(2, len(companies)))
        for old_company in old_company_selection:
            if new_company["industry"] != old_company["industry"]:
                company_pairs.append((new_company["name"], old_company["name"]))
    
    # 创建合作关系
    for company1_name, company2_name in company_pairs:
        c1_node = graph.nodes.match("company", name=company1_name).first()
        c2_node = graph.nodes.match("company", name=company2_name).first()
        if c1_node and c2_node:
            relation_type = random.choice(["合作伙伴", "战略合作", "技术合作", "供应商"])
            # 检查关系是否已存在
            existing_rel = graph.match_one((c1_node, c2_node), r_type=relation_type)
            if not existing_rel:
                graph.create(Relationship(c1_node, relation_type, c2_node))
    
    # 添加技术关联
    logger.info("为新产品创建技术关联")
    # 新增一些技术关键词
    new_technologies = [
        "纳米技术", "石墨烯", "超导材料", "仿生材料", "复合材料", 
        "智能材料", "3D打印", "生物材料", "光电转换", "催化材料"
    ]
    
    # 为每个新产品添加1-3个技术关联
    for product in new_products:
        product_node = graph.nodes.match("product", name=product["name"]).first()
        if product_node:
            # 为每个产品随机选择1-3个技术
            selected_techs = random.sample(new_technologies, min(3, random.randint(1, 3)))
            for tech in selected_techs:
                # 检查技术节点是否存在，不存在则创建
                tech_node = graph.nodes.match("technology", name=tech).first()
                if not tech_node:
                    tech_node = Node("technology", name=tech, description=f"{tech}相关技术")
                    graph.create(tech_node)
                
                # 创建产品与技术的关联关系
                relation_type = random.choice(["应用", "基于", "使用"])
                # 检查关系是否已存在
                existing_rel = graph.match_one((product_node, tech_node), r_type=relation_type)
                if not existing_rel:
                    graph.create(Relationship(product_node, relation_type, tech_node))
    
    logger.info("新增示例数据创建完成")
    return len(new_industries) + len(new_companies) + len(new_products)

# 主函数
def main():
    print("\n知识图谱示例数据生成工具")
    print("=======================")
    print("1. 清空数据库并创建全新的示例数据")
    print("2. 在现有数据库中增加示例数据（不清空现有数据）")
    print("3. 退出")
    
    choice = input("\n请选择操作 [1/2/3]: ")
    
    if choice == "1":
        confirm = input("确认要清空数据库吗？这将删除所有现有数据！(y/n): ")
        if confirm.lower() == 'y':
            clear_database()
            create_data()
            create_tech_relations()
            logger.info("全新示例数据创建完成")
            print("全新示例数据创建完成！")
        else:
            logger.info("清空数据库操作已取消")
            print("操作已取消。")
    
    elif choice == "2":
        print("在不清空数据库的情况下增加新的示例数据...")
        count = add_additional_data()
        print(f"操作完成！成功添加了{count}个新节点及相关关系。")
    
    elif choice == "3":
        print("程序已退出。")
    
    else:
        print("无效的选择，请重新运行程序并选择有效的选项。")

if __name__ == "__main__":
    main() 