"""
网络图可视化模块，用于生成和显示知识图谱网络图
"""
import streamlit as st
from pyvis.network import Network
import networkx as nx
import tempfile
import os
import logging
import json

logger = logging.getLogger(__name__)

def create_network_graph(nodes, edges, title="知识图谱"):
    """
    创建网络图可视化
    
    参数:
    - nodes: 节点列表，格式为 [{"id": id, "label": label, "group": group}, ...]
    - edges: 边列表，格式为 [{"from": source_id, "to": target_id, "label": label}, ...]
    - title: 图表标题
    
    返回:
    - HTML文件路径
    """
    try:
        # 创建NetworkX图
        G = nx.DiGraph()
        
        # 添加节点
        for node in nodes:
            G.add_node(node["id"], label=node["label"], group=node["group"])
        
        # 添加边
        for edge in edges:
            G.add_edge(edge["from"], edge["to"], title=edge["label"])
        
        # 创建Pyvis网络图
        net = Network(notebook=True, height="600px", width="100%", directed=True)
        net.from_nx(G)
        
        # 设置节点颜色
        for node in net.nodes:
            group = node.get("group", 0)
            if group == 0:  # 产业
                node["color"] = "#2ca02c"
            elif group == 1:  # 公司
                node["color"] = "#ff7f0e"
            else:  # 产品
                node["color"] = "#d62728"
        
        # 保存为临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as f:
            path = f.name
            net.save_graph(path)
            
        return path
    except Exception as e:
        logger.error(f"创建网络图失败: {e}")
        return None

def display_network(nodes, edges, title="知识图谱"):
    """在Streamlit中显示网络图"""
    try:
        path = create_network_graph(nodes, edges, title)
        if path:
            # 读取HTML文件并在Streamlit中显示
            with open(path, 'r', encoding='utf-8') as f:
                html = f.read()
            st.components.v1.html(html, height=600)
            # 删除临时文件
            os.unlink(path)
            return True
        return False
    except Exception as e:
        st.error(f"显示网络图失败: {e}")
        logger.error(f"显示网络图失败: {e}")
        return False

def create_echarts_graph(nodes, edges, title="知识图谱"):
    """
    创建ECharts网络图配置
    
    参数:
    - nodes: 节点列表，格式为 [{"id": id, "label": label, "group": group}, ...]
    - edges: 边列表，格式为 [{"from": source_id, "to": target_id, "label": label}, ...]
    - title: 图表标题
    
    返回:
    - ECharts配置字典
    """
    try:
        # 转换节点格式为ECharts格式
        echarts_nodes = []
        for node in nodes:
            category = node.get("group", 0)
            echarts_nodes.append({
                "id": str(node["id"]),  # 确保ID是字符串
                "name": node["label"],
                "symbolSize": 40 if category == 0 else 30 if category == 1 else 25,
                "category": category
            })
        
        # 转换边格式为ECharts格式
        echarts_edges = []
        for edge in edges:
            echarts_edges.append({
                "source": str(edge["from"]),  # 确保ID是字符串
                "target": str(edge["to"]),    # 确保ID是字符串
                "name": edge["label"]
            })
        
        # 创建ECharts配置
        categories = [{"name": "产业"}, {"name": "公司"}, {"name": "产品"}]
        options = {
            "title": {"text": title},
            "tooltip": {},
            "legend": {"data": [cat["name"] for cat in categories]},
            "series": [{
                "type": "graph",
                "layout": "force",
                "data": echarts_nodes,
                "links": echarts_edges,
                "categories": categories,
                "roam": True,
                "label": {"show": True},
                "force": {"repulsion": 100}
            }]
        }
        
        # 验证配置是否可序列化
        json.dumps(options)
        
        return options
    except Exception as e:
        logger.error(f"创建ECharts图表失败: {e}")
        return None 