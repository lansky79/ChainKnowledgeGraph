#!/usr/bin/env python3
# coding: utf-8
# File: debug_matrix.py
# 调试矩阵关系问题

from utils.db_connector import Neo4jConnector

def debug_matrix():
    db = Neo4jConnector()
    
    print("=== 调试公司-产品矩阵关系 ===\n")
    
    # 1. 检查互联网行业的公司-产品关系
    query1 = """
    MATCH (i:industry {name: '互联网'})<-[:所属行业]-(c:company)-[:主营产品]->(p:product)
    RETURN c.name as company_name, p.name as product_name
    ORDER BY c.name, p.name
    LIMIT 20
    """
    
    results1 = db.query(query1)
    print(f'1. 互联网行业的公司-产品关系 (前20个):')
    for result in results1:
        print(f'   {result["company_name"]} -> {result["product_name"]}')
    
    print(f'\n   总共找到 {len(results1)} 个关系\n')
    
    # 2. 检查高级可视化页面使用的查询
    query2 = """
    MATCH (i:industry {name: '互联网'})
    OPTIONAL MATCH (c:company)-[r1:所属行业]->(i)
    OPTIONAL MATCH (c)-[r2:主营产品]->(p:product)
    OPTIONAL MATCH (i)-[r3]-(related:industry)
    RETURN i, collect(distinct c) as companies, 
           collect(distinct p) as products,
           collect(distinct related) as related_industries
    """
    
    results2 = db.query(query2)
    if results2:
        companies = results2[0].get("companies", [])
        products = results2[0].get("products", [])
        
        print(f'2. 高级可视化查询结果:')
        print(f'   公司数量: {len([c for c in companies if c])}')
        print(f'   产品数量: {len([p for p in products if p])}')
        
        print(f'\n   公司列表:')
        for company in companies:
            if company:
                print(f'     - {company["name"]}')
        
        print(f'\n   产品列表 (前10个):')
        for i, product in enumerate(products):
            if product and i < 10:
                print(f'     - {product["name"]}')
    
    # 3. 检查具体的华为产品关系
    query3 = """
    MATCH (c:company {name: '华为'})-[:主营产品]->(p:product)
    RETURN p.name as product_name
    ORDER BY p.name
    """
    
    results3 = db.query(query3)
    print(f'\n3. 华为的产品:')
    for result in results3:
        print(f'   - {result["product_name"]}')
    
    # 4. 检查阿里巴巴产品关系
    query4 = """
    MATCH (c:company {name: '阿里巴巴'})-[:主营产品]->(p:product)
    RETURN p.name as product_name
    ORDER BY p.name
    """
    
    results4 = db.query(query4)
    print(f'\n4. 阿里巴巴的产品:')
    for result in results4:
        print(f'   - {result["product_name"]}')

if __name__ == "__main__":
    debug_matrix()