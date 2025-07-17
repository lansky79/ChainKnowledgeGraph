#!/usr/bin/env python3
# coding: utf-8
# File: debug_streamlit_matrix.py
# 调试Streamlit矩阵显示

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from utils.db_connector import Neo4jConnector

st.title("调试公司-产品矩阵")

# 连接数据库
db = Neo4jConnector()

# 查询互联网行业的公司-产品关系
st.subheader("1. 数据查询")

query = """
MATCH (i:industry {name: '互联网'})<-[:所属行业]-(c:company)-[:主营产品]->(p:product)
RETURN c.name as company_name, p.name as product_name
ORDER BY c.name, p.name
LIMIT 30
"""

results = db.query(query)
st.write(f"找到 {len(results)} 个公司-产品关系")

# 显示前10个关系
st.subheader("2. 关系列表")
for i, result in enumerate(results[:10]):
    st.write(f"{i+1}. {result['company_name']} -> {result['product_name']}")

# 创建简化的矩阵
st.subheader("3. 矩阵创建")

if results:
    # 获取唯一的公司和产品
    companies = list(set([r['company_name'] for r in results]))
    products = list(set([r['product_name'] for r in results]))
    
    # 限制数量
    companies = sorted(companies)[:8]  # 最多8个公司
    products = sorted(products)[:15]   # 最多15个产品
    
    st.write(f"公司数量: {len(companies)}")
    st.write(f"产品数量: {len(products)}")
    
    # 创建矩阵
    matrix = np.zeros((len(companies), len(products)))
    
    # 创建映射
    company_to_idx = {company: i for i, company in enumerate(companies)}
    product_to_idx = {product: i for i, product in enumerate(products)}
    
    # 填充矩阵
    relations_count = 0
    for result in results:
        company = result['company_name']
        product = result['product_name']
        
        if company in company_to_idx and product in product_to_idx:
            company_idx = company_to_idx[company]
            product_idx = product_to_idx[product]
            matrix[company_idx][product_idx] = 1
            relations_count += 1
    
    st.write(f"矩阵中的关系数量: {relations_count}")
    st.write(f"矩阵非零元素: {np.sum(matrix > 0)}")
    
    # 显示矩阵
    st.subheader("4. 矩阵可视化")
    
    # 设置中文字体支持
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False
    
    # 创建图表
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # 显示矩阵
    im = ax.imshow(matrix, cmap="Blues")
    
    # 设置坐标轴标签
    ax.set_xticks(np.arange(len(products)))
    ax.set_yticks(np.arange(len(companies)))
    ax.set_xticklabels(products, fontsize=8)
    ax.set_yticklabels(companies, fontsize=10)
    
    # 添加标题
    ax.set_title(f"公司-产品关系矩阵 ({len(companies)}×{len(products)})", fontsize=14)
    
    # 在矩阵中添加文本标签
    marked_count = 0
    for i in range(len(companies)):
        for j in range(len(products)):
            if matrix[i, j] > 0:
                # 使用明显的标记
                ax.text(j, i, "●", ha="center", va="center", color="red", fontsize=12, weight="bold")
                # 添加背景色
                rect = Rectangle((j-0.4, i-0.4), 0.8, 0.8, fill=True, color='lightcoral', alpha=0.3)
                ax.add_patch(rect)
                marked_count += 1
    
    st.write(f"添加了 {marked_count} 个红色标记")
    
    # 旋转X轴标签
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
    
    # 添加网格线
    ax.set_xticks(np.arange(-.5, len(products), 1), minor=True)
    ax.set_yticks(np.arange(-.5, len(companies), 1), minor=True)
    ax.grid(which="minor", color="w", linestyle='-', linewidth=1)
    
    # 调整布局
    plt.tight_layout()
    
    # 显示图形
    st.pyplot(fig)
    
    # 显示具体的关系
    st.subheader("5. 具体关系")
    for i, company in enumerate(companies):
        company_products = []
        for j, product in enumerate(products):
            if matrix[i, j] > 0:
                company_products.append(product)
        if company_products:
            st.write(f"**{company}**: {', '.join(company_products)}")