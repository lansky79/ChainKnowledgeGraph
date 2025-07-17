"""
知识图谱可视化应用主入口
"""
import streamlit as st
import logging
import os
import sys
import traceback
from datetime import datetime

# 导入自定义模块
from utils.db_connector import Neo4jConnector
from utils.data_processor import process_neo4j_results, get_entity_options
from utils.logger import setup_logger
from visualizers.network_viz import display_network, create_echarts_graph
from config import APP_CONFIG

# 设置日志
logger = setup_logger("KnowledgeGraph")

# 页面配置
st.set_page_config(
    page_title="知识图谱主页",
    page_icon="🏠",
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

# 初始化数据库连接
@st.cache_resource
def get_db_connector():
    """获取数据库连接器（缓存资源）"""
    return Neo4jConnector()

db = get_db_connector()

# 应用标题
st.title("知识图谱可视化")

# 创建侧边栏
st.sidebar.header("查询选项")

# 添加示例数据导入功能
if st.sidebar.button("导入示例数据", help="导入包括阿里巴巴、华为等公司的示例数据"):
    with st.spinner("正在导入示例数据..."):
        try:
            # 定义示例数据
            company_data = [
                {"name": "阿里巴巴", "description": "中国领先的电子商务公司"},
                {"name": "腾讯", "description": "中国领先的互联网服务提供商"},
                {"name": "百度", "description": "中国领先的搜索引擎公司"},
                {"name": "华为", "description": "全球领先的通信设备制造商"},
                {"name": "小米", "description": "中国领先的智能手机制造商"}
            ]
            industry_data = [
                {"name": "互联网", "description": "互联网行业"},
                {"name": "电子商务", "description": "电子商务行业"},
                {"name": "人工智能", "description": "人工智能行业"},
                {"name": "通信", "description": "通信行业"},
                {"name": "智能硬件", "description": "智能硬件行业"}
            ]
            product_data = [
                {"name": "淘宝", "description": "阿里巴巴旗下电子商务平台"},
                {"name": "微信", "description": "腾讯旗下社交通讯软件"},
                {"name": "百度搜索", "description": "百度旗下搜索引擎"},
                {"name": "华为手机", "description": "华为生产的智能手机"},
                {"name": "小米手机", "description": "小米生产的智能手机"}
            ]
            
            # 清除现有数据
            db.query("MATCH (n) DETACH DELETE n")
            
            # 导入公司节点
            for company in company_data:
                db.query(
                    "CREATE (c:company {name: $name, description: $description})",
                    {"name": company["name"], "description": company["description"]}
                )
            
            # 导入行业节点
            for industry in industry_data:
                db.query(
                    "CREATE (i:industry {name: $name, description: $description})",
                    {"name": industry["name"], "description": industry["description"]}
                )
            
            # 导入产品节点
            for product in product_data:
                db.query(
                    "CREATE (p:product {name: $name, description: $description})",
                    {"name": product["name"], "description": product["description"]}
                )
            
            # 创建公司-行业关系
            relationships = [
                ("阿里巴巴", "互联网"), ("阿里巴巴", "电子商务"),
                ("腾讯", "互联网"), ("百度", "互联网"),
                ("百度", "人工智能"), ("华为", "通信"),
                ("华为", "智能硬件"), ("小米", "智能硬件")
            ]
            
            for rel in relationships:
                db.query(
                    "MATCH (c:company {name: $company}), (i:industry {name: $industry}) "
                    "CREATE (c)-[:所属行业]->(i)",
                    {"company": rel[0], "industry": rel[1]}
                )
            
            # 创建公司-产品关系
            product_rels = [
                ("阿里巴巴", "淘宝"), ("腾讯", "微信"),
                ("百度", "百度搜索"), ("华为", "华为手机"),
                ("小米", "小米手机")
            ]
            
            for rel in product_rels:
                db.query(
                    "MATCH (c:company {name: $company}), (p:product {name: $product}) "
                    "CREATE (c)-[:主营产品]->(p)",
                    {"company": rel[0], "product": rel[1]}
                )
            
            # 创建产品-产品关系（上游材料）
            upstream_rels = [
                ("华为手机", "微信"), ("小米手机", "微信")
            ]
            
            for rel in upstream_rels:
                db.query(
                    "MATCH (p1:product {name: $product1}), (p2:product {name: $product2}) "
                    "CREATE (p1)-[:上游材料]->(p2)",
                    {"product1": rel[0], "product2": rel[1]}
                )
            
            # 创建行业-行业关系
            industry_rels = [
                ("电子商务", "互联网"), ("人工智能", "互联网")
            ]
            
            for rel in industry_rels:
                db.query(
                    "MATCH (i1:industry {name: $industry1}), (i2:industry {name: $industry2}) "
                    "CREATE (i1)-[:上级行业]->(i2)",
                    {"industry1": rel[0], "industry2": rel[1]}
                )
            
            st.sidebar.success("示例数据导入成功！")
            # 刷新缓存
            st.cache_data.clear()
        except Exception as e:
            st.sidebar.error(f"导入示例数据失败: {str(e)}")
            logger.error(f"导入示例数据失败: {str(e)}\n{traceback.format_exc()}")

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

# 可视化类型选择
viz_type = st.sidebar.radio(
    "可视化类型",
    ["交互式网络图", "ECharts网络图"]
)

# 可视化按钮
if selected_entity and st.sidebar.button("生成可视化", use_container_width=True):
    # 显示标题
    st.header(f"{selected_entity} 知识图谱")
    
    with st.spinner("正在生成知识图谱..."):
        try:
            # 构建查询
            if entity_type == "industry":
                query = f"""
                MATCH (i:{entity_type} {{name: $name}})<-[r1:所属行业]-(c:company)
                OPTIONAL MATCH (c)-[r2:主营产品]->(p:product)
                RETURN i, collect(distinct c) as companies, collect(distinct p) as products
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
                RETURN p, collect(distinct c) as companies, collect(distinct up) as upstream_products
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
                                
                                # 找到关联的公司
                                for company in companies:
                                    if company:
                                        company_id = company.identity
                                        # 添加公司->产品的边
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
                
                except Exception as e:
                    logger.error(f"处理查询结果时出错: {str(e)}")
                    logger.error(traceback.format_exc())
                    st.error(f"处理查询结果时出错: {str(e)}")
                
                # 显示节点和边的数量
                st.info(f"找到 {len(nodes)} 个节点和 {len(edges)} 条关系")
                
                # 显示网络图
                if nodes and edges:
                    if viz_type == "交互式网络图":
                        if display_network(nodes, edges, f"{selected_entity} 知识图谱"):
                            st.success(f"成功生成 {selected_entity} 的知识图谱")
                        else:
                            st.error("生成网络图失败")
                    else:  # ECharts网络图
                        try:
                            import streamlit_echarts as st_echarts
                            options = create_echarts_graph(nodes, edges, f"{selected_entity} 知识图谱")
                            if options:
                                st_echarts.st_echarts(options=options, height="600px")
                                st.success(f"成功生成 {selected_entity} 的知识图谱")
                            else:
                                st.error("生成ECharts图表失败")
                        except ImportError:
                            st.error("未安装streamlit_echarts库，请使用交互式网络图或安装该库")
                else:
                    st.warning(f"没有找到与 {selected_entity} 相关的节点和关系")
            else:
                st.warning(f"没有找到与 {selected_entity} 相关的数据")
        except Exception as e:
            st.error(f"生成可视化时出错: {str(e)}")
            logger.error(f"生成可视化时出错: {str(e)}\n{traceback.format_exc()}")
else:
    # 显示数据库状态
    st.subheader("数据库状态")
    
    try:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            company_count = db.get_node_count("company")
            st.metric("公司节点数量", company_count)
        
        with col2:
            industry_count = db.get_node_count("industry")
            st.metric("行业节点数量", industry_count)
        
        with col3:
            product_count = db.get_node_count("product")
            st.metric("产品节点数量", product_count)
        
        # 显示系统介绍
        st.markdown("""
        ## 知识图谱可视化系统
        
        本系统提供了知识图谱的可视化功能，包括：
        
        1. **基础网络图可视化**：在当前页面可以查看实体的基本关系网络图
        2. **数据导入**：在"数据导入"页面可以导入自定义数据
        3. **高级可视化**：在"高级可视化"页面可以查看更多可视化类型，如层级树、关系矩阵、产业链等
        
        ### 使用方法
        
        1. 在左侧选择实体类型（公司、行业、产品）
        2. 搜索并选择具体实体
        3. 点击"生成可视化"按钮查看知识图谱
        
        ### 示例数据
        
        可以点击左侧的"导入示例数据"按钮导入包括阿里巴巴、华为等公司的示例数据。
        """)
        
        # 显示功能导航
        st.subheader("功能导航")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.info("📊 [数据导入](/数据导入) - 导入自定义知识图谱数据")
        
        with col2:
            st.info("🔍 [高级可视化](/高级可视化) - 查看更多可视化类型")
        
    except Exception as e:
        st.error(f"获取数据库状态时出错: {str(e)}")
        logger.error(f"获取数据库状态时出错: {str(e)}")

# 页脚
st.markdown("---")
st.caption(f"知识图谱可视化系统 | {datetime.now().strftime('%Y-%m-%d')}")

if __name__ == "__main__":
    logger.info("应用启动") 