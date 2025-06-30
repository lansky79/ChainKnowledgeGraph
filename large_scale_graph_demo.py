#!/usr/bin/env python3
# coding: utf-8
# File: large_scale_graph_demo.py
# 创建大规模知识图谱，包含约4000个节点和5000+关系

from py2neo import Graph, Node, Relationship
import time
import random
import string
import tqdm
import math

# 配置参数
COMPANY_COUNT = 1000  # 公司节点数量
INDUSTRY_COUNT = 500  # 行业节点数量
PRODUCT_COUNT = 2500  # 产品节点数量
BATCH_SIZE = 500      # 批量插入大小

# 行业分类和产品类别
INDUSTRY_CATEGORIES = [
    "电子信息", "新能源", "医疗健康", "金融服务", "消费品", "工业制造", 
    "农业科技", "教育培训", "文化娱乐", "交通物流", "建筑地产", "环保能源",
    "化工材料", "食品饮料", "服装纺织", "旅游酒店", "互联网服务", "软件开发",
    "人工智能", "云计算", "大数据", "区块链", "物联网", "生物技术"
]

INDUSTRY_LEVELS = ["一级行业", "二级行业", "三级行业", "四级行业"]

PRODUCT_CATEGORIES = [
    "原材料", "半成品", "组件", "终端产品", "软件", "服务", "解决方案",
    "智能设备", "网络设备", "计算设备", "存储设备", "显示设备", "输入设备",
    "家电", "汽车零部件", "医疗器械", "工业设备", "农业设备", "办公设备",
    "消费电子", "通信设备", "安防设备", "能源设备", "环保设备"
]

CITIES = [
    "北京", "上海", "深圳", "广州", "杭州", "南京", "成都", "重庆", "武汉", 
    "西安", "苏州", "天津", "郑州", "长沙", "青岛", "宁波", "厦门", "福州", 
    "大连", "沈阳", "济南", "合肥", "昆明", "贵阳", "南宁", "哈尔滨", "长春"
]

