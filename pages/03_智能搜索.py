"""
智能搜索页面
提供高级搜索、实体推荐、搜索历史等功能
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import uuid

# 导入自定义模块
from utils.db_connector import Neo4jConnector
from utils.search_engine import SearchEngine
from utils.export_handler import ExportHandler
from utils.logger import setup_logger
from visualizers.network_viz import display_network

# 设置日志
logger = setup_logger("KG_Smart_Search")

# 页面配置
st.set_page_config(
    page_title="智能搜索",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
    .search-result-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        background-color: #f9f9f9;
    }
    .entity-type-badge {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
        margin-right: 8px;
    }
    .company-badge { background-color: #e3f2fd; color: #1976d2; }
    .industry-badge { background-color: #f3e5f5; color: #7b1fa2; }
    .product-badge { background-color: #e8f5e8; color: #388e3c; }
    .relevance-score {
        float: right;
        color: #666;
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)

# 初始化数据库连接和搜索引擎
@st.cache_resource
def get_search_engine():
    """获取搜索引擎实例（缓存资源）"""
    db = Neo4jConnector()
    return SearchEngine(db)

@st.cache_resource
def get_export_handler():
    """获取导出处理器实例（缓存资源）"""
    db = Neo4jConnector()
    return ExportHandler(db)

search_engine = get_search_engine()
export_handler = get_export_handler()

# 初始化会话状态
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "search_history" not in st.session_state:
    st.session_state.search_history = []

if "selected_entity" not in st.session_state:
    st.session_state.selected_entity = None

if "selected_entity_type" not in st.session_state:
    st.session_state.selected_entity_type = None

# 页面标题
st.title("🔍 智能搜索")

# 创建主要布局
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("搜索知识图谱")
    
    # 搜索配置
    search_col1, search_col2 = st.columns([3, 1])
    
    with search_col1:
        search_query = st.text_input(
            "搜索实体",
            placeholder="输入公司、行业或产品名称...",
            key="main_search"
        )
    
    with search_col2:
        entity_type_filter = st.selectbox(
            "类型筛选",
            ["全部", "公司", "行业", "产品"],
            key="entity_filter"
        )
    
    # 搜索建议
    if search_query and len(search_query) >= 1:
        # 转换类型筛选
        type_mapping = {"全部": None, "公司": "company", "行业": "industry", "产品": "product"}
        filter_type = type_mapping.get(entity_type_filter)
        
        # 获取搜索建议
        suggestions = search_engine.get_search_suggestions(
            search_query, 
            entity_type=filter_type,
            limit=5
        )
        
        if suggestions:
            st.write("**搜索建议:**")
            suggestion_cols = st.columns(min(len(suggestions), 5))
            for i, suggestion in enumerate(suggestions):
                with suggestion_cols[i]:
                    if st.button(suggestion, key=f"suggestion_{i}"):
                        st.session_state.main_search = suggestion
                        st.rerun()
    
    # 执行搜索
    if search_query and len(search_query) >= 2:
        with st.spinner("正在搜索..."):
            # 执行搜索
            filter_type = type_mapping.get(entity_type_filter)
            search_results = search_engine.fuzzy_search(
                search_query,
                entity_type=filter_type,
                limit=20
            )
            
            if search_results:
                st.success(f"找到 {len(search_results)} 个相关实体")
                
                # 显示搜索结果
                for i, result in enumerate(search_results):
                    entity_name = result["entity_name"]
                    entity_type = result["entity_type"]
                    description = result["description"]
                    relevance = result["relevance_score"]
                    
                    # 实体类型标签样式
                    type_labels = {
                        "company": ("公司", "company-badge"),
                        "industry": ("行业", "industry-badge"),
                        "product": ("产品", "product-badge")
                    }
                    
                    type_label, badge_class = type_labels.get(entity_type, ("未知", ""))
                    
                    # 创建结果卡片
                    with st.container():
                        st.markdown(f"""
                        <div class="search-result-card">
                            <div>
                                <span class="entity-type-badge {badge_class}">{type_label}</span>
                                <strong>{entity_name}</strong>
                                <span class="relevance-score">相关度: {relevance:.2f}</span>
                            </div>
                            <div style="margin-top: 8px; color: #666;">
                                {description}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # 操作按钮
                        button_col1, button_col2, button_col3 = st.columns([1, 1, 2])
                        
                        with button_col1:
                            if st.button("查看详情", key=f"detail_{i}"):
                                st.session_state.selected_entity = entity_name
                                st.session_state.selected_entity_type = entity_type
                                # 更新搜索历史
                                search_engine.update_search_history(
                                    st.session_state.session_id,
                                    entity_name,
                                    entity_type
                                )
                        
                        with button_col2:
                            if st.button("获取推荐", key=f"recommend_{i}"):
                                st.session_state.selected_entity = entity_name
                                st.session_state.selected_entity_type = entity_type
                                st.session_state.show_recommendations = True
                        
                        st.markdown("---")
            
            else:
                st.warning(f"未找到包含 '{search_query}' 的实体")
    
    elif search_query and len(search_query) < 2:
        st.info("请输入至少2个字符进行搜索")

