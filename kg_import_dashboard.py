import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import traceback
import json
import io
import os
from datetime import datetime
import time
import pickle
import plotly.express as px
import logging
import sys
from build_graph import MedicalGraph
import streamlit_echarts as st_echarts
from kg_visualization import (
    get_entity_options,
    display_network_graph,
    display_hierarchy_tree,
    display_relationship_matrix,
    display_industry_chain
)
from kg_network_visualization import visualize_network, visualize_matrix
from src.neo4j_handler import Neo4jHandler, Config
from pathlib import Path

# 检测操作系统
import platform
is_windows = platform.system() == "Windows"

# 确保日志目录存在
os.makedirs("logs", exist_ok=True)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join("logs", "app.log"), mode='a'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("KG_Dashboard")

logger.info("启动知识图谱数据导入可视化工具")

# 加载配置文件
def load_config():
    try:
        # 优先加载专用配置
        config_file = None
        if is_windows and os.path.exists('config_windows.json'):
            logger.info("加载Windows专用配置文件")
            config_file = 'config_windows.json'
        # 如果没有专用配置，加载通用配置
        elif os.path.exists('config.json'):
            logger.info("加载通用配置文件")
            config_file = 'config.json'
        
        if config_file:
            with open(config_file, 'r', encoding='utf-8') as f:
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
                    "title": "知识图谱数据导入可视化工具",
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
    page_title="知识图谱数据导入可视化工具",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 自定义CSS，使界面更紧凑
st.markdown("""
<style>
    /* General container padding */
    .block-container {
        padding-top: 0.1rem; /* Reduced from 0.5rem */
        padding-bottom: 0.1rem; /* Reduced from 0.5rem */
        padding-left: 0.5rem; /* Add some horizontal padding */
        padding-right: 0.5rem; /* Add some horizontal padding */
    }
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 3px; /* Reduced gap */
    }
    .stTabs [data-baseweb="tab"] {
        height: 28px; /* Reduced height */
        white-space: pre-wrap;
        padding: 3px 8px; /* Reduced padding */
        font-size: 0.85rem; /* Slightly smaller font for tabs */
    }
    /* Sidebar width (if used, though collapsed) */
    div[data-testid="stSidebar"] {
        width: 180px !important; /* Slightly reduced */
    }
    /* Slider margins */
    div[role="slider"] {
        margin-top: 0.1rem; /* Reduced from 0.3rem */
        margin-bottom: 0.1rem; /* Reduced from 0.3rem */
    }
    /* Alert/Info/Warning messages */
    .stAlert {
        padding: 3px; /* Reduced from 5px */
        margin-top: 0.1rem; /* Reduced from 0.3rem */
        margin-bottom: 0.1rem; /* Reduced from 0.3rem */
        font-size: 0.85rem; /* Slightly smaller font */
    }
    /* Dataframe margins */
    .stDataFrame {
        margin-top: 0.1rem; /* Reduced from 0.3rem */
        margin-bottom: 0.1rem; /* Reduced from 0.3rem */
    }
    /* Button padding */
    .stButton button {
        width: 100%;
        padding: 1px 6px; /* Reduced from 2px 8px */
        font-size: 0.85rem; /* Slightly smaller font */
    }
    /* Markdown headings and text */
    .stMarkdown {
        margin-top: 0.1rem; /* Reduced from 0.2rem */
        margin-bottom: 0.1rem; /* Reduced from 0.2rem */
    }
    h1, h2, h3, h4, h5, h6 {
        margin-top: 0.1rem; /* Reduced from 0.3rem */
        margin-bottom: 0.1rem; /* Reduced from 0.3rem */
    }
    .stMarkdown h3 {
        font-size: 1.1rem; /* Slightly smaller */
    }
    .stMarkdown h4 {
        font-size: 0.95rem; /* Slightly smaller */
    }
    .stMarkdown h5 {
        font-size: 0.85rem; /* Slightly smaller */
        margin-top: 0.05rem; /* Reduced from 0.1rem */
        margin-bottom: 0.05rem; /* Reduced from 0.1rem */
    }
    .stMarkdown h6 {
        font-size: 0.8rem; /* Slightly smaller */
        margin-top: 0.05rem; /* Reduced from 0.1rem */
        margin-bottom: 0.05rem; /* Reduced from 0.1rem */
    }
    /* Element container margins */
    .element-container {
        margin-top: 0.1rem; /* Reduced from 0.2rem */
        margin-bottom: 0.1rem; /* Reduced from 0.2rem */
    }
    /* Selectbox and TextInput heights/margins */
    .stSelectbox, .stTextInput {
        margin-top: 0.1rem; /* Reduced from 0.2rem */
        margin-bottom: 0.1rem; /* Reduced from 0.2rem */
    }
    div[data-baseweb="select"], div[data-baseweb="input"] {
        min-height: 28px; /* Reduced from 32px */
        font-size: 0.85rem; /* Slightly smaller font */
    }
    /* Notification padding */
    div[data-baseweb="notification"] {
        padding: 0.2rem; /* Reduced from 0.3rem */
    }
    /* Echarts margins */
    .echarts-for-react {
        margin: 0 !important;
        padding: 0 !important;
    }
    /* Expander padding */
    .streamlit-expanderHeader {
        padding-top: 0.1rem; /* Reduced from 0.2rem */
        padding-bottom: 0.1rem; /* Reduced from 0.2rem */
        font-size: 0.85rem; /* Slightly smaller font */
    }
    .streamlit-expanderContent {
        padding-top: 0.1rem; /* Reduced from 0.2rem */
        padding-bottom: 0.1rem; /* Reduced from 0.2rem */
    }
    /* Slider height */
    div[data-testid="stSlider"] {
        padding-top: 0.1rem; /* Reduced from 0.2rem */
        padding-bottom: 0.1rem; /* Reduced from 0.2rem */
    }
    /* Metric component */
    div[data-testid="stMetric"] {
        padding: 0.1rem; /* Reduce padding */
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.8rem; /* Smaller label */
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.2rem; /* Smaller value */
    }
    div[data-testid="stMetricDelta"] {
        font-size: 0.7rem; /* Smaller delta */
    }
    /* Plotly chart margins */
    .js-plotly-plot .plotly .modebar {
        margin-top: -20px; /* Move modebar up to save space */
    }
</style>
""", unsafe_allow_html=True)

