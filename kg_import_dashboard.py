import streamlit as st
import pandas as pd
import numpy as np
import time
import json
import os
import pickle
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from build_graph import MedicalGraph

# 设置页面配置
st.set_page_config(
    page_title="知识图谱数据导入工具",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 自定义CSS样式
st.markdown("""
<style>
    .main {
        background-color: #f5f7f9;
    }
    .stProgress > div > div > div > div {
        background-color: #4CAF50;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 10px 24px;
        border-radius: 4px;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .highlight {
        background-color: #e6f7ff;
        padding: 10px;
        border-radius: 5px;
    }
    .warning {
        background-color: #fff3e0;
        padding: 10px;
        border-radius: 5px;
    }
    .success {
        background-color: #e8f5e9;
        padding: 10px;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# 初始化会话状态
if 'import_history' not in st.session_state:
    st.session_state.import_history = []

if 'last_refresh' not in st.session_state:
    st.session_state.last_refresh = time.time()

if 'is_importing' not in st.session_state:
    st.session_state.is_importing = False

# 侧边栏
st.sidebar.title("知识图谱数据导入工具")
st.sidebar.image("https://neo4j.com/wp-content/themes/neo4jweb/assets/images/neo4j-logo-2015.png", width=200)

# 创建MedicalGraph实例
@st.cache_resource
def get_graph_handler():
    return MedicalGraph()

handler = get_graph_handler()

# 获取导入状态数据
def get_import_status():
    # 从handler获取导入状态
    import_state = handler.import_state
    
    # 节点数据
    node_files = {
        'company': handler.company_path,
        'industry': handler.industry_path,
        'product': handler.product_path
    }
    
    # 关系数据
    rel_files = {
        'company_industry': handler.company_industry_path,
        'industry_industry': handler.industry_industry,
        'company_product': handler.company_product_path,
        'product_product': handler.product_product
    }
    
    # 节点导入状态
    node_stats = []
    total_nodes = 0
    imported_nodes = 0
    
    for node_type, file_path in node_files.items():
        total = handler._count_file_lines(file_path)
        imported = import_state[node_type]
        progress = (imported / total * 100) if total > 0 else 0
        remaining = total - imported
        
        total_nodes += total
        imported_nodes += imported
        
        node_stats.append({
            "类型": node_type,
            "已导入": imported,
            "总数": total,
            "进度": progress,
            "剩余": remaining
        })
    
    # 关系导入状态
    rel_stats = []
    total_rels = 0
    imported_rels = 0
    
    for rel_type, file_path in rel_files.items():
        total = handler._count_file_lines(file_path)
        imported = import_state[rel_type]
        progress = (imported / total * 100) if total > 0 else 0
        remaining = total - imported
        
        total_rels += total
        imported_rels += imported
        
        rel_stats.append({
            "类型": rel_type,
            "已导入": imported,
            "总数": total,
            "进度": progress,
            "剩余": remaining
        })
    
    # 总体进度
    total_all = total_nodes + total_rels
    imported_all = imported_nodes + imported_rels
    overall_progress = (imported_all / total_all * 100) if total_all > 0 else 0
    remaining_all = total_all - imported_all
    
    # 最后导入时间
    last_import_time = None
    if import_state['last_import_time']:
        last_import_time = datetime.fromtimestamp(import_state['last_import_time']).strftime('%Y-%m-%d %H:%M:%S')
    
    return {
        "node_stats": node_stats,
        "rel_stats": rel_stats,
        "total_nodes": total_nodes,
        "imported_nodes": imported_nodes,
        "total_rels": total_rels,
        "imported_rels": imported_rels,
        "total_all": total_all,
        "imported_all": imported_all,
        "overall_progress": overall_progress,
        "remaining_all": remaining_all,
        "last_import_time": last_import_time
    }

# 执行导入操作
def run_import(batch_size):
    if st.session_state.is_importing:
        return
    
    st.session_state.is_importing = True
    
    # 记录开始时间
    start_time = time.time()
    
    # 执行导入
    result = handler.incremental_import(batch_size)
    
    # 记录结束时间
    end_time = time.time()
    
    # 添加到历史记录
    history_entry = {
        "时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "批次大小": batch_size,
        "导入节点数": result["nodes_count"],
        "导入关系数": result["rels_count"],
        "总耗时(秒)": result["total_time"],
        "节点导入速度(个/秒)": result["nodes_count"] / result["nodes_time"] if result["nodes_time"] > 0 else 0,
        "关系导入速度(个/秒)": result["rels_count"] / result["rels_time"] if result["rels_time"] > 0 else 0
    }
    
    st.session_state.import_history.append(history_entry)
    st.session_state.is_importing = False
    
    return result

# 主页面内容
st.title("知识图谱数据导入可视化工具")

# 创建三个标签页
tab1, tab2, tab3, tab4 = st.tabs(["导入进度仪表盘", "数据分布统计", "导入历史记录", "操作控制面板"])

# 获取最新状态
status = get_import_status()

# 标签页1: 导入进度仪表盘
with tab1:
    st.header("导入进度仪表盘")
    
    # 创建三列布局
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("总体进度")
        st.progress(status["overall_progress"] / 100)
        st.metric(
            label="总体完成率", 
            value=f"{status['overall_progress']:.2f}%", 
            delta=f"{status['imported_all']}/{status['total_all']}"
        )
    
    with col2:
        st.subheader("节点导入进度")
        node_progress = (status["imported_nodes"] / status["total_nodes"] * 100) if status["total_nodes"] > 0 else 0
        st.progress(node_progress / 100)
        st.metric(
            label="节点完成率", 
            value=f"{node_progress:.2f}%", 
            delta=f"{status['imported_nodes']}/{status['total_nodes']}"
        )
    
    with col3:
        st.subheader("关系导入进度")
        rel_progress = (status["imported_rels"] / status["total_rels"] * 100) if status["total_rels"] > 0 else 0
        st.progress(rel_progress / 100)
        st.metric(
            label="关系完成率", 
            value=f"{rel_progress:.2f}%", 
            delta=f"{status['imported_rels']}/{status['total_rels']}"
        )
    
    # 显示最后导入时间
    if status["last_import_time"]:
        st.info(f"最后导入时间: {status['last_import_time']}")
    
    # 显示节点导入详情
    st.subheader("节点导入详情")
    node_df = pd.DataFrame(status["node_stats"])
    
    # 创建进度条图表
    fig = go.Figure()
    for i, row in node_df.iterrows():
        fig.add_trace(go.Bar(
            name=row["类型"],
            y=[row["类型"]],
            x=[row["进度"]],
            orientation='h',
            marker=dict(color='rgba(76, 175, 80, 0.8)'),
            text=f"{row['进度']:.2f}%",
            textposition='auto'
        ))
    
    fig.update_layout(
        title="节点类型导入进度",
        xaxis_title="完成百分比 (%)",
        yaxis_title="节点类型",
        barmode='stack',
        height=300,
        margin=dict(l=20, r=20, t=40, b=20),
    )
    
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(node_df, use_container_width=True)
    
    # 显示关系导入详情
    st.subheader("关系导入详情")
    rel_df = pd.DataFrame(status["rel_stats"])
    
    # 创建进度条图表
    fig = go.Figure()
    for i, row in rel_df.iterrows():
        fig.add_trace(go.Bar(
            name=row["类型"],
            y=[row["类型"]],
            x=[row["进度"]],
            orientation='h',
            marker=dict(color='rgba(33, 150, 243, 0.8)'),
            text=f"{row['进度']:.2f}%",
            textposition='auto'
        ))
    
    fig.update_layout(
        title="关系类型导入进度",
        xaxis_title="完成百分比 (%)",
        yaxis_title="关系类型",
        barmode='stack',
        height=300,
        margin=dict(l=20, r=20, t=40, b=20),
    )
    
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(rel_df, use_container_width=True)

# 标签页2: 数据分布统计
with tab2:
    st.header("数据分布统计")
    
    # 节点分布饼图
    st.subheader("节点类型分布")
    node_df = pd.DataFrame(status["node_stats"])
    
    fig = px.pie(
        node_df, 
        values='总数', 
        names='类型',
        title='节点类型分布',
        color_discrete_sequence=px.colors.sequential.Viridis
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # 关系分布饼图
    st.subheader("关系类型分布")
    rel_df = pd.DataFrame(status["rel_stats"])
    
    fig = px.pie(
        rel_df, 
        values='总数', 
        names='类型',
        title='关系类型分布',
        color_discrete_sequence=px.colors.sequential.Plasma
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # 导入进度对比柱状图
    st.subheader("导入进度对比")
    
    # 准备数据
    compare_data = []
    
    for row in node_df.to_dict('records'):
        compare_data.append({
            '类型': row['类型'],
            '数据类别': '节点',
            '已导入': row['已导入'],
            '未导入': row['剩余']
        })
    
    for row in rel_df.to_dict('records'):
        compare_data.append({
            '类型': row['类型'],
            '数据类别': '关系',
            '已导入': row['已导入'],
            '未导入': row['剩余']
        })
    
    compare_df = pd.DataFrame(compare_data)
    
    # 创建堆叠柱状图
    fig = go.Figure()
    
    for i, row in compare_df.iterrows():
        fig.add_trace(go.Bar(
            name=f"{row['类型']} - 已导入",
            x=[row['类型']],
            y=[row['已导入']],
            marker_color='rgba(76, 175, 80, 0.8)'
        ))
        
        fig.add_trace(go.Bar(
            name=f"{row['类型']} - 未导入",
            x=[row['类型']],
            y=[row['未导入']],
            marker_color='rgba(244, 67, 54, 0.8)'
        ))
    
    fig.update_layout(
        title="各类型数据导入状态对比",
        xaxis_title="数据类型",
        yaxis_title="数据量",
        barmode='stack',
        height=500,
        margin=dict(l=20, r=20, t=40, b=20),
    )
    
    st.plotly_chart(fig, use_container_width=True)

# 标签页3: 导入历史记录
with tab3:
    st.header("导入历史记录")
    
    if len(st.session_state.import_history) > 0:
        history_df = pd.DataFrame(st.session_state.import_history)
        st.dataframe(history_df, use_container_width=True)
        
        # 导入历史趋势图
        st.subheader("导入历史趋势")
        
        # 转换时间列为datetime类型
        history_df['时间'] = pd.to_datetime(history_df['时间'])
        
        # 创建折线图
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=history_df['时间'],
            y=history_df['导入节点数'],
            mode='lines+markers',
            name='导入节点数',
            line=dict(color='rgba(76, 175, 80, 0.8)', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=history_df['时间'],
            y=history_df['导入关系数'],
            mode='lines+markers',
            name='导入关系数',
            line=dict(color='rgba(33, 150, 243, 0.8)', width=2)
        ))
        
        fig.update_layout(
            title="导入数据量历史趋势",
            xaxis_title="时间",
            yaxis_title="数据量",
            height=400,
            margin=dict(l=20, r=20, t=40, b=20),
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 导入速度趋势图
        st.subheader("导入速度趋势")
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=history_df['时间'],
            y=history_df['节点导入速度(个/秒)'],
            mode='lines+markers',
            name='节点导入速度',
            line=dict(color='rgba(76, 175, 80, 0.8)', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=history_df['时间'],
            y=history_df['关系导入速度(个/秒)'],
            mode='lines+markers',
            name='关系导入速度',
            line=dict(color='rgba(33, 150, 243, 0.8)', width=2)
        ))
        
        fig.update_layout(
            title="导入速度历史趋势",
            xaxis_title="时间",
            yaxis_title="速度 (个/秒)",
            height=400,
            margin=dict(l=20, r=20, t=40, b=20),
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 清除历史记录按钮
        if st.button("清除历史记录"):
            st.session_state.import_history = []
            st.experimental_rerun()
    else:
        st.info("暂无导入历史记录")

# 标签页4: 操作控制面板
with tab4:
    st.header("操作控制面板")
    
    # 创建两列布局
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("导入控制")
        
        # 批次大小选择
        batch_size = st.slider("选择批次大小", min_value=1000, max_value=50000, value=10000, step=1000)
        
        # 导入按钮
        if st.button("开始导入"):
            with st.spinner("正在导入数据..."):
                result = run_import(batch_size)
                st.success(f"导入完成! 共导入 {result['nodes_count']} 个节点和 {result['rels_count']} 个关系")
                st.experimental_rerun()
    
    with col2:
        st.subheader("其他操作")
        
        # 刷新状态按钮
        if st.button("刷新状态"):
            st.session_state.last_refresh = time.time()
            st.experimental_rerun()
        
        # 重置导入状态按钮
        st.warning("⚠️ 危险操作")
        if st.button("重置导入状态"):
            confirm = st.checkbox("我确认要重置所有导入状态")
            if confirm:
                handler.reset_import_state()
                st.success("导入状态已重置!")
                st.experimental_rerun()

# 侧边栏状态摘要
st.sidebar.header("状态摘要")
st.sidebar.metric(
    label="总体完成率", 
    value=f"{status['overall_progress']:.2f}%", 
    delta=f"{status['imported_all']}/{status['total_all']}"
)

# 刷新按钮
if st.sidebar.button("刷新数据"):
    st.session_state.last_refresh = time.time()
    st.experimental_rerun()

# 显示最后刷新时间
st.sidebar.caption(f"最后刷新时间: {datetime.fromtimestamp(st.session_state.last_refresh).strftime('%H:%M:%S')}")

# 添加说明
st.sidebar.markdown("""
### 使用说明
1. **导入进度仪表盘**: 查看当前导入进度和详情
2. **数据分布统计**: 查看节点和关系的分布情况
3. **导入历史记录**: 查看历史导入操作记录和趋势
4. **操作控制面板**: 执行导入操作和其他管理功能
""")

# 添加版权信息
st.sidebar.markdown("---")
st.sidebar.caption("© 2023 知识图谱数据导入工具") 