with col2:
    st.subheader("搜索工具")
    
    # 搜索历史
    with st.expander("🕒 搜索历史", expanded=True):
        history = search_engine.get_search_history(st.session_state.session_id, limit=10)
        
        if history:
            for item in history:
                entity_name = item["entity_name"]
                entity_type = item["entity_type"]
                search_count = item["search_count"]
                
                type_labels = {
                    "company": "🏢",
                    "industry": "🏭", 
                    "product": "📦"
                }
                
                icon = type_labels.get(entity_type, "❓")
                
                if st.button(
                    f"{icon} {entity_name} ({search_count}次)",
                    key=f"history_{entity_name}",
                    help=f"点击查看 {entity_name} 的详情"
                ):
                    st.session_state.selected_entity = entity_name
                    st.session_state.selected_entity_type = entity_type
                    st.rerun()
        else:
            st.info("暂无搜索历史")
    
    # 快速搜索
    with st.expander("⚡ 快速搜索"):
        st.write("**热门实体:**")
        
        # 获取一些示例实体
        try:
            db = Neo4jConnector()
            sample_query = """
            CALL {
                MATCH (c:company) RETURN c.name as name, 'company' as type LIMIT 3
                UNION ALL
                MATCH (i:industry) RETURN i.name as name, 'industry' as type LIMIT 2
                UNION ALL
                MATCH (p:product) RETURN p.name as name, 'product' as type LIMIT 2
            }
            RETURN name, type
            ORDER BY type, name
            """
            
            sample_results = db.query(sample_query)
            
            for result in sample_results:
                name = result["name"]
                entity_type = result["type"]
                
                type_labels = {
                    "company": "🏢",
                    "industry": "🏭",
                    "product": "📦"
                }
                
                icon = type_labels.get(entity_type, "❓")
                
                if st.button(f"{icon} {name}", key=f"quick_{name}"):
                    st.session_state.selected_entity = name
                    st.session_state.selected_entity_type = entity_type
                    st.rerun()
                    
        except Exception as e:
            st.error(f"获取示例数据失败: {str(e)}")