def generate_random_code(length=6):
    """生成随机股票代码"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def create_large_scale_graph():
    """创建大规模知识图谱"""
    print("开始创建大规模知识图谱...")
    start_time = time.time()
    
    # 连接Neo4j数据库
    try:
        print("尝试连接Neo4j数据库...")
        g = Graph("bolt://127.0.0.1:7687", auth=("neo4j", "12345678"))
        print("Neo4j数据库连接成功！")
        
        # 清空数据库，确保从干净环境开始
        print("清空现有数据...")
        g.run("MATCH (n) DETACH DELETE n")
        print("数据库已清空，准备构建大规模知识图谱...")
        
        # 生成并批量创建公司节点
        print(f"开始生成{COMPANY_COUNT}个公司节点...")
        companies = []
        for i in range(COMPANY_COUNT):
            industry = random.choice(INDUSTRY_CATEGORIES)
            company_name = f"{industry}科技{i+1}号"
            company = {
                "name": company_name,
                "code": generate_random_code(),
                "location": random.choice(CITIES),
                "industry": industry,
                "size": random.choice(["大型", "中型", "小型", "初创"]),
                "founded": random.randint(1980, 2023)
            }
            companies.append(company)
        
        # 批量创建公司节点
        for i in tqdm.tqdm(range(0, len(companies), BATCH_SIZE), desc="创建公司节点"):
            batch = companies[i:i+BATCH_SIZE]
            query = """
            UNWIND $batch AS company
            CREATE (c:company {
                name: company.name,
                code: company.code,
                location: company.location,
                industry: company.industry,
                size: company.size,
                founded: company.founded
            })
            """
            g.run(query, batch=batch)
        
        # 生成并批量创建行业节点
        print(f"\n开始生成{INDUSTRY_COUNT}个行业节点...")
        industries = []
        
        # 添加主要行业类别作为一级行业
        for category in INDUSTRY_CATEGORIES:
            industry = {
                "name": category,
                "level": "一级行业",
                "description": f"{category}相关的企业和产品",
                "market_size": random.randint(1000, 10000)
            }
            industries.append(industry)
        
        # 生成剩余的行业节点
        remaining_count = INDUSTRY_COUNT - len(industries)
        for i in range(remaining_count):
            parent_industry = random.choice(INDUSTRY_CATEGORIES)
            level = random.choice(INDUSTRY_LEVELS[1:])  # 二级及以下行业
            industry_name = f"{parent_industry}{random.choice(['技术', '服务', '制造', '研发', '应用', '解决方案'])}{i+1}号"
            industry = {
                "name": industry_name,
                "level": level,
                "description": f"{industry_name}相关的企业和产品",
                "market_size": random.randint(100, 5000),
                "parent_industry": parent_industry
            }
            industries.append(industry)
        
        # 批量创建行业节点
        for i in tqdm.tqdm(range(0, len(industries), BATCH_SIZE), desc="创建行业节点"):
            batch = industries[i:i+BATCH_SIZE]
            query = """
            UNWIND $batch AS industry
            CREATE (i:industry {
                name: industry.name,
                level: industry.level,
                description: industry.description,
                market_size: industry.market_size
            })
            """
            g.run(query, batch=batch)
        
        # 生成并批量创建产品节点
        print(f"\n开始生成{PRODUCT_COUNT}个产品节点...")
        products = []
        for i in range(PRODUCT_COUNT):
            category = random.choice(PRODUCT_CATEGORIES)
            related_industry = random.choice(INDUSTRY_CATEGORIES)
            product_name = f"{related_industry}{category}{i+1}号"
            product = {
                "name": product_name,
                "category": category,
                "related_industry": related_industry,
                "price_level": random.choice(["高端", "中端", "低端"]),
                "lifecycle": random.choice(["导入期", "成长期", "成熟期", "衰退期"])
            }
            products.append(product)
        
        # 批量创建产品节点
        for i in tqdm.tqdm(range(0, len(products), BATCH_SIZE), desc="创建产品节点"):
            batch = products[i:i+BATCH_SIZE]
            query = """
            UNWIND $batch AS product
            CREATE (p:product {
                name: product.name,
                category: product.category,
                related_industry: product.related_industry,
                price_level: product.price_level,
                lifecycle: product.lifecycle
            })
            """
            g.run(query, batch=batch)
        
        node_creation_time = time.time() - start_time
        print(f"\n节点创建完成，耗时: {node_creation_time:.2f}秒")
        
        # 创建公司-行业关系
        print("\n开始创建公司-行业关系...")
        # 为每个公司随机关联1-3个行业
        company_industry_rels = []
        for company in tqdm.tqdm(companies, desc="生成公司-行业关系"):
            # 主行业关联
            company_industry_rels.append({
                "company": company["name"],
                "industry": company["industry"]
            })
            
            # 随机关联额外的行业
            extra_industry_count = random.randint(0, 2)
            for _ in range(extra_industry_count):
                industry = random.choice([i["name"] for i in industries])
                if industry != company["industry"]:
                    company_industry_rels.append({
                        "company": company["name"],
                        "industry": industry
                    })
        
        # 批量创建公司-行业关系
        for i in tqdm.tqdm(range(0, len(company_industry_rels), BATCH_SIZE), desc="创建公司-行业关系"):
            batch = company_industry_rels[i:i+BATCH_SIZE]
            query = """
            UNWIND $batch AS rel
            MATCH (c:company {name: rel.company})
            MATCH (i:industry {name: rel.industry})
            CREATE (c)-[:所属行业]->(i)
            """
            g.run(query, batch=batch)
        
        # 创建行业-行业关系
        print("\n开始创建行业-行业关系...")
        industry_industry_rels = []
        
        # 为非一级行业创建上级行业关系
        for industry in tqdm.tqdm([i for i in industries if i["level"] != "一级行业"], desc="生成行业-行业关系"):
            parent = industry.get("parent_industry")
            if parent:
                industry_industry_rels.append({
                    "from_industry": industry["name"],
                    "to_industry": parent
                })
        
        # 批量创建行业-行业关系
        for i in tqdm.tqdm(range(0, len(industry_industry_rels), BATCH_SIZE), desc="创建行业-行业关系"):
            batch = industry_industry_rels[i:i+BATCH_SIZE]
            query = """
            UNWIND $batch AS rel
            MATCH (i1:industry {name: rel.from_industry})
            MATCH (i2:industry {name: rel.to_industry})
            CREATE (i1)-[:上级行业]->(i2)
            """
            g.run(query, batch=batch)
        
        # 创建公司-产品关系
        print("\n开始创建公司-产品关系...")
        company_product_rels = []
        
        # 为每个公司随机关联2-5个产品
        for company in tqdm.tqdm(companies, desc="生成公司-产品关系"):
            # 找出与公司行业相关的产品
            related_products = [p for p in products if p["related_industry"] == company["industry"]]
            
            # 如果没有足够的相关产品，则从所有产品中选择
            if len(related_products) < 5:
                related_products = products
            
            # 随机选择2-5个产品
            product_count = random.randint(2, 5)
            selected_products = random.sample(related_products, min(product_count, len(related_products)))
            
            # 创建关系
            total_weight = 0
            for product in selected_products:
                weight = round(random.uniform(0.1, 0.9), 2)
                total_weight += weight
                company_product_rels.append({
                    "company": company["name"],
                    "product": product["name"],
                    "weight": weight
                })
            
            # 归一化权重，确保总和为1
            if total_weight > 0:
                for rel in company_product_rels[-product_count:]:
                    rel["weight"] = round(rel["weight"] / total_weight, 2)
        
        # 批量创建公司-产品关系
        for i in tqdm.tqdm(range(0, len(company_product_rels), BATCH_SIZE), desc="创建公司-产品关系"):
            batch = company_product_rels[i:i+BATCH_SIZE]
            query = """
            UNWIND $batch AS rel
            MATCH (c:company {name: rel.company})
            MATCH (p:product {name: rel.product})
            CREATE (c)-[:主营产品 {权重: toString(rel.weight)}]->(p)
            """
            g.run(query, batch=batch)
        
        # 创建产品-产品关系
        print("\n开始创建产品-产品上下游关系...")
        product_product_rels = []
        
        # 定义产品类别的上下游关系概率
        upstream_probability = {
            "原材料": 0.0,
            "半成品": 0.7,
            "组件": 0.9,
            "终端产品": 1.0,
            "软件": 0.5,
            "服务": 0.2,
            "解决方案": 0.3,
            "智能设备": 0.8,
            "网络设备": 0.7,
            "计算设备": 0.8,
            "存储设备": 0.7,
            "显示设备": 0.8,
            "输入设备": 0.7,
            "家电": 0.9,
            "汽车零部件": 0.8,
            "医疗器械": 0.7,
            "工业设备": 0.8,
            "农业设备": 0.8,
            "办公设备": 0.8,
            "消费电子": 0.9,
            "通信设备": 0.8,
            "安防设备": 0.8,
            "能源设备": 0.7,
            "环保设备": 0.7
        }
        
        # 为每个产品随机创建0-3个上游产品
        for product in tqdm.tqdm(products, desc="生成产品-产品关系"):
            # 根据产品类别决定是否需要上游产品
            if random.random() < upstream_probability.get(product["category"], 0.5):
                # 随机选择0-3个上游产品
                upstream_count = random.randint(0, 3)
                potential_upstream = [p for p in products if p != product]
                selected_upstream = random.sample(potential_upstream, min(upstream_count, len(potential_upstream)))
                
                for upstream_product in selected_upstream:
                    product_product_rels.append({
                        "from_product": upstream_product["name"],
                        "to_product": product["name"]
                    })
        
        # 批量创建产品-产品关系
        for i in tqdm.tqdm(range(0, len(product_product_rels), BATCH_SIZE), desc="创建产品-产品关系"):
            batch = product_product_rels[i:i+BATCH_SIZE]
            query = """
            UNWIND $batch AS rel
            MATCH (p1:product {name: rel.from_product})
            MATCH (p2:product {name: rel.to_product})
            CREATE (p1)-[:上游材料]->(p2)
            """
            g.run(query, batch=batch)
        
        rel_creation_time = time.time() - start_time - node_creation_time
        print(f"\n关系创建完成，耗时: {rel_creation_time:.2f}秒")
        
        # 统计信息
        print("\n计算统计信息...")
        node_count = g.run("MATCH (n) RETURN count(n) as count").data()[0]['count']
        rel_count = g.run("MATCH ()-[r]->() RETURN count(r) as count").data()[0]['count']
        company_count = g.run("MATCH (n:company) RETURN count(n) as count").data()[0]['count']
        product_count = g.run("MATCH (n:product) RETURN count(n) as count").data()[0]['count']
        industry_count = g.run("MATCH (n:industry) RETURN count(n) as count").data()[0]['count']
        
        print("\n=== 知识图谱统计信息 ===")
        print(f"总节点数: {node_count}")
        print(f"总关系数: {rel_count}")
        print(f"公司节点数: {company_count}")
        print(f"产品节点数: {product_count}")
        print(f"行业节点数: {industry_count}")
        print("=========================\n")
        
        # 提供示例查询
        print("您可以在Neo4j浏览器中使用以下查询语句查看图谱:")
        print("1. 查看所有节点(限制返回50个): MATCH (n) RETURN n LIMIT 50")
        print("2. 查看公司及其关系(限制返回20个): MATCH (c:company)-[r]->(n) RETURN c, r, n LIMIT 20")
        print("3. 查看产品上下游关系(限制返回20个): MATCH (p1:product)-[r:上游材料]->(p2:product) RETURN p1, r, p2 LIMIT 20")
        print("4. 查看行业层级关系(限制返回20个): MATCH (i1:industry)-[r:上级行业]->(i2:industry) RETURN i1, r, i2 LIMIT 20")
        print("5. 查看完整产业链(限制返回10个): MATCH path = (c:company)-[r1:主营产品]->(p:product)-[r2:上游材料*1..3]->(p2:product) RETURN path LIMIT 10")
        print("6. 查看高权重主营产品(限制返回20个): MATCH (c:company)-[r:主营产品]->(p:product) WHERE toFloat(r.权重) > 0.5 RETURN c, r, p LIMIT 20")
        print("7. 查看特定行业的公司(限制返回20个): MATCH (c:company)-[:所属行业]->(i:industry {name:'电子信息'}) RETURN c, i LIMIT 20")
        print("8. 查看特定城市的公司分布: MATCH (c:company) RETURN c.location as city, count(c) as company_count ORDER BY company_count DESC LIMIT 10")
        print("9. 查看产品类别分布: MATCH (p:product) RETURN p.category as category, count(p) as product_count ORDER BY product_count DESC LIMIT 10")
        
        end_time = time.time()
        total_time = end_time - start_time
        print(f"\n大规模知识图谱构建完成！总耗时: {total_time:.2f}秒")
        
        return True
    except Exception as e:
        print(f"创建知识图谱时出错: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    create_large_scale_graph()
    print("请访问 http://127.0.0.1:7474 查看效果")
    print("注意：由于数据量较大，可视化时请使用LIMIT限制返回结果数量") 