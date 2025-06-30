import streamlit as st
import pandas as pd
import numpy as np
import time
import json
import os
import pickle
import matplotlib.pyplot as plt
import plotly.express as px
from datetime import datetime
import logging
import sys
import traceback
from build_graph import MedicalGraph

# 确保日志目录存在
os.makedirs("logs", exist_ok=True)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs\\app.log", mode='a'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("KG_Dashboard_Windows")

logger.info("启动Windows版知识图谱数据导入可视化工具")

# 加载配置文件
def load_config():
    try:
        # 优先加载Windows专用配置
        if os.path.exists('config_windows.json'):
            logger.info("加载Windows专用配置文件")
            with open('config_windows.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        # 如果没有Windows专用配置，加载通用配置
        elif os.path.exists('config.json'):
            logger.info("加载通用配置文件")
            with open('config.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            logger.warning("配置文件不存在，使用默认配置")
            return {
                "neo4j": {
                    "uri": "bolt://127.0.0.1:7687",
                    "username": "neo4j",
                    "password": "12345678"
                },
                "app": {
                    "title": "知识图谱数据导入可视化工具 - Windows版",
                    "batch_size_default": 10000,
                    "batch_size_min": 1000,
                    "batch_size_max": 50000
                }
            }
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
        st.error(f"加载配置文件失败: {e}")
        return {}

# 加载配置
config = load_config()

# 设置页面配置
st.set_page_config(
    page_title="知识图谱数据导入可视化工具 - Windows版",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 自定义CSS，使界面更紧凑
st.markdown("""
<style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        white-space: pre-wrap;
        padding: 5px 10px;
    }
    div[data-testid="stSidebar"] {
        width: 200px !important;
    }
    div[role="slider"] {
        margin-top: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .stAlert {
        padding: 10px;
        margin-top: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .stDataFrame {
        margin-top: 0.5rem;
        margin-bottom: 0.5rem;
    }
    .stButton button {
        width: 100%;
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

if 'error_message' not in st.session_state:
    st.session_state.error_message = None

# 创建MedicalGraph实例
@st.cache_resource
def get_graph_handler():
    logger.info("初始化图谱处理器")
    try:
        return MedicalGraph()
    except Exception as e:
        logger.error(f"初始化图谱处理器失败: {e}")
        return None

# 尝试获取图谱处理器
try:
    logger.info("尝试初始化图谱处理器")
    handler = get_graph_handler()
    logger.info(f"图谱处理器初始化结果: {handler is not None}")
except Exception as e:
    logger.error(f"获取图谱处理器时发生异常: {e}")
    handler = None

# 主页面
st.title("知识图谱数据导入可视化工具 - Windows版")
st.write("版本: 1.0.1 - 修复版")

# 检查图谱处理器是否成功初始化
if handler is None:
    st.error("图谱处理器初始化失败，请检查Neo4j连接和数据文件。")
    st.warning("应用将以有限功能模式运行，请确保Neo4j服务已启动后刷新页面。")
    
    # 显示Neo4j连接设置
    st.subheader("Neo4j连接设置")
    if os.path.exists('config_windows.json'):
        try:
            with open('config_windows.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                neo4j_config = config.get('neo4j', {})
                st.write(f"连接URI: {neo4j_config.get('uri', 'bolt://127.0.0.1:7687')}")
                st.write(f"用户名: {neo4j_config.get('username', 'neo4j')}")
                st.write("密码: ********")
        except Exception as e:
            st.error(f"读取配置文件失败: {e}")
    else:
        st.warning("未找到配置文件 config_windows.json")
    
    # 提供Neo4j启动指南
    with st.expander("Neo4j启动指南", expanded=True):
        st.markdown("""
        ### 启动Neo4j数据库的步骤
        
        1. **通过Neo4j Desktop启动**:
           - 打开Neo4j Desktop应用
           - 选择您的数据库，点击"Start"按钮
           
        2. **通过Windows服务启动**:
           - 按Win+R打开运行对话框
           - 输入`services.msc`并按回车
           - 找到Neo4j服务，右键选择"启动"
           
        3. **通过命令行启动**:
           - 打开命令提示符或PowerShell
           - 导航到Neo4j安装目录的bin文件夹
           - 执行`neo4j.bat console`命令
        
        启动Neo4j后，请刷新此页面。
        """)
    
    # 刷新按钮
    if st.button("刷新页面", key="refresh_page"):
        st.experimental_rerun()
    
    # 不完全停止应用，只是不执行导入相关功能
    st.info("应用以有限功能模式运行中，无法执行数据导入操作。")
    st.stop()

# 简化版本的导入状态获取函数
def get_simple_import_status():
    try:
        # 从handler获取导入状态
        import_state = handler.import_state
        
        # 提取基本信息
        node_types = ['company', 'industry', 'product']
        rel_types = ['company_industry', 'industry_industry', 'company_product', 'product_product']
        
        # 节点状态
        node_data = []
        total_nodes = 0
        imported_nodes = 0
        
        for node_type in node_types:
            if node_type in import_state:
                imported = import_state[node_type]
                imported_nodes += imported
                node_data.append({
                    "类型": node_type,
                    "已导入数量": imported
                })
        
        # 关系状态
        rel_data = []
        total_rels = 0
        imported_rels = 0
        
        for rel_type in rel_types:
            if rel_type in import_state:
                imported = import_state[rel_type]
                imported_rels += imported
                rel_data.append({
                    "类型": rel_type,
                    "已导入数量": imported
                })
        
        return {
            "node_data": node_data,
            "rel_data": rel_data,
            "imported_nodes": imported_nodes,
            "imported_rels": imported_rels,
            "total_imported": imported_nodes + imported_rels
        }
    except Exception as e:
        logger.error(f"获取导入状态失败: {e}")
        st.session_state.error_message = f"获取导入状态失败: {str(e)}"
        return None

# 简化版本的导入函数
def run_simple_import(batch_size):
    try:
        logger.info(f"开始导入任务，批次大小: {batch_size}")
        st.session_state.is_importing = True
        st.session_state.error_message = None
        
        # 记录开始时间
        start_time = time.time()
        
        # 创建Streamlit进度条
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # 定义进度回调函数
        def update_progress(current, total, message):
            if total > 0:
                progress = min(current / total, 1.0)
                progress_bar.progress(progress)
                status_text.text(f"{message}: {current}/{total} ({int(progress * 100)}%)")
        
        # 运行导入 - 修复: 确保兼容方法被正确调用
        logger.info("开始导入节点...")
        status_text.text("正在导入节点...")
        node_count = handler.create_graphnodes(batch_size)
        logger.info(f"节点导入完成，数量: {node_count}")
        
        # 更新进度条
        progress_bar.progress(0.5)
        status_text.text(f"节点导入完成，数量: {node_count}，正在导入关系...")
        
        logger.info("开始导入关系...")
        rel_count = handler.create_graphrels(batch_size)
        logger.info(f"关系导入完成，数量: {rel_count}")
        
        # 完成进度条
        progress_bar.progress(1.0)
        status_text.text(f"导入完成! 共导入 {node_count} 个节点和 {rel_count} 条关系")
        
        # 记录结束时间
        end_time = time.time()
        duration = end_time - start_time
        
        # 添加到历史记录
        status = get_simple_import_status()
        if status:
            st.session_state.import_history.append({
                "时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "批次大小": batch_size,
                "导入节点数": node_count,
                "导入关系数": rel_count,
                "耗时(秒)": round(duration, 2)
            })
        
        logger.info(f"导入任务完成，耗时: {round(duration, 2)}秒")
        st.session_state.is_importing = False
        return True
    except Exception as e:
        error_msg = f"导入任务失败: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        st.session_state.error_message = error_msg
        st.session_state.is_importing = False
        return False

# 创建简单的选项卡
tab1, tab2 = st.tabs(["导入状态", "操作控制"])

with tab1:
    # 创建三列布局
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("导入摘要")
        # 获取当前状态
        status = get_simple_import_status()
        
        if status:
            # 显示基本信息（更紧凑的布局）
            st.metric("已导入节点总数", f"{status['imported_nodes']:,}")
            st.metric("已导入关系总数", f"{status['imported_rels']:,}")
            st.metric("总导入数据量", f"{status['total_imported']:,}")
            
            # 数据表格
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.subheader("节点导入详情")
                if status["node_data"]:
                    # 增加表格显示行数
                    st.dataframe(pd.DataFrame(status["node_data"]), height=250, use_container_width=True)
                else:
                    st.info("暂无节点导入数据")
            
            with col_right:
                st.subheader("关系导入详情")
                if status["rel_data"]:
                    # 增加表格显示行数
                    st.dataframe(pd.DataFrame(status["rel_data"]), height=250, use_container_width=True)
                else:
                    st.info("暂无关系导入数据")
        else:
            st.warning("无法获取导入状态数据")
    
    with col2:
        if status and (status["node_data"] or status["rel_data"]):
            # 使用选项卡来节省空间
            chart_tabs = st.tabs(["节点统计", "关系统计"])
            
            with chart_tabs[0]:
                if status["node_data"]:
                    df = pd.DataFrame(status["node_data"])
                    fig = px.bar(
                        df,
                        x="类型",
                        y="已导入数量",
                        title="各类型节点导入数量",
                        height=300,
                        text_auto=True
                    )
                    fig.update_layout(margin=dict(l=0, r=0, t=30, b=0))
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("暂无节点数据可供可视化")
                
            with chart_tabs[1]:
                if status["rel_data"]:
                    df = pd.DataFrame(status["rel_data"])
                    fig = px.bar(
                        df,
                        x="类型",
                        y="已导入数量",
                        title="各类型关系导入数量",
                        height=300,
                        text_auto=True
                    )
                    fig.update_layout(margin=dict(l=0, r=0, t=30, b=0))
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("暂无关系数据可供可视化")

with tab2:
    # 使用两列布局
    col_controls, col_history = st.columns([1, 1])
    
    with col_controls:
        # 一个更紧凑的控制面板
        st.subheader("操作控制")
        
        # 批次大小设置，使用更小的间距
        batch_size = st.slider(
            "批次大小", 
            min_value=config["app"].get("batch_size_min", 1000),
            max_value=config["app"].get("batch_size_max", 50000),
            value=config["app"].get("batch_size_default", 10000),
            step=1000
        )
        
        # 并排放置按钮
        col_start, col_refresh = st.columns(2)
        
        with col_start:
            # 添加更详细的提示
            import_help = "导入指定批次大小的节点和关系数据到Neo4j数据库"
            if st.button("开始导入", disabled=st.session_state.is_importing, key="start_btn", use_container_width=True, help=import_help):
                with st.spinner('正在导入数据，请稍候...'):
                    try:
                        # 首先检查Neo4j连接是否成功初始化
                        if handler.g is None:
                            error_msg = "Neo4j连接未成功初始化，请确保Neo4j数据库已启动"
                            logger.error(error_msg)
                            st.session_state.error_message = error_msg
                            st.error(error_msg)
                        # 如果连接成功，再检查连接是否有效
                        elif handler.g:  # 简单检查连接对象是否存在，而不是调用exists()方法
                            try:
                                # 尝试执行一个简单的Cypher查询来验证连接
                                handler.g.run("RETURN 1 AS test").data()
                                logger.info("Neo4j数据库连接正常，开始导入流程")
                                success = run_simple_import(batch_size)
                                if success:
                                    st.success(f"成功导入一批数据，批次大小: {batch_size}")
                                else:
                                    st.error("导入过程中出现错误，请查看下方错误信息")
                            except Exception as e:
                                error_msg = f"Neo4j数据库连接测试失败: {str(e)}"
                                logger.error(error_msg)
                                st.session_state.error_message = error_msg
                                st.error(error_msg)
                        else:
                            error_msg = "无法连接到Neo4j数据库，请确保数据库已启动"
                            logger.error(error_msg)
                            st.session_state.error_message = error_msg
                            st.error(error_msg)
                    except Exception as e:
                        error_msg = f"导入前检查失败: {str(e)}\n{traceback.format_exc()}"
                        logger.error(error_msg)
                        st.session_state.error_message = error_msg
                        st.error("导入前检查失败，请查看错误详情")
        
        with col_refresh:
            refresh_help = "刷新页面显示最新的导入状态"
            if st.button("刷新状态", key="refresh_btn", use_container_width=True, help=refresh_help):
                st.session_state.last_refresh = time.time()
                st.experimental_rerun()
        
        # 显示错误信息
        if st.session_state.error_message:
            with st.expander("查看错误详情", expanded=True):
                st.error(st.session_state.error_message)
                if st.button("清除错误信息"):
                    st.session_state.error_message = None
                    st.experimental_rerun()
        
        # 高级选项作为折叠面板
        with st.expander("高级选项", expanded=False):
            st.warning("警告：重置导入状态将清除所有导入进度，无法恢复！")
            if st.button("重置导入状态", key="reset_btn"):
                confirm = st.text_input("输入'确认'以重置所有导入状态（这将清除所有导入进度）:")
                if confirm == "确认":
                    try:
                        handler.reset_import_state()
                        st.success("导入状态已重置")
                        st.session_state.import_history = []
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"重置导入状态失败: {e}")
    
    with col_history:
        # 导入历史
        st.subheader("导入历史")
        if st.session_state.import_history:
            # 创建一个更紧凑的数据框，增加高度
            history_df = pd.DataFrame(st.session_state.import_history)
            st.dataframe(history_df, use_container_width=True, height=350)
            
            # 添加清除历史按钮
            if st.button("清除历史记录", key="clear_history"):
                st.session_state.import_history = []
                st.experimental_rerun()
        else:
            st.info("暂无导入历史记录") 