# 统一的页面标题
st.markdown("<h4 style='font-size:1.1rem; margin:0; padding:0.2rem 0; text-align: center;'>知识图谱数据导入可视化工具 <span style='font-size:0.8rem; color:#666;'>版本: 1.0</span></h4>", unsafe_allow_html=True)

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
# st.markdown("<h3 style='font-size:1.2rem; margin-bottom:0.2rem;'>知识图谱数据导入可视化工具 <span style='font-size:0.8rem; color:#666;'>版本: 1.0</span></h3>", unsafe_allow_html=True)

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
        
        # 验证导入结果 - 新增部分
        import_results = verify_import_results()
        st.session_state.last_import_results = import_results
        
        logger.info(f"导入任务完成，耗时: {round(duration, 2)}秒")
        st.session_state.is_importing = False
        return True
    except Exception as e:
        error_msg = f"导入任务失败: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        st.session_state.error_message = error_msg
        st.session_state.is_importing = False
        return False

# 新增: 验证导入结果的函数
def verify_import_results():
    """验证数据导入结果，返回导入的文件和节点信息"""
    try:
        results = {
            "files": [],
            "node_counts": {},
            "sample_nodes": {},
            "total_nodes": 0,
            "total_rels": 0,
            "verification_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 获取导入的文件列表
        if handler:
            data_files = {
                "company": handler.company_path,
                "industry": handler.industry_path,
                "product": handler.product_path,
                "company_industry": handler.company_industry_path,
                "industry_industry": handler.industry_industry,
                "company_product": handler.company_product_path,
                "product_product": handler.product_product
            }
            
            for file_type, file_path in data_files.items():
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path) / 1024  # KB
                    results["files"].append({
                        "type": file_type,
                        "path": file_path,
                        "size": f"{file_size:.2f} KB"
                    })
        
        # 获取各类型节点数量和示例
        node_types = ["company", "industry", "product"]
        for node_type in node_types:
            # 获取节点数量
            count_query = f"MATCH (n:{node_type}) RETURN count(n) as count"
            count_result = handler.g.run(count_query).data()
            node_count = count_result[0]["count"] if count_result else 0
            results["node_counts"][node_type] = node_count
            results["total_nodes"] += node_count
            
            # 获取前50个节点示例
            sample_query = f"MATCH (n:{node_type}) RETURN n.name as name LIMIT 50"
            sample_results = handler.g.run(sample_query).data()
            results["sample_nodes"][node_type] = [node["name"] for node in sample_results]
        
        # 获取各类型关系数量
        rel_types = ["属于", "拥有", "上级行业", "上游材料", "主营产品"]
        rel_count = 0
        for rel_type in rel_types:
            count_query = f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count"
            try:
                count_result = handler.g.run(count_query).data()
                if count_result:
                    rel_count += count_result[0]["count"]
            except:
                # 关系类型可能不存在
                pass
        
        results["total_rels"] = rel_count
        
        return results
    except Exception as e:
        logger.error(f"验证导入结果时出错: {e}")
        return {"error": str(e)}

# 新增: 检查是否还有数据需要导入
def check_remaining_data():
    """检查是否还有数据需要导入，返回剩余数据数量和详细信息"""
    try:
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
        
        remaining_data = {
            "nodes": {},
            "relationships": {},
            "total_remaining": 0,
            "verification_details": {}
        }
        
        # 检查节点数据
        for node_type, file_path in node_files.items():
            if os.path.exists(file_path):
                try:
                    # 获取文件总行数
                    total_lines = handler._count_file_lines(file_path)
                    # 获取已导入行数
                    imported = handler.import_state.get(node_type, 0)
                    # 计算剩余行数
                    remaining = max(0, total_lines - imported)
                    
                    # 添加验证步骤：检查数据库中实际节点数量
                    query = f"MATCH (n:{node_type}) RETURN count(n) as count"
                    result = handler.g.run(query).data()
                    actual_count = result[0]["count"] if result else 0
                    
                    # 如果实际节点数量与导入状态不一致，调整剩余数量
                    if actual_count > imported:
                        logger.warning(f"{node_type}节点导入状态不一致：导入状态记录{imported}个，实际数据库中有{actual_count}个")
                        # 更新导入状态以匹配实际数据库状态
                        handler.import_state[node_type] = actual_count
                        remaining = max(0, total_lines - actual_count)
                    
                    # 记录验证详情
                    remaining_data["verification_details"][node_type] = {
                        "total_lines": total_lines,
                        "imported_state": imported,
                        "actual_count": actual_count,
                        "remaining": remaining
                    }
                    
                    if remaining > 0:
                        remaining_data["nodes"][node_type] = remaining
                        remaining_data["total_remaining"] += remaining
                except Exception as e:
                    logger.error(f"检查{node_type}节点数据时出错: {e}")
        
        # 检查关系数据
        for rel_type, file_path in rel_files.items():
            if os.path.exists(file_path):
                try:
                    # 获取文件总行数
                    total_lines = handler._count_file_lines(file_path)
                    # 获取已导入行数
                    imported = handler.import_state.get(rel_type, 0)
                    # 计算剩余行数
                    remaining = max(0, total_lines - imported)
                    
                    # 添加验证步骤：尝试检查数据库中实际关系数量
                    # 由于关系类型可能有多种，这里使用一个简化的方法
                    actual_count = 0
                    if rel_type == 'company_industry':
                        query = "MATCH ()-[r:属于|隶属|所属|BELONGS_TO]->() RETURN count(r) as count"
                        result = handler.g.run(query).data()
                        actual_count = result[0]["count"] if result else 0
                    elif rel_type == 'industry_industry':
                        query = "MATCH (:industry)-[r]->(:industry) RETURN count(r) as count"
                        result = handler.g.run(query).data()
                        actual_count = result[0]["count"] if result else 0
                    elif rel_type == 'company_product':
                        query = "MATCH (:company)-[r:拥有|生产|主营|OWNS|PRODUCES]->(:product) RETURN count(r) as count"
                        result = handler.g.run(query).data()
                        actual_count = result[0]["count"] if result else 0
                    elif rel_type == 'product_product':
                        query = "MATCH (:product)-[r]->(:product) RETURN count(r) as count"
                        result = handler.g.run(query).data()
                        actual_count = result[0]["count"] if result else 0
                    
                    # 如果实际关系数量与导入状态不一致，调整剩余数量
                    if actual_count > imported:
                        logger.warning(f"{rel_type}关系导入状态不一致：导入状态记录{imported}条，实际数据库中有{actual_count}条")
                        # 更新导入状态以匹配实际数据库状态
                        handler.import_state[rel_type] = actual_count
                        remaining = max(0, total_lines - actual_count)
                    
                    # 记录验证详情
                    remaining_data["verification_details"][rel_type] = {
                        "total_lines": total_lines,
                        "imported_state": imported,
                        "actual_count": actual_count,
                        "remaining": remaining
                    }
                    
                    if remaining > 0:
                        remaining_data["relationships"][rel_type] = remaining
                        remaining_data["total_remaining"] += remaining
                except Exception as e:
                    logger.error(f"检查{rel_type}关系数据时出错: {e}")
        
        # 保存更新后的导入状态
        handler.save_import_state()
        
        return remaining_data
    except Exception as e:
        logger.error(f"检查剩余数据时出错: {str(e)}")
        return {"error": str(e), "total_remaining": 0}

