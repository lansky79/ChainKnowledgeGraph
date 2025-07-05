import streamlit as st
import streamlit_echarts as st_echarts
import pandas as pd
import numpy as np
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile
import os
import logging

# 设置日志
logger = logging.getLogger("KG_Visualization")

# 获取实体选项列表
def get_entity_options(graph, entity_type):
    """根据实体类型获取实体列表"""
    query = f"MATCH (n:{entity_type}) RETURN n.name AS name ORDER BY name"
    results = graph.run_query(query)
    return [record["name"] for record in results]

# 网络图可视化
def display_network_graph(graph, entity_type, entity_name, depth):
    """生成并显示网络图可视化"""
    try:
        # 构建查询
        if entity_type == "industry":
            query = f"""
            MATCH path = (i:{entity_type} {{name: $name}})-[r1:上级行业|所属行业*0..{depth}]-(related)
            OPTIONAL MATCH (company:company)-[r2:所属行业]->(related)
            WHERE related:{entity_type}
            RETURN path, collect(distinct company) as companies
            """
        elif entity_type == "company":
            query = f"""
            MATCH path = (c:{entity_type} {{name: $name}})-[r1:所属行业|主营产品*0..{depth}]-(related)
            RETURN path
            """
        else:  # product
            query = f"""
            MATCH path = (p:{entity_type} {{name: $name}})-[r1:上游材料*0..{depth}]-(related)
            OPTIONAL MATCH (company:company)-[r2:主营产品]->(related)
            WHERE related:{entity_type}
            RETURN path, collect(distinct company) as companies
            """
        
        # 执行查询
        results = graph.run_query(query, name=entity_name)
        
        # 处理结果，构建节点和边
        nodes = []
        edges = []
        node_ids = {}  # 使用字典存储节点ID到索引的映射
        
        # 处理查询结果
        for record in results:
            # 处理路径中的节点和关系
            path = record["path"]
            for node in path.nodes:
                node_name = node["name"]
                if node_name not in node_ids:
                    node_type = list(node.labels)[0]
                    node_index = len(nodes)
                    nodes.append({
                        "name": str(node_name),  # 确保名称是字符串
                        "symbolSize": 40 if node_type == "industry" else 30 if node_type == "company" else 25,
                        "category": 0 if node_type == "industry" else 1 if node_type == "company" else 2,
                    })
                    node_ids[node_name] = node_index
            
            for rel in path.relationships:
                start_name = rel.start_node["name"]
                end_name = rel.end_node["name"]
                if start_name in node_ids and end_name in node_ids:
                    edges.append({
                        "source": node_ids[start_name],
                        "target": node_ids[end_name],
                        "value": str(rel.type)  # 确保类型是字符串
                    })
            
            # 处理公司节点（如果有）
            if "companies" in record:
                companies = record["companies"]
                for company in companies:
                    company_name = company["name"]
                    if company_name and company_name not in node_ids:
                        node_index = len(nodes)
                        nodes.append({
                            "name": str(company_name),  # 确保名称是字符串
                            "symbolSize": 30,
                            "category": 1,
                        })
                        node_ids[company_name] = node_index
        
        # 构建ECharts配置
        category_names = ["产业", "公司", "产品"]
        categories = [{"name": name} for name in category_names]
        
        # 极度简化的配置
        options = {
            "title": {"text": f"{entity_name}相关知识图谱"},
            "tooltip": {},
            "legend": {"data": category_names},
            "series": [{
                "type": "graph",
                "layout": "force",
                "data": nodes,
                "links": edges,
                "categories": categories,
                "roam": True,
                "label": {"show": True},
                "force": {"repulsion": 100}
            }]
        }
        
        # 使用Pyvis作为备选方案
        if not nodes:
            return False, f"没有找到与 {entity_name} 相关的节点"
        
        # 尝试使用纯字典序列化
        import json
        # 序列化测试
        try:
            json.dumps(options)
        except TypeError as e:
            st.error(f"配置序列化失败: {e}")
            # 在此处可以添加调试信息或应急方案
            # 创建更简单的配置
            options = {
                "title": {"text": f"{entity_name}相关知识图谱"},
                "series": [{
                    "type": "graph",
                    "layout": "force",
                    "data": [{"name": str(n["name"]), "category": int(n["category"])} for n in nodes],
                    "links": [{"source": int(e["source"]), "target": int(e["target"])} for e in edges],
                    "categories": [{"name": n} for n in category_names],
                }]
            }
        
        # 显示图表
        st_echarts.st_echarts(
            options=options,
            height="600px",
        )
        
        return True, f"成功可视化 {entity_name} 的相关知识图谱"
    except Exception as e:
        logger.error(f"网络图可视化失败: {str(e)}")
        return False, f"网络图可视化失败: {str(e)}"

