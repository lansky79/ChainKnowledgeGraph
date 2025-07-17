#!/usr/bin/env python3
# coding: utf-8
# File: debug_industry_matrix.py
# 专门调试行业关系矩阵

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from utils.db_connector import Neo4jConnector

st.title("调试行业关系矩阵")

# 连接数据库
db = Neo4jConnector()

st.subheader("1. 查询与互联网相关的行业")

# 查询与互联网相关的行业
related_query = """
MATCH (i:industry {name: '互联网'})-[r]-(related:industry)
RETURN collect(distinct related.name) as related_industries
"""

related_results = db.query(related_query)
if related_results:
    related_industries = related_results[0]["related_industries"]
    all_industries = ["互联网"] + related_industries
    
    st.write(f"与互联网相关的行业 ({len(all_industries)}个):")
    for industry in all_industries:
        st.write(f"  - {industry}")
    
    st.subheader("2. 查询所有交叉关系")
    
    # 查询这些行业之间的所有交叉关系
    cross_query = """
    MATCH (i1:industry)-[r:相关行业]->(i2:industry)
    WHERE i1.name IN $industry_names AND i2.name IN $industry_names
    RETURN i1.name as from_industry, i2.name as to_industry, r.type as relation_type
    ORDER BY from_industry, to_industry
    """
    
    cross_results = db.query(cross_query, {"industry_names": all_industries})
    
    st.write(f"找到 {len(cross_results)} 个交叉关系:")
    
    # 显示所有关系
    for i, rel in enumerate(cross_results):
        st.write(f"{i+1}. {rel['from_industry']} -> {rel['to_industry']} ({rel['relation_type']})")
    
    st.subheader("3. 创建行业关系矩阵")
    
    if len(all_industries) >= 2 and len(cross_results) > 0:
        # 创建矩阵
        matrix = np.zeros((len(all_industries), len(all_industries)))
        
        # 创建行业名称到索引的映射
        industry_to_idx = {industry: i for i, industry in enumerate(all_industries)}
        
        # 填充矩阵
        relations_count = 0
        for rel in cross_results:
            from_industry = rel['from_industry']
            to_industry = rel['to_industry']
            
            if from_industry in industry_to_idx and to_industry in industry_to_idx:
                from_idx = industry_to_idx[from_industry]
                to_idx = industry_to_idx[to_industry]
                matrix[from_idx][to_idx] = 1
                relations_count += 1
        
        st.write(f"矩阵填充统计:")
        st.write(f"  - 矩阵大小: {len(all_industries)} x {len(all_industries)}")
        st.write(f"  - 填充的关系数: {relations_count}")
        st.write(f"  - 矩阵中非零元素: {np.sum(matrix > 0)}")
        st.write(f"  - 填充率: {np.sum(matrix > 0) / matrix.size * 100:.2f}%")
        
        # 显示矩阵内容
        st.subheader("4. 矩阵内容")
        st.write("矩阵数值 (1表示有关系，0表示无关系):")
        
        # 创建DataFrame来更好地显示矩阵
        import pandas as pd
        matrix_df = pd.DataFrame(matrix, index=all_industries, columns=all_industries)
        st.dataframe(matrix_df)
        
        # 显示具体的关系对
        st.write("具体关系对:")
        for i, from_industry in enumerate(all_industries):
            for j, to_industry in enumerate(all_industries):
                if matrix[i, j] > 0:
                    st.write(f"  [{i}][{j}] {from_industry} -> {to_industry}")
        
        st.subheader("5. 可视化矩阵")
        
        # 设置中文字体支持
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 创建图表
        fig, ax = plt.subplots(figsize=(12, 10))
        
        # 显示矩阵
        im = ax.imshow(matrix, cmap="Blues")
        
        # 设置坐标轴标签
        ax.set_xticks(np.arange(len(all_industries)))
        ax.set_yticks(np.arange(len(all_industries)))
        ax.set_xticklabels(all_industries, fontsize=10)
        ax.set_yticklabels(all_industries, fontsize=10)
        
        # 添加标题
        ax.set_title(f"行业关系矩阵 ({len(all_industries)}×{len(all_industries)})", fontsize=14)
        
        # 在矩阵中添加文本标签
        marked_count = 0
        for i in range(len(all_industries)):
            for j in range(len(all_industries)):
                if matrix[i, j] > 0:
                    # 使用明显的标记
                    ax.text(j, i, "●", ha="center", va="center", color="red", fontsize=14, weight="bold")
                    # 添加背景色
                    rect = Rectangle((j-0.4, i-0.4), 0.8, 0.8, fill=True, color='lightcoral', alpha=0.3)
                    ax.add_patch(rect)
                    marked_count += 1
        
        st.write(f"在矩阵中添加了 {marked_count} 个红色标记")
        
        # 旋转X轴标签
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
        
        # 添加网格线
        ax.set_xticks(np.arange(-.5, len(all_industries), 1), minor=True)
        ax.set_yticks(np.arange(-.5, len(all_industries), 1), minor=True)
        ax.grid(which="minor", color="w", linestyle='-', linewidth=1)
        
        # 调整布局
        plt.tight_layout()
        
        # 显示图形
        st.pyplot(fig)
        
        st.subheader("6. 关系统计")
        
        # 统计每个行业的出度和入度
        for i, industry in enumerate(all_industries):
            outgoing = np.sum(matrix[i, :])
            incoming = np.sum(matrix[:, i])
            st.write(f"{industry}: 出度={int(outgoing)}, 入度={int(incoming)}, 总计={int(outgoing + incoming)}")
    
    else:
        st.error("没有足够的数据来创建矩阵")
else:
    st.error("没有找到与互联网相关的行业")