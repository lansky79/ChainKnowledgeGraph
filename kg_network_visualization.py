import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import traceback
from streamlit_agraph import agraph, Node, Edge, Config
import matplotlib as mpl

# 设置matplotlib支持中文显示
plt.rcParams["font.sans-serif"] = ["SimHei", "Arial Unicode MS", "DejaVu Sans", "sans-serif"]
plt.rcParams["axes.unicode_minus"] = False
mpl.rcParams["font.family"] = ["SimHei", "Arial Unicode MS", "DejaVu Sans", "sans-serif"]

def visualize_network(nodes_data, relationships_data, node_map):
    """
    使用streamlit_agraph可视化网络图
    
    参数:
    - nodes_data: 节点数据列表，格式为[(node_id, node_name, node_type), ...]
    - relationships_data: 关系数据列表，格式为[(start, rel_type, end), ...]
    - node_map: 节点名称到索引的映射字典
    
    返回:
    - success: 是否成功渲染
    - message: 如果失败，返回错误信息
    """
    try:
        # 创建节点和边
        nodes = []
        edges = []
        
        # 处理节点
        for i, (node_id, node_name, node_type) in enumerate(nodes_data):
            # 为不同类型的节点设置不同的颜色
            color = "#1f77b4"  # 默认蓝色
            if node_type == "company":
                color = "#ff7f0e"  # 橙色
            elif node_type == "industry":
                color = "#2ca02c"  # 绿色
            elif node_type == "product":
                color = "#d62728"  # 红色
                
            # 使用更小的节点尺寸
            nodes.append(Node(id=i, 
                             label=node_name, 
                             size=20,  # 减小节点尺寸
                             shape="circle",
                             color=color))
        
        # 处理边
        for start, rel_type, end in relationships_data:
            if start in node_map and end in node_map:
                edges.append(Edge(source=node_map[start], 
                                 target=node_map[end], 
                                 label=rel_type))
        
        # 配置 - 减小图表尺寸，调整物理引擎参数使布局更紧凑
        config = Config(width=600,  # 减小宽度
                       height=400,  # 减小高度
                       directed=True,
                       physics=True,
                       hierarchical=False,
                       nodeHighlightBehavior=True,
                       highlightColor="#F7A7A6",
                       collapsible=True)
        
        # 显示网络图
        st.caption("关系网络图")  # 使用caption替代subheader，减少占用空间
        agraph(nodes=nodes, edges=edges, config=config)
        
        return True, "成功渲染网络图"
    except Exception as e:
        return False, f"无法显示网络图: {str(e)}\n{traceback.format_exc()}"

def visualize_matrix(relationships_data, node_map):
    """
    创建并显示关系矩阵
    
    参数:
    - relationships_data: 关系数据列表，格式为[(start, rel_type, end), ...]
    - node_map: 节点名称到索引的映射字典
    
    返回:
    - fig: matplotlib图形对象
    """
    # 准备矩阵数据
    entities = list(node_map.keys())
    matrix = np.zeros((len(entities), len(entities)))
    
    for start, rel_type, end in relationships_data:
        if start in node_map and end in node_map:
            matrix[node_map[start]][node_map[end]] = 1
    
    # 创建图形 - 减小图形尺寸
    fig, ax = plt.subplots(figsize=(8, 8))  # 减小图形尺寸
    ax.matshow(matrix, cmap="Blues")
    
    # 设置坐标轴标签
    ax.set_xticks(np.arange(len(entities)))
    ax.set_yticks(np.arange(len(entities)))
    
    # 如果实体数量过多，减少显示的标签
    if len(entities) > 10:
        # 只显示部分标签
        ax.set_xticks(np.arange(0, len(entities), max(1, len(entities) // 10)))
        ax.set_yticks(np.arange(0, len(entities), max(1, len(entities) // 10)))
    
    # 设置字体大小，使标签更紧凑
    fontsize = max(6, min(8, 120 // len(entities)))  # 根据实体数量动态调整字体大小
    ax.set_xticklabels(entities, rotation=90, fontsize=fontsize)
    ax.set_yticklabels(entities, fontsize=fontsize)
    
    # 在每个单元格中显示值（只在矩阵较小时显示）
    if len(entities) <= 20:  # 只在实体数量较少时显示数值
        for i in range(len(entities)):
            for j in range(len(entities)):
                if matrix[i, j] > 0:
                    ax.text(j, i, int(matrix[i, j]), ha="center", va="center", fontsize=fontsize)
    
    plt.tight_layout()  # 优化布局，减少空白
    return fig