# 创建选项卡
tab1, tab2, tab3, tab4, tab5 = st.tabs(["导入状态", "操作控制", "图谱探索", "图谱可视化", "行业链分析"])

with tab1:
    status = get_simple_import_status()
    
    if status:
        st.markdown("<h5 style='font-size:0.9rem; margin:0.1rem 0;'>导入摘要</h5>", unsafe_allow_html=True)
        metrics_cols = st.columns(3)
        with metrics_cols[0]:
            st.metric("已导入节点总数", f"{status['imported_nodes']:,}")
        with metrics_cols[1]:
            st.metric("已导入关系总数", f"{status['imported_rels']:,}")
        with metrics_cols[2]:
            st.metric("总导入数据量", f"{status['total_imported']:,}")
        
        main_col1, main_col2 = st.columns([1, 1]) # New main columns for tables and charts
        
        with main_col1:
            st.markdown("<h6 style='font-size:0.8rem; margin:0.1rem 0;'>节点导入详情</h6>", unsafe_allow_html=True)
            if status["node_data"]:
                st.dataframe(pd.DataFrame(status["node_data"]), height=130, use_container_width=True)
            else:
                st.info("暂无节点导入数据")
            
            st.markdown("<h6 style='font-size:0.8rem; margin:0.1rem 0;'>关系导入详情</h6>", unsafe_allow_html=True)
            if status["rel_data"]:
                st.dataframe(pd.DataFrame(status["rel_data"]), height=130, use_container_width=True)
            else:
                st.info("暂无关系导入数据")
        
        with main_col2:
            if status and (status["node_data"] or status["rel_data"]):
                chart_tabs = st.tabs(["节点统计", "关系统计"])
                
                with chart_tabs[0]:
                    if status["node_data"]:
                        df = pd.DataFrame(status["node_data"])
                        fig = px.bar(
                            df,
                            x="类型",
                            y="已导入数量",
                            title="各类型节点导入数量",
                            height=320,  # Adjusted height to fill space
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
                            height=320,  # Adjusted height to fill space
                            text_auto=True
                        )
                        fig.update_layout(margin=dict(l=0, r=0, t=30, b=0))
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("暂无关系数据可供可视化")
    else:
        st.info("暂无导入状态数据。请尝试导入数据。")

with tab2:
    # 使用两列布局
    col_controls, col_history = st.columns([1, 1])
    
    with col_controls:
        # 一个更紧凑的控制面板
        st.markdown("<h5 style='font-size:0.9rem; margin:0.1rem 0;'>操作控制</h5>", unsafe_allow_html=True)
        
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
                        elif handler.g:
                            try:
                                # 尝试执行一个简单的Cypher查询来验证连接
                                handler.g.run("RETURN 1 AS test").data()
                                logger.info("Neo4j数据库连接正常，开始导入流程")
                                
                                # 新增：检查是否有数据需要导入
                                remaining_data = check_remaining_data()
                                if remaining_data.get("total_remaining", 0) == 0:
                                    st.info("所有数据已导入完成，无需再次导入")
                                    
                                    # 显示当前数据库状态摘要
                                    import_results = verify_import_results()
                                    if "error" not in import_results:
                                        st.success(f"数据库中已有 {import_results['total_nodes']} 个节点和 {import_results['total_rels']} 条关系")
                                    
                                    # 提供导入示例数据的建议
                                    if import_results.get('total_nodes', 0) == 0:
                                        st.info("数据库中没有数据。您可以在'图谱探索'标签页中点击'导入示例数据'按钮添加一些示例数据进行测试。")
                                else:
                                    # 显示剩余数据信息
                                    st.info(f"发现 {remaining_data['total_remaining']} 条数据待导入")
                                    
                                    # 如果有数据需要导入，则执行导入
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
            with st.expander("查看错误详情", expanded=False):  # 默认折叠错误信息
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
            
            # 新增：数据库完全重置功能
            st.error("危险操作：重置Neo4j数据库将删除所有节点和关系！")
            if st.button("重置Neo4j数据库", key="reset_db_btn"):
                confirm_db = st.text_input("输入'我确认删除所有数据'以重置Neo4j数据库（此操作将删除所有节点和关系，无法恢复）:")
                if confirm_db == "我确认删除所有数据":
                    try:
                        # 执行清空数据库的Cypher查询
                        handler.g.run("MATCH (n) DETACH DELETE n")
                        # 重置导入状态
                        handler.reset_import_state()
                        st.success("Neo4j数据库已重置，所有节点和关系已删除")
                        st.session_state.import_history = []
                        # 添加一个空的导入结果记录
                        st.session_state.last_import_results = {
                            "files": [],
                            "node_counts": {"company": 0, "industry": 0, "product": 0},
                            "sample_nodes": {"company": [], "industry": [], "product": []},
                            "total_nodes": 0,
                            "total_rels": 0,
                            "verification_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"重置Neo4j数据库失败: {str(e)}")
            
            # 新增：清理导入数据库前的测试数据
            st.warning("清理测试数据：删除系统自动创建的示例数据（华为、阿里巴巴等）")
            if st.button("清理示例数据", key="clean_samples_btn"):
                try:
                    # 删除示例公司节点
                    sample_companies = ["阿里巴巴", "腾讯", "百度", "华为", "小米", "京东", "网易", "美团", "字节跳动", "拼多多"]
                    for company in sample_companies:
                        handler.g.run(f"MATCH (c:company {{name: '{company}'}}) DETACH DELETE c")
                    
                    # 删除示例行业和产品节点
                    handler.g.run("MATCH (i:industry) WHERE i.name IN ['互联网', '电子商务', '人工智能', '通信', '智能硬件'] DETACH DELETE i")
                    handler.g.run("MATCH (p:product) WHERE p.name IN ['淘宝', '微信', '百度搜索', '华为手机', '小米手机'] DETACH DELETE p")
                    
                    st.success("示例数据已清理完成")
                    # 刷新导入结果
                    if 'last_import_results' in st.session_state:
                        st.session_state.last_import_results = verify_import_results()
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"清理示例数据失败: {str(e)}")
        
        # 添加导入结果显示部分
        if 'last_import_results' in st.session_state:
            with st.expander("查看最近导入结果", expanded=True):
                results = st.session_state.last_import_results
                
                if "error" in results:
                    st.error(f"获取导入结果时出错: {results['error']}")
                else:
                    st.success(f"导入验证时间: {results['verification_time']}")
                    
                    # 显示导入文件信息
                    st.markdown("<h6 style='font-size:0.8rem; margin:0.1rem 0;'>导入的数据文件</h6>", unsafe_allow_html=True)
                    file_data = []
                    for file_info in results["files"]:
                        file_data.append({
                            "文件类型": file_info["type"],
                            "文件路径": file_info["path"],
                            "文件大小": file_info["size"]
                        })
                    st.dataframe(pd.DataFrame(file_data), use_container_width=True)
                    
                    # 显示节点数量统计
                    st.markdown("<h6 style='font-size:0.8rem; margin:0.1rem 0;'>节点数量统计</h6>", unsafe_allow_html=True)
                    cols = st.columns(len(results["node_counts"]) + 1)
                    
                    for i, (node_type, count) in enumerate(results["node_counts"].items()):
                        with cols[i]:
                            st.metric(f"{node_type}节点数", f"{count:,}")
                    
                    with cols[-1]:
                        st.metric("总节点数", f"{results['total_nodes']:,}")
                    
                    # 显示前50个节点示例
                    st.markdown("<h6 style='font-size:0.8rem; margin:0.1rem 0;'>节点示例 (前50个)</h6>", unsafe_allow_html=True)
                    node_tabs = st.tabs(list(results["sample_nodes"].keys()))
                    
                    for i, (node_type, samples) in enumerate(results["sample_nodes"].items()):
                        with node_tabs[i]:
                            if samples:
                                sample_text = ", ".join(samples)
                                st.write(sample_text)
                            else:
                                st.info(f"没有找到{node_type}类型的节点")
                                
                    # 显示关系数量
                    st.markdown("<h6 style='font-size:0.8rem; margin:0.1rem 0;'>关系统计</h6>", unsafe_allow_html=True)
                    st.metric("总关系数", f"{results['total_rels']:,}")
    
    with col_history:
        # 导入历史
        st.markdown("<h5 style='font-size:0.9rem; margin:0.1rem 0;'>导入历史</h5>", unsafe_allow_html=True)
        if st.session_state.import_history:
            # 创建一个更紧凑的数据框，减小高度
            history_df = pd.DataFrame(st.session_state.import_history)
            st.dataframe(history_df, use_container_width=True, height=150)
            
            # 添加清除历史按钮
            if st.button("清除历史记录", key="clear_history"):
                st.session_state.import_history = []
                st.experimental_rerun()
        else:
            st.info("暂无导入历史记录")

