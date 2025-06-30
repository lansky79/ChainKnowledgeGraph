import streamlit as st
import pandas as pd
import os
import json
import time
from datetime import datetime
import logging
import sys

# 确保日志目录存在
os.makedirs("logs", exist_ok=True)

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join("logs", "simple_app.log"), mode='a', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("Simple_KG_Dashboard")

logger.info("启动简化版知识图谱数据查看工具")

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
                    "title": "知识图谱数据查看工具 - 简化版",
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
    page_title="知识图谱数据查看工具 - 简化版",
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

# 主页面
st.title("知识图谱数据查看工具 - 简化版")

# 节点和关系数据加载函数
def load_data_file(filepath, limit=None):
    """加载JSON行数据文件，并返回DataFrame"""
    try:
        if not os.path.exists(filepath):
            logger.warning(f"数据文件不存在: {filepath}")
            return pd.DataFrame()
        
        data = []
        with open(filepath, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if limit and i >= limit:
                    break
                try:
                    item = json.loads(line.strip())
                    data.append(item)
                except json.JSONDecodeError:
                    logger.error(f"解析JSON行失败: {line}")
                    continue
        
        return pd.DataFrame(data)
    except Exception as e:
        logger.error(f"加载数据文件失败: {e}")
        return pd.DataFrame()

# 从配置中获取数据文件路径
def get_data_paths():
    """从配置中获取数据文件路径"""
    if 'data_paths' in config:
        return config['data_paths']
    else:
        # 默认数据路径
        return {
            "company": os.path.join("data", "company.json"),
            "industry": os.path.join("data", "industry.json"),
            "product": os.path.join("data", "product.json"),
            "company_industry": os.path.join("data", "company_industry.json"),
            "industry_industry": os.path.join("data", "industry_industry.json"),
            "company_product": os.path.join("data", "company_product.json"),
            "product_product": os.path.join("data", "product_product.json")
        }

# 获取数据文件路径
data_paths = get_data_paths()

# 创建选项卡
tab1, tab2, tab3 = st.tabs(["数据查看", "配置信息", "系统状态"])

with tab1:
    st.header("数据查看")
    
    # 选择数据类型
    data_type = st.selectbox(
        "选择数据类型",
        ["节点 - 公司", "节点 - 行业", "节点 - 产品", 
         "关系 - 公司-行业", "关系 - 行业-行业", "关系 - 公司-产品", "关系 - 产品-产品"]
    )
    
    # 设置显示行数
    display_rows = st.slider("显示行数", 10, 100, 20)
    
    # 根据选择的数据类型加载相应的数据
    if data_type == "节点 - 公司":
        df = load_data_file(data_paths.get("company", os.path.join("data", "company.json")), limit=1000)
    elif data_type == "节点 - 行业":
        df = load_data_file(data_paths.get("industry", os.path.join("data", "industry.json")), limit=1000)
    elif data_type == "节点 - 产品":
        df = load_data_file(data_paths.get("product", os.path.join("data", "product.json")), limit=1000)
    elif data_type == "关系 - 公司-行业":
        df = load_data_file(data_paths.get("company_industry", os.path.join("data", "company_industry.json")), limit=1000)
    elif data_type == "关系 - 行业-行业":
        df = load_data_file(data_paths.get("industry_industry", os.path.join("data", "industry_industry.json")), limit=1000)
    elif data_type == "关系 - 公司-产品":
        df = load_data_file(data_paths.get("company_product", os.path.join("data", "company_product.json")), limit=1000)
    elif data_type == "关系 - 产品-产品":
        df = load_data_file(data_paths.get("product_product", os.path.join("data", "product_product.json")), limit=1000)
    
    # 显示数据
    if not df.empty:
        st.write(f"共 {len(df)} 条记录")
        st.dataframe(df.head(display_rows))
    else:
        st.warning(f"未找到{data_type}数据")

with tab2:
    st.header("配置信息")
    
    # 显示Neo4j配置
    st.subheader("Neo4j配置")
    neo4j_config = config.get('neo4j', {})
    st.write(f"连接URI: {neo4j_config.get('uri', 'bolt://127.0.0.1:7687')}")
    st.write(f"用户名: {neo4j_config.get('username', 'neo4j')}")
    st.write("密码: ********")
    
    # 显示应用配置
    st.subheader("应用配置")
    app_config = config.get('app', {})
    for key, value in app_config.items():
        st.write(f"{key}: {value}")
    
    # 显示数据文件路径
    st.subheader("数据文件路径")
    for key, value in data_paths.items():
        st.write(f"{key}: {value}")

with tab3:
    st.header("系统状态")
    
    # 显示系统信息
    st.subheader("运行环境")
    st.write(f"Python版本: {sys.version}")
    st.write(f"操作系统: {sys.platform}")
    st.write(f"当前工作目录: {os.getcwd()}")
    
    # 显示数据文件状态
    st.subheader("数据文件状态")
    data_file_status = []
    
    for name, path in data_paths.items():
        if os.path.exists(path):
            size = os.path.getsize(path) / 1024  # KB
            mtime = datetime.fromtimestamp(os.path.getmtime(path)).strftime('%Y-%m-%d %H:%M:%S')
            status = "存在"
        else:
            size = 0
            mtime = "N/A"
            status = "不存在"
        
        data_file_status.append({
            "文件名": name,
            "路径": path,
            "状态": status,
            "大小(KB)": round(size, 2),
            "修改时间": mtime
        })
    
    st.table(pd.DataFrame(data_file_status))
    
    # 刷新按钮
    if st.button("刷新页面"):
        st.experimental_rerun()

# 页脚
st.markdown("---")
st.markdown("知识图谱数据查看工具 - 简化版 | 不依赖Neo4j连接 | 仅供测试使用") 