# 层级树可视化
def display_hierarchy_tree(graph, entity_type, entity_name, depth):
    """生成并显示层级树可视化"""
    try:
        if entity_type != "industry":
            return False, "层级树可视化仅支持产业类型的实体"
        
        # 构建查询
        query = f"""
        MATCH path = (i:industry {{name: $name}})<-[:上级行业*0..{depth}]-(sub:industry)
        OPTIONAL MATCH (c:company)-[:所属行业]->(sub)
        RETURN i, sub, collect(c) as companies
        """
        
        # 执行查询
        results = graph.run_query(query, name=entity_name)
        
        # 处理结果，构建树形结构
        root = {
            "name": entity_name,
            "children": []
        }
        
        industry_map = {entity_name: root}
        
        for record in results:
            parent = record["i"]["name"]
            child = record["sub"]["name"]
            companies = record["companies"]
            
            if child not in industry_map:
                child_node = {
                    "name": child,
                    "children": []
                }
                industry_map[child] = child_node
                
                # 添加公司作为子节点
                for company in companies:
                    if company["name"]:  # 确保公司名不为空
                        child_node["children"].append({
                            "name": company["name"],
                            "value": 1
                        })
                
                # 将子产业添加到父产业
                if parent in industry_map:
                    industry_map[parent]["children"].append(child_node)
        
        # 修改：简化配置，移除可能导致序列化问题的项
        options = {
            "title": {"text": f"{entity_name}产业层级结构", "top": "top", "left": "center"},
            "tooltip": {"trigger": "item"},
            "series": [{
                "type": "tree",
                "data": [root],
                "top": "10%",
                "left": "8%",
                "bottom": "22%",
                "right": "20%",
                "symbolSize": 7,
                "label": {
                    "position": "left",
                    "verticalAlign": "middle",
                    "align": "right",
                    "fontSize": 12
                },
                "leaves": {
                    "label": {
                        "position": "right",
                        "verticalAlign": "middle",
                        "align": "left"
                    }
                },
                "expandAndCollapse": True
            }]
        }
        
        # 显示图表
        st_echarts.st_echarts(
            options=options,
            height="600px",
        )
        
        return True, f"成功可视化 {entity_name} 的产业层级结构"
    except Exception as e:
        logger.error(f"层级树可视化失败: {str(e)}")
        return False, f"层级树可视化失败: {str(e)}"

# 关系矩阵可视化
def display_relationship_matrix(graph, entity_type, entity_name, depth):
    """生成并显示关系矩阵可视化"""
    try:
        if entity_type == "industry":
            # 构建查询 - 获取行业内公司和它们的产品
            query = f"""
            MATCH (i:industry {{name: $name}})<-[:所属行业]-(c:company)-[:主营产品]->(p:product)
            RETURN c.name as company, collect(p.name) as products
            LIMIT 20
            """
        else:
            return False, "关系矩阵可视化当前仅支持产业类型"
        
        # 执行查询
        results = graph.run_query(query, name=entity_name)
        
        # 处理结果
        companies = []
        all_products = set()
        company_products = {}
        
        for record in results:
            company = record["company"]
            products = record["products"]
            companies.append(company)
            company_products[company] = products
            all_products.update(products)
        
        if not companies or not all_products:
            return False, f"未找到与 {entity_name} 相关的公司-产品关系数据"
        
        # 将产品列表转换为有序列表
        products_list = sorted(list(all_products))
        
        # 构建矩阵数据
        matrix_data = []
        for company in companies:
            for product in products_list:
                value = 1 if product in company_products[company] else 0
                if value > 0:  # 只添加存在的关系
                    matrix_data.append([companies.index(company), products_list.index(product), value])
        
        # 修改：简化配置，移除可能导致序列化问题的项
        options = {
            "title": {"text": f"{entity_name}行业公司-产品关系矩阵", "top": "top", "left": "center"},
            "tooltip": {"position": "top"},
            "grid": {"height": "50%", "top": "10%"},
            "xAxis": {
                "type": "category",
                "data": products_list,
                "splitArea": {"show": True},
                "axisLabel": {"interval": 0, "rotate": 45}
            },
            "yAxis": {
                "type": "category",
                "data": companies,
                "splitArea": {"show": True}
            },
            "visualMap": {
                "min": 0,
                "max": 1,
                "calculable": True,
                "orient": "horizontal",
                "left": "center",
                "bottom": "15%"
            },
            "series": [{
                "name": "公司-产品关系",
                "type": "heatmap",
                "data": matrix_data,
                "label": {"show": True}
            }]
        }
        
        # 显示图表
        st_echarts.st_echarts(
            options=options,
            height="600px",
        )
        
        return True, f"成功可视化 {entity_name} 行业的公司-产品关系矩阵"
    except Exception as e:
        logger.error(f"关系矩阵可视化失败: {str(e)}")
        return False, f"关系矩阵可视化失败: {str(e)}"

