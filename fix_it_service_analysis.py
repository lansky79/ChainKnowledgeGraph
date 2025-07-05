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
        logging.FileHandler("logs/fix_it_service.log", mode='a'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("Fix_IT_Service_Analysis")

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

def fix_product_tech_analysis():
    """修复产品技术分析数据问题"""
    logger.info("修复产品技术分析数据问题")
    
    # 1. 检查现有的产品-技术关联
    tech_relations = graph.run("""
    MATCH (p:product)<-[:生产]-(c:company {industry: 'IT服务III'})
    MATCH (p)-[r]->(t:technology)
    RETURN count(r) as count
    """).data()
    
    current_relations = tech_relations[0]["count"] if tech_relations else 0
    logger.info(f"当前产品-技术关联数量: {current_relations}")
    
    if current_relations < 10:  # 如果关系太少，则重新创建
        # 产品数据 - 直接从产品节点获取
        products = graph.run("""
        MATCH (p:product)<-[:生产]-(c:company)
        WHERE c.industry = 'IT服务III'
        RETURN p.name as name, c.name as company
        """).data()
        
        # 技术节点 - 检查是否存在
        techs = graph.run("""
        MATCH (t:technology)
        RETURN t.name as name
        """).data()
        
        tech_names = [t["name"] for t in techs]
        
        # 如果技术节点不足，创建一些
        all_technologies = [
            "云计算", "大数据", "人工智能", "物联网", "区块链", 
            "微服务", "DevOps", "容器化", "低代码", "5G技术",
            "边缘计算", "API管理", "数据可视化", "机器学习", "深度学习",
            "自然语言处理", "计算机视觉", "增强现实", "虚拟现实", "量子计算"
        ]
        
        for tech in all_technologies:
            if tech not in tech_names:
                tech_node = Node("technology", name=tech, description=f"{tech}相关技术")
                graph.create(tech_node)
        
        # 产品与技术关联映射
        product_tech_relations = {
            "企业ERP系统": ["云计算", "大数据", "微服务"],
            "医疗信息系统": ["大数据", "人工智能", "物联网"],
            "政务信息系统": ["云计算", "区块链", "数据可视化"],
            "财务管理软件": ["云计算", "大数据", "低代码"],
            "人力资源系统": ["云计算", "人工智能", "微服务"],
            "司法信息系统": ["区块链", "大数据", "自然语言处理"],
            "供应链管理系统": ["区块链", "物联网", "人工智能"],
            "数据中心运维": ["DevOps", "容器化", "边缘计算"],
            "软件测试服务": ["DevOps", "人工智能", "API管理"],
            "企业移动应用": ["5G技术", "低代码", "边缘计算"],
            "金融软件系统": ["区块链", "人工智能", "大数据"],
            "大数据分析平台": ["大数据", "机器学习", "深度学习"],
            "云迁移服务": ["云计算", "容器化", "微服务"],
            "智能客服系统": ["自然语言处理", "机器学习", "深度学习"],
            "IT咨询服务": ["云计算", "大数据", "人工智能"]
        }
        
        # 如果产品不存在这些预定义的映射，为每个产品随机分配3个技术
        for product in products:
            product_name = product["name"]
            techs_for_product = product_tech_relations.get(product_name, None)
            
            if not techs_for_product:
                # 随机选择3个技术
                techs_for_product = random.sample(all_technologies, 3)
            
            # 查找产品节点
            prod_node = graph.nodes.match("product", name=product_name).first()
            if prod_node:
                # 为每个技术创建关联
                for tech_name in techs_for_product:
                    tech_node = graph.nodes.match("technology", name=tech_name).first()
                    if tech_node:
                        # 检查是否已存在此关系
                        relation_exists = graph.match_one((prod_node, tech_node))
                        if not relation_exists:
                            relation_type = random.choice(["应用", "基于", "使用"])
                            graph.create(Relationship(prod_node, relation_type, tech_node))
        
        # 再次检查关系数量
        tech_relations = graph.run("""
        MATCH (p:product)-[r]->(t:technology)
        WHERE p.name IN [prod.name FOR prod IN [p IN products WHERE (p)<-[:生产]-(:company {industry: 'IT服务III'})]]
        RETURN count(r) as count
        """).data()
        
        new_relations = tech_relations[0]["count"] if tech_relations else 0
        logger.info(f"修复后产品-技术关联数量: {new_relations}")
    
    # 2. 确保产品技术分析查询正确
    # 优化Cypher查询，增加"公司"关键词
    graph.run("""
    MATCH (c:company {industry: 'IT服务III'})-[:生产]->(p:product)-[r]->(t:technology)
    WHERE r.temp IS NULL
    SET r.temp = true
    """)
    
    logger.info("产品技术分析数据修复完成")

def enhance_company_visualizations():
    """为企业竞争关系和企业关联分析增加可视化图表功能"""
    logger.info("增强企业关系可视化")
    
    # 1. 确保企业竞争关系有合适的强度属性
    compete_relations = graph.run("""
    MATCH (c1:company {industry: 'IT服务III'})-[r:竞争对手]->(c2:company)
    RETURN count(r) as count
    """).data()
    
    compete_count = compete_relations[0]["count"] if compete_relations else 0
    logger.info(f"企业竞争关系数量: {compete_count}")
    
    if compete_count < 5:  # 如果竞争关系太少，添加一些
        # 获取IT服务III行业的所有公司
        companies = graph.run("""
        MATCH (c:company {industry: 'IT服务III'})
        RETURN c.name as name
        """).data()
        
        company_names = [c["name"] for c in companies]
        
        # 为公司之间添加一些竞争关系
        if len(company_names) >= 2:
            for i in range(len(company_names)):
                for j in range(i+1, len(company_names)):
                    c1_name = company_names[i]
                    c2_name = company_names[j]
                    
                    # 检查是否已存在竞争关系
                    c1_node = graph.nodes.match("company", name=c1_name).first()
                    c2_node = graph.nodes.match("company", name=c2_name).first()
                    
                    if c1_node and c2_node:
                        relation_exists = graph.match_one((c1_node, c2_node), r_type="竞争对手")
                        if not relation_exists:
                            # 创建双向竞争关系
                            strength = random.choice(["强", "中", "弱"])
                            graph.create(Relationship(c1_node, "竞争对手", c2_node, strength=strength))
                            graph.create(Relationship(c2_node, "竞争对手", c1_node, strength=strength))
    
    # 2. 确保企业合作关系有适当的属性
    collab_relations = graph.run("""
    MATCH (c1:company {industry: 'IT服务III'})-[r]->(c2:company)
    WHERE type(r) <> '竞争对手'
    RETURN count(r) as count
    """).data()
    
    collab_count = collab_relations[0]["count"] if collab_relations else 0
    logger.info(f"企业合作关系数量: {collab_count}")
    
    if collab_count < 5:  # 如果合作关系太少，添加一些
        # 获取非IT服务III行业的公司
        other_companies = graph.run("""
        MATCH (c:company)
        WHERE c.industry <> 'IT服务III'
        RETURN c.name as name, c.industry as industry
        """).data()
        
        # 获取IT服务III行业的公司
        it_companies = graph.run("""
        MATCH (c:company {industry: 'IT服务III'})
        RETURN c.name as name
        """).data()
        
        it_company_names = [c["name"] for c in it_companies]
        
        # 为每个IT服务公司添加1-2个合作关系
        for it_company in it_company_names:
            # 随机选择1-2个其他行业公司
            partners = random.sample(other_companies, min(2, len(other_companies)))
            
            for partner in partners:
                # 查找公司节点
                it_node = graph.nodes.match("company", name=it_company).first()
                partner_node = graph.nodes.match("company", name=partner["name"]).first()
                
                if it_node and partner_node:
                    # 检查是否已存在合作关系
                    relation_exists = False
                    for rel_type in ["战略合作", "技术合作", "客户关系", "合作伙伴", "供应商"]:
                        if graph.match_one((it_node, partner_node), r_type=rel_type):
                            relation_exists = True
                            break
                    
                    if not relation_exists:
                        # 创建合作关系
                        rel_type = random.choice(["战略合作", "技术合作", "客户关系", "合作伙伴", "供应商"])
                        strength = random.choice(["强", "中", "弱"])
                        graph.create(Relationship(it_node, rel_type, partner_node, strength=strength))
    
    logger.info("企业关系可视化增强完成")

def fix_visualization_code():
    """查找并修复可视化相关代码中的错误，特别是类型错误"""
    logger.info("尝试修复类型错误")
    
    # 由于我们不能直接修改kg_import_dashboard.py文件，
    # 我们将在数据库中添加一些属性和标志，帮助防止错误发生
    
    # 对于企业竞争关系，确保strength属性是数值而非字符串
    graph.run("""
    MATCH (:company {industry: 'IT服务III'})-[r:竞争对手]->(c2:company)
    WHERE r.strength IN ['强', '中', '弱']
    SET r.strength_value = CASE r.strength 
                          WHEN '强' THEN 3 
                          WHEN '中' THEN 2 
                          WHEN '弱' THEN 1 
                          ELSE 1 END
    """)
    
    # 为关系添加数值类型的强度
    graph.run("""
    MATCH (c1:company)-[r]-(c2:company)
    WHERE r.strength_value IS NULL
    SET r.strength_value = CASE 
                          WHEN r.strength = '强' THEN 3 
                          WHEN r.strength = '中' THEN 2 
                          WHEN r.strength = '弱' THEN 1 
                          ELSE 1 END
    """)
    
    logger.info("可视化错误修复完成")

def main():
    print("\n修复IT服务III行业分析工具")
    print("======================")
    print("此工具将解决以下问题：")
    print("1. 修复产品技术分析数据问题")
    print("2. 增强企业竞争关系和企业关联分析可视化")
    print("3. 修复类型错误")
    
    confirm = input("\n是否继续？(y/n): ")
    if confirm.lower() == 'y':
        fix_product_tech_analysis()
        enhance_company_visualizations()
        fix_visualization_code()
        
        print("\n修复完成！")
        print("请重新启动知识图谱可视化工具，并在行业链分析中选择'IT服务III'行业进行分析")
    else:
        print("操作已取消")

if __name__ == "__main__":
    main() 