with tab3:
    st.markdown("<h4 style='font-size:1rem; margin:0.1rem 0;'>图谱探索</h4>", unsafe_allow_html=True)

    # 将示例数据导入功能放入一个折叠面板中，以节省空间
    with st.expander("示例数据操作"):
        if st.button("导入预定义示例数据", key="import_samples", help="导入包括阿里巴巴、华为等公司的示例数据到Neo4j", use_container_width=True):
            with st.spinner("正在导入示例数据..."):
                try:
                    # 定义真实公司示例数据
                    company_data = [
                        {"name": "阿里巴巴", "description": "中国领先的电子商务公司"},
                        {"name": "腾讯", "description": "中国领先的互联网服务提供商"},
                        {"name": "百度", "description": "中国领先的搜索引擎公司"},
                        {"name": "华为", "description": "全球领先的通信设备制造商"},
                        {"name": "小米", "description": "中国领先的智能手机制造商"},
                        {"name": "京东", "description": "中国领先的电子商务平台"},
                        {"name": "网易", "description": "中国领先的互联网科技公司"},
                        {"name": "美团", "description": "中国领先的生活服务电子商务平台"},
                        {"name": "字节跳动", "description": "中国领先的互联网科技公司"},
                        {"name": "拼多多", "description": "中国领先的电子商务平台"}
                    ]
                    industry_data = [{"name": "互联网", "description": "互联网行业"}, {"name": "电子商务", "description": "电子商务行业"}, {"name": "人工智能", "description": "人工智能行业"}, {"name": "通信", "description": "通信行业"}, {"name": "智能硬件", "description": "智能硬件行业"}]
                    product_data = [{"name": "淘宝", "description": "阿里巴巴旗下电子商务平台"}, {"name": "微信", "description": "腾讯旗下社交通讯软件"}, {"name": "百度搜索", "description": "百度旗下搜索引擎"}, {"name": "华为手机", "description": "华为生产的智能手机"}, {"name": "小米手机", "description": "小米生产的智能手机"}]
                    company_industry_data = [
                        {"start_name": "阿里巴巴", "end_name": "互联网"}, {"start_name": "阿里巴巴", "end_name": "电子商务"},
                        {"start_name": "腾讯", "end_name": "互联网"}, {"start_name": "百度", "end_name": "互联网"},
                        {"start_name": "百度", "end_name": "人工智能"}, {"start_name": "华为", "end_name": "通信"},
                        {"start_name": "华为", "end_name": "智能硬件"}, {"start_name": "小米", "end_name": "智能硬件"}
                    ]
                    
                    # 分离不同关系类型的数据
                    company_product_own_data = [
                        {"start_name": "阿里巴巴", "end_name": "淘宝", "rel_weight": "100%"},
                        {"start_name": "腾讯", "end_name": "微信", "rel_weight": "100%"},
                        {"start_name": "百度", "end_name": "百度搜索", "rel_weight": "100%"}
                    ]
                    company_product_produce_data = [
                        {"start_name": "华为", "end_name": "华为手机", "rel_weight": "100%"},
                        {"start_name": "小米", "end_name": "小米手机", "rel_weight": "100%"}
                    ]

                    # 使用handler导入数据
                    handler.import_nodes("company", company_data, is_file=False)
                    handler.import_nodes("industry", industry_data, is_file=False)
                    handler.import_nodes("product", product_data, is_file=False)
                    
                    # 分别导入不同类型的关系
                    handler._import_relationships("company_industry", company_industry_data, "company", "industry", "属于", is_file=False)
                    handler._import_relationships(rel_key="company_product_own", data=company_product_own_data, start_label="company", end_label="product", rel_type="拥有", is_file=False)
                    handler._import_relationships(rel_key="company_product_produce", data=company_product_produce_data, start_label="company", end_label="product", rel_type="生产", is_file=False)

                    total_nodes = len(company_data) + len(industry_data) + len(product_data)
                    total_rels = len(company_industry_data) + len(company_product_own_data) + len(company_product_produce_data)
                    st.success(f"成功导入示例数据: {total_nodes} 个节点和 {total_rels} 条关系")
                    st.info("现在您可以搜索以下示例实体: 阿里巴巴, 腾讯, 百度, 华为, 小米")
                except Exception as e:
                    st.error(f"导入示例数据失败: {str(e)}")
                    st.code(traceback.format_exc())

    # 创建两列用于放置"实体搜索"和"关系探索"控件
    control_col1, control_col2 = st.columns(2)

    with control_col1:
        st.markdown("<h5 style='font-size:0.9rem; margin:0.05rem 0;'>实体搜索</h5>", unsafe_allow_html=True)
        search_cols = st.columns([1, 1])
        with search_cols[0]:
            entity_type = st.selectbox("实体类型", ["公司(company)", "行业(industry)", "产品(product)", "所有类型(all)"], label_visibility="collapsed")
            st.caption("实体类型")
        with search_cols[1]:
            search_term = st.text_input("实体名称", label_visibility="collapsed", placeholder="输入关键词")
            st.caption("搜索关键词")

        with st.expander("搜索选项", expanded=False):
            option_cols = st.columns(2)
            with option_cols[0]:
                case_sensitive = st.checkbox("区分大小写", value=False)
                limit_results = st.slider("结果数量", 10, 100, 20)
            with option_cols[1]:
                exact_match = st.checkbox("精确匹配", value=False)

        if st.button("搜索实体", use_container_width=True):
            if not search_term:
                st.warning("请输入搜索关键词")
            else:
                with st.spinner("正在搜索..."):
                    # (代码内容不变)
                    # ... [原有的实体搜索查询逻辑] ...
                    try:
                        if entity_type == "所有类型(all)": entity_label = None
                        else: entity_label = entity_type.split("(")[1].split(")")[0]
                        if entity_label:
                            if exact_match:
                                if case_sensitive: query = f"MATCH (n:{entity_label}) WHERE n.name = $search_term RETURN n.name AS name, labels(n) AS labels LIMIT {limit_results}"
                                else: query = f"MATCH (n:{entity_label}) WHERE toLower(n.name) = toLower($search_term) RETURN n.name AS name, labels(n) AS labels LIMIT {limit_results}"
                            else:
                                if case_sensitive: query = f"MATCH (n:{entity_label}) WHERE n.name CONTAINS $search_term RETURN n.name AS name, labels(n) AS labels LIMIT {limit_results}"
                                else: query = f"MATCH (n:{entity_label}) WHERE toLower(n.name) CONTAINS toLower($search_term) RETURN n.name AS name, labels(n) AS labels LIMIT {limit_results}"
                        else:
                            if exact_match:
                                if case_sensitive: query = f"MATCH (n) WHERE n.name = $search_term RETURN n.name AS name, labels(n) AS labels LIMIT {limit_results}"
                                else: query = f"MATCH (n) WHERE toLower(n.name) = toLower($search_term) RETURN n.name AS name, labels(n) AS labels LIMIT {limit_results}"
                            else:
                                if case_sensitive: query = f"MATCH (n) WHERE n.name CONTAINS $search_term RETURN n.name AS name, labels(n) AS labels LIMIT {limit_results}"
                                else: query = f"MATCH (n) WHERE toLower(n.name) CONTAINS toLower($search_term) RETURN n.name AS name, labels(n) AS labels LIMIT {limit_results}"
                        result = handler.g.run(query, search_term=search_term).data()
                        if result: st.session_state.search_result = result
                        else:
                            st.info(f"未找到匹配 '{search_term}' 的实体")
                            st.session_state.search_result = []
                    except Exception as e:
                        st.error(f"搜索失败: {str(e)}")
                        st.session_state.search_result = []

    with control_col2:
        st.markdown("<h5 style='font-size:0.9rem; margin:0.05rem 0;'>关系探索</h5>", unsafe_allow_html=True)
        if 'search_result' in st.session_state and st.session_state.search_result:
            entity_names = [item['name'] for item in st.session_state.search_result]
            selected_entity = st.selectbox("从搜索结果选择实体", entity_names, help="选择要探索关系的实体", label_visibility="collapsed")
            st.caption("选择实体进行探索")
            
            depth = st.slider("探索深度", 1, 3, 1, help="设置关系探索的深度")
            
            if st.button("探索关系", use_container_width=True):
                with st.spinner(f"正在探索 {selected_entity} 的关系..."):
                    # (代码内容不变)
                    # ... [原有的关系探索查询逻辑] ...
                    try:
                        query = f"MATCH path = (n)-[*1..{depth}]-(m) WHERE n.name = $entity_name RETURN path LIMIT 100"
                        result = handler.g.run(query, entity_name=selected_entity).data()
                        if result:
                            nodes = set()
                            relationships = []
                            for record in result:
                                path = record['path']
                                path_nodes = path.nodes
                                path_relationships = path.relationships
                                for node in path_nodes: nodes.add((node.identity, node.get('name'), list(node.labels)[0]))
                                for rel in path_relationships:
                                    start_node = rel.start_node.get('name')
                                    end_node = rel.end_node.get('name')
                                    rel_type = type(rel).__name__
                                    relationships.append((start_node, rel_type, end_node))
                            st.session_state.explored_nodes = list(nodes)
                            st.session_state.explored_relationships = relationships
                        else:
                            st.info(f"未找到与 '{selected_entity}' 相关的关系")
                            st.session_state.explored_nodes = []
                            st.session_state.explored_relationships = []
                    except Exception as e:
                        st.error(f"关系探索失败: {str(e)}")
                        st.session_state.explored_nodes = []
                        st.session_state.explored_relationships = []
        else:
            st.info("请先在左侧搜索实体，然后在此处探索关系")

    # --- 结果显示区 ---
    # 使用tabs组织不同类型的结果，使显示更紧凑
    result_tabs = st.tabs(["实体搜索结果", "关系探索结果", "可视化"])

    with result_tabs[0]:
        if 'search_result' in st.session_state and st.session_state.search_result:
            st.success(f"找到 {len(st.session_state.search_result)} 个匹配的实体")
            df = pd.DataFrame(st.session_state.search_result)
            st.dataframe(df, use_container_width=True, height=400)
        else:
            st.info("搜索结果将显示在这里")

    with result_tabs[1]:
        if 'explored_relationships' in st.session_state and st.session_state.explored_relationships:
            st.success(f"找到 {len(st.session_state.explored_relationships)} 条关系")
            rel_data = [{"起始实体": s, "关系类型": r, "目标实体": e} for s, r, e in st.session_state.explored_relationships]
            if rel_data:
                rel_df = pd.DataFrame(rel_data)
                st.dataframe(rel_df, use_container_width=True, height=400)
        else:
            st.info("关系探索结果将显示在这里")
    
    with result_tabs[2]:
        if 'explored_relationships' in st.session_state and st.session_state.explored_relationships:
            st.subheader("关系网络图")
            try:
                # (代码内容不变)
                # ... [原有的可视化逻辑] ...
                node_map = {}
                if 'explored_nodes' in st.session_state:
                    for i, (node_id, node_name, node_type) in enumerate(st.session_state.explored_nodes):
                        node_map[node_name] = i
                success, message = visualize_network(st.session_state.explored_nodes, st.session_state.explored_relationships, node_map)
                if not success:
                    st.error(message)
                    st.warning('无法显示网络图，将显示关系矩阵作为替代')
                    fig = visualize_matrix(st.session_state.explored_relationships, node_map)
                    st.pyplot(fig)
                else:
                    with st.expander('查看关系矩阵'):
                        fig = visualize_matrix(st.session_state.explored_relationships, node_map)
                        st.pyplot(fig)
            except Exception as e:
                st.error(f"创建可视化图表时出错: {e}")
        else:
            st.info("关系探索后，可视化图表将显示在这里")

