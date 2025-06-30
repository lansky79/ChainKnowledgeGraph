#!/usr/bin/env python3
# coding: utf-8
# File: extended_graph_demo.py
# 创建扩展版知识图谱，包含更多节点和关系

from py2neo import Graph
import time

def create_extended_graph():
    print("开始创建扩展版知识图谱...")
    start_time = time.time()
    
    # 连接Neo4j数据库
    try:
        print("尝试连接Neo4j数据库...")
        g = Graph("bolt://127.0.0.1:7687", auth=("neo4j", "12345678"))
        print("Neo4j数据库连接成功！")
        
        # 清空数据库，确保从干净环境开始
        print("清空现有数据...")
        g.run("MATCH (n) DETACH DELETE n")
        print("数据库已清空，准备构建扩展版知识图谱...")
        
        # 创建公司节点 - 扩展到10家公司
        print("创建公司节点...")
        companies = [
            ("华为技术", "HUAWEI", "深圳", "通信设备"),
            ("中芯国际", "SMIC", "上海", "半导体制造"),
            ("联想集团", "LENOVO", "北京", "计算机设备"),
            ("小米科技", "XIAOMI", "北京", "消费电子"),
            ("阿里巴巴", "BABA", "杭州", "互联网服务"),
            ("腾讯控股", "TENCENT", "深圳", "互联网服务"),
            ("京东方", "BOE", "北京", "显示技术"),
            ("比亚迪", "BYD", "深圳", "汽车制造"),
            ("宁德时代", "CATL", "宁德", "电池制造"),
            ("海尔集团", "HAIER", "青岛", "家电制造")
        ]
        
        for name, code, location, industry in companies:
            g.run(
                "CREATE (c:company {name: $name, code: $code, location: $location, industry: $industry})",
                name=name, code=code, location=location, industry=industry
            )
        
        # 创建行业节点 - 扩展到10个行业
        print("创建行业节点...")
        industries = [
            ("电子信息", "一级行业"),
            ("半导体", "二级行业"),
            ("消费电子", "二级行业"),
            ("计算机设备", "二级行业"),
            ("互联网服务", "二级行业"),
            ("显示技术", "三级行业"),
            ("新能源汽车", "二级行业"),
            ("电池技术", "三级行业"),
            ("家电制造", "二级行业"),
            ("通信设备", "二级行业")
        ]
        
        for name, level in industries:
            g.run(
                "CREATE (i:industry {name: $name, level: $level})",
                name=name, level=level
            )
        
        # 创建产品节点 - 扩展到20个产品
        print("创建产品节点...")
        products = [
            ("芯片", "半导体"),
            ("晶圆", "原材料"),
            ("智能手机", "终端产品"),
            ("笔记本电脑", "终端产品"),
            ("显示屏", "组件"),
            ("操作系统", "软件"),
            ("存储器", "组件"),
            ("电池", "组件"),
            ("摄像头", "组件"),
            ("路由器", "网络设备"),
            ("服务器", "计算设备"),
            ("电动汽车", "终端产品"),
            ("冰箱", "家电"),
            ("洗衣机", "家电"),
            ("云服务", "互联网服务"),
            ("电商平台", "互联网服务"),
            ("社交软件", "互联网服务"),
            ("游戏", "软件"),
            ("智能音箱", "智能设备"),
            ("可穿戴设备", "智能设备")
        ]
        
        for name, category in products:
            g.run(
                "CREATE (p:product {name: $name, category: $category})",
                name=name, category=category
            )
        
        print(f"节点创建完成，耗时: {time.time() - start_time:.2f}秒")
        
        # 创建公司-行业关系
        print("创建公司-行业关系...")
        company_industry_rels = [
            ("华为技术", "电子信息"),
            ("华为技术", "通信设备"),
            ("中芯国际", "半导体"),
            ("联想集团", "计算机设备"),
            ("联想集团", "消费电子"),
            ("小米科技", "消费电子"),
            ("小米科技", "智能手机"),
            ("阿里巴巴", "互联网服务"),
            ("腾讯控股", "互联网服务"),
            ("京东方", "显示技术"),
            ("比亚迪", "新能源汽车"),
            ("宁德时代", "电池技术"),
            ("海尔集团", "家电制造")
        ]
        
        for company, industry in company_industry_rels:
            g.run("""
            MATCH (c:company), (i:industry)
            WHERE c.name = $company AND i.name = $industry
            CREATE (c)-[:所属行业]->(i)
            """, company=company, industry=industry)
        
        # 创建行业-行业关系
        print("创建行业-行业关系...")
        industry_industry_rels = [
            ("半导体", "电子信息"),
            ("消费电子", "电子信息"),
            ("计算机设备", "电子信息"),
            ("互联网服务", "电子信息"),
            ("显示技术", "消费电子"),
            ("通信设备", "电子信息"),
            ("新能源汽车", "电子信息"),
            ("电池技术", "新能源汽车"),
            ("家电制造", "消费电子")
        ]
        
        for from_industry, to_industry in industry_industry_rels:
            g.run("""
            MATCH (i1:industry), (i2:industry)
            WHERE i1.name = $from_industry AND i2.name = $to_industry
            CREATE (i1)-[:上级行业]->(i2)
            """, from_industry=from_industry, to_industry=to_industry)
        
        # 创建公司-产品关系
        print("创建公司-产品关系...")
        company_product_rels = [
            ("华为技术", "智能手机", 0.45),
            ("华为技术", "路由器", 0.25),
            ("华为技术", "服务器", 0.20),
            ("华为技术", "操作系统", 0.10),
            ("中芯国际", "芯片", 0.80),
            ("中芯国际", "晶圆", 0.20),
            ("联想集团", "笔记本电脑", 0.60),
            ("联想集团", "服务器", 0.30),
            ("联想集团", "智能手机", 0.10),
            ("小米科技", "智能手机", 0.50),
            ("小米科技", "智能音箱", 0.20),
            ("小米科技", "可穿戴设备", 0.15),
            ("小米科技", "电商平台", 0.15),
            ("阿里巴巴", "电商平台", 0.70),
            ("阿里巴巴", "云服务", 0.30),
            ("腾讯控股", "社交软件", 0.40),
            ("腾讯控股", "游戏", 0.40),
            ("腾讯控股", "云服务", 0.20),
            ("京东方", "显示屏", 0.90),
            ("比亚迪", "电动汽车", 0.80),
            ("比亚迪", "电池", 0.20),
            ("宁德时代", "电池", 0.95),
            ("海尔集团", "冰箱", 0.50),
            ("海尔集团", "洗衣机", 0.40),
            ("海尔集团", "智能家电", 0.10)
        ]
        
        for company, product, weight in company_product_rels:
            g.run("""
            MATCH (c:company), (p:product)
            WHERE c.name = $company AND p.name = $product
            CREATE (c)-[:主营产品 {权重: $weight}]->(p)
            """, company=company, product=product, weight=str(weight))
        
        # 创建产品-产品关系
        print("创建产品-产品关系...")
        product_product_rels = [
            ("晶圆", "芯片"),
            ("芯片", "智能手机"),
            ("芯片", "笔记本电脑"),
            ("芯片", "服务器"),
            ("芯片", "路由器"),
            ("芯片", "智能音箱"),
            ("显示屏", "智能手机"),
            ("显示屏", "笔记本电脑"),
            ("显示屏", "电视机"),
            ("电池", "智能手机"),
            ("电池", "笔记本电脑"),
            ("电池", "电动汽车"),
            ("电池", "可穿戴设备"),
            ("摄像头", "智能手机"),
            ("摄像头", "笔记本电脑"),
            ("操作系统", "智能手机"),
            ("操作系统", "笔记本电脑"),
            ("操作系统", "服务器"),
            ("存储器", "智能手机"),
            ("存储器", "笔记本电脑"),
            ("存储器", "服务器")
        ]
        
        for from_product, to_product in product_product_rels:
            g.run("""
            MATCH (p1:product), (p2:product)
            WHERE p1.name = $from_product AND p2.name = $to_product
            CREATE (p1)-[:上游材料]->(p2)
            """, from_product=from_product, to_product=to_product)
        
        print(f"关系创建完成，耗时: {time.time() - start_time:.2f}秒")
        
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
        print("5. 查看完整产业链: MATCH path = (c:company)-[r1:主营产品]->(p:product)-[r2:上游材料*1..3]->(p2:product) RETURN path LIMIT 10")
        print("6. 查看高权重主营产品: MATCH (c:company)-[r:主营产品]->(p:product) WHERE toFloat(r.权重) > 0.5 RETURN c, r, p")
        print("7. 查看特定公司的产业链: MATCH path = (c:company {name:'华为技术'})-[r1:主营产品]->(p:product)-[r2:上游材料*]->(p2:product) RETURN path")
        print("8. 查看特定行业的公司: MATCH (c:company)-[:所属行业]->(i:industry {name:'消费电子'}) RETURN c, i")
        
        end_time = time.time()
        total_time = end_time - start_time
        print(f"\n知识图谱构建完成！总耗时: {total_time:.2f}秒")
        
        return True
    except Exception as e:
        print(f"创建知识图谱时出错: {e}")
        return False

if __name__ == "__main__":
    create_extended_graph()
    print("请访问 http://127.0.0.1:7474 查看效果") 