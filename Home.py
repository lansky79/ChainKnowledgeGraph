"""
知识图谱可视化应用主入口
"""
import streamlit as st
import logging
import os
import sys
import traceback
from datetime import datetime

# 导入自定义模块
from utils.db_connector import Neo4jConnector
from utils.data_processor import process_neo4j_results, get_entity_options
from utils.logger import setup_logger
from visualizers.network_viz import display_network, create_echarts_graph
from config import APP_CONFIG

# 设置日志
logger = setup_logger("KnowledgeGraph")

# 页面配置
st.set_page_config(
    page_title="快速导航",
    page_icon="🏠",
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
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 30px;
        padding: 5px 10px;
    }
    /* 尝试修改侧边栏导航标题 */
    .css-1d391kg p {
        font-size: 0px;
    }
    .css-1d391kg p:after {
        content: "快速导航";
        font-size: 14px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# 初始化数据库连接
@st.cache_resource
def get_db_connector():
    """获取数据库连接器（缓存资源）"""
    return Neo4jConnector()

db = get_db_connector()

# 应用标题
st.title("快速导航")

# 欢迎信息
st.markdown("""
## 欢迎使用知识图谱可视化系统

这是一个功能完整的知识图谱管理和可视化平台，提供数据导入、智能搜索、分析统计、实体管理等功能。

### 🚀 快速开始
""")

# 功能导航卡片
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    #### 📊 数据管理
    - **[数据管理](/数据管理)** - 导入和管理知识图谱数据
    - **[实体管理](/实体管理)** - 创建、编辑、删除实体和关系
    
    #### 🔍 数据探索  
    - **[智能搜索](/智能搜索)** - 智能搜索和实体推荐
    - **[图谱可视](/图谱可视)** - 多种图谱可视化方式
    """)

with col2:
    st.markdown("""
    #### 📈 数据分析
    - **[数据分析](/数据分析)** - 统计分析和趋势洞察
    - **[高级查询](/高级查询)** - 自定义查询构建器
    
    #### ⚙️ 系统功能
    - 数据导出和分享
    - 批量操作管理
    """)

# 数据库状态概览
st.subheader("📊 系统状态概览")

# 侧边栏保持空白，只显示页面导航

# 主要内容区域 - 显示详细的数据库状态
try:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        company_count = db.get_node_count("company")
        st.metric("公司节点数量", f"{company_count:,}")
    
    with col2:
        industry_count = db.get_node_count("industry")
        st.metric("行业节点数量", f"{industry_count:,}")
    
    with col3:
        product_count = db.get_node_count("product")
        st.metric("产品节点数量", f"{product_count:,}")
    
    # 显示系统使用指南
    st.subheader("📖 使用指南")
    
    st.markdown("""
    ### 🎯 快速开始步骤
    
    1. **📊 数据准备** - 如果是首次使用，建议先到"数据管理"页面导入示例数据
    2. **🔍 探索数据** - 使用"智能搜索"功能查找感兴趣的实体
    3. **📈 分析洞察** - 在"数据分析"页面查看统计信息和趋势
    4. **⚙️ 管理维护** - 使用"实体管理"功能编辑和维护数据
    5. **🎨 可视化** - 在"图谱可视"页面查看多种图表类型
    6. **🔧 高级查询** - 使用查询构建器进行复杂数据查询
    
    ### 💡 功能亮点
    
    - **智能搜索**: 模糊搜索、实体推荐、相似度计算
    - **丰富分析**: 7种分析类型、15+种图表
    - **完整管理**: 创建、编辑、删除实体和关系
    - **数据导出**: 多格式导出、分享链接
    - **批量操作**: 高效的批量数据处理
    - **高级查询**: 可视化查询构建器和Cypher编辑器
    """)
    
except Exception as e:
    st.error(f"获取系统状态时出错: {str(e)}")
    logger.error(f"获取系统状态时出错: {str(e)}")

# 页脚
st.markdown("---")
st.caption(f"知识图谱可视化系统 | {datetime.now().strftime('%Y-%m-%d')}")

if __name__ == "__main__":
    logger.info("应用启动") 