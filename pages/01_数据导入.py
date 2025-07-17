"""
知识图谱数据导入页面
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
from utils.logger import setup_logger
import time

# 设置日志
logger = setup_logger("KG_Import")

# 页面配置
st.set_page_config(
    page_title="知识图谱数据导入",
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
</style>
""", unsafe_allow_html=True)

# 页面标题
st.title("知识图谱数据导入")

# 初始化数据库连接
@st.cache_resource
def get_db_connector():
    """获取数据库连接器（缓存资源）"""
    return Neo4jConnector()

db = get_db_connector()

# 创建选项卡
tab1, tab2, tab3 = st.tabs(["数据导入", "数据查看", "示例数据"])

# 数据导入选项卡
with tab1:
    st.header("导入数据到知识图谱")
    
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
    if st.button("导入数据", key="import_button"):
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
                    st.success(f"成功导入 {nodes_imported} 个节点和 {relationships_imported} 条关系")
                    # 清除缓存
                    st.cache_data.clear()
                else:
                    st.warning("未导入任何数据，请上传至少一个数据文件")
            
            except Exception as e:
                st.error(f"导入数据失败: {str(e)}")
                logger.error(f"导入数据失败: {str(e)}\n{traceback.format_exc()}")

# 数据查看选项卡
with tab2:
    st.header("查看知识图谱数据")
    
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
        
        # 显示关系数量
        st.subheader("关系数量")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            company_industry_count = db.get_relationship_count("company", "industry", "所属行业")
            st.metric("公司-行业关系", company_industry_count)
        
        with col2:
            company_product_count = db.get_relationship_count("company", "product", "主营产品")
            st.metric("公司-产品关系", company_product_count)
        
        with col3:
            industry_industry_count = db.get_relationship_count("industry", "industry", "上级行业")
            st.metric("行业-行业关系", industry_industry_count)
        
    except Exception as e:
        st.error(f"获取数据库状态时出错: {str(e)}")
        logger.error(f"获取数据库状态时出错: {str(e)}")

# 示例数据选项卡
with tab3:
    st.header("导入示例数据")
    
    if st.button("导入示例数据", help="导入包括阿里巴巴、华为等公司的示例数据", key="import_sample_button"):
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
                
                st.success("示例数据导入成功！")
                # 清除缓存
                st.cache_data.clear()
            except Exception as e:
                st.error(f"导入示例数据失败: {str(e)}")
                logger.error(f"导入示例数据失败: {str(e)}\n{traceback.format_exc()}")
    
    # 显示示例数据结构
    with st.expander("查看示例数据结构"):
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
st.caption(f"知识图谱数据导入工具 | {datetime.now().strftime('%Y-%m-%d')}") 