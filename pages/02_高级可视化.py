"""
知识图谱高级可视化页面
"""
import streamlit as st
import streamlit_echarts as st_echarts
import pandas as pd
import numpy as np
from pyvis.network import Network
import streamlit.components.v1 as components
import tempfile
import os
import logging
import traceback
import json
from datetime import datetime

# 导入自定义模块
from utils.db_connector import Neo4jConnector
from utils.data_processor import process_neo4j_results, get_entity_options
from utils.logger import setup_logger
from visualizers.network_viz import display_network, create_echarts_graph

# 设置日志
logger = setup_logger("KG_Advanced_Viz")

# 页面配置
st.set_page_config(
    page_title="知识图谱高级可视化",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS，使界面更紧凑
st.markdown("""
<style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    h1, h2, h3, h4, h5, h6 {
        margin-top: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 30px;
        padding: 5px 10px;
    }
</style>
""", unsafe_allow_html=True)

# 辅助函数：直接渲染ECharts HTML
def render_echarts_html(options, height="700px"):
    """使用HTML直接渲染ECharts图表"""
    try:
        # 确保所有数值字段都是数字类型
        def ensure_numeric(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k in ["symbolSize", "value", "category"]:
                        if isinstance(v, str) and v.isdigit():
                            obj[k] = int(v)
                    else:
                        ensure_numeric(v)
            elif isinstance(obj, list):
                for item in obj:
                    ensure_numeric(item)
            return obj
        
        # 处理数据类型
        options = ensure_numeric(options)
        
        # 转换为JSON字符串
        options_str = json.dumps(options, ensure_ascii=False)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
        </head>
        <body>
            <div id="chart-container" style="width:100%; height:{height};"></div>
            <script>
                var chartDom = document.getElementById('chart-container');
                var myChart = echarts.init(chartDom);
                var options = {options_str};
                
                try {{
                    myChart.setOption(options);
                    
                    // 自适应大小
                    window.addEventListener('resize', function() {{
                        myChart.resize();
                    }});
                }} catch(e) {{
                    console.error("ECharts错误:", e);
                    document.getElementById('chart-container').innerHTML = 
                        '<div style="color:red;padding:20px;">图表渲染错误: ' + e.message + '</div>';
                }}
            </script>
        </body>
        </html>
        """
        
        components.html(html, height=height)
    except Exception as e:
        st.error(f"图表渲染错误: {str(e)}")
        st.code(json.dumps(options, indent=2, ensure_ascii=False), language="json")

# 初始化数据库连接
@st.cache_resource
def get_db_connector():
    """获取数据库连接器（缓存资源）"""
    return Neo4jConnector()

db = get_db_connector()

# 页面标题
st.title("知识图谱高级可视化")

# 创建侧边栏
st.sidebar.header("查询选项")

# 实体类型选择
entity_type_options = {
    "company": "公司",
    "industry": "行业",
    "product": "产品"
}

entity_type = st.sidebar.selectbox(
    "选择实体类型",
    list(entity_type_options.keys()),
    format_func=lambda x: entity_type_options.get(x, x)
)

# 搜索框
search_query = st.sidebar.text_input("搜索实体", placeholder="输入实体名称")

# 获取实体列表
@st.cache_data(ttl=300)
def get_entities_cached(entity_type, search_term=""):
    """缓存实体列表查询结果"""
    return get_entity_options(db, entity_type, search_term)

@st.cache_data(ttl=300)
def get_related_industries(industry_name):
    """获取与指定行业相关的其他行业"""
    query = """
    MATCH (i:industry {name: $name})
    OPTIONAL MATCH (i)-[r]-(related:industry)
    RETURN collect(distinct related) as related_industries
    """
    results = db.query(query, {"name": industry_name})
    if results and "related_industries" in results[0]:
        return results[0]["related_industries"]
    return []

if search_query:
    entities = get_entities_cached(entity_type, search_query)
    if entities:
        selected_entity = st.sidebar.selectbox("选择实体", entities)
    else:
        st.sidebar.warning(f"未找到包含 '{search_query}' 的{entity_type_options.get(entity_type)}实体")
        selected_entity = None
else:
    entities = get_entities_cached(entity_type)
    selected_entity = st.sidebar.selectbox("选择实体", entities) if entities else None

# 深度选择
depth = st.sidebar.slider("关系深度", 1, 3, 1)

# 创建选项卡
tab1, tab2, tab3, tab4 = st.tabs(["网络图", "层级树", "关系矩阵", "产业链"])

# 在每个选项卡中添加初始内容
with tab1:
    st.info("点击左侧的'生成可视化'按钮，查看网络图可视化")
    
with tab2:
    st.info("点击左侧的'生成可视化'按钮，查看层级树可视化（仅支持行业类型）")
    
with tab3:
    if selected_entity:
        # 选择实体后，显示矩阵类型选择
        st.subheader("关系矩阵配置")
        
        # 初始化session state
        if "matrix_type" not in st.session_state:
            st.session_state.matrix_type = "同类型实体矩阵"
        
        # 提供矩阵类型选择
        matrix_type_options = ["同类型实体矩阵", "公司-产品矩阵"]
        matrix_type = st.radio("选择矩阵类型", matrix_type_options, 
                             index=matrix_type_options.index(st.session_state.matrix_type),
                             key="matrix_type_selection")
        
        # 更新session state中的矩阵类型
        st.session_state.matrix_type = matrix_type
        
        st.info("点击左侧的'生成可视化'按钮，查看关系矩阵可视化")
    else:
        st.info("请先选择实体，然后可以配置矩阵类型")
    
with tab4:
    st.info("点击左侧的'生成可视化'按钮，查看产业链可视化（仅支持行业类型）")

# 可视化按钮
if selected_entity and st.sidebar.button("生成可视化", use_container_width=True):
    # 初始化session state
    if "matrix_type" not in st.session_state:
        st.session_state.matrix_type = "同类型实体矩阵"
    
    # 显示标题
    st.header(f"{selected_entity} 知识图谱")
    
    with st.spinner("正在生成知识图谱..."):
        try:
            # 构建查询
            if entity_type == "industry":
                query = f"""
                MATCH (i:{entity_type} {{name: $name}})
                OPTIONAL MATCH (c:company)-[r1:所属行业]->(i)
                OPTIONAL MATCH (c)-[r2:主营产品]->(p:product)
                OPTIONAL MATCH (i)-[r3]-(related:industry)
                RETURN i, collect(distinct c) as companies, 
                       collect(distinct p) as products,
                       collect(distinct related) as related_industries
                """
            elif entity_type == "company":
                query = f"""
                MATCH (c:{entity_type} {{name: $name}})
                OPTIONAL MATCH (c)-[r1:所属行业]->(i:industry)
                OPTIONAL MATCH (c)-[r2:主营产品]->(p:product)
                RETURN c, collect(distinct i) as industries, collect(distinct p) as products
                """
            else:  # product
                query = f"""
                MATCH (p:{entity_type} {{name: $name}})
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
            
            # 执行查询
            logger.info(f"执行查询: {query}")
            results = db.query(query, {"name": selected_entity})
            
            if results:
                # 创建节点和边的列表
                nodes = []
                edges = []
                node_ids = {}
                
                try:
                    # 处理中心实体
                    if entity_type == "industry":
                        if "i" in results[0]:
                            industry = results[0]["i"]
                            industry_id = industry.identity
                            nodes.append({
                                "id": industry_id,
                                "label": industry["name"],
                                "group": 0  # 行业
                            })
                            node_ids[industry_id] = True
                        
                        # 处理相关行业
                        related_industries = results[0].get("related_industries", [])
                        related_industry_names = [selected_entity]  # 包含中心行业
                        
                        for rel_industry in related_industries:
                            if rel_industry and rel_industry.identity != industry_id:  # 避免重复添加中心行业
                                rel_industry_id = rel_industry.identity
                                if rel_industry_id not in node_ids:
                                    nodes.append({
                                        "id": rel_industry_id,
                                        "label": rel_industry["name"],
                                        "group": 0  # 行业
                                    })
                                    node_ids[rel_industry_id] = True
                                    related_industry_names.append(rel_industry["name"])
                                    
                                    # 添加行业间关系边
                                    edges.append({
                                        "from": industry_id,
                                        "to": rel_industry_id,
                                        "label": "相关行业"
                                    })
                        
                        # 查询所有相关行业之间的交叉关系
                        if len(related_industry_names) > 1:
                            cross_relations_query = """
                            MATCH (i1:industry)-[r:相关行业]->(i2:industry)
                            WHERE i1.name IN $industry_names AND i2.name IN $industry_names
                            RETURN i1.name as from_industry, i2.name as to_industry, r.type as relation_type
                            """
                            
                            cross_relations = db.query(cross_relations_query, {"industry_names": related_industry_names})
                            
                            # 创建行业名称到节点ID的映射
                            industry_name_to_id = {}
                            for node in nodes:
                                if node.get("group") == 0:  # 行业节点
                                    industry_name_to_id[node["label"]] = node["id"]
                            
                            # 添加交叉关系边
                            for cross_rel in cross_relations:
                                from_industry = cross_rel["from_industry"]
                                to_industry = cross_rel["to_industry"]
                                
                                # 查找对应的节点ID
                                if from_industry in industry_name_to_id and to_industry in industry_name_to_id:
                                    from_id = industry_name_to_id[from_industry]
                                    to_id = industry_name_to_id[to_industry]
                                    
                                    # 检查是否已经存在这条边（避免重复）
                                    edge_exists = any(
                                        edge["from"] == from_id and edge["to"] == to_id 
                                        for edge in edges
                                    )
                                    
                                    if not edge_exists:
                                        edges.append({
                                            "from": from_id,
                                            "to": to_id,
                                            "label": f"相关行业({cross_rel['relation_type']})"
                                        })
                    
                        # 处理公司
                        companies = results[0].get("companies", [])
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
                                    
                                    # 添加公司->行业的边
                                    edges.append({
                                        "from": company_id,
                                        "to": industry_id,
                                        "label": "所属行业"
                                    })
                        
                        # 处理产品 - 需要重新查询真实的公司-产品关系
                        # 先添加所有产品节点
                        products = results[0].get("products", [])
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
                        
                        # 查询真实的公司-产品关系，使用名称匹配
                        company_product_query = """
                        MATCH (i:industry {name: $industry_name})<-[:所属行业]-(c:company)-[:主营产品]->(p:product)
                        RETURN c.name as company_name, p.name as product_name
                        """
                        
                        cp_results = db.query(company_product_query, {"industry_name": selected_entity})
                        
                        # 创建公司名称和产品名称到节点ID的映射
                        company_name_to_id = {}
                        product_name_to_id = {}
                        
                        for node in nodes:
                            if node.get("group") == 1:  # 公司
                                company_name_to_id[node["label"]] = node["id"]
                            elif node.get("group") == 2:  # 产品
                                product_name_to_id[node["label"]] = node["id"]
                        
                        # 根据真实关系创建边
                        for cp_result in cp_results:
                            company_name = cp_result["company_name"]
                            product_name = cp_result["product_name"]
                            
                            # 查找对应的节点ID
                            if company_name in company_name_to_id and product_name in product_name_to_id:
                                company_id = company_name_to_id[company_name]
                                product_id = product_name_to_id[product_name]
                                
                                edges.append({
                                    "from": company_id,
                                    "to": product_id,
                                    "label": "主营产品"
                                })
                    
                    elif entity_type == "company":
                        if "c" in results[0]:
                            company = results[0]["c"]
                            company_id = company.identity
                            nodes.append({
                                "id": company_id,
                                "label": company["name"],
                                "group": 1  # 公司
                            })
                            node_ids[company_id] = True
                        
                        # 处理行业
                        industries = results[0].get("industries", [])
                        for industry in industries:
                            if industry:
                                industry_id = industry.identity
                                if industry_id not in node_ids:
                                    nodes.append({
                                        "id": industry_id,
                                        "label": industry["name"],
                                        "group": 0  # 行业
                                    })
                                    node_ids[industry_id] = True
                                    
                                    # 添加公司->行业的边
                                    edges.append({
                                        "from": company_id,
                                        "to": industry_id,
                                        "label": "所属行业"
                                    })
                        
                        # 处理产品
                        products = results[0].get("products", [])
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
                                    
                                    # 添加公司->产品的边
                                    edges.append({
                                        "from": company_id,
                                        "to": product_id,
                                        "label": "主营产品"
                                    })
                    
                    else:  # product
                        if "p" in results[0]:
                            product = results[0]["p"]
                            product_id = product.identity
                            nodes.append({
                                "id": product_id,
                                "label": product["name"],
                                "group": 2  # 产品
                            })
                            node_ids[product_id] = True
                        
                        # 处理公司
                        companies = results[0].get("companies", [])
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
                                    
                                    # 添加公司->产品的边
                                    edges.append({
                                        "from": company_id,
                                        "to": product_id,
                                        "label": "主营产品"
                                    })
                        
                        # 处理上游产品
                        upstream_products = results[0].get("upstream_products", [])
                        for upstream in upstream_products:
                            if upstream:
                                upstream_id = upstream.identity
                                if upstream_id not in node_ids:
                                    nodes.append({
                                        "id": upstream_id,
                                        "label": upstream["name"],
                                        "group": 2  # 产品
                                    })
                                    node_ids[upstream_id] = True
                                    
                                    # 添加产品->上游产品的边
                                    edges.append({
                                        "from": product_id,
                                        "to": upstream_id,
                                        "label": "上游材料"
                                    })
                        
                        # 处理子产品（属于该类别的具体产品）
                        child_products = results[0].get("child_products", [])
                        for child in child_products:
                            if child:
                                child_id = child.identity
                                if child_id not in node_ids:
                                    nodes.append({
                                        "id": child_id,
                                        "label": child["name"],
                                        "group": 2  # 产品
                                    })
                                    node_ids[child_id] = True
                                    
                                    # 添加子产品->父产品的边
                                    edges.append({
                                        "from": child_id,
                                        "to": product_id,
                                        "label": "属于类别"
                                    })
                        
                        # 处理父产品（该产品所属的类别）
                        parent_products = results[0].get("parent_products", [])
                        for parent in parent_products:
                            if parent:
                                parent_id = parent.identity
                                if parent_id not in node_ids:
                                    nodes.append({
                                        "id": parent_id,
                                        "label": parent["name"],
                                        "group": 2  # 产品
                                    })
                                    node_ids[parent_id] = True
                                    
                                    # 添加产品->父产品的边
                                    edges.append({
                                        "from": product_id,
                                        "to": parent_id,
                                        "label": "属于类别"
                                    })
                        
                        # 处理相关产品（有产品关系的产品）
                        related_products = results[0].get("related_products", [])
                        for related in related_products:
                            if related:
                                related_id = related.identity
                                if related_id not in node_ids:
                                    nodes.append({
                                        "id": related_id,
                                        "label": related["name"],
                                        "group": 2  # 产品
                                    })
                                    node_ids[related_id] = True
                        
                        # 查询具体的产品关系
                        if len(nodes) > 1:  # 如果有多个产品节点
                            product_names = [node["label"] for node in nodes if node.get("group") == 2]
                            
                            product_relations_query = """
                            MATCH (p1:product)-[r:产品关系]->(p2:product)
                            WHERE p1.name IN $product_names AND p2.name IN $product_names
                            RETURN p1.name as from_product, p2.name as to_product, r.type as relation_type
                            """
                            
                            product_relations = db.query(product_relations_query, {"product_names": product_names})
                            
                            # 创建产品名称到节点ID的映射
                            product_name_to_id = {}
                            for node in nodes:
                                if node.get("group") == 2:  # 产品节点
                                    product_name_to_id[node["label"]] = node["id"]
                            
                            # 添加产品关系边
                            for prod_rel in product_relations:
                                from_product = prod_rel["from_product"]
                                to_product = prod_rel["to_product"]
                                
                                if from_product in product_name_to_id and to_product in product_name_to_id:
                                    from_id = product_name_to_id[from_product]
                                    to_id = product_name_to_id[to_product]
                                    
                                    # 检查是否已经存在这条边
                                    edge_exists = any(
                                        edge["from"] == from_id and edge["to"] == to_id 
                                        for edge in edges
                                    )
                                    
                                    if not edge_exists:
                                        edges.append({
                                            "from": from_id,
                                            "to": to_id,
                                            "label": f"产品关系({prod_rel['relation_type']})"
                                        })
                
                except Exception as e:
                    logger.error(f"处理查询结果时出错: {str(e)}")
                    logger.error(traceback.format_exc())
                    st.error(f"处理查询结果时出错: {str(e)}")
                
                # 显示节点和边的数量
                st.info(f"找到 {len(nodes)} 个节点和 {len(edges)} 条关系")
                
                # 添加调试信息：显示边的类型统计
                edge_types = {}
                for edge in edges:
                    edge_type = edge.get("label", "未知")
                    edge_types[edge_type] = edge_types.get(edge_type, 0) + 1
                
                st.write("关系类型统计:")
                for edge_type, count in edge_types.items():
                    st.write(f"  - {edge_type}: {count}条")
                
                # 显示行业间关系的详细信息
                industry_edges = [edge for edge in edges if "相关行业" in edge.get("label", "")]
                if industry_edges:
                    st.write(f"\n行业间关系 ({len(industry_edges)}条):")
                    for i, edge in enumerate(industry_edges[:10]):  # 显示前10条
                        source_node = next((node for node in nodes if node["id"] == edge["from"]), None)
                        target_node = next((node for node in nodes if node["id"] == edge["to"]), None)
                        if source_node and target_node:
                            st.write(f"  {i+1}. {source_node['label']} -> {target_node['label']} ({edge['label']})")
                
                # 在不同选项卡中显示不同的可视化
                if nodes and edges:
                    # 网络图选项卡
                    with tab1:
                        if display_network(nodes, edges, f"{selected_entity} 知识图谱"):
                            st.success(f"成功生成 {selected_entity} 的网络图")
                        else:
                            st.error("生成网络图失败")
                    
                    # 层级树选项卡
                    with tab2:
                        try:
                            # 构建层级树数据
                            if entity_type == "industry":
                                # 构建层级树查询
                                tree_query = f"""
                                MATCH (i:industry {{name: $name}})
                                OPTIONAL MATCH (sub:industry)-[:上级行业]->(i)
                                OPTIONAL MATCH (c:company)-[:所属行业]->(i)
                                OPTIONAL MATCH (c2:company)-[:所属行业]->(sub)
                                RETURN i, collect(distinct sub) as sub_industries, 
                                       collect(distinct c) as direct_companies,
                                       collect(distinct c2) as sub_companies
                                """
                                
                                tree_results = db.query(tree_query, {"name": selected_entity})
                                
                                if tree_results:
                                    # 获取查询结果中的数据
                                    sub_industries = tree_results[0].get("sub_industries", [])
                                    direct_companies = tree_results[0].get("direct_companies", [])
                                    sub_companies = tree_results[0].get("sub_companies", [])
                                    
                                    # 使用Streamlit原生组件构建层级树
                                    st.subheader("行业层级结构")
                                    
                                    # 构建简单的树形结构
                                    tree_data = {}
                                    
                                    # 添加根节点（选中的行业）
                                    tree_data[selected_entity] = {"子行业": {}, "直属公司": []}
                                    
                                    # 添加子行业
                                    for sub in sub_industries:
                                        if sub and sub["name"] != selected_entity:
                                            tree_data[selected_entity]["子行业"][sub["name"]] = {"直属公司": []}
                                    
                                    # 添加直属公司
                                    for company in direct_companies:
                                        if company:
                                            tree_data[selected_entity]["直属公司"].append(company["name"])
                                    
                                    # 添加子行业的公司
                                    for company in sub_companies:
                                        if company:
                                            # 查找该公司属于哪个子行业
                                            for sub in sub_industries:
                                                if sub:
                                                    rel_query = """
                                                    MATCH (c:company {name: $company_name})-[r:所属行业]->(i:industry {name: $industry_name})
                                                    RETURN count(r) > 0 as has_relationship
                                                    """
                                                    rel_result = db.query(rel_query, {
                                                        "company_name": company["name"],
                                                        "industry_name": sub["name"]
                                                    })
                                                    
                                                    if rel_result and rel_result[0]["has_relationship"]:
                                                        if sub["name"] in tree_data[selected_entity]["子行业"]:
                                                            tree_data[selected_entity]["子行业"][sub["name"]]["直属公司"].append(company["name"])
                                    
                                    # 显示树形结构
                                    st.json(tree_data, expanded=True)
                                    
                                    # 创建可视化表示
                                    st.subheader("层级树可视化")
                                    
                                    # 使用Markdown创建简单的树形图
                                    md_tree = f"### {selected_entity}\n"
                                    
                                    # 添加子行业
                                    if tree_data[selected_entity]["子行业"]:
                                        md_tree += "\n#### 子行业\n"
                                        for sub_name, sub_data in tree_data[selected_entity]["子行业"].items():
                                            md_tree += f"- **{sub_name}**\n"
                                            if sub_data["直属公司"]:
                                                md_tree += "  - 直属公司:\n"
                                                for company in sub_data["直属公司"]:
                                                    md_tree += f"    - {company}\n"
                                    
                                    # 添加直属公司
                                    if tree_data[selected_entity]["直属公司"]:
                                        md_tree += "\n#### 直属公司:\n"
                                        for company in tree_data[selected_entity]["直属公司"]:
                                            md_tree += f"- {company}\n"
                                    
                                    st.markdown(md_tree)
                                    st.success(f"成功生成 {selected_entity} 的层级树")
                                else:
                                    st.warning("没有找到层级树数据")
                            else:
                                st.info("层级树可视化仅支持行业类型的实体")
                        except Exception as e:
                            st.error(f"生成层级树时出错: {str(e)}")
                            logger.error(f"生成层级树时出错: {str(e)}\n{traceback.format_exc()}")
                    
                    # 关系矩阵选项卡
                    with tab3:
                        try:
                            # 使用session state中保存的矩阵类型
                            if "matrix_type" not in st.session_state:
                                st.session_state.matrix_type = "同类型实体矩阵"
                            matrix_type = st.session_state.matrix_type
                            
                            # 显示当前选择的矩阵类型
                            st.info(f"当前矩阵类型: {matrix_type}")
                            
                            # 按实体类型对节点进行分组
                            node_types = {}
                            for node in nodes:
                                # 获取节点类型
                                node_type = node.get("group", 0)
                                if node_type not in node_types:
                                    node_types[node_type] = []
                                node_types[node_type].append(node)
                            
                            matrix = None
                            matrix_nodes = None
                            matrix_nodes_x = None
                            matrix_nodes_y = None
                            
                            if matrix_type == "同类型实体矩阵":
                                # 让用户选择要显示的实体类型
                                type_names = {0: "行业", 1: "公司", 2: "产品"}
                                available_types = [type_names.get(t, f"类型{t}") for t in node_types.keys()]
                                
                                if not available_types:
                                    st.warning("没有足够的节点来创建矩阵")
                                else:
                                    selected_type = st.selectbox("选择实体类型", available_types)
                                    
                                    # 获取选择的类型索引
                                    selected_type_idx = list(type_names.values()).index(selected_type) if selected_type in type_names.values() else 0
                                    
                                    # 获取该类型的所有节点
                                    if selected_type_idx not in node_types or len(node_types[selected_type_idx]) < 2:
                                        st.warning(f"没有足够的{selected_type}节点来创建矩阵")
                                    else:
                                        type_nodes = node_types[selected_type_idx]
                                        matrix_nodes = [node["label"] for node in type_nodes]
                                        
                                        # 创建矩阵
                                        matrix = np.zeros((len(matrix_nodes), len(matrix_nodes)))
                                        
                                        # 节点标签到索引的映射
                                        node_label_to_index = {node["label"]: i for i, node in enumerate(type_nodes)}
                                        
                                        # 填充矩阵
                                        for edge in edges:
                                            source_node = next((node for node in nodes if node["id"] == edge["from"]), None)
                                            target_node = next((node for node in nodes if node["id"] == edge["to"]), None)
                                            
                                            # 确保两个节点都是所选类型
                                            if (source_node and target_node and 
                                                source_node.get("group", 0) == selected_type_idx and 
                                                target_node.get("group", 0) == selected_type_idx):
                                                
                                                source_label = source_node["label"]
                                                target_label = target_node["label"]
                                                
                                                if source_label in node_label_to_index and target_label in node_label_to_index:
                                                    source_idx = node_label_to_index[source_label]
                                                    target_idx = node_label_to_index[target_label]
                                                    matrix[source_idx][target_idx] = 1
                            
                            elif matrix_type == "公司-产品矩阵":
                                # 确保有公司和产品节点
                                if 1 not in node_types or 2 not in node_types:
                                    st.warning("没有足够的公司和产品节点来创建矩阵")
                                else:
                                    # 获取公司和产品节点
                                    company_nodes = node_types[1]
                                    product_nodes = node_types[2]
                                    
                                    # 显示数据统计信息
                                    st.info(f"发现 {len(company_nodes)} 个公司和 {len(product_nodes)} 个产品")
                                    
                                    # 如果产品数量过多，提供选项来限制显示
                                    max_products = 50  # 最大显示产品数量
                                    if len(product_nodes) > max_products:
                                        st.warning(f"产品数量过多（{len(product_nodes)}个），为了更好的显示效果，将只显示前{max_products}个产品")
                                        
                                        # 按产品名称排序，选择前N个
                                        product_nodes_sorted = sorted(product_nodes, key=lambda x: x["label"])
                                        product_nodes = product_nodes_sorted[:max_products]
                                    
                                    # 创建矩阵
                                    matrix = np.zeros((len(company_nodes), len(product_nodes)))
                                    
                                    # 公司和产品标签到索引的映射
                                    company_label_to_index = {node["label"]: i for i, node in enumerate(company_nodes)}
                                    product_label_to_index = {node["label"]: i for i, node in enumerate(product_nodes)}
                                    
                                    # 填充矩阵
                                    relations_found = 0
                                    company_product_pairs = []
                                    
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
                                                    company_product_pairs.append(f"{source_label} -> {target_label}")
                                    
                                    st.info(f"在矩阵中找到 {relations_found} 个公司-产品关系")
                                    
                                    # 显示前几个关系作为调试信息
                                    if company_product_pairs:
                                        st.write("示例关系:")
                                        for pair in company_product_pairs[:10]:  # 显示前10个关系
                                            st.write(f"  - {pair}")
                                    
                                    # 显示矩阵统计信息
                                    total_cells = len(company_nodes) * len(product_nodes)
                                    filled_cells = np.sum(matrix > 0)
                                    st.write(f"矩阵统计: {filled_cells}/{total_cells} 个位置有关系 ({filled_cells/total_cells*100:.1f}%)")
                                    
                                    # 设置矩阵节点标签
                                    matrix_nodes_x = [node["label"] for node in product_nodes]
                                    matrix_nodes_y = [node["label"] for node in company_nodes]
                            
                            # 显示矩阵图
                            if matrix is not None:
                                import matplotlib.pyplot as plt
                                import matplotlib
                                from matplotlib.patches import Rectangle
                                
                                # 设置中文字体支持
                                plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
                                plt.rcParams['axes.unicode_minus'] = False
                                
                                # 创建图表
                                fig, ax = plt.subplots(figsize=(12, 10))
                                
                                if matrix_type == "同类型实体矩阵":
                                    im = ax.imshow(matrix, cmap="Blues")
                                    
                                    # 设置坐标轴标签
                                    ax.set_xticks(np.arange(len(matrix_nodes)))
                                    ax.set_yticks(np.arange(len(matrix_nodes)))
                                    ax.set_xticklabels(matrix_nodes, fontsize=10)
                                    ax.set_yticklabels(matrix_nodes, fontsize=10)
                                    
                                    # 添加标题
                                    ax.set_title(f"{selected_entity} {selected_type}关系矩阵", fontsize=14)
                                    
                                    # 在矩阵中添加文本标签
                                    for i in range(len(matrix_nodes)):
                                        for j in range(len(matrix_nodes)):
                                            if matrix[i, j] > 0:
                                                ax.text(j, i, "●", ha="center", va="center", color="white", fontsize=12)
                                
                                elif matrix_type == "公司-产品矩阵":
                                    im = ax.imshow(matrix, cmap="Blues")
                                    
                                    # 根据产品数量动态调整字体大小和图表大小
                                    num_products = len(matrix_nodes_x)
                                    num_companies = len(matrix_nodes_y)
                                    
                                    # 动态调整字体大小
                                    if num_products > 30:
                                        x_fontsize = 6
                                    elif num_products > 20:
                                        x_fontsize = 8
                                    else:
                                        x_fontsize = 10
                                    
                                    if num_companies > 20:
                                        y_fontsize = 8
                                    else:
                                        y_fontsize = 10
                                    
                                    # 设置坐标轴标签
                                    ax.set_xticks(np.arange(len(matrix_nodes_x)))
                                    ax.set_yticks(np.arange(len(matrix_nodes_y)))
                                    ax.set_xticklabels(matrix_nodes_x, fontsize=x_fontsize)
                                    ax.set_yticklabels(matrix_nodes_y, fontsize=y_fontsize)
                                    
                                    # 添加标题
                                    ax.set_title(f"{selected_entity} 公司-产品关系矩阵 ({num_companies}×{num_products})", fontsize=14)
                                    
                                    # 在矩阵中添加文本标签
                                    for i in range(len(matrix_nodes_y)):
                                        for j in range(len(matrix_nodes_x)):
                                            if matrix[i, j] > 0:
                                                # 使用更明显的标记和颜色
                                                ax.text(j, i, "●", ha="center", va="center", color="darkred", fontsize=14, weight="bold")
                                                # 也可以添加背景色
                                                ax.add_patch(plt.Rectangle((j-0.4, i-0.4), 0.8, 0.8, fill=True, color='lightcoral', alpha=0.3))
                                
                                # 旋转X轴标签
                                plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
                                
                                # 添加网格线
                                if matrix_type == "同类型实体矩阵":
                                    ax.set_xticks(np.arange(-.5, len(matrix_nodes), 1), minor=True)
                                    ax.set_yticks(np.arange(-.5, len(matrix_nodes), 1), minor=True)
                                else:
                                    ax.set_xticks(np.arange(-.5, len(matrix_nodes_x), 1), minor=True)
                                    ax.set_yticks(np.arange(-.5, len(matrix_nodes_y), 1), minor=True)
                                ax.grid(which="minor", color="w", linestyle='-', linewidth=1)
                                
                                # 调整布局
                                plt.tight_layout()
                                
                                # 显示图形
                                st.pyplot(fig)
                                st.success(f"成功生成 {selected_entity} 的关系矩阵")
                        except Exception as e:
                            st.error(f"生成关系矩阵时出错: {str(e)}")
                            logger.error(f"生成关系矩阵时出错: {str(e)}\n{traceback.format_exc()}")
                    
                    # 产业链选项卡
                    with tab4:
                        try:
                            # 构建产业链数据
                            if entity_type == "industry":
                                # 构建产业链查询
                                chain_query = f"""
                                MATCH (i:industry {{name: $name}})
                                OPTIONAL MATCH (c:company)-[:所属行业]->(i)
                                OPTIONAL MATCH (c)-[:主营产品]->(p:product)
                                OPTIONAL MATCH (p)-[:上游材料]->(up:product)
                                RETURN i, collect(distinct c) as companies, 
                                       collect(distinct p) as products,
                                       collect(distinct up) as upstream_products
                                """
                                
                                chain_results = db.query(chain_query, {"name": selected_entity})
                                
                                if chain_results:
                                    # 使用Pyvis库创建产业链可视化
                                    st.subheader("产业链可视化")
                                    
                                    # 创建Pyvis网络图
                                    net = Network(height="700px", width="100%", bgcolor="#ffffff", font_color="black")
                                    
                                    # 添加节点
                                    # 添加行业节点
                                    net.add_node(selected_entity, label=selected_entity, title=selected_entity, 
                                                color="#5470c6", size=30, group=1)
                                    
                                    # 添加公司节点
                                    companies = chain_results[0].get("companies", [])
                                    for company in companies:
                                        if company:
                                            company_name = company["name"]
                                            net.add_node(company_name, label=company_name, title=company_name,
                                                        color="#91cc75", size=25, group=2)
                                            net.add_edge(company_name, selected_entity, title="所属行业")
                                    
                                    # 添加产品节点
                                    products = chain_results[0].get("products", [])
                                    for product in products:
                                        if product:
                                            product_name = product["name"]
                                            net.add_node(product_name, label=product_name, title=product_name,
                                                        color="#fac858", size=20, group=3)
                                            
                                            # 找到关联的公司
                                            for company in companies:
                                                if company:
                                                    # 查询公司和产品的关系
                                                    rel_query = """
                                                    MATCH (c:company {name: $company_name})-[r:主营产品]->(p:product {name: $product_name})
                                                    RETURN count(r) > 0 as has_relationship
                                                    """
                                                    rel_result = db.query(rel_query, {
                                                        "company_name": company["name"],
                                                        "product_name": product_name
                                                    })
                                                    
                                                    if rel_result and rel_result[0]["has_relationship"]:
                                                        net.add_edge(company["name"], product_name, title="主营产品")
                                    
                                    # 添加上游产品节点
                                    upstream_products = chain_results[0].get("upstream_products", [])
                                    for upstream in upstream_products:
                                        if upstream:
                                            upstream_name = upstream["name"]
                                            net.add_node(upstream_name, label=upstream_name, title=upstream_name,
                                                        color="#ee6666", size=15, group=4)
                                            
                                            # 找到关联的产品
                                            for product in products:
                                                if product:
                                                    # 查询产品和上游产品的关系
                                                    rel_query = """
                                                    MATCH (p:product {name: $product_name})-[r:上游材料]->(up:product {name: $upstream_name})
                                                    RETURN count(r) > 0 as has_relationship
                                                    """
                                                    rel_result = db.query(rel_query, {
                                                        "product_name": product["name"],
                                                        "upstream_name": upstream_name
                                                    })
                                                    
                                                    if rel_result and rel_result[0]["has_relationship"]:
                                                        net.add_edge(product["name"], upstream_name, title="上游材料")
                                    
                                    # 设置网络图选项
                                    net.toggle_physics(True)
                                    net.set_options("""
                                    var options = {
                                      "physics": {
                                        "forceAtlas2Based": {
                                          "gravitationalConstant": -50,
                                          "centralGravity": 0.01,
                                          "springLength": 100,
                                          "springConstant": 0.08
                                        },
                                        "minVelocity": 0.75,
                                        "solver": "forceAtlas2Based"
                                      }
                                    }
                                    """)
                                    
                                    # 保存到临时文件并显示
                                    try:
                                        with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmpfile:
                                            temp_path = tmpfile.name
                                            net.save_graph(temp_path)
                                            
                                        with open(temp_path, 'r', encoding='utf-8') as f:
                                            html_content = f.read()
                                            
                                        components.html(html_content, height=700)
                                        st.success(f"成功生成 {selected_entity} 的产业链")
                                        
                                        # 删除临时文件
                                        try:
                                            os.unlink(temp_path)
                                        except:
                                            pass
                                    except Exception as e:
                                        st.error(f"渲染产业链图表时出错: {str(e)}")
                                        logger.error(f"渲染产业链图表时出错: {str(e)}\n{traceback.format_exc()}")
                                else:
                                    st.warning("没有找到产业链数据")
                            else:
                                st.info("产业链可视化仅支持行业类型的实体")
                        except Exception as e:
                            st.error(f"生成产业链时出错: {str(e)}")
                            logger.error(f"生成产业链时出错: {str(e)}\n{traceback.format_exc()}")
                else:
                    st.warning(f"没有找到与 {selected_entity} 相关的节点和关系")
            else:
                st.warning(f"没有找到与 {selected_entity} 相关的数据")
        except Exception as e:
            st.error(f"生成可视化时出错: {str(e)}")
            logger.error(f"生成可视化时出错: {str(e)}\n{traceback.format_exc()}")
else:
    # 显示使用说明
    st.info("请在左侧选择实体并点击'生成可视化'按钮来查看高级知识图谱可视化")
    
    # 显示示例图片
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("网络图示例")
        st.image("img/1.png", caption="知识图谱网络图示例", use_container_width=True)
    
    with col2:
        st.subheader("层级树示例")
        st.image("img/2.png", caption="知识图谱层级树示例", use_container_width=True)

# 页脚
st.markdown("---")
st.caption(f"知识图谱高级可视化 | {datetime.now().strftime('%Y-%m-%d')}")