# 产业链可视化
def display_industry_chain(graph, entity_type, entity_name, depth):
    """生成并显示产业链可视化"""
    try:
        if entity_type not in ["industry", "product"]:
            return False, "产业链可视化仅支持产业或产品类型的实体"
        
        # 构建查询
        if entity_type == "industry":
            query = f"""
            MATCH (i:industry {{name: $name}})<-[:所属行业]-(c:company)
            OPTIONAL MATCH (c)-[:主营产品]->(p:product)
            OPTIONAL MATCH (p)-[:上游材料]->(upstream:product)
            RETURN i, collect(distinct c) as companies, 
                   collect(distinct p) as products,
                   collect(distinct upstream) as upstream_products
            """
        else:  # product
            query = f"""
            MATCH (p:product {{name: $name}})
            OPTIONAL MATCH (p)<-[:主营产品]-(c:company)
            OPTIONAL MATCH (c)-[:所属行业]->(i:industry)
            OPTIONAL MATCH (p)-[:上游材料]->(upstream:product)
            RETURN p, collect(distinct c) as companies, 
                   collect(distinct i) as industries,
                   collect(distinct upstream) as upstream_products
            """
        
        # 执行查询
        results = graph.run_query(query, name=entity_name)
        
        # 处理结果，构建桑基图数据
        nodes = []
        links = []
        
        # 节点类别
        categories = ["产业", "公司", "产品", "上游产品"]
        
        # 节点ID映射
        node_map = {}
        
        # 添加节点函数
        def add_node(name, category):
            if name not in node_map:
                node_map[name] = len(nodes)
                # 修改：简化节点配置，使用简单的颜色字符串
                color_map = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]
                nodes.append({
                    "name": name, 
                    "itemStyle": {"color": color_map[category]}
                })
            return node_map[name]
        
        for record in results:
            if entity_type == "industry":
                industry = record["i"]
                industry_id = add_node(industry["name"], 0)  # 产业
                
                # 添加公司节点和产业->公司链接
                companies = record["companies"]
                for company in companies:
                    if company["name"]:
                        company_id = add_node(company["name"], 1)  # 公司
                        links.append({
                            "source": industry_id,
                            "target": company_id,
                            "value": 1
                        })
                
                # 添加产品节点和公司->产品链接
                products = record["products"]
                for product in products:
                    if product["name"]:
                        product_id = add_node(product["name"], 2)  # 产品
                        # 找到生产该产品的公司
                        for company in companies:
                            if company["name"]:
                                company_id = node_map[company["name"]]
                                links.append({
                                    "source": company_id,
                                    "target": product_id,
                                    "value": 1
                                })
                
                # 添加上游产品节点和产品->上游产品链接
                upstream_products = record["upstream_products"]
                for upstream in upstream_products:
                    if upstream["name"]:
                        upstream_id = add_node(upstream["name"], 3)  # 上游产品
                        # 找到使用该上游产品的产品
                        for product in products:
                            if product["name"]:
                                product_id = node_map[product["name"]]
                                links.append({
                                    "source": product_id,
                                    "target": upstream_id,
                                    "value": 1
                                })
            else:  # product
                product = record["p"]
                product_id = add_node(product["name"], 2)  # 产品
                
                # 添加公司节点和公司->产品链接
                companies = record["companies"]
                for company in companies:
                    if company["name"]:
                        company_id = add_node(company["name"], 1)  # 公司
                        links.append({
                            "source": company_id,
                            "target": product_id,
                            "value": 1
                        })
                
                # 添加产业节点和产业->公司链接
                industries = record["industries"]
                for industry in industries:
                    if industry["name"]:
                        industry_id = add_node(industry["name"], 0)  # 产业
                        # 找到属于该产业的公司
                        for company in companies:
                            if company["name"]:
                                company_id = node_map[company["name"]]
                                links.append({
                                    "source": industry_id,
                                    "target": company_id,
                                    "value": 1
                                })
                
                # 添加上游产品节点和产品->上游产品链接
                upstream_products = record["upstream_products"]
                for upstream in upstream_products:
                    if upstream["name"]:
                        upstream_id = add_node(upstream["name"], 3)  # 上游产品
                        links.append({
                            "source": product_id,
                            "target": upstream_id,
                            "value": 1
                        })
        
        # 修改：简化配置，移除可能导致序列化问题的项
        options = {
            "title": {"text": f"{entity_name}产业链分析", "top": "top", "left": "center"},
            "tooltip": {"trigger": "item"},
            "series": [{
                "type": "sankey",
                "data": nodes,
                "links": links,
                "lineStyle": {
                    "color": "gradient",
                    "curveness": 0.5
                }
            }]
        }
        
        # 显示图表
        st_echarts.st_echarts(
            options=options,
            height="600px",
        )
        
        return True, f"成功可视化 {entity_name} 的产业链分析"
    except Exception as e:
        logger.error(f"产业链可视化失败: {str(e)}")
        return False, f"产业链可视化失败: {str(e)}"

