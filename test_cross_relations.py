#!/usr/bin/env python3
# coding: utf-8
# File: test_cross_relations.py
# 测试交叉关系查询

from utils.db_connector import Neo4jConnector

def test_cross_relations():
    db = Neo4jConnector()
    
    print("=== 测试交叉关系查询 ===\n")
    
    # 1. 查询与互联网相关的行业
    related_query = """
    MATCH (i:industry {name: '互联网'})-[r]-(related:industry)
    RETURN collect(distinct related.name) as related_industries
    """
    
    related_results = db.query(related_query)
    if related_results:
        related_industries = related_results[0]["related_industries"]
        all_industries = ["互联网"] + related_industries
        
        print(f"与互联网相关的行业 ({len(all_industries)}个):")
        for industry in all_industries:
            print(f"  - {industry}")
        
        # 2. 查询这些行业之间的所有交叉关系
        cross_query = """
        MATCH (i1:industry)-[r:相关行业]->(i2:industry)
        WHERE i1.name IN $industry_names AND i2.name IN $industry_names
        RETURN i1.name as from_industry, i2.name as to_industry, r.type as relation_type
        ORDER BY from_industry, to_industry
        """
        
        cross_results = db.query(cross_query, {"industry_names": all_industries})
        
        print(f"\n这些行业之间的交叉关系 ({len(cross_results)}个):")
        
        # 按源行业分组显示
        from_industries = {}
        for rel in cross_results:
            from_ind = rel["from_industry"]
            if from_ind not in from_industries:
                from_industries[from_ind] = []
            from_industries[from_ind].append(f"{rel['to_industry']} ({rel['relation_type']})")
        
        for from_ind, targets in from_industries.items():
            print(f"\n  {from_ind}:")
            for target in targets:
                print(f"    -> {target}")
        
        # 3. 创建矩阵统计
        print(f"\n矩阵统计:")
        print(f"  矩阵大小: {len(all_industries)} x {len(all_industries)}")
        print(f"  总关系数: {len(cross_results)}")
        print(f"  填充率: {len(cross_results) / (len(all_industries) * len(all_industries)) * 100:.2f}%")
        
        # 4. 显示矩阵预览
        print(f"\n矩阵预览 (行->列关系):")
        print("行业".ljust(12), end="")
        for col_ind in all_industries[:5]:  # 只显示前5列
            print(col_ind[:8].ljust(10), end="")
        print("...")
        
        for row_ind in all_industries[:5]:  # 只显示前5行
            print(row_ind[:10].ljust(12), end="")
            for col_ind in all_industries[:5]:
                has_relation = any(
                    rel["from_industry"] == row_ind and rel["to_industry"] == col_ind 
                    for rel in cross_results
                )
                print("●".ljust(10) if has_relation else " ".ljust(10), end="")
            print("...")

if __name__ == "__main__":
    test_cross_relations()