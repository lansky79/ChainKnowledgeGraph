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
            nodes.append(Node(id=str(i), 
                             label=node_name, 
                             size=20,  # 减小节点尺寸
                             shape="circle",
                             color=color))
        
        # 处理边
        for start, rel_type, end in relationships_data:
            if start in node_map and end in node_map:
                edges.append(Edge(source=str(node_map[start]), 
                                 target=str(node_map[end]), 
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

def visualize_matrix(relationships_data, node_map, node_types=None):
    """
    创建并显示关系矩阵
    
    参数:
    - relationships_data: 关系数据列表，格式为[(start, rel_type, end), ...]
    - node_map: 节点名称到索引的映射字典
    - node_types: 节点名称到类型的映射字典，如果为None则不按类型分组
    
    返回:
    - fig: matplotlib图形对象
    """
    import streamlit as st
    
    # 准备矩阵数据
    entities = list(node_map.keys())
    
    # 如果没有提供节点类型信息，则使用默认的矩阵视图
    if node_types is None:
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
    
    # 如果提供了节点类型信息，则按类型分组
    else:
        # 获取不同的节点类型
        unique_types = list(set(node_types.values()))
        type_names = {
            "industry": "行业",
            "company": "公司",
            "product": "产品"
        }
        
        # 提供矩阵类型选择
        matrix_type_options = ["同类型实体矩阵"]
        if "company" in unique_types and "product" in unique_types:
            matrix_type_options.append("公司-产品矩阵")
        
        matrix_type = st.radio("选择矩阵类型", matrix_type_options)
        
        if matrix_type == "同类型实体矩阵":
            # 让用户选择要显示的实体类型
            available_types = [type_names.get(t, t) for t in unique_types]
            selected_type = st.selectbox("选择实体类型", available_types)
            
            # 获取选择的类型
            selected_type_raw = next((t for t, name in type_names.items() if name == selected_type), selected_type)
            
            # 获取该类型的所有节点
            type_entities = [e for e, t in node_types.items() if t == selected_type_raw]
            
            if len(type_entities) < 2:
                st.warning(f"没有足够的{selected_type}节点来创建矩阵")
                return None
            
            # 创建映射
            type_node_map = {entity: i for i, entity in enumerate(type_entities)}
            
            # 创建矩阵
            matrix = np.zeros((len(type_entities), len(type_entities)))
            
            # 填充矩阵
            for start, rel_type, end in relationships_data:
                if (start in type_entities and end in type_entities and
                    start in type_node_map and end in type_node_map):
                    matrix[type_node_map[start]][type_node_map[end]] = 1
            
            # 创建图形
            fig, ax = plt.subplots(figsize=(10, 8))
            ax.matshow(matrix, cmap="Blues")
            
            # 设置坐标轴标签
            ax.set_xticks(np.arange(len(type_entities)))
            ax.set_yticks(np.arange(len(type_entities)))
            
            # 如果实体数量过多，减少显示的标签
            if len(type_entities) > 10:
                # 只显示部分标签
                ax.set_xticks(np.arange(0, len(type_entities), max(1, len(type_entities) // 10)))
                ax.set_yticks(np.arange(0, len(type_entities), max(1, len(type_entities) // 10)))
            
            # 设置字体大小
            fontsize = max(6, min(8, 120 // len(type_entities)))
            ax.set_xticklabels(type_entities, rotation=90, fontsize=fontsize)
            ax.set_yticklabels(type_entities, fontsize=fontsize)
            
            # 添加标题
            ax.set_title(f"{selected_type}关系矩阵", fontsize=14)
            
            # 在矩阵中添加标记
            if len(type_entities) <= 20:
                for i in range(len(type_entities)):
                    for j in range(len(type_entities)):
                        if matrix[i, j] > 0:
                            ax.text(j, i, "●", ha="center", va="center", color="white", fontsize=fontsize)
            
            plt.tight_layout()
            return fig
            
        elif matrix_type == "公司-产品矩阵":
            # 获取公司和产品节点
            company_entities = [e for e, t in node_types.items() if t == "company"]
            product_entities = [e for e, t in node_types.items() if t == "product"]
            
            if len(company_entities) < 1 or len(product_entities) < 1:
                st.warning("没有足够的公司和产品节点来创建矩阵")
                return None
            
            # 创建映射
            company_map = {entity: i for i, entity in enumerate(company_entities)}
            product_map = {entity: i for i, entity in enumerate(product_entities)}
            
            # 创建矩阵
            matrix = np.zeros((len(company_entities), len(product_entities)))
            
            # 填充矩阵
            for start, rel_type, end in relationships_data:
                # 公司 -> 产品关系
                if start in company_entities and end in product_entities:
                    if start in company_map and end in product_map:
                        matrix[company_map[start]][product_map[end]] = 1
                # 产品 -> 公司关系
                elif start in product_entities and end in company_entities:
                    if end in company_map and start in product_map:
                        matrix[company_map[end]][product_map[start]] = 1
            
            # 创建图形
            fig, ax = plt.subplots(figsize=(12, 8))
            ax.matshow(matrix, cmap="Blues")
            
            # 设置坐标轴标签
            ax.set_xticks(np.arange(len(product_entities)))
            ax.set_yticks(np.arange(len(company_entities)))
            
            # 如果实体数量过多，减少显示的标签
            if len(product_entities) > 10:
                ax.set_xticks(np.arange(0, len(product_entities), max(1, len(product_entities) // 10)))
            if len(company_entities) > 10:
                ax.set_yticks(np.arange(0, len(company_entities), max(1, len(company_entities) // 10)))
            
            # 设置字体大小
            x_fontsize = max(6, min(8, 120 // len(product_entities)))
            y_fontsize = max(6, min(8, 120 // len(company_entities)))
            ax.set_xticklabels(product_entities, rotation=90, fontsize=x_fontsize)
            ax.set_yticklabels(company_entities, fontsize=y_fontsize)
            
            # 添加标题
            ax.set_title("公司-产品关系矩阵", fontsize=14)
            
            # 在矩阵中添加标记
            if len(company_entities) * len(product_entities) <= 400:
                for i in range(len(company_entities)):
                    for j in range(len(product_entities)):
                        if matrix[i, j] > 0:
                            ax.text(j, i, "●", ha="center", va="center", color="white", fontsize=min(x_fontsize, y_fontsize))
            
            plt.tight_layout()
            return fig
    
    return None