with tab4:
    st.markdown("<h4 style='font-size:1rem; margin:0.1rem 0;'>知识图谱可视化</h4>", unsafe_allow_html=True)
    
    # 顶部控制面板，使用列来布局
    vis_control_col1, vis_control_col2 = st.columns([1, 1])

    with vis_control_col1:
        st.markdown("<h5 style='font-size:0.9rem; margin:0.1rem 0;'>可视化控制面板</h5>", unsafe_allow_html=True)
        
        # 缓存实体选项
        @st.cache_data(ttl=300)
        def get_entity_options_cached(entity_type):
            return get_entity_options(handler, entity_type)

        entity_type_vis = st.selectbox(
            "选择实体类型进行可视化",
            ["公司(company)", "行业(industry)", "产品(product)"],
            key="vis_entity_type",
            index=0,
            label_visibility="collapsed"
        )
        st.caption("选择实体类型")

        entity_options = get_entity_options_cached(entity_type_vis.split("(")[1].split(")")[0])
        selected_entities = st.multiselect(
            "选择一个或多个实体",
            entity_options,
            default=entity_options[:2] if entity_options else [],
            key="vis_entities",
            label_visibility="collapsed"
        )
        st.caption(f"已选择 {len(selected_entities)} 个实体")
        
    with vis_control_col2:
        st.markdown("<h5 style='font-size:0.9rem; margin:0.1rem 0;'>&nbsp;</h5>", unsafe_allow_html=True) # for alignment
        
        visualization_type = st.selectbox(
            "选择可视化类型",
            ["关系网络图", "层次结构树", "关系矩阵"],
            key="vis_type",
            label_visibility="collapsed"
        )
        st.caption("选择可视化类型")

        depth_vis = st.slider("关系深度", 1, 3, 1, key="vis_depth")

        if st.button("生成可视化图表", use_container_width=True, key="generate_vis"):
            if not selected_entities:
                st.warning("请至少选择一个实体")
            else:
                with st.spinner("正在生成图表..."):
                    try:
                        st.session_state.visualization_data = {
                            "type": visualization_type,
                            "entities": selected_entities,
                            "depth": depth_vis
                        }
                    except Exception as e:
                        st.error(f"生成可视化失败: {e}")
                        st.code(traceback.format_exc())

    # 可视化结果显示区
    st.markdown("<h5 style='font-size:0.9rem; margin:0.1rem 0;'>可视化结果</h5>", unsafe_allow_html=True)
    if 'visualization_data' in st.session_state:
        data = st.session_state.visualization_data
        vis_type = data['type']
        
        with st.container():
            if vis_type == "关系网络图":
                fig = display_network_graph(handler, data['entities'], data['depth'])
                if fig:
                    st_echarts(options=fig, height="600px")
                else:
                    st.info("没有找到可用于生成关系网络图的数据。")
            
            elif vis_type == "层次结构树":
                fig = display_hierarchy_tree(handler, data['entities'][0] if data['entities'] else None)
                if fig:
                    st_echarts(options=fig, height="600px")
                else:
                    st.info("没有找到可用于生成层次结构树的数据。请确保选择了单个实体。")

            elif vis_type == "关系矩阵":
                fig = display_relationship_matrix(handler, data['entities'])
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("没有找到可用于生成关系矩阵的数据。")
    else:
        st.info("点击上方按钮生成可视化图表。")

