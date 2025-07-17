#!/usr/bin/env python3
# coding: utf-8
# File: check_relations.py
# 检查数据库中的公司-产品关系

from utils.db_connector import Neo4jConnector

def check_relations():
    db = Neo4jConnector()
    
    # 检查互联网行业的公司-产品关系
    query = """
    MATCH (i:industry {name: '互联网'})
    OPTIONAL MATCH (c:company)-[r1:所属行业]->(i)
    OPTIONAL MATCH (c)-[r2:主营产品]->(p:product)
    RETURN c.name as company, collect(p.name) as products
    ORDER BY c.name
    """
    
    results = db.query(query)
    print('互联网行业的公司-产品关系:')
    for result in results:
        if result['company']:
            products = [p for p in result['products'] if p]
            print(f'{result["company"]}: {len(products)} products - {products[:3]}...')
    
    # 检查所有公司-产品关系
    query2 = """
    MATCH (c:company)-[r:主营产品]->(p:product)
    RETURN c.name as company, p.name as product
    ORDER BY c.name, p.name
    LIMIT 15
    """
    
    results2 = db.query(query2)
    print('\n所有公司-产品关系（前15个）:')
    for result in results2:
        print(f'{result["company"]} -> {result["product"]}')
    
    # 检查互联网行业是否存在
    query3 = """
    MATCH (i:industry {name: '互联网'})
    RETURN i.name as industry_name
    """
    
    results3 = db.query(query3)
    print(f'\n互联网行业节点: {results3}')
    
    # 检查公司-行业关系
    query4 = """
    MATCH (c:company)-[r:所属行业]->(i:industry)
    RETURN c.name as company, i.name as industry
    ORDER BY c.name
    LIMIT 10
    """
    
    results4 = db.query(query4)
    print('\n公司-行业关系（前10个）:')
    for result in results4:
        print(f'{result["company"]} -> {result["industry"]}')

if __name__ == "__main__":
    check_relations()