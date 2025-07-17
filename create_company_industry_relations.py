#!/usr/bin/env python3
# coding: utf-8
# File: create_company_industry_relations.py
# 创建公司-行业关系

from utils.db_connector import Neo4jConnector

def create_company_industry_relations():
    db = Neo4jConnector()
    
    # 定义公司-行业关系
    company_industry_relations = [
        {"company": "华为", "industry": "互联网"},
        {"company": "阿里巴巴", "industry": "互联网"},
        {"company": "腾讯", "industry": "互联网"},
        {"company": "百度", "industry": "互联网"},
        {"company": "小米", "industry": "互联网"},
        {"company": "字节跳动", "industry": "互联网"},
        {"company": "美团", "industry": "互联网"},
        {"company": "滴滴", "industry": "互联网"},
        {"company": "京东", "industry": "互联网"},
        {"company": "网易", "industry": "互联网"},
        {"company": "OPPO", "industry": "互联网"},
        {"company": "vivo", "industry": "互联网"},
    ]
    
    # 创建公司-行业关系
    create_relations_query = """
    UNWIND $relations AS rel
    MATCH (c:company {name: rel.company})
    MATCH (i:industry {name: rel.industry})
    MERGE (c)-[r:所属行业]->(i)
    """
    
    db.query(create_relations_query, {"relations": company_industry_relations})
    print(f"创建了 {len(company_industry_relations)} 个公司-行业关系")
    
    # 验证关系
    verify_query = """
    MATCH (i:industry {name: '互联网'})<-[:所属行业]-(c:company)
    RETURN c.name as company
    ORDER BY c.name
    """
    
    results = db.query(verify_query)
    print(f"\n互联网行业的公司 ({len(results)}个):")
    for result in results:
        print(f"  - {result['company']}")

if __name__ == "__main__":
    create_company_industry_relations()