#!/usr/bin/env python3
# coding: utf-8
# File: quick_graph_demo.py
# 使用高效方式快速构建小型知识图谱，2分钟内完成

from py2neo import Graph
import time

def create_quick_graph():
    print("开始创建快速知识图谱示例...")
    start_time = time.time()
    
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
        g.run("CREATE (c:company {name: '华为技术', code: 'HUAWEI', location: '深圳'})")
        g.run("CREATE (c:company {name: '中芯国际', code: 'SMIC', location: '上海'})")
        g.run("CREATE (c:company {name: '联想集团', code: 'LENOVO', location: '北京'})")
        
        # 创建行业节点
        print("创建行业节点...")
        g.run("CREATE (i:industry {name: '电子信息', level: '一级行业'})")
        g.run("CREATE (i:industry {name: '半导体', level: '二级行业'})")
        g.run("CREATE (i:industry {name: '消费电子', level: '二级行业'})")
        
        # 创建产品节点
        print("创建产品节点...")
        g.run("CREATE (p:product {name: '芯片', category: '半导体'})")
        g.run("CREATE (p:product {name: '晶圆', category: '原材料'})")
        g.run("CREATE (p:product {name: '智能手机', category: '终端产品'})")
        g.run("CREATE (p:product {name: '笔记本电脑', category: '终端产品'})")
        g.run("CREATE (p:product {name: '显示屏', category: '组件'})")
        
        print(f"节点创建完成，耗时: {time.time() - start_time:.2f}秒")
        
        # 创建公司-行业关系
        print("创建公司-行业关系...")
        g.run("""
        MATCH (c:company), (i:industry)
        WHERE c.name = '华为技术' AND i.name = '电子信息'
        CREATE (c)-[:所属行业]->(i)
        """)
        
        g.run("""
        MATCH (c:company), (i:industry)
        WHERE c.name = '中芯国际' AND i.name = '半导体'
        CREATE (c)-[:所属行业]->(i)
        """)
        
        g.run("""
        MATCH (c:company), (i:industry)
        WHERE c.name = '联想集团' AND i.name = '消费电子'
        CREATE (c)-[:所属行业]->(i)
        """)
        
        # 创建行业-行业关系
        print("创建行业-行业关系...")
        g.run("""
        MATCH (i1:industry), (i2:industry)
        WHERE i1.name = '半导体' AND i2.name = '电子信息'
        CREATE (i1)-[:上级行业]->(i2)
        """)
        
        g.run("""
        MATCH (i1:industry), (i2:industry)
        WHERE i1.name = '消费电子' AND i2.name = '电子信息'
        CREATE (i1)-[:上级行业]->(i2)
        """)
        
        # 创建公司-产品关系
        print("创建公司-产品关系...")
        g.run("""
        MATCH (c:company), (p:product)
        WHERE c.name = '华为技术' AND p.name = '智能手机'
        CREATE (c)-[:主营产品 {权重: '0.65'}]->(p)
        """)
        
        g.run("""
        MATCH (c:company), (p:product)
        WHERE c.name = '中芯国际' AND p.name = '芯片'
        CREATE (c)-[:主营产品 {权重: '0.80'}]->(p)
        """)
        
        g.run("""
        MATCH (c:company), (p:product)
        WHERE c.name = '中芯国际' AND p.name = '晶圆'
        CREATE (c)-[:主营产品 {权重: '0.20'}]->(p)
        """)
        
        g.run("""
        MATCH (c:company), (p:product)
        WHERE c.name = '联想集团' AND p.name = '笔记本电脑'
        CREATE (c)-[:主营产品 {权重: '0.75'}]->(p)
        """)
        
        # 创建产品-产品关系
        print("创建产品-产品关系...")
        g.run("""
        MATCH (p1:product), (p2:product)
        WHERE p1.name = '晶圆' AND p2.name = '芯片'
        CREATE (p1)-[:上游材料]->(p2)
        """)
        
        g.run("""
        MATCH (p1:product), (p2:product)
        WHERE p1.name = '芯片' AND p2.name = '智能手机'
        CREATE (p1)-[:上游材料]->(p2)
        """)
        
        g.run("""
        MATCH (p1:product), (p2:product)
        WHERE p1.name = '芯片' AND p2.name = '笔记本电脑'
        CREATE (p1)-[:上游材料]->(p2)
        """)
        
        g.run("""
        MATCH (p1:product), (p2:product)
        WHERE p1.name = '显示屏' AND p2.name = '智能手机'
        CREATE (p1)-[:上游材料]->(p2)
        """)
        
        g.run("""
        MATCH (p1:product), (p2:product)
        WHERE p1.name = '显示屏' AND p2.name = '笔记本电脑'
        CREATE (p1)-[:上游材料]->(p2)
        """)
        
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
        print("5. 查看完整产业链: MATCH path = (c:company)-[r1:主营产品]->(p:product)-[r2:上游材料*]->(p2:product) RETURN path")
        print("6. 查看高权重主营产品: MATCH (c:company)-[r:主营产品]->(p:product) WHERE toFloat(r.权重) > 0.5 RETURN c, r, p")
        
        end_time = time.time()
        total_time = end_time - start_time
        print(f"\n知识图谱构建完成！总耗时: {total_time:.2f}秒")
        
        return True
    except Exception as e:
        print(f"创建知识图谱时出错: {e}")
        return False

if __name__ == "__main__":
    create_quick_graph()
    print("请访问 http://127.0.0.1:7474 查看效果") 