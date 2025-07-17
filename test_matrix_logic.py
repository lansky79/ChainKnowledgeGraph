#!/usr/bin/env python3
# coding: utf-8
# File: test_matrix_logic.py
# 测试矩阵逻辑

from utils.db_connector import Neo4jConnector
import numpy as np

def test_matrix_logic():
    db = Neo4jConnector()
    
    print("=== 测试矩阵逻辑 ===\n")
    
    # 模拟高级可视化页面的查询逻辑
    selected_entity = "互联网"
    
    # 1. 主查询
    query = """
    MATCH (i:industry {name: $name})
    OPTIONAL MATCH (c:company)-[r1:所属行业]->(i)
    OPTIONAL MATCH (c)-[r2:主营产品]->(p:product)
    OPTIONAL MATCH (i)-[r3]-(related:industry)
    RETURN i, collect(distinct c) as companies, 
           collect(distinct p) as products,
           collect(distinct related) as related_industries
    """
    
    results = db.query(query, {"name": selected_entity})
    
    if results:
        companies = results[0].get("companies", [])
        products = results[0].get("products", [])
        
        print(f"主查询结果:")
        print(f"  公司数量: {len([c for c in companies if c])}")
        print(f"  产品数量: {len([p for p in products if p])}")
        
        # 2. 创建节点列表（模拟）
        nodes = []
        node_ids = {}
        
        # 添加行业节点
        if "i" in results[0]:
            industry = results[0]["i"]
            industry_id = industry.identity
            nodes.append({
                "id": industry_id,
                "label": industry["name"],
                "group": 0  # 行业
            })
            node_ids[industry_id] = True
        
        # 添加公司节点
        for company in companies:
            if company:
                company_id = company.identity
                if company_id not in node_ids:
                    nodes.append({
                        "id": company_id,
                        "label": company["name"],
                        "group": 1  # 公司
                    })
                    node_ids[company_id] = True
        
        # 添加产品节点
        for product in products:
            if product:
                product_id = product.identity
                if product_id not in node_ids:
                    nodes.append({
                        "id": product_id,
                        "label": product["name"],
                        "group": 2  # 产品
                    })
                    node_ids[product_id] = True
        
        print(f"\n节点统计:")
        print(f"  总节点数: {len(nodes)}")
        print(f"  行业节点: {len([n for n in nodes if n['group'] == 0])}")
        print(f"  公司节点: {len([n for n in nodes if n['group'] == 1])}")
        print(f"  产品节点: {len([n for n in nodes if n['group'] == 2])}")
        
        # 3. 查询真实的公司-产品关系
        company_product_query = """
        MATCH (i:industry {name: $industry_name})<-[:所属行业]-(c:company)-[:主营产品]->(p:product)
        RETURN c.name as company_name, p.name as product_name
        """
        
        cp_results = db.query(company_product_query, {"industry_name": selected_entity})
        
        print(f"\n公司-产品关系查询:")
        print(f"  找到 {len(cp_results)} 个关系")
        
        # 显示前10个关系
        for i, cp_result in enumerate(cp_results[:10]):
            print(f"    {i+1}. {cp_result['company_name']} -> {cp_result['product_name']}")
        
        # 4. 创建名称到ID的映射
        company_name_to_id = {}
        product_name_to_id = {}
        
        for node in nodes:
            if node.get("group") == 1:  # 公司
                company_name_to_id[node["label"]] = node["id"]
            elif node.get("group") == 2:  # 产品
                product_name_to_id[node["label"]] = node["id"]
        
        print(f"\n名称映射:")
        print(f"  公司名称映射: {len(company_name_to_id)} 个")
        print(f"  产品名称映射: {len(product_name_to_id)} 个")
        
        # 5. 创建边列表
        edges = []
        matched_relations = 0
        
        for cp_result in cp_results:
            company_name = cp_result["company_name"]
            product_name = cp_result["product_name"]
            
            if company_name in company_name_to_id and product_name in product_name_to_id:
                company_id = company_name_to_id[company_name]
                product_id = product_name_to_id[product_name]
                
                edges.append({
                    "from": company_id,
                    "to": product_id,
                    "label": "主营产品"
                })
                matched_relations += 1
        
        print(f"\n边创建结果:")
        print(f"  成功匹配的关系: {matched_relations}")
        print(f"  创建的边数量: {len(edges)}")
        
        # 6. 测试矩阵创建
        company_nodes = [n for n in nodes if n['group'] == 1]
        product_nodes = [n for n in nodes if n['group'] == 2]
        
        if len(company_nodes) > 0 and len(product_nodes) > 0:
            # 限制产品数量
            max_products = 20
            if len(product_nodes) > max_products:
                product_nodes = sorted(product_nodes, key=lambda x: x["label"])[:max_products]
            
            print(f"\n矩阵创建:")
            print(f"  公司数量: {len(company_nodes)}")
            print(f"  产品数量: {len(product_nodes)}")
            
            # 创建矩阵
            matrix = np.zeros((len(company_nodes), len(product_nodes)))
            
            # 创建标签到索引的映射
            company_label_to_index = {node["label"]: i for i, node in enumerate(company_nodes)}
            product_label_to_index = {node["label"]: i for i, node in enumerate(product_nodes)}
            
            # 填充矩阵
            relations_found = 0
            for edge in edges:
                source_node = next((node for node in nodes if node["id"] == edge["from"]), None)
                target_node = next((node for node in nodes if node["id"] == edge["to"]), None)
                
                if source_node and target_node:
                    source_group = source_node.get("group", 0)
                    target_group = target_node.get("group", 0)
                    
                    # 公司 -> 产品 关系
                    if source_group == 1 and target_group == 2:
                        source_label = source_node["label"]
                        target_label = target_node["label"]
                        
                        if source_label in company_label_to_index and target_label in product_label_to_index:
                            company_idx = company_label_to_index[source_label]
                            product_idx = product_label_to_index[target_label]
                            matrix[company_idx][product_idx] = 1
                            relations_found += 1
                            print(f"    矩阵[{company_idx}][{product_idx}] = 1 ({source_label} -> {target_label})")
            
            print(f"\n矩阵填充结果:")
            print(f"  填充的关系数量: {relations_found}")
            print(f"  矩阵中非零元素: {np.sum(matrix > 0)}")
            print(f"  矩阵总大小: {matrix.size}")
            print(f"  填充率: {np.sum(matrix > 0) / matrix.size * 100:.2f}%")

if __name__ == "__main__":
    test_matrix_logic()