# 显示选中实体的详细信息
if st.session_state.selected_entity:
    st.markdown("---")
    st.subheader(f"📋 {st.session_state.selected_entity} 详细信息")
    
    entity_name = st.session_state.selected_entity
    entity_type = st.session_state.selected_entity_type
    
    # 创建选项卡
    detail_tab1, detail_tab2, detail_tab3 = st.tabs(["基本信息", "推荐实体", "相似实体"])
    
    with detail_tab1:
        # 显示基本信息
        try:
            db = Neo4jConnector()
            info_query = f"""
            MATCH (n:{entity_type} {{name: $name}})
            RETURN n.name as name, n.description as description
            """
            
            info_results = db.query(info_query, {"name": entity_name})
            
            if info_results:
                info = info_results[0]
                st.write(f"**名称:** {info['name']}")
                st.write(f"**描述:** {info.get('description', '暂无描述')}")
                
                # 显示关系统计
                if entity_type == "company":
                    stats_query = """
                    MATCH (c:company {name: $name})
                    OPTIONAL MATCH (c)-[:所属行业]->(i:industry)
                    OPTIONAL MATCH (c)-[:主营产品]->(p:product)
                    RETURN count(DISTINCT i) as industries, count(DISTINCT p) as products
                    """
                elif entity_type == "industry":
                    stats_query = """
                    MATCH (i:industry {name: $name})
                    OPTIONAL MATCH (c:company)-[:所属行业]->(i)
                    OPTIONAL MATCH (c)-[:主营产品]->(p:product)
                    RETURN count(DISTINCT c) as companies, count(DISTINCT p) as products
                    """
                else:  # product
                    stats_query = """
                    MATCH (p:product {name: $name})
                    OPTIONAL MATCH (c:company)-[:主营产品]->(p)
                    OPTIONAL MATCH (c)-[:所属行业]->(i:industry)
                    RETURN count(DISTINCT c) as companies, count(DISTINCT i) as industries
                    """
                
                stats_results = db.query(stats_query, {"name": entity_name})
                
                if stats_results:
                    stats = stats_results[0]
                    st.write("**关系统计:**")
                    
                    stats_col1, stats_col2 = st.columns(2)
                    
                    if entity_type == "company":
                        with stats_col1:
                            st.metric("所属行业", stats.get("industries", 0))
                        with stats_col2:
                            st.metric("主营产品", stats.get("products", 0))
                    elif entity_type == "industry":
                        with stats_col1:
                            st.metric("相关公司", stats.get("companies", 0))
                        with stats_col2:
                            st.metric("相关产品", stats.get("products", 0))
                    else:  # product
                        with stats_col1:
                            st.metric("相关公司", stats.get("companies", 0))
                        with stats_col2:
                            st.metric("相关行业", stats.get("industries", 0))
                
                # 添加导出功能
                st.markdown("---")
                st.write("**导出实体详情:**")
                
                export_col1, export_col2, export_col3 = st.columns(3)
                
                with export_col1:
                    if st.button("导出JSON", key=f"export_json_{entity_name}"):
                        success, message, file_data = export_handler.export_entity_details(
                            entity_name, entity_type, "json"
                        )
                        if success and file_data:
                            st.download_button(
                                label="下载JSON文件",
                                data=file_data,
                                file_name=f"{entity_name}_details.json",
                                mime="application/json",
                                key=f"download_json_{entity_name}"
                            )
                            st.success(message)
                        else:
                            st.error(message)
                
                with export_col2:
                    if st.button("导出CSV", key=f"export_csv_{entity_name}"):
                        success, message, file_data = export_handler.export_entity_details(
                            entity_name, entity_type, "csv"
                        )
                        if success and file_data:
                            st.download_button(
                                label="下载CSV文件",
                                data=file_data,
                                file_name=f"{entity_name}_details.csv",
                                mime="text/csv",
                                key=f"download_csv_{entity_name}"
                            )
                            st.success(message)
                        else:
                            st.error(message)
                
                with export_col3:
                    if st.button("创建分享链接", key=f"share_{entity_name}"):
                        # 创建分享配置
                        share_config = {
                            "entity_name": entity_name,
                            "entity_type": entity_type,
                            "view_type": "entity_details"
                        }
                        
                        success, message, share_id = export_handler.create_share_link(
                            share_config, f"{entity_name} 实体详情"
                        )
                        
                        if success and share_id:
                            share_url = f"?share_id={share_id}"
                            st.success(message)
                            st.code(f"分享链接: {share_url}")
                            st.info("💡 复制上面的链接参数，添加到当前页面URL后即可分享")
                        else:
                            st.error(message)
            
        except Exception as e:
            st.error(f"获取实体信息失败: {str(e)}")
    
    with detail_tab2:
        # 显示推荐实体
        with st.spinner("正在获取推荐..."):
            recommendations = search_engine.get_recommendations(
                entity_name, 
                entity_type, 
                limit=10
            )
            
            if recommendations:
                st.success(f"为您推荐 {len(recommendations)} 个相关实体")
                
                for rec_idx, rec in enumerate(recommendations):
                    rec_name = rec["entity_name"]
                    rec_type = rec["entity_type"]
                    relation_type = rec["relation_type"]
                    confidence = rec["confidence_score"]
                    description = rec.get("description", "")
                    
                    type_labels = {
                        "company": ("🏢", "公司"),
                        "industry": ("🏭", "行业"),
                        "product": ("📦", "产品")
                    }
                    
                    icon, type_label = type_labels.get(rec_type, ("❓", "未知"))
                    
                    with st.container():
                        st.markdown(f"""
                        **{icon} {rec_name}** ({type_label})  
                        关系: {relation_type} | 置信度: {confidence:.2f}  
                        {description}
                        """)
                        
                        if st.button(f"查看 {rec_name}", key=f"rec_{entity_name}_{rec_idx}_{rec_name}_{rec_type}"):
                            st.session_state.selected_entity = rec_name
                            st.session_state.selected_entity_type = rec_type
                            st.rerun()
                        
                        st.markdown("---")
            else:
                st.info("暂无推荐实体")
    
    with detail_tab3:
        # 显示相似实体
        with st.spinner("正在计算相似度..."):
            similar_entities = search_engine.get_similar_entities(
                entity_name,
                entity_type,
                limit=10
            )
            
            if similar_entities:
                st.success(f"找到 {len(similar_entities)} 个相似实体")
                
                for sim_idx, sim in enumerate(similar_entities):
                    sim_name = sim["entity_name"]
                    sim_type = sim["entity_type"]
                    similarity = sim["similarity_score"]
                    description = sim.get("description", "")
                    
                    type_labels = {
                        "company": ("🏢", "公司"),
                        "industry": ("🏭", "行业"),
                        "product": ("📦", "产品")
                    }
                    
                    icon, type_label = type_labels.get(sim_type, ("❓", "未知"))
                    
                    with st.container():
                        st.markdown(f"""
                        **{icon} {sim_name}** ({type_label})  
                        相似度: {similarity:.3f}  
                        {description}
                        """)
                        
                        if st.button(f"查看 {sim_name}", key=f"sim_{entity_name}_{sim_idx}_{sim_name}_{sim_type}"):
                            st.session_state.selected_entity = sim_name
                            st.session_state.selected_entity_type = sim_type
                            st.rerun()
                        
                        st.markdown("---")
            else:
                st.info("暂无相似实体")

# 页脚
st.markdown("---")
st.caption(f"智能搜索系统 | {datetime.now().strftime('%Y-%m-%d')}")