def get_popular_industries(handler):
    """
    获取数据库中热门的行业（出现频率最高的行业）
    """
    if not handler or not handler.g:
        return []
    try:
        query = (
            "MATCH (i:industry)<-[:BELONGS_TO]-(c:company) "
            "RETURN i.name AS industry, count(c) AS company_count "
            "ORDER BY company_count DESC "
            "LIMIT 20"
        )
        result = handler.g.run(query).data()
        return [row['industry'] for row in result]
    except Exception as e:
        logger.error(f"获取热门行业失败: {e}")
        return []

with tab5:
    st.markdown("<h4 style='font-size:1rem; margin:0.1rem 0;'>行业链分析</h4>", unsafe_allow_html=True)
    
    # 将页面分为控制区和结果区
    control_col, result_col = st.columns([1, 2])
    
    with control_col:
        st.markdown("<h5 style='font-size:0.9rem; margin:0.1rem 0;'>分析参数</h5>", unsafe_allow_html=True)

        # 使用缓存函数获取行业列表
        @st.cache_data(ttl=300)
        def get_popular_industries_cached():
            return get_popular_industries(handler)

        popular_industries = get_popular_industries_cached()
        selected_industry = st.selectbox("选择一个行业进行分析", popular_industries, index=0 if popular_industries else -1, label_visibility="collapsed")
        st.caption("选择行业")

        analysis_type = st.selectbox(
            "选择分析类型",
            ["产业链分析", "竞争情报分析", "企业关联分析", "产品技术分析"],
            key="analysis_type",
            label_visibility="collapsed"
        )
        st.caption("选择分析类型")

        # 将分析维度和按钮放在Expander中，并使用列布局
        with st.expander("高级选项和操作"):
            dim_cols = st.columns(2)
            with dim_cols[0]:
                st.markdown("<h6 style='font-size:0.8rem; margin:0.1rem 0;'>分析维度</h6>", unsafe_allow_html=True)
                upstream_depth = st.slider("上游深度", 1, 3, 1, key="upstream_depth")
                downstream_depth = st.slider("下游深度", 1, 3, 1, key="downstream_depth")
            
            with dim_cols[1]:
                st.markdown("<h6 style='font-size:0.8rem; margin:0.1rem 0;'>&nbsp;</h6>", unsafe_allow_html=True) # for alignment
                if st.button("开始分析", use_container_width=True, key="start_analysis"):
                    if not selected_industry:
                        st.warning("请选择一个行业")
                    else:
                        with st.spinner(f"正在分析 {selected_industry} 的{analysis_type}..."):
                            try:
                                analysis_func = st.session_state.analysis_functions.get(analysis_type)
                                if analysis_func:
                                    results = analysis_func(selected_industry, upstream_depth, downstream_depth)
                                    st.session_state.analysis_results = {
                                        "industry": selected_industry,
                                        "type": analysis_type,
                                        "results": results
                                    }
                                    st.success(f"分析完成，找到 {len(results)} 条结果")
                                else:
                                    st.error(f"未找到“{analysis_type}”对应的分析功能。")
                            except Exception as e:
                                st.error(f"分析失败: {str(e)}")
                                st.code(traceback.format_exc())
    
    with result_col:
        st.markdown("<h5 style='font-size:0.9rem; margin:0.1rem 0;'>分析结果</h5>", unsafe_allow_html=True)
        if 'analysis_results' not in st.session_state:
            st.info("分析结果将显示在这里。")
        else:
            analysis_data = st.session_state.analysis_results
            st.markdown(f"**行业**: {analysis_data['industry']} | **分析类型**: {analysis_data['type']}")
            
            # 使用Tabs来组织数据表格和可视化图表
            res_tab1, res_tab2, res_tab3 = st.tabs(["数据表格", "可视化图表", "数据洞察"])
            
            with res_tab1:
                # 数据表格展示逻辑
                if analysis_data['type'] == "产业链分析":
                    if not analysis_data['results']:
                        st.warning("未找到产业链数据")
                    else:
                        # 提取数据
                        industry_data = analysis_data['results'][0]
                        
                        # 创建上下游表格和企业分布表格
                        upstream_data = []
                        downstream_data = []
                        companies_data = []
                        
                        if 'upstream' in industry_data and industry_data['upstream']:
                            for up in industry_data['upstream']:
                                if hasattr(up, 'get'):
                                    upstream_data.append({"行业名称": up.get('name', '未知'), "类型": "上游"})
                        
                        if 'downstream' in industry_data and industry_data['downstream']:
                            for down in industry_data['downstream']:
                                if hasattr(down, 'get'):
                                    downstream_data.append({"行业名称": down.get('name', '未知'), "类型": "下游"})
                        
                        if 'companies' in industry_data and industry_data['companies']:
                            for company in industry_data['companies']:
                                if hasattr(company, 'get'):
                                    companies_data.append({"企业名称": company.get('name', '未知')})
                        
                        # 显示上下游表格
                        if upstream_data or downstream_data:
                            st.markdown("<h6 style='font-size:0.8rem; margin:0.1rem 0;'>上下游行业</h6>", unsafe_allow_html=True)
                            chain_df = pd.DataFrame(upstream_data + downstream_data)
                            st.dataframe(chain_df, use_container_width=True, height=150)
                        
                        # 显示企业分布表格
                        if companies_data:
                            st.markdown("<h6 style='font-size:0.8rem; margin:0.1rem 0;'>企业分布</h6>", unsafe_allow_html=True)
                            companies_df = pd.DataFrame(companies_data)
                            st.dataframe(companies_df, use_container_width=True, height=150)
                
                elif analysis_data['type'] == "竞争情报分析":
                    if not analysis_data['results']:
                        st.warning("未找到竞争情报数据")
                    else:
                        # 创建竞争关系表格
                        competition_data = []
                        for item in analysis_data['results']:
                            competition_data.append({
                                "企业1": item.get('company1', '未知'),
                                "企业2": item.get('company2', '未知'),
                                "关联强度": item.get('strength', 0)
                            })
                        
                        if competition_data:
                            st.markdown("<h6 style='font-size:0.8rem; margin:0.1rem 0;'>企业竞争关系</h6>", unsafe_allow_html=True)
                            competition_df = pd.DataFrame(competition_data)
                            st.dataframe(competition_df, use_container_width=True, height=250)
                
                elif analysis_data['type'] == "企业关联分析":
                    if not analysis_data['results']:
                        st.warning("未找到企业关联数据")
                    else:
                        # 创建企业关联表格
                        relation_data = []
                        for item in analysis_data['results']:
                            relation_data.append({
                                "企业": item.get('company', '未知'),
                                "关系类型": item.get('relationship', '未知'),
                                "关联实体": item.get('related_entity', '未知'),
                                "实体类型": item.get('entity_type', '未知')
                            })
                        
                        if relation_data:
                            st.markdown("<h6 style='font-size:0.8rem; margin:0.1rem 0;'>企业关联网络</h6>", unsafe_allow_html=True)
                            relation_df = pd.DataFrame(relation_data)
                            st.dataframe(relation_df, use_container_width=True, height=250)
                
                else:  # 产品技术分析
                    if not analysis_data['results']:
                        st.warning("未找到产品技术数据")
                    else:
                        # 创建产品技术表格
                        product_data = []
                        for item in analysis_data['results']:
                            product_data.append({
                                "产品": item.get('product', '未知'),
                                "关联实体数": item.get('connection_count', 0),
                                "关联实体": ", ".join(item.get('related_entities', []))[:50] + ("..." if len(", ".join(item.get('related_entities', []))) > 50 else "")
                            })
                        
                        if product_data:
                            st.markdown("<h6 style='font-size:0.8rem; margin:0.1rem 0;'>产品技术路线图</h6>", unsafe_allow_html=True)
                            product_df = pd.DataFrame(product_data)
                            st.dataframe(product_df, use_container_width=True, height=250)
            
            with res_tab2:
                # 可视化图表展示逻辑
                if analysis_data['type'] == "产业链分析":
                    st.markdown("<h6 style='font-size:0.8rem; margin:0.1rem 0;'>产业链图</h6>", unsafe_allow_html=True)
                    # 这里可以添加产业链可视化代码
                    st.info("产业链图将在此显示")
                
                elif analysis_data['type'] == "竞争情报分析":
                    st.markdown("<h6 style='font-size:0.8rem; margin:0.1rem 0;'>竞争网络图</h6>", unsafe_allow_html=True)
                    # 这里可以添加竞争网络可视化代码
                    st.info("竞争网络图将在此显示")
                
                elif analysis_data['type'] == "企业关联分析":
                    st.markdown("<h6 style='font-size:0.8rem; margin:0.1rem 0;'>关联网络图</h6>", unsafe_allow_html=True)
                    # 这里可以添加企业关联网络可视化代码
                    st.info("企业关联网络图将在此显示")
                
                else:  # 产品技术分析
                    st.markdown("<h6 style='font-size:0.8rem; margin:0.1rem 0;'>产品技术关联图</h6>", unsafe_allow_html=True)
                    # 这里可以添加产品技术关联图可视化代码
                    st.info("产品技术关联图将在此显示")

            with res_tab3:
                # 数据洞察展示逻辑
                # 根据实际数据生成洞察
                insights = []
                
                # 获取数据统计
                if analysis_data['type'] == "产业链分析" and analysis_data['results']:
                    industry_data = analysis_data['results'][0]
                    
                    # 统计数据
                    companies_count = len(industry_data.get('companies', []))
                    products_count = len(industry_data.get('products', []))
                    upstream_count = len(industry_data.get('upstream', []))
                    downstream_count = len(industry_data.get('downstream', []))
                    
                    # 生成洞察
                    if companies_count > 0:
                        insights.append(f"**企业分布**：{analysis_data['industry']}行业共有{companies_count}家相关企业")
                        
                        # 增强：企业集中度分析
                        if companies_count > 5:
                            insights.append(f"**企业集中度**：该行业企业数量较多，市场竞争较为充分")
                        else:
                            insights.append(f"**企业集中度**：该行业企业数量较少，可能存在寡头竞争格局")
                    
                    if products_count > 0:
                        insights.append(f"**产品分布**：该行业涉及{products_count}种产品或服务")
                    
                    if upstream_count > 0 or downstream_count > 0:
                        insights.append(f"**产业链结构**：发现{upstream_count}个上游行业和{downstream_count}个下游行业")
                        
                        # 增强：产业链位置分析
                        if upstream_count > 0 and downstream_count == 0:
                            insights.append(f"**产业链位置**：该行业位于产业链末端，为终端消费或应用行业")
                        elif upstream_count == 0 and downstream_count > 0:
                            insights.append(f"**产业链位置**：该行业位于产业链源头，为基础原材料或技术行业")
                        else:
                            insights.append(f"**产业链位置**：该行业位于产业链中游，承上启下")
                
                elif analysis_data['type'] == "竞争情报分析" and analysis_data['results']:
                    # 统计竞争对手数量
                    companies = set()
                    for item in analysis_data['results']:
                        companies.add(item.get('company1', ''))
                        companies.add(item.get('company2', ''))
                    
                    if companies:
                        insights.append(f"**竞争格局**：{analysis_data['industry']}行业中发现{len(companies)}家主要竞争企业")
                        
                        # 增强：竞争关系密度分析
                        competition_pairs = len(analysis_data['results'])
                        max_pairs = len(companies) * (len(companies) - 1) / 2
                        competition_density = competition_pairs / max_pairs if max_pairs > 0 else 0
                        
                        if competition_density > 0.7:
                            insights.append(f"**竞争强度**：竞争关系密度为{competition_density:.1%}，市场竞争激烈")
                        elif competition_density > 0.3:
                            insights.append(f"**竞争强度**：竞争关系密度为{competition_density:.1%}，市场竞争较为充分")
                        else:
                            insights.append(f"**竞争强度**：竞争关系密度为{competition_density:.1%}，可能存在细分市场区隔")
                
                elif analysis_data['type'] == "企业关联分析" and analysis_data['results']:
                    # 统计关系类型
                    rel_types = {}
                    for item in analysis_data['results']:
                        rel_type = item.get('relationship', '未知')
                        if rel_type not in rel_types:
                            rel_types[rel_type] = 0
                        rel_types[rel_type] += 1
                    
                    if rel_types:
                        main_rel_type = max(rel_types.items(), key=lambda x: x[1])[0]
                        insights.append(f"**关系网络**：企业间主要通过'{main_rel_type}'关系进行连接，共{len(rel_types)}种关联")
                        
                        # 增强：关系多样性分析
                        if len(rel_types) > 3:
                            insights.append(f"**关系多样性**：企业间存在{len(rel_types)}种不同类型的关联，关系网络丰富多样")
                
                elif analysis_data['type'] == "产品技术分析" and analysis_data['results']:
                    # 统计产品数量和关联强度
                    if analysis_data['results']:
                        product_count = len(analysis_data['results'])
                        avg_connections = sum(item.get('connection_count', 0) for item in analysis_data['results']) / product_count if product_count > 0 else 0
                        
                        insights.append(f"**产品分析**：{analysis_data['industry']}行业涉及{product_count}种主要产品，平均每种产品有{avg_connections:.1f}个关联实体")
                        
                        # 增强：产品关联度分析
                        if avg_connections > 5:
                            insights.append(f"**产品关联度**：产品平均关联度为{avg_connections:.1f}，产品间集成度高")
                        else:
                            insights.append(f"**产品关联度**：产品平均关联度为{avg_connections:.1f}，产品相对独立")
                        
                        # 增强：产品技术路径分析
                        if avg_connections > 0:
                            max_conn_item = max(analysis_data['results'], key=lambda x: x.get('connection_count', 0))
                            insights.append(f"**核心产品**：{max_conn_item.get('product', '')}是该行业关联最广泛的产品，共有{max_conn_item.get('connection_count', 0)}个关联实体")
                
                # 如果没有生成任何洞察，添加一个通用提示
                if not insights:
                    insights.append("**数据不足**：当前分析的数据量不足以生成有意义的洞察。请尝试选择其他行业或导入更多数据。")
                
                # 显示洞察
                for insight in insights:
                    st.markdown(f"- {insight}")