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
        logging.FileHandler("logs/it_service_demo.log", mode='a'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("IT_Service_Demo_Generator")

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

# IT服务III行业模型
# 主行业
it_service = {"name": "IT服务III", "description": "IT服务第三代行业，包括云服务、软件开发、IT咨询等"}

# 上游行业
upstream_industries = [
    {"name": "基础软件", "description": "操作系统、数据库、中间件等基础软件行业"},
    {"name": "硬件设备", "description": "服务器、存储设备、网络设备等硬件设备行业"},
    {"name": "云基础设施", "description": "云计算基础设施服务行业"},
    {"name": "网络服务", "description": "网络通信服务行业"},
    {"name": "安全服务", "description": "网络安全、数据安全等安全服务行业"}
]

# 下游行业
downstream_industries = [
    {"name": "金融科技", "description": "金融行业信息技术应用行业"},
    {"name": "智慧医疗", "description": "医疗行业信息技术应用行业"},
    {"name": "智慧零售", "description": "零售行业信息技术应用行业"},
    {"name": "智能制造", "description": "制造业信息技术应用行业"},
    {"name": "智慧政务", "description": "政务信息技术应用行业"}
]

# IT服务III行业公司
it_companies = [
    {"name": "用友网络", "description": "中国领先的企业管理软件提供商", "scale": "大型", "founded_year": 1988},
    {"name": "东软集团", "description": "中国领先的IT服务提供商", "scale": "大型", "founded_year": 1991},
    {"name": "中科软", "description": "中国知名的软件开发与IT服务提供商", "scale": "中型", "founded_year": 1996},
    {"name": "浪潮软件", "description": "中国领先的软件和信息技术服务提供商", "scale": "大型", "founded_year": 1994},
    {"name": "华宇软件", "description": "中国领先的行业应用软件开发商", "scale": "中型", "founded_year": 2001},
    {"name": "赛意信息", "description": "专注企业数字化转型的IT咨询服务商", "scale": "中型", "founded_year": 2005},
    {"name": "天玑科技", "description": "专注于IT基础设施第三方服务的提供商", "scale": "中型", "founded_year": 2000},
    {"name": "博彦科技", "description": "全球性的IT专业服务及外包服务提供商", "scale": "中型", "founded_year": 1995},
    {"name": "润和软件", "description": "专业的软件开发和IT服务提供商", "scale": "中型", "founded_year": 2006},
    {"name": "信雅达", "description": "专注于金融科技的IT服务提供商", "scale": "中型", "founded_year": 1996}
]

# 上游行业公司
upstream_companies = [
    {"name": "金蝶国际", "description": "中国领先的企业管理软件提供商", "industry": "基础软件"},
    {"name": "金山软件", "description": "中国知名的办公软件提供商", "industry": "基础软件"},
    {"name": "浪潮信息", "description": "中国领先的服务器供应商", "industry": "硬件设备"},
    {"name": "曙光信息", "description": "中国领先的高性能计算机供应商", "industry": "硬件设备"},
    {"name": "阿里云", "description": "中国领先的云计算服务提供商", "industry": "云基础设施"},
    {"name": "腾讯云", "description": "中国领先的云计算服务提供商", "industry": "云基础设施"},
    {"name": "华为云", "description": "中国领先的云计算服务提供商", "industry": "云基础设施"},
    {"name": "中国电信", "description": "中国领先的通信服务提供商", "industry": "网络服务"},
    {"name": "中国移动", "description": "中国领先的通信服务提供商", "industry": "网络服务"},
    {"name": "奇安信", "description": "中国领先的网络安全服务提供商", "industry": "安全服务"},
    {"name": "启明星辰", "description": "中国领先的网络安全服务提供商", "industry": "安全服务"}
]

# 下游行业公司
downstream_companies = [
    {"name": "平安科技", "description": "中国领先的金融科技服务提供商", "industry": "金融科技"},
    {"name": "微众银行", "description": "中国领先的互联网银行", "industry": "金融科技"},
    {"name": "阿里健康", "description": "中国领先的互联网医疗服务提供商", "industry": "智慧医疗"},
    {"name": "平安好医生", "description": "中国领先的互联网医疗服务提供商", "industry": "智慧医疗"},
    {"name": "阿里巴巴", "description": "中国领先的电子商务平台", "industry": "智慧零售"},
    {"name": "京东", "description": "中国领先的电子商务平台", "industry": "智慧零售"},
    {"name": "海尔集团", "description": "中国领先的智能家电制造商", "industry": "智能制造"},
    {"name": "美的集团", "description": "中国领先的智能家电制造商", "industry": "智能制造"},
    {"name": "阿里政务", "description": "中国领先的政务信息化解决方案提供商", "industry": "智慧政务"},
    {"name": "腾讯政务", "description": "中国领先的政务信息化解决方案提供商", "industry": "智慧政务"}
]

# IT服务III行业产品
it_products = [
    {"name": "企业ERP系统", "description": "企业资源规划系统", "company": "用友网络"},
    {"name": "医疗信息系统", "description": "医疗机构信息管理系统", "company": "东软集团"},
    {"name": "政务信息系统", "description": "政府部门信息管理系统", "company": "中科软"},
    {"name": "财务管理软件", "description": "企业财务管理软件", "company": "用友网络"},
    {"name": "人力资源系统", "description": "企业人力资源管理系统", "company": "浪潮软件"},
    {"name": "司法信息系统", "description": "司法机构信息管理系统", "company": "华宇软件"},
    {"name": "供应链管理系统", "description": "企业供应链管理系统", "company": "赛意信息"},
    {"name": "数据中心运维", "description": "IT基础设施运维服务", "company": "天玑科技"},
    {"name": "软件测试服务", "description": "软件测试与质量保障服务", "company": "博彦科技"},
    {"name": "企业移动应用", "description": "企业移动应用开发服务", "company": "润和软件"},
    {"name": "金融软件系统", "description": "银行金融软件系统", "company": "信雅达"},
    {"name": "大数据分析平台", "description": "企业大数据分析平台", "company": "用友网络"},
    {"name": "云迁移服务", "description": "企业上云迁移服务", "company": "东软集团"},
    {"name": "智能客服系统", "description": "企业智能客服系统", "company": "中科软"},
    {"name": "IT咨询服务", "description": "企业IT战略咨询服务", "company": "赛意信息"}
]

# 技术关键词
technologies = [
    "云计算", "大数据", "人工智能", "物联网", "区块链", 
    "微服务", "DevOps", "容器化", "低代码", "5G技术",
    "边缘计算", "API管理", "数据可视化", "机器学习", "深度学习",
    "自然语言处理", "计算机视觉", "增强现实", "虚拟现实", "量子计算"
]

# 产品与技术关联
product_tech_relations = [
    {"product": "企业ERP系统", "tech": ["云计算", "大数据", "微服务"]},
    {"product": "医疗信息系统", "tech": ["大数据", "人工智能", "物联网"]},
    {"product": "政务信息系统", "tech": ["云计算", "区块链", "数据可视化"]},
    {"product": "财务管理软件", "tech": ["云计算", "大数据", "低代码"]},
    {"product": "人力资源系统", "tech": ["云计算", "人工智能", "微服务"]},
    {"product": "司法信息系统", "tech": ["区块链", "大数据", "自然语言处理"]},
    {"product": "供应链管理系统", "tech": ["区块链", "物联网", "人工智能"]},
    {"product": "数据中心运维", "tech": ["DevOps", "容器化", "边缘计算"]},
    {"product": "软件测试服务", "tech": ["DevOps", "人工智能", "API管理"]},
    {"product": "企业移动应用", "tech": ["5G技术", "低代码", "边缘计算"]},
    {"product": "金融软件系统", "tech": ["区块链", "人工智能", "大数据"]},
    {"product": "大数据分析平台", "tech": ["大数据", "机器学习", "深度学习"]},
    {"product": "云迁移服务", "tech": ["云计算", "容器化", "微服务"]},
    {"product": "智能客服系统", "tech": ["自然语言处理", "机器学习", "深度学习"]},
    {"product": "IT咨询服务", "tech": ["云计算", "大数据", "人工智能"]}
]

# 企业合作与竞争关系
company_relations = [
    # IT服务企业之间的竞争关系
    {"company1": "用友网络", "company2": "金蝶国际", "relation": "竞争对手", "strength": "强"},
    {"company1": "用友网络", "company2": "浪潮软件", "relation": "竞争对手", "strength": "中"},
    {"company1": "东软集团", "company2": "中科软", "relation": "竞争对手", "strength": "中"},
    {"company1": "中科软", "company2": "华宇软件", "relation": "竞争对手", "strength": "弱"},
    {"company1": "博彦科技", "company2": "润和软件", "relation": "竞争对手", "strength": "中"},
    {"company1": "赛意信息", "company2": "天玑科技", "relation": "竞争对手", "strength": "弱"},
    
    # IT服务企业与上游企业的合作关系
    {"company1": "用友网络", "company2": "阿里云", "relation": "战略合作", "strength": "强"},
    {"company1": "东软集团", "company2": "华为云", "relation": "战略合作", "strength": "强"},
    {"company1": "中科软", "company2": "腾讯云", "relation": "技术合作", "strength": "中"},
    {"company1": "浪潮软件", "company2": "浪潮信息", "relation": "集团关系", "strength": "强"},
    {"company1": "华宇软件", "company2": "奇安信", "relation": "战略合作", "strength": "中"},
    {"company1": "天玑科技", "company2": "曙光信息", "relation": "技术合作", "strength": "中"},
    {"company1": "博彦科技", "company2": "金山软件", "relation": "技术合作", "strength": "弱"},
    
    # IT服务企业与下游企业的合作关系
    {"company1": "用友网络", "company2": "阿里巴巴", "relation": "客户关系", "strength": "强"},
    {"company1": "东软集团", "company2": "平安好医生", "relation": "客户关系", "strength": "强"},
    {"company1": "中科软", "company2": "阿里政务", "relation": "合作伙伴", "strength": "中"},
    {"company1": "浪潮软件", "company2": "微众银行", "relation": "客户关系", "strength": "中"},
    {"company1": "华宇软件", "company2": "腾讯政务", "relation": "合作伙伴", "strength": "中"},
    {"company1": "赛意信息", "company2": "京东", "relation": "客户关系", "strength": "中"},
    {"company1": "润和软件", "company2": "海尔集团", "relation": "客户关系", "strength": "中"},
    {"company1": "信雅达", "company2": "平安科技", "relation": "战略合作", "strength": "强"}
]

# 跨行业关系
cross_industry_relations = [
    {"upstream": "基础软件", "downstream": "IT服务III", "relation": "上游材料"},
    {"upstream": "硬件设备", "downstream": "IT服务III", "relation": "上游材料"},
    {"upstream": "云基础设施", "downstream": "IT服务III", "relation": "上游材料"},
    {"upstream": "网络服务", "downstream": "IT服务III", "relation": "上游材料"},
    {"upstream": "安全服务", "downstream": "IT服务III", "relation": "上游材料"},
    
    {"upstream": "IT服务III", "downstream": "金融科技", "relation": "上游材料"},
    {"upstream": "IT服务III", "downstream": "智慧医疗", "relation": "上游材料"},
    {"upstream": "IT服务III", "downstream": "智慧零售", "relation": "上游材料"},
    {"upstream": "IT服务III", "downstream": "智能制造", "relation": "上游材料"},
    {"upstream": "IT服务III", "downstream": "智慧政务", "relation": "上游材料"}
]

# 创建IT服务III行业示例数据
def create_it_service_data():
    # 清除现有相关数据
    logger.info("清除IT服务III相关数据")
    graph.run("""
    MATCH (n)-[r]-() 
    WHERE n.name IN $names OR n.industry IS NOT NULL AND n.industry IN $industries
    DELETE r
    """, names=["IT服务III"] + [i["name"] for i in upstream_industries + downstream_industries] + 
              [c["name"] for c in it_companies + upstream_companies + downstream_companies] +
              [p["name"] for p in it_products],
         industries=["IT服务III"] + [i["name"] for i in upstream_industries + downstream_industries])
    
    graph.run("""
    MATCH (n) 
    WHERE n.name IN $names OR n.industry IS NOT NULL AND n.industry IN $industries
    DELETE n
    """, names=["IT服务III"] + [i["name"] for i in upstream_industries + downstream_industries] + 
              [c["name"] for c in it_companies + upstream_companies + downstream_companies] +
              [p["name"] for p in it_products],
         industries=["IT服务III"] + [i["name"] for i in upstream_industries + downstream_industries])
    
    # 创建IT服务III行业节点
    logger.info("创建IT服务III行业节点")
    it_node = Node("industry", name=it_service["name"], description=it_service["description"])
    graph.create(it_node)
    
    # 创建上游行业节点
    logger.info("创建上游行业节点")
    for industry in upstream_industries:
        ind_node = Node("industry", name=industry["name"], description=industry["description"])
        graph.create(ind_node)
        # 建立上游关系
        graph.create(Relationship(ind_node, "上游材料", it_node))
    
    # 创建下游行业节点
    logger.info("创建下游行业节点")
    for industry in downstream_industries:
        ind_node = Node("industry", name=industry["name"], description=industry["description"])
        graph.create(ind_node)
        # 建立下游关系
        graph.create(Relationship(it_node, "上游材料", ind_node))
    
    # 创建IT服务III公司节点
    logger.info("创建IT服务III公司节点")
    for company in it_companies:
        comp_node = Node("company", name=company["name"], description=company["description"], 
                         scale=company["scale"], founded_year=company["founded_year"],
                         industry="IT服务III")
        graph.create(comp_node)
        # 建立行业关系
        graph.create(Relationship(comp_node, "属于", it_node))
    
    # 创建上游行业公司节点
    logger.info("创建上游行业公司节点")
    for company in upstream_companies:
        comp_node = Node("company", name=company["name"], description=company["description"], 
                         industry=company["industry"])
        graph.create(comp_node)
        # 建立行业关系
        ind_node = graph.nodes.match("industry", name=company["industry"]).first()
        if ind_node:
            graph.create(Relationship(comp_node, "属于", ind_node))
    
    # 创建下游行业公司节点
    logger.info("创建下游行业公司节点")
    for company in downstream_companies:
        comp_node = Node("company", name=company["name"], description=company["description"], 
                         industry=company["industry"])
        graph.create(comp_node)
        # 建立行业关系
        ind_node = graph.nodes.match("industry", name=company["industry"]).first()
        if ind_node:
            graph.create(Relationship(comp_node, "属于", ind_node))
    
    # 创建IT服务III产品节点
    logger.info("创建IT服务III产品节点")
    for product in it_products:
        prod_node = Node("product", name=product["name"], description=product["description"])
        graph.create(prod_node)
        # 建立公司与产品关系
        comp_node = graph.nodes.match("company", name=product["company"]).first()
        if comp_node:
            graph.create(Relationship(comp_node, "生产", prod_node, 权重="主营"))
    
    # 创建技术节点及与产品的关联
    logger.info("创建技术节点及与产品的关联")
    for tech in technologies:
        tech_node = graph.nodes.match("technology", name=tech).first()
        if not tech_node:
            tech_node = Node("technology", name=tech, description=f"{tech}相关技术")
            graph.create(tech_node)
    
    # 建立产品与技术的关联
    for relation in product_tech_relations:
        prod_node = graph.nodes.match("product", name=relation["product"]).first()
        if prod_node:
            for tech in relation["tech"]:
                tech_node = graph.nodes.match("technology", name=tech).first()
                if tech_node:
                    relation_type = random.choice(["应用", "基于", "使用"])
                    graph.create(Relationship(prod_node, relation_type, tech_node))
    
    # 创建企业间的合作与竞争关系
    logger.info("创建企业间的合作与竞争关系")
    for relation in company_relations:
        comp1_node = graph.nodes.match("company", name=relation["company1"]).first()
        comp2_node = graph.nodes.match("company", name=relation["company2"]).first()
        if comp1_node and comp2_node:
            rel = Relationship(comp1_node, relation["relation"], comp2_node, strength=relation["strength"])
            graph.create(rel)
            # 如果是竞争关系，创建双向关系
            if relation["relation"] == "竞争对手":
                rel = Relationship(comp2_node, relation["relation"], comp1_node, strength=relation["strength"])
                graph.create(rel)
    
    # 统计创建的节点和关系数量
    logger.info("统计创建的节点和关系数量")
    node_count = len(it_companies) + len(upstream_companies) + len(downstream_companies) + \
                 len(it_products) + 1 + len(upstream_industries) + len(downstream_industries) + \
                 len(technologies)
    
    rel_count = len(it_companies) + len(upstream_companies) + len(downstream_companies) + \
                len(it_products) + len(upstream_industries) + len(downstream_industries) + \
                len(product_tech_relations) * 3 + len(company_relations) + len(cross_industry_relations)
    
    logger.info(f"创建完成，共创建{node_count}个节点和{rel_count}条关系")
    return node_count, rel_count

# 主函数
def main():
    print("\nIT服务III行业示例数据生成工具")
    print("===========================")
    print("此工具将为知识图谱创建IT服务III行业的详细示例数据")
    print("包括上下游行业关系、企业竞争关系、企业关联关系和产品技术分析")
    
    confirm = input("\n是否继续？(y/n): ")
    if confirm.lower() == 'y':
        node_count, rel_count = create_it_service_data()
        print(f"\n成功创建IT服务III行业示例数据！")
        print(f"共创建{node_count}个节点和{rel_count}条关系")
        print("\n现在您可以在知识图谱可视化工具中选择'IT服务III'行业进行分析")
    else:
        print("操作已取消")

if __name__ == "__main__":
    main() 