import streamlit as st
import streamlit_echarts as st_echarts
import pandas as pd
import numpy as np
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile
import os
import os.path
import logging
from src.neo4j_handler import Neo4jHandler # 导入 Neo4jHandler

# 设置日志
logger = logging.getLogger("KG_Visualization")

# 获取实体选项列表
def get_entity_options(handler, entity_type, search_term=""):
    """根据实体类型获取实体列表"""
    if not handler or not handler.g:
        return []
    query_parts = [f"MATCH (n:{entity_type})"]
    params = {}

    if search_term:
        query_parts.append("WHERE toLower(n.name) CONTAINS toLower($search_term)")
        params["search_term"] = search_term
    
    query_parts.append("RETURN n.name AS name ORDER BY name LIMIT 100")
    query = " ".join(query_parts)

    try:
        results = handler.g.run(query, **params).data()
        return [record["name"] for record in results]
    except Exception as e:
        logger.error(f"获取实体列表失败: {e}")
        return []

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
            path_data = record["path"]
            for node_dict in path_data["nodes"]:
                node_name = node_dict["properties"]["name"]
                if node_name not in node_ids:
                    node_type = node_dict["labels"][0]
                    node_index = len(nodes)
                    nodes.append({
                        "name": str(node_name),  # 确保名称是字符串
                        "symbolSize": 40 if node_type == "industry" else 30 if node_type == "company" else 25,
                        "category": 0 if node_type == "industry" else 1 if node_type == "company" else 2,
                    })
                    node_ids[node_name] = node_index
            
            for rel_dict in path_data["relationships"]:
                start_name = rel_dict["start"]["properties"]["name"]
                end_name = rel_dict["end"]["properties"]["name"]
                if start_name in node_ids and end_name in node_ids:
                    edges.append({
                        "source": node_ids[start_name],  # 使用索引而不是名称
                        "target": node_ids[end_name],    # 使用索引而不是名称
                        "name": str(rel_dict["type"]),
                        "value": 1
                    })
            
            # 处理公司节点（如果有）
            if "companies" in record:
                companies_data = record["companies"]
                for company_dict in companies_data:
                    company_name = company_dict["properties"]["name"]
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
                "edgeLabel": {
                    "show": True,
                    "formatter": "{c}"
                },
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
                    "links": [{"source": node_ids[e["source"]] if isinstance(e["source"], str) else e["source"], 
                               "target": node_ids[e["target"]] if isinstance(e["target"], str) else e["target"]} for e in edges],
                    "categories": [{"name": n} for n in category_names],
                }]
            }
        
        # 如果没有节点，返回None
        if not nodes:
            st.info(f"没有找到与 {entity_name} 相关的节点。")
            return None

        return options
    except Exception as e:
        error_message = f"网络图可视化失败: {str(e)}"
        logger.error(error_message)
        st.error(error_message) # 在Streamlit页面显示错误
        return None

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
            parent = record["i"]["properties"]["name"]
            child = record["sub"]["properties"]["name"]
            companies = record["companies"]
            
            if child not in industry_map:
                child_node = {
                    "name": child,
                    "children": []
                }
                industry_map[child] = child_node
                
                # 添加公司作为子节点
                for company_dict in companies:
                    if company_dict["properties"]["name"]:  # 确保公司名不为空
                        child_node["children"].append({
                            "name": company_dict["properties"]["name"],
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
        
        # 如果没有根节点，返回None
        if not root["children"] and not root["name"] == entity_name:
            st.info(f"没有找到与 {entity_name} 相关的层级数据。")
            return None

        return options
    except Exception as e:
        error_message = f"层级树可视化失败: {str(e)}"
        logger.error(error_message)
        st.error(error_message) # 在Streamlit页面显示错误
        return None

# 关系矩阵可视化
def display_relationship_matrix(graph, entity_type, entity_name, depth):
    """生成并显示关系矩阵可视化
    
    关系矩阵的定义：
    1. 公司-公司矩阵：显示同一行业内不同公司之间的关系
    2. 产品-产品矩阵：显示同类产品之间的关系
    3. 行业-行业矩阵：显示不同行业之间的关系
    """
    try:
        # 提供矩阵类型选择
        matrix_type = st.radio(
            "请选择矩阵类型：",
            ["公司-公司矩阵", "产品类别矩阵", "行业-行业矩阵"],
            index=0  # 默认选择公司-公司矩阵
        )
        
        if entity_type == "industry":
            if matrix_type == "公司-公司矩阵":
                # 构建查询 - 获取行业内的公司
                query = f"""
                MATCH (i:industry {{name: $name}})<-[:所属行业]-(c:company)
                RETURN c.name as company
                """
            elif matrix_type == "产品类别矩阵":
                # 构建查询 - 获取行业内公司的产品类型
                query = f"""
                MATCH (i:industry {{name: $name}})<-[:所属行业]-(c:company)-[:主营产品]->(p:product)
                RETURN p.type as product_type, collect(p.name) as products
                """
            elif matrix_type == "行业-行业矩阵":
                # 构建查询 - 获取与该行业相关的其他行业
                query = f"""
                MATCH (i:industry {{name: $name}})-[r]-(other:industry)
                RETURN i.name as industry1, other.name as industry2, type(r) as relation
                """
        else:
            return False, "关系矩阵可视化当前仅支持产业类型"
        
        # 执行查询
        results = graph.run_query(query, name=entity_name)
        
        if matrix_type == "公司-公司矩阵":
            # 处理公司-公司矩阵数据
            companies = []
            for record in results:
                company = record["company"]
                if company not in companies:
                    companies.append(company)
            
            if not companies:
                st.info(f"未找到与 {entity_name} 行业相关的公司数据")
                return None
                
            # 构建公司-公司关系矩阵
            st.subheader(f"{entity_name}行业内的公司关系矩阵")
            
            # 这里可以添加公司间的关系查询，目前简单展示公司列表
            st.write(f"该行业包含 {len(companies)} 家公司:")
            for company in companies:
                st.write(f"- {company}")
            
            return None  # 已经显示了公司列表
            
        elif matrix_type == "产品类别矩阵":
            # 处理产品类别矩阵数据
            product_types = []
            type_products = {}
            
            for record in results:
                product_type = record["product_type"] if record["product_type"] else "未分类"
                products = record["products"]
                if product_type not in product_types:
                    product_types.append(product_type)
                    type_products[product_type] = []
                type_products[product_type].extend(products)
            
            if not product_types:
                st.info(f"未找到与 {entity_name} 行业相关的产品类别数据")
                return None
                
            # 显示产品类别信息
            st.subheader(f"{entity_name}行业的产品类别")
            for ptype in product_types:
                st.write(f"**{ptype}**: {len(type_products[ptype])} 个产品")
                with st.expander(f"查看 {ptype} 类别的产品"):
                    for product in sorted(type_products[ptype]):
                        st.write(f"- {product}")
            
            return None  # 已经显示了产品类别信息
            
        elif matrix_type == "行业-行业矩阵":
            # 处理行业-行业矩阵数据
            industry_relations = []
            industries = set()
            
            for record in results:
                industry1 = record["industry1"]
                industry2 = record["industry2"]
                relation = record["relation"]
                industry_relations.append((industry1, industry2, relation))
                industries.add(industry1)
                industries.add(industry2)
            
            if not industry_relations:
                st.info(f"未找到与 {entity_name} 相关的行业关系数据")
                return None
                
            # 显示行业关系
            st.subheader(f"{entity_name}与其他行业的关系")
            for i1, i2, rel in industry_relations:
                st.write(f"- {i1} **{rel}** {i2}")
            
            return None  # 已经显示了行业关系
        
        # 兼容旧版本处理逻辑（以防万一）
        companies = []
        all_products = set()
        company_products = {}
        
        try:
            for record in results:
                if "company" in record and "products" in record:
                    company = record["company"]
                    products = record["products"]
                    companies.append(company)
                    company_products[company] = products
                    all_products.update(products)
        except Exception as e:
            st.error(f"处理查询结果时出错: {str(e)}")
            return None
        
        if not companies and not all_products:
            st.info(f"未找到与 {entity_name} 相关的关系数据")
            return None
        
        # 将产品列表转换为有序列表
        products_list = sorted([str(p) for p in all_products])
        
        # 提示用户这是旧版的矩阵视图，建议使用新版
        st.warning("您正在使用旧版矩阵视图，建议在上方选择更合适的矩阵类型。")
        filter_option = "按公司分组显示"  # 默认使用公司分组视图
            
            if filter_option == "按公司分组显示":
                # 为每个公司创建单独的矩阵
                for company in companies:
                    company_specific_products = sorted(company_products[company])
                    if not company_specific_products:
                        continue
                        
                    # 为该公司构建单独的矩阵数据
                    matrix_data = []
                    for product in company_specific_products:
                        matrix_data.append([0, company_specific_products.index(product), 1])
                    
                    # 创建该公司的选项
                    company_options = {
                        "title": {"text": f"{company}的产品关系矩阵", "top": "top", "left": "center"},
                        "tooltip": {"position": "top"},
                        "grid": {"height": "50%", "top": "10%"},
                        "xAxis": {
                            "type": "category",
                            "data": company_specific_products,
                            "splitArea": {"show": True},
                            "axisLabel": {"interval": 0, "rotate": 45}
                        },
                        "yAxis": {
                            "type": "category",
                            "data": [company],
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
                    
                    # 使用streamlit显示该公司的矩阵
                    st.subheader(f"{company}的产品矩阵")
                    st_echarts(options=company_options, height="400px")
                
                return None  # 已经在循环中显示了所有公司的矩阵
                
            elif filter_option == "只显示前20个产品":
                products_list = products_list[:max_products]
                st.info(f"仅显示前 {max_products} 个产品")
                
            elif filter_option == "按产品名称前缀分组":
                # 尝试按产品名称前缀分组
                prefixes = {}
                for product in products_list:
                    # 假设产品名称格式为"品牌+型号"，取前面的部分作为前缀
                    parts = product.split(' ')
                    if len(parts) > 1:
                        prefix = parts[0]
                    else:
                        # 如果没有空格，则取前5个字符作为前缀
                        prefix = product[:5]
                    
                    if prefix not in prefixes:
                        prefixes[prefix] = []
                    prefixes[prefix].append(product)
                
                # 让用户选择要显示的前缀组
                selected_prefix = st.selectbox("选择产品组:", list(prefixes.keys()))
                products_list = prefixes[selected_prefix]
                st.info(f"显示前缀为 '{selected_prefix}' 的 {len(products_list)} 个产品")
        
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
        
        # 如果没有公司或产品数据，返回None
        if not companies or not all_products:
            st.info(f"未找到与 {entity_name} 相关的公司-产品关系数据。")
            return None

        return options
    except Exception as e:
        error_message = f"关系矩阵可视化失败: {str(e)}"
        logger.error(error_message)
        st.error(error_message) # 在Streamlit页面显示错误
        return None

# 产业链可视化
def display_industry_chain(graph, entity_type, entity_name, depth):
    """生成并显示产业链可视化"""
    try:
        if entity_type == "company":
            st.info("产业链可视化目前不支持公司类型的实体。请选择产业或产品类型。")
            return None
        elif entity_type not in ["industry", "product"]:
            st.info("产业链可视化仅支持产业或产品类型的实体")
            return None
        
        # 构建查询
        st.info("Step 1: Building Cypher query...")
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
        st.info(f"Step 2: Executing query for {entity_name}...")
        results = graph.run_query(query, name=entity_name)
        st.info("Step 3: Query executed. Displaying raw results...")
        st.json(results) # 临时添加：显示原始查询结果，用于调试
        
        # 如果结果为空，提前返回
        if not results:
            st.info(f"没有找到与 {entity_name} 相关的产业链数据。")
            return None
        
        st.info("Step 4: Processing results...")
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
                industry_data = record["i"]
                industry_id = add_node(industry_data["properties"]["name"], 0)  # 产业
                
                # 添加公司节点和产业->公司链接
                companies_data = record["companies"]
                for company_dict in companies_data:
                    if company_dict["properties"]["name"]:
                        company_id = add_node(company_dict["properties"]["name"], 1)  # 公司
                        links.append({
                            "source": industry_id,
                            "target": company_id,
                            "value": 1
                        })
                
                # 添加产品节点和公司->产品链接
                products_data = record["products"]
                for product_dict in products_data:
                    if product_dict["properties"]["name"]:
                        product_id = add_node(product_dict["properties"]["name"], 2)  # 产品
                        # 找到生产该产品的公司
                        for company_dict in companies_data:
                            if company_dict["properties"]["name"]:
                                company_id = node_map[company_dict["properties"]["name"]]
                                links.append({
                                    "source": company_id,
                                    "target": product_id,
                                    "value": 1
                                })
                
                # 添加上游产品节点和产品->上游产品链接
                upstream_products_data = record["upstream_products"]
                for upstream_dict in upstream_products_data:
                    if upstream_dict["properties"]["name"]:
                        upstream_id = add_node(upstream_dict["properties"]["name"], 3)  # 上游产品
                        # 找到使用该上游产品的产品
                        for product_dict in products_data:
                            if product_dict["properties"]["name"]:
                                product_id = node_map[product_dict["properties"]["name"]]
                                links.append({
                                    "source": product_id,
                                    "target": upstream_id,
                                    "value": 1
                                })
            else:  # product
                product_data = record["p"]
                product_id = add_node(product_data["properties"]["name"], 2)  # 产品
                
                # 添加公司节点和公司->产品链接
                companies_data = record["companies"]
                for company_dict in companies_data:
                    if company_dict["properties"]["name"]:
                        company_id = add_node(company_dict["properties"]["name"], 1)  # 公司
                        links.append({
                            "source": company_id,
                            "target": product_id,
                            "value": 1
                        })
                
                # 添加产业节点和产业->公司链接
                industries_data = record["industries"]
                for industry_dict in industries_data:
                    if industry_dict["properties"]["name"]:
                        industry_id = add_node(industry_dict["properties"]["name"], 0)  # 产业
                        # 找到属于该产业的公司
                        for company_dict in companies_data:
                            if company_dict["properties"]["name"]:
                                company_id = node_map[company_dict["properties"]["name"]]
                                links.append({
                                    "source": industry_id,
                                    "target": company_id,
                                    "value": 1
                                })
                
                # 添加上游产品节点和产品->上游产品链接
                upstream_products_data = record["upstream_products"]
                for upstream_dict in upstream_products_data:
                    if upstream_dict["properties"]["name"]:
                        upstream_id = add_node(upstream_dict["properties"]["name"], 3)  # 上游产品
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
        
        # 如果没有公司或产品数据，返回None
        if not companies or not all_products:
            st.info(f"未找到与 {entity_name} 相关的公司-产品关系数据。")
            return None

        return options
    except Exception as e:
        error_message = f"关系矩阵可视化失败: {str(e)}"
        logger.error(error_message)
        st.error(error_message) # 在Streamlit页面显示错误
        return None

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
        
        result = graph.run_query(query, name=entity_name)
        
        # 处理结果
        nodes = []
        edges = []
        node_ids = set()
        
        for record in result:
            # 处理路径
            path_data = record["path"]
            
            # 处理路径中的节点
            for node_dict in path_data["nodes"]:
                node_id = node_dict["id"]
                if node_id not in node_ids:
                    node_type = node_dict["labels"][0]
                    nodes.append({
                        "id": node_id,
                        "name": node_dict["properties"]["name"],
                        "type": node_type
                    })
                    node_ids.add(node_id)
            
            # 处理路径中的关系
            for rel_dict in path_data["relationships"]:
                edges.append({
                    "source": rel_dict["start"]["id"],
                    "target": rel_dict["end"]["id"],
                    "type": rel_dict["type"]
                })
            
            # 处理公司节点（如果有）
            if "companies" in record:
                companies_data = record["companies"]
                for company_dict in companies_data:
                    company_id = company_dict["id"]
                    if company_id not in node_ids and company_dict["properties"]["name"]:
                        nodes.append({
                            "id": company_id,
                            "name": company_dict["properties"]["name"],
                            "type": "company"
                        })
                        node_ids.add(company_id)
        
        return {"nodes": nodes, "edges": edges}
    
    except Exception as e:
        logger.error(f"获取可视化数据出错: {str(e)}")
        st.error(f"获取可视化数据出错: {str(e)}") # 在Streamlit页面显示错误
        return {"nodes": [], "edges": []}

# Streamlit 应用主逻辑
def main():
    st.set_page_config(layout="wide")
    st.title("知识图谱可视化")

    # 初始化 Neo4jHandler
    graph_handler = Neo4jHandler()

    st.sidebar.header("可视化选项")
    
    entity_type = st.sidebar.selectbox("选择实体类型", ["industry", "company", "product"])
    
    # 获取实体名称选项
    entity_options = get_entity_options(graph_handler, entity_type)
    if not entity_options:
        st.sidebar.warning(f"未找到 {entity_type} 类型的实体。请确保Neo4j数据库中有数据。")
        entity_name = None
    else:
        entity_name = st.sidebar.selectbox(f"选择 {entity_type} 名称", entity_options)
    
    depth = st.sidebar.slider("探索深度", 0, 3, 1)
    
    visualization_type = st.sidebar.selectbox(
        "选择可视化类型",
        ["网络图", "层级树", "关系矩阵", "产业链"]
    )

    if entity_name:
        st.subheader(f"显示 {entity_name} 的 {visualization_type}")
        
        if visualization_type == "网络图":
            success, message = display_network_graph(graph_handler, entity_type, entity_name, depth)
        elif visualization_type == "层级树":
            success, message = display_hierarchy_tree(graph_handler, entity_type, entity_name, depth)
        elif visualization_type == "关系矩阵":
            success, message = display_relationship_matrix(graph_handler, entity_type, entity_name, depth)
        elif visualization_type == "产业链":
            success, message = display_industry_chain(graph_handler, entity_type, entity_name, depth)
        
        if not success:
            st.error(message)
    else:
        st.info("请选择实体类型和名称以开始可视化。")

if __name__ == "__main__":
    main()
