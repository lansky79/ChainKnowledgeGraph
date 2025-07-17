#!/usr/bin/env python3
# coding: utf-8
# File: test_product_query.py
# 测试产品查询

from utils.db_connector import Neo4jConnector

def test_product_query():
    db = Neo4jConnector()
    
    # 测试手机产品的查询
    query = """
    MATCH (p:product {name: '手机'})
    OPTIONAL MATCH (c:company)-[r1:主营产品]->(p)
    OPTIONAL MATCH (p)-[r2:上游材料]->(up:product)
    OPTIONAL MATCH (child:product)-[r3:属于类别]->(p)
    OPTIONAL MATCH (p)-[r4:属于类别]->(parent:product)
    OPTIONAL MATCH (p)-[r5:产品关系]-(related:product)
    RETURN p, collect(distinct c) as companies, 
           collect(distinct up) as upstream_products,
           collect(distinct child) as child_products,
           collect(distinct parent) as parent_products,
           collect(distinct related) as related_products
    """
    
    results = db.query(query)
    if results:
        result = results[0]
        print('手机产品查询结果:')
        print(f'中心产品: {result["p"]["name"] if result["p"] else "未找到"}')
        print(f'关联公司: {len([c for c in result["companies"] if c])}个')
        print(f'上游产品: {len([u for u in result["upstream_products"] if u])}个')
        print(f'子产品: {len([c for c in result["child_products"] if c])}个')
        print(f'父产品: {len([p for p in result["parent_products"] if p])}个')
        print(f'相关产品: {len([r for r in result["related_products"] if r])}个')
        
        # 显示子产品
        child_products = [c['name'] for c in result['child_products'] if c]
        if child_products:
            print(f'子产品列表: {child_products}')
        
        # 显示相关产品
        related_products = [r['name'] for r in result['related_products'] if r]
        if related_products:
            print(f'相关产品列表: {related_products[:5]}')
        
        # 计算总节点数和关系数
        total_nodes = 1  # 中心产品
        total_nodes += len([c for c in result["companies"] if c])
        total_nodes += len([u for u in result["upstream_products"] if u])
        total_nodes += len([c for c in result["child_products"] if c])
        total_nodes += len([p for p in result["parent_products"] if p])
        total_nodes += len([r for r in result["related_products"] if r])
        
        print(f'\n预期节点总数: {total_nodes}')
        
    else:
        print('未找到手机产品')
    
    # 也测试一下具体的产品关系
    print('\n测试产品间关系:')
    relations_query = """
    MATCH (p1:product)-[r:产品关系]->(p2:product)
    WHERE p1.name CONTAINS '手机' OR p2.name CONTAINS '手机'
    RETURN p1.name as from_product, p2.name as to_product, r.type as relation_type
    LIMIT 10
    """
    
    relations = db.query(relations_query)
    if relations:
        print(f'找到 {len(relations)} 个手机相关的产品关系:')
        for rel in relations:
            print(f'  {rel["from_product"]} --{rel["relation_type"]}--> {rel["to_product"]}')
    else:
        print('未找到手机相关的产品关系')

if __name__ == "__main__":
    test_product_query()