"""
知识图谱数据管理页面
提供数据导入、导出、查看等功能
"""
import streamlit as st
import pandas as pd
import numpy as np
import os
import json
import traceback
import logging
import sys
from datetime import datetime
from utils.db_connector import Neo4jConnector
from utils.export_handler import ExportHandler
from utils.analytics import Analytics
from utils.logger import setup_logger
import time

# 设置日志
logger = setup_logger("KG_Data_Management")

# 页面配置
st.set_page_config(
    page_title="数据管理",
    page_icon="📊",
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
    .export-section {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# 页面标题
st.title("📊 数据管理")

# 初始化组件
@st.cache_resource
def get_components():
    """获取组件实例（缓存资源）"""
    db = Neo4jConnector()
    return {
        "db": db,
        "export_handler": ExportHandler(db),
        "analytics": Analytics(db)
    }

components = get_components()
db = components["db"]
export_handler = components["export_handler"]
analytics = components["analytics"]

# 创建选项卡
tab1, tab2, tab3, tab4 = st.tabs(["数据导入", "数据导出", "数据查看", "示例数据"])

# 数据导入选项卡
with tab1:
    st.header("📥 导入数据到知识图谱")
    
    # 文件上传部分
    st.subheader("上传数据文件")
    
    col1, col2 = st.columns(2)
    
    with col1:
        company_file = st.file_uploader("上传公司数据 (JSON格式)", type=["json"], key="company_file")
        industry_file = st.file_uploader("上传行业数据 (JSON格式)", type=["json"], key="industry_file")
        product_file = st.file_uploader("上传产品数据 (JSON格式)", type=["json"], key="product_file")
    
    with col2:
        company_industry_file = st.file_uploader("上传公司-行业关系数据 (JSON格式)", type=["json"], key="company_industry_file")
        company_product_file = st.file_uploader("上传公司-产品关系数据 (JSON格式)", type=["json"], key="company_product_file")
        industry_industry_file = st.file_uploader("上传行业-行业关系数据 (JSON格式)", type=["json"], key="industry_industry_file")
    
    # 导入按钮
    if st.button("📥 导入数据", key="import_button"):
        with st.spinner("正在导入数据..."):
            try:
                # 导入节点数据
                nodes_imported = 0
                relationships_imported = 0
                
                # 导入公司数据
                if company_file:
                    company_data = json.load(company_file)
                    st.info(f"正在导入 {len(company_data)} 个公司节点...")
                    
                    for company in company_data:
                        db.query(
                            "MERGE (c:company {name: $name}) "
                            "ON CREATE SET c.description = $description",
                            {"name": company["name"], "description": company.get("description", "")}
                        )
                    
                    nodes_imported += len(company_data)
                
                # 导入行业数据
                if industry_file:
                    industry_data = json.load(industry_file)
                    st.info(f"正在导入 {len(industry_data)} 个行业节点...")
                    
                    for industry in industry_data:
                        db.query(
                            "MERGE (i:industry {name: $name}) "
                            "ON CREATE SET i.description = $description",
                            {"name": industry["name"], "description": industry.get("description", "")}
                        )
                    
                    nodes_imported += len(industry_data)
                
                # 导入产品数据
                if product_file:
                    product_data = json.load(product_file)
                    st.info(f"正在导入 {len(product_data)} 个产品节点...")
                    
                    for product in product_data:
                        db.query(
                            "MERGE (p:product {name: $name}) "
                            "ON CREATE SET p.description = $description",
                            {"name": product["name"], "description": product.get("description", "")}
                        )
                    
                    nodes_imported += len(product_data)
                
                # 导入关系数据
                # 导入公司-行业关系
                if company_industry_file:
                    company_industry_data = json.load(company_industry_file)
                    st.info(f"正在导入 {len(company_industry_data)} 个公司-行业关系...")
                    
                    for rel in company_industry_data:
                        db.query(
                            "MATCH (c:company {name: $company_name}), (i:industry {name: $industry_name}) "
                            "MERGE (c)-[r:所属行业]->(i)",
                            {"company_name": rel["company_name"], "industry_name": rel["industry_name"]}
                        )
                    
                    relationships_imported += len(company_industry_data)
                
                # 导入公司-产品关系
                if company_product_file:
                    company_product_data = json.load(company_product_file)
                    st.info(f"正在导入 {len(company_product_data)} 个公司-产品关系...")
                    
                    for rel in company_product_data:
                        db.query(
                            "MATCH (c:company {name: $company_name}), (p:product {name: $product_name}) "
                            "MERGE (c)-[r:主营产品]->(p)",
                            {"company_name": rel["company_name"], "product_name": rel["product_name"]}
                        )
                    
                    relationships_imported += len(company_product_data)
                
                # 导入行业-行业关系
                if industry_industry_file:
                    industry_industry_data = json.load(industry_industry_file)
                    st.info(f"正在导入 {len(industry_industry_data)} 个行业-行业关系...")
                    
                    for rel in industry_industry_data:
                        db.query(
                            "MATCH (i1:industry {name: $from_industry}), (i2:industry {name: $to_industry}) "
                            "MERGE (i1)-[r:上级行业]->(i2)",
                            {"from_industry": rel["from_industry"], "to_industry": rel["to_industry"]}
                        )
                    
                    relationships_imported += len(industry_industry_data)
                
                # 显示导入结果
                if nodes_imported > 0 or relationships_imported > 0:
                    st.success(f"✅ 成功导入 {nodes_imported} 个节点和 {relationships_imported} 条关系")
                    # 清除缓存
                    st.cache_data.clear()
                else:
                    st.warning("未导入任何数据，请上传至少一个数据文件")
            
            except Exception as e:
                st.error(f"导入数据失败: {str(e)}")
                logger.error(f"导入数据失败: {str(e)}\n{traceback.format_exc()}")

# 数据导出选项卡
with tab2:
    st.header("📤 导出知识图谱数据")
    
    # 导出选项
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("导出设置")
        
        # 导出类型选择
        export_type = st.selectbox(
            "选择导出类型",
            ["完整图谱数据", "分析报告", "实体详情"],
            help="选择要导出的数据类型"
        )
        
        # 导出格式选择
        export_format = st.selectbox(
            "导出格式",
            ["JSON", "CSV", "Excel"],
            help="选择导出文件格式"
        )
        
        # 如果是实体详情，需要选择实体
        if export_type == "实体详情":
            entity_type = st.selectbox(
                "实体类型",
                ["company", "industry", "product"],
                format_func=lambda x: {"company": "公司", "industry": "行业", "product": "产品"}.get(x, x)
            )
            
            # 获取实体列表
            try:
                entity_query = f"MATCH (n:{entity_type}) RETURN n.name as name ORDER BY n.name LIMIT 100"
                entity_results = db.query(entity_query)
                entity_names = [r["name"] for r in entity_results]
                
                if entity_names:
                    selected_entity = st.selectbox("选择实体", entity_names)
                else:
                    st.warning(f"暂无{entity_type}数据")
                    selected_entity = None
            except Exception as e:
                st.error(f"获取实体列表失败: {str(e)}")
                selected_entity = None
    
    with col2:
        st.subheader("导出操作")
        
        # 导出按钮
        if st.button("🚀 开始导出", key="export_button"):
            with st.spinner("正在准备导出数据..."):
                try:
                    success = False
                    message = ""
                    file_data = None
                    filename = ""
                    
                    if export_type == "完整图谱数据":
                        # 导出完整图谱数据
                        # 获取所有节点和边
                        nodes_query = """
                        CALL {
                            MATCH (c:company) RETURN id(c) as id, c.name as label, 'company' as type, c as properties
                            UNION ALL
                            MATCH (i:industry) RETURN id(i) as id, i.name as label, 'industry' as type, i as properties
                            UNION ALL
                            MATCH (p:product) RETURN id(p) as id, p.name as label, 'product' as type, p as properties
                        }
                        RETURN id, label, type, properties
                        """
                        
                        edges_query = """
                        MATCH (a)-[r]->(b)
                        RETURN id(a) as from, id(b) as to, type(r) as label, r as properties
                        """
                        
                        nodes_results = db.query(nodes_query)
                        edges_results = db.query(edges_query)
                        
                        nodes = [{"id": r["id"], "label": r["label"], "type": r["type"], **dict(r["properties"])} for r in nodes_results]
                        edges = [{"from": r["from"], "to": r["to"], "label": r["label"], **dict(r["properties"])} for r in edges_results]
                        
                        format_mapping = {"JSON": "json", "CSV": "csv", "Excel": "xlsx"}
                        success, message, file_data = export_handler.export_graph_data(
                            nodes, edges, format_mapping[export_format]
                        )
                        filename = f"knowledge_graph_full.{format_mapping[export_format]}"
                    
                    elif export_type == "分析报告":
                        # 导出分析报告
                        report_data = analytics.generate_summary_report()
                        
                        format_mapping = {"JSON": "json", "CSV": "csv", "Excel": "xlsx"}
                        success, message, file_data = export_handler.export_analysis_report(
                            report_data, format_mapping[export_format]
                        )
                        filename = f"analysis_report.{format_mapping[export_format]}"
                    
                    elif export_type == "实体详情" and selected_entity:
                        # 导出实体详情
                        format_mapping = {"JSON": "json", "CSV": "csv", "Excel": "xlsx"}
                        success, message, file_data = export_handler.export_entity_details(
                            selected_entity, entity_type, format_mapping[export_format]
                        )
                        filename = f"{selected_entity}_details.{format_mapping[export_format]}"
                    
                    # 显示导出结果
                    if success and file_data:
                        st.success(message)
                        
                        # 设置MIME类型
                        mime_types = {
                            "json": "application/json",
                            "csv": "text/csv",
                            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        }
                        
                        format_ext = format_mapping[export_format]
                        
                        st.download_button(
                            label=f"📥 下载 {export_format} 文件",
                            data=file_data,
                            file_name=filename,
                            mime=mime_types.get(format_ext, "application/octet-stream"),
                            key="download_export_file"
                        )
                    else:
                        st.error(message or "导出失败")
                        
                except Exception as e:
                    st.error(f"导出失败: {str(e)}")
                    logger.error(f"导出失败: {str(e)}")
        
        # 导出统计信息
        st.markdown("---")
        st.subheader("📊 导出统计")
        
        try:
            export_stats = export_handler.get_export_statistics()
            if export_stats:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("活跃分享链接", export_stats.get('active_shares', 0))
                    st.metric("总访问次数", export_stats.get('total_accesses', 0))
                with col2:
                    st.write("**支持格式:**")
                    for fmt in export_stats.get('export_formats_supported', []):
                        st.write(f"- {fmt.upper()}")
            else:
                st.info("暂无导出统计数据")
        except Exception as e:
            st.error(f"获取导出统计失败: {str(e)}")

# 数据查看选项卡
with tab3:
    st.header("👀 查看知识图谱数据")
    
    # 显示数据库状态
    st.subheader("数据库状态")
    
    try:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            company_count = db.get_node_count("company")
            st.metric("公司节点数量", f"{company_count:,}")
        
        with col2:
            industry_count = db.get_node_count("industry")
            st.metric("行业节点数量", f"{industry_count:,}")
        
        with col3:
            product_count = db.get_node_count("product")
            st.metric("产品节点数量", f"{product_count:,}")
        
        # 显示关系数量
        st.subheader("关系统计")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            try:
                company_industry_count = db.get_relationship_count("company", "industry", "所属行业")
                st.metric("公司-行业关系", f"{company_industry_count:,}")
            except:
                st.metric("公司-行业关系", "N/A")
        
        with col2:
            try:
                company_product_count = db.get_relationship_count("company", "product", "主营产品")
                st.metric("公司-产品关系", f"{company_product_count:,}")
            except:
                st.metric("公司-产品关系", "N/A")
        
        with col3:
            try:
                industry_industry_count = db.get_relationship_count("industry", "industry", "上级行业")
                st.metric("行业-行业关系", f"{industry_industry_count:,}")
            except:
                st.metric("行业-行业关系", "N/A")
        
        # 数据样本预览
        st.subheader("数据样本预览")
        
        preview_type = st.selectbox(
            "选择预览类型",
            ["company", "industry", "product"],
            format_func=lambda x: {"company": "公司", "industry": "行业", "product": "产品"}.get(x, x)
        )
        
        try:
            preview_query = f"""
            MATCH (n:{preview_type})
            RETURN n.name as name, n.description as description
            ORDER BY n.name
            LIMIT 10
            """
            
            preview_results = db.query(preview_query)
            
            if preview_results:
                df = pd.DataFrame(preview_results)
                df.columns = ["名称", "描述"]
                st.dataframe(df, use_container_width=True)
            else:
                st.info(f"暂无{preview_type}数据")
                
        except Exception as e:
            st.error(f"获取数据预览失败: {str(e)}")
        
    except Exception as e:
        st.error(f"获取数据库状态时出错: {str(e)}")
        logger.error(f"获取数据库状态时出错: {str(e)}")

# 示例数据选项卡
with tab4:
    st.header("🚀 导入示例数据")
    
    st.info("💡 如果您是首次使用，建议导入示例数据来体验系统功能")
    
    if st.button("📥 导入示例数据", help="导入包括阿里巴巴、华为等公司的示例数据", key="import_sample_button"):
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
                
                st.success("✅ 示例数据导入成功！")
                st.info("🎉 您现在可以使用其他功能页面来探索这些数据了")
                
                # 清除缓存
                st.cache_data.clear()
                
            except Exception as e:
                st.error(f"导入示例数据失败: {str(e)}")
                logger.error(f"导入示例数据失败: {str(e)}\n{traceback.format_exc()}")
    
    # 显示示例数据结构
    with st.expander("📋 查看示例数据结构"):
        st.code("""
# 公司数据格式 (JSON)
[
    {"name": "阿里巴巴", "description": "中国领先的电子商务公司"},
    {"name": "腾讯", "description": "中国领先的互联网服务提供商"},
    ...
]

# 行业数据格式 (JSON)
[
    {"name": "互联网", "description": "互联网行业"},
    {"name": "电子商务", "description": "电子商务行业"},
    ...
]

# 产品数据格式 (JSON)
[
    {"name": "淘宝", "description": "阿里巴巴旗下电子商务平台"},
    {"name": "微信", "description": "腾讯旗下社交通讯软件"},
    ...
]

# 公司-行业关系数据格式 (JSON)
[
    {"company_name": "阿里巴巴", "industry_name": "互联网"},
    {"company_name": "阿里巴巴", "industry_name": "电子商务"},
    ...
]

# 公司-产品关系数据格式 (JSON)
[
    {"company_name": "阿里巴巴", "product_name": "淘宝"},
    {"company_name": "腾讯", "product_name": "微信"},
    ...
]

# 行业-行业关系数据格式 (JSON)
[
    {"from_industry": "电子商务", "to_industry": "互联网"},
    {"from_industry": "人工智能", "to_industry": "互联网"},
    ...
]
        """, language="json")

# 页脚
st.markdown("---")
st.caption(f"知识图谱数据管理工具 | {datetime.now().strftime('%Y-%m-%d')}")

# 侧边栏帮助信息
with st.sidebar:
    st.markdown("---")
    st.subheader("📖 功能说明")
    
    with st.expander("数据管理功能"):
        st.markdown("""
        - **数据导入**: 上传JSON格式的数据文件
        - **数据导出**: 导出图谱数据和分析报告
        - **数据查看**: 查看数据库状态和数据样本
        - **示例数据**: 快速导入演示数据
        """)
    
    with st.expander("支持的文件格式"):
        st.markdown("""
        **导入格式:**
        - JSON (推荐)
        
        **导出格式:**
        - JSON - 结构化数据
        - CSV - 表格数据
        - Excel - 电子表格
        """)