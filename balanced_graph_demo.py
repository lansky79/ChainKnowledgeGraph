#!/usr/bin/env python3
# coding: utf-8
# File: balanced_graph_demo.py
# 创建一个平衡的知识图谱示例，确保每种查询都有结果

from py2neo import Graph
import time

def create_balanced_graph():
    print("开始创建平衡知识图谱示例...")
    
    # 连接Neo4j数据库
    try:
        print("尝试连接Neo4j数据库...")
        g = Graph("bolt://127.0.0.1:7687", auth=("neo4j", "12345678"))
        print("Neo4j数据库连接成功！")
        
        # 清空数据库，确保从干净环境开始
        print("清空现有数据...")
        g.run("MATCH (n) DETACH DELETE n")
        print("数据库已清空，准备构建样本知识图谱...")
        
        # 创建公司节点
        print("创建公司节点...")
        companies = [
            {"name": "华为技术", "code": "HUAWEI", "location": "深圳"},
            {"name": "中芯国际", "code": "SMIC", "location": "上海"},
            {"name": "紫光集团", "code": "UNIS", "location": "北京"},
            {"name": "联想集团", "code": "LENOVO", "location": "北京"},
            {"name": "小米科技", "code": "XIAOMI", "location": "北京"}
        ]
        
        for company in companies:
            g.run(
                "CREATE (c:company {name: $name, code: $code, location: $location})",
                name=company["name"], code=company["code"], location=company["location"]
            )
        
        # 创建行业节点
        print("创建行业节点...")
        industries = [
            {"name": "电子信息", "level": "一级行业"},
            {"name": "半导体", "level": "二级行业"},
            {"name": "集成电路", "level": "三级行业"},
            {"name": "消费电子", "level": "二级行业"},
            {"name": "智能手机", "level": "三级行业"},
            {"name": "计算机设备", "level": "二级行业"}
        ]
        
        for industry in industries:
            g.run(
                "CREATE (i:industry {name: $name, level: $level})",
                name=industry["name"], level=industry["level"]
            )
        
        # 创建产品节点
        print("创建产品节点...")
        products = [
            {"name": "芯片", "category": "半导体"},
            {"name": "CPU", "category": "芯片"},
            {"name": "GPU", "category": "芯片"},
            {"name": "晶圆", "category": "原材料"},
            {"name": "硅片", "category": "原材料"},
            {"name": "智能手机", "category": "终端产品"},
            {"name": "笔记本电脑", "category": "终端产品"},
            {"name": "操作系统", "category": "软件"},
            {"name": "存储器", "category": "芯片"},
            {"name": "显示屏", "category": "组件"}
        ]
        
        for product in products:
            g.run(
                "CREATE (p:product {name: $name, category: $category})",
                name=product["name"], category=product["category"]
            )
        
        # 创建公司-行业关系
        print("创建公司-行业关系...")
        company_industry_rels = [
            {"company": "华为技术", "industry": "电子信息", "rel": "所属行业"},
            {"company": "华为技术", "industry": "智能手机", "rel": "所属行业"},
            {"company": "中芯国际", "industry": "半导体", "rel": "所属行业"},
            {"company": "中芯国际", "industry": "集成电路", "rel": "所属行业"},
            {"company": "紫光集团", "industry": "电子信息", "rel": "所属行业"},
            {"company": "紫光集团", "industry": "半导体", "rel": "所属行业"},
            {"company": "联想集团", "industry": "计算机设备", "rel": "所属行业"},
            {"company": "联想集团", "industry": "消费电子", "rel": "所属行业"},
            {"company": "小米科技", "industry": "智能手机", "rel": "所属行业"},
            {"company": "小米科技", "industry": "消费电子", "rel": "所属行业"}
        ]
        
        for rel in company_industry_rels:
            g.run(
                "MATCH (c:company {name: $company}), (i:industry {name: $industry}) "
                "CREATE (c)-[r:" + rel["rel"] + "]->(i)",
                company=rel["company"], industry=rel["industry"]
            )
        
        # 创建行业-行业关系
        print("创建行业-行业关系...")
        industry_industry_rels = [
            {"from_industry": "半导体", "to_industry": "电子信息", "rel": "上级行业"},
            {"from_industry": "集成电路", "to_industry": "半导体", "rel": "上级行业"},
            {"from_industry": "消费电子", "to_industry": "电子信息", "rel": "上级行业"},
            {"from_industry": "智能手机", "to_industry": "消费电子", "rel": "上级行业"},
            {"from_industry": "计算机设备", "to_industry": "电子信息", "rel": "上级行业"}
        ]
        
        for rel in industry_industry_rels:
            g.run(
                "MATCH (i1:industry {name: $from_industry}), (i2:industry {name: $to_industry}) "
                "CREATE (i1)-[r:" + rel["rel"] + "]->(i2)",
                from_industry=rel["from_industry"], to_industry=rel["to_industry"]
            )
        
        # 创建公司-产品关系（带权重）
        print("创建公司-产品关系...")
        company_product_rels = [
            {"company": "华为技术", "product": "智能手机", "rel": "主营产品", "weight": 0.45},
            {"company": "华为技术", "product": "芯片", "rel": "主营产品", "weight": 0.30},
            {"company": "华为技术", "product": "操作系统", "rel": "主营产品", "weight": 0.25},
            {"company": "中芯国际", "product": "芯片", "rel": "主营产品", "weight": 0.60},
            {"company": "中芯国际", "product": "晶圆", "rel": "主营产品", "weight": 0.40},
            {"company": "紫光集团", "product": "存储器", "rel": "主营产品", "weight": 0.55},
            {"company": "紫光集团", "product": "CPU", "rel": "主营产品", "weight": 0.45},
            {"company": "联想集团", "product": "笔记本电脑", "rel": "主营产品", "weight": 0.70},
            {"company": "联想集团", "product": "显示屏", "rel": "主营产品", "weight": 0.30},
            {"company": "小米科技", "product": "智能手机", "rel": "主营产品", "weight": 0.65},
            {"company": "小米科技", "product": "操作系统", "rel": "主营产品", "weight": 0.35}
        ]
        
        for rel in company_product_rels:
            g.run(
                "MATCH (c:company {name: $company}), (p:product {name: $product}) "
                "CREATE (c)-[r:" + rel["rel"] + " {权重: $weight}]->(p)",
                company=rel["company"], product=rel["product"], weight=str(rel["weight"])
            )
        
        # 创建产品-产品关系（上下游）
        print("创建产品-产品关系...")
        product_product_rels = [
            {"from_product": "硅片", "to_product": "晶圆", "rel": "上游材料"},
            {"from_product": "晶圆", "to_product": "芯片", "rel": "上游材料"},
            {"from_product": "芯片", "to_product": "CPU", "rel": "上游材料"},
            {"from_product": "芯片", "to_product": "GPU", "rel": "上游材料"},
            {"from_product": "芯片", "to_product": "存储器", "rel": "上游材料"},
            {"from_product": "CPU", "to_product": "智能手机", "rel": "上游材料"},
            {"from_product": "CPU", "to_product": "笔记本电脑", "rel": "上游材料"},
            {"from_product": "GPU", "to_product": "智能手机", "rel": "上游材料"},
            {"from_product": "GPU", "to_product": "笔记本电脑", "rel": "上游材料"},
            {"from_product": "存储器", "to_product": "智能手机", "rel": "上游材料"},
            {"from_product": "存储器", "to_product": "笔记本电脑", "rel": "上游材料"},
            {"from_product": "显示屏", "to_product": "智能手机", "rel": "上游材料"},
            {"from_product": "显示屏", "to_product": "笔记本电脑", "rel": "上游材料"},
            {"from_product": "操作系统", "to_product": "智能手机", "rel": "上游材料"},
            {"from_product": "操作系统", "to_product": "笔记本电脑", "rel": "上游材料"}
        ]
        
        for rel in product_product_rels:
            g.run(
                "MATCH (p1:product {name: $from_product}), (p2:product {name: $to_product}) "
                "CREATE (p1)-[r:" + rel["rel"] + "]->(p2)",
                from_product=rel["from_product"], to_product=rel["to_product"]
            )
        
        # 统计信息
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
        print("1. 查看所有节点: MATCH (n) RETURN n")
        print("2. 查看公司及其关系: MATCH (c:company)-[r]->(n) RETURN c, r, n")
        print("3. 查看产品上下游关系: MATCH (p1:product)-[r:上游材料]->(p2:product) RETURN p1, r, p2")
        print("4. 查看行业层级关系: MATCH (i1:industry)-[r:上级行业]->(i2:industry) RETURN i1, r, i2")
        print("5. 查看华为的产业链: MATCH (c:company {name:'华为技术'})-[r1]->(p:product)-[r2:上游材料*]->(p2:product) RETURN c, r1, p, r2, p2")
        print("6. 查看高权重主营产品: MATCH (c:company)-[r:主营产品]->(p:product) WHERE toFloat(r.权重) > 0.5 RETURN c, r, p")
        
        return True
    except Exception as e:
        print(f"创建知识图谱时出错: {e}")
        return False

if __name__ == "__main__":
    start_time = time.time()
    success = create_balanced_graph()
    end_time = time.time()
    
    if success:
        print(f"知识图谱创建完成！耗时: {end_time - start_time:.2f}秒")
        print("请访问 http://127.0.0.1:7474 查看效果")
    else:
        print("知识图谱创建失败，请检查错误信息。") 