# 添加到build_graph.py的方法
def get_graph_visualization_data(graph, entity_type, entity_name, depth=2):
    """
    获取用于可视化的图数据
    
    Args:
        graph: Neo4j图数据库连接
        entity_type: 实体类型 (industry, company, product)
        entity_name: 实体名称
        depth: 探索深度
        
    Returns:
        nodes: 节点列表
        edges: 边列表
    """
    try:
        if entity_type == "industry":
            query = f"""
            MATCH path = (i:{entity_type} {{name: $name}})-[r1:上级行业|所属行业*0..{depth}]-(related)
            OPTIONAL MATCH (company:company)-[r2:所属行业]->(related)
            WHERE related:{entity_type}
            RETURN path, collect(distinct company) as companies
            """
        elif entity_type == "company":
            query = f"""
            MATCH path = (c:{entity_type} {{name: $name}})-[r1:所属行业|主营产品*0..{depth}]-(related)
            RETURN path
            """
        else:  # product
            query = f"""
            MATCH path = (p:{entity_type} {{name: $name}})-[r1:上游材料*0..{depth}]-(related)
            OPTIONAL MATCH (company:company)-[r2:主营产品]->(related)
            WHERE related:{entity_type}
            RETURN path, collect(distinct company) as companies
            """
        
        result = graph.run(query, name=entity_name)
        
        # 处理结果
        nodes = []
        edges = []
        node_ids = set()
        
        for record in result:
            # 处理路径
            path = record["path"]
            for node in path.nodes:
                if node.id not in node_ids:
                    node_type = list(node.labels)[0]
                    nodes.append({
                        "id": node.id,
                        "name": node["name"],
                        "type": node_type
                    })
                    node_ids.add(node.id)
            
            for rel in path.relationships:
                edges.append({
                    "source": rel.start_node.id,
                    "target": rel.end_node.id,
                    "type": rel.type
                })
            
            # 处理公司节点（如果有）
            if "companies" in record:
                companies = record["companies"]
                for company in companies:
                    if company.id not in node_ids and company["name"]:
                        nodes.append({
                            "id": company.id,
                            "name": company["name"],
                            "type": "company"
                        })
                        node_ids.add(company.id)
        
        return {"nodes": nodes, "edges": edges}
    
    except Exception as e:
        logger.error(f"获取可视化数据出错: {str(e)}")
        return {"nodes": [], "edges": []}