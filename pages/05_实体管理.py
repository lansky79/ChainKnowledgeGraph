"""
实体管理页面
提供实体搜索、查看、编辑、关系管理、批量操作等功能
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import json

# 导入自定义模块
from utils.db_connector import Neo4jConnector
from utils.search_engine import SearchEngine
from utils.logger import setup_logger
from components.entity_detail import EntityDetail

# 设置日志
logger = setup_logger("KG_Entity_Management")

# 页面配置
st.set_page_config(
    page_title="实体管理",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
    .entity-card {
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
    .action-button {
        margin: 2px;
        padding: 4px 8px;
        font-size: 12px;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 4px;
        padding: 10px;
        margin: 10px 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 4px;
        padding: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# 初始化组件
@st.cache_resource
def get_components():
    """获取组件实例（缓存资源）"""
    db = Neo4jConnector()
    return {
        "db": db,
        "search_engine": SearchEngine(db),
        "entity_detail": EntityDetail(db)
    }

components = get_components()
db = components["db"]
search_engine = components["search_engine"]
entity_detail = components["entity_detail"]

# 初始化会话状态
if "selected_entity" not in st.session_state:
    st.session_state.selected_entity = None

if "selected_entity_type" not in st.session_state:
    st.session_state.selected_entity_type = None

if "management_mode" not in st.session_state:
    st.session_state.management_mode = "browse"

if "show_confirmation" not in st.session_state:
    st.session_state.show_confirmation = False

# 页面标题
st.title("⚙️ 实体管理")

# 创建侧边栏
st.sidebar.header("管理选项")

# 管理模式选择
management_mode = st.sidebar.selectbox(
    "管理模式",
    ["browse", "edit", "batch", "create"],
    format_func=lambda x: {
        "browse": "🔍 浏览模式",
        "edit": "✏️ 编辑模式", 
        "batch": "📦 批量操作",
        "create": "➕ 创建实体"
    }.get(x, x),
    key="management_mode_select"
)

st.session_state.management_mode = management_mode

# 实体类型选择
entity_type_options = {
    "company": "公司",
    "industry": "行业",
    "product": "产品"
}

selected_entity_type = st.sidebar.selectbox(
    "实体类型",
    list(entity_type_options.keys()),
    format_func=lambda x: entity_type_options.get(x, x),
    key="entity_type_select"
)

# 搜索功能
st.sidebar.subheader("🔍 搜索实体")
search_query = st.sidebar.text_input("搜索关键词", placeholder="输入实体名称...")

# 快速操作按钮
st.sidebar.subheader("⚡ 快速操作")

if st.sidebar.button("🔄 刷新数据"):
    st.cache_data.clear()
    st.rerun()

if st.sidebar.button("📊 查看统计"):
    st.session_state.show_statistics = True

# 根据管理模式显示不同内容
if management_mode == "browse":
    # 浏览模式
    st.subheader(f"🔍 浏览{entity_type_options[selected_entity_type]}")
    
    # 获取实体列表
    if search_query:
        # 搜索模式
        search_results = search_engine.fuzzy_search(
            search_query, 
            entity_type=selected_entity_type,
            limit=50
        )
        
        if search_results:
            st.success(f"找到 {len(search_results)} 个匹配的实体")
            
            for i, result in enumerate(search_results):
                entity_name = result["entity_name"]
                description = result["description"]
                relevance = result["relevance_score"]
                
                # 实体卡片
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        type_badge_class = {
                            "company": "company-badge",
                            "industry": "industry-badge", 
                            "product": "product-badge"
                        }.get(selected_entity_type, "")
                        
                        st.markdown(f"""
                        <div class="entity-card">
                            <span class="entity-type-badge {type_badge_class}">
                                {entity_type_options[selected_entity_type]}
                            </span>
                            <strong>{entity_name}</strong>
                            <span style="float: right; color: #666;">相关度: {relevance:.2f}</span>
                            <br>
                            <small style="color: #666;">{description}</small>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        if st.button("查看详情", key=f"view_{i}_{entity_name}"):
                            st.session_state.selected_entity = entity_name
                            st.session_state.selected_entity_type = selected_entity_type
                    
                    with col3:
                        if st.button("编辑", key=f"edit_{i}_{entity_name}"):
                            st.session_state.selected_entity = entity_name
                            st.session_state.selected_entity_type = selected_entity_type
                            st.session_state.management_mode = "edit"
                            st.rerun()
        else:
            st.warning(f"未找到包含 '{search_query}' 的{entity_type_options[selected_entity_type]}")
    
    else:
        # 显示所有实体
        try:
            query = f"""
            MATCH (n:{selected_entity_type})
            RETURN n.name as name, n.description as description
            ORDER BY n.name
            LIMIT 100
            """
            
            results = db.query(query)
            
            if results:
                st.info(f"显示前100个{entity_type_options[selected_entity_type]}（共{len(results)}个）")
                
                # 创建分页
                items_per_page = 20
                total_pages = (len(results) + items_per_page - 1) // items_per_page
                
                if total_pages > 1:
                    page = st.selectbox("选择页面", range(1, total_pages + 1)) - 1
                    start_idx = page * items_per_page
                    end_idx = min(start_idx + items_per_page, len(results))
                    page_results = results[start_idx:end_idx]
                else:
                    page_results = results
                
                # 显示实体列表
                for i, result in enumerate(page_results):
                    entity_name = result["name"]
                    description = result.get("description", "")
                    
                    with st.container():
                        col1, col2, col3 = st.columns([3, 1, 1])
                        
                        with col1:
                            type_badge_class = {
                                "company": "company-badge",
                                "industry": "industry-badge",
                                "product": "product-badge"
                            }.get(selected_entity_type, "")
                            
                            st.markdown(f"""
                            <div class="entity-card">
                                <span class="entity-type-badge {type_badge_class}">
                                    {entity_type_options[selected_entity_type]}
                                </span>
                                <strong>{entity_name}</strong>
                                <br>
                                <small style="color: #666;">{description}</small>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        with col2:
                            if st.button("查看详情", key=f"view_all_{i}_{entity_name}"):
                                st.session_state.selected_entity = entity_name
                                st.session_state.selected_entity_type = selected_entity_type
                        
                        with col3:
                            if st.button("编辑", key=f"edit_all_{i}_{entity_name}"):
                                st.session_state.selected_entity = entity_name
                                st.session_state.selected_entity_type = selected_entity_type
                                st.session_state.management_mode = "edit"
                                st.rerun()
            else:
                st.info(f"暂无{entity_type_options[selected_entity_type]}数据")
                
        except Exception as e:
            st.error(f"获取实体列表失败: {str(e)}")

elif management_mode == "edit":
    # 编辑模式
    st.subheader("✏️ 编辑实体")
    
    if st.session_state.selected_entity:
        entity_name = st.session_state.selected_entity
        entity_type = st.session_state.selected_entity_type or selected_entity_type
        
        # 显示当前编辑的实体
        st.info(f"正在编辑: **{entity_name}** ({entity_type_options.get(entity_type, entity_type)})")
        
        # 创建选项卡
        edit_tab1, edit_tab2, edit_tab3 = st.tabs(["基本信息", "关系管理", "危险操作"])
        
        with edit_tab1:
            # 显示可编辑的实体信息
            entity_detail.display_entity_info(entity_name, entity_type, editable=True)
        
        with edit_tab2:
            # 显示可编辑的关系信息
            entity_detail.display_entity_relationships(entity_name, entity_type, editable=True)
        
        with edit_tab3:
            # 危险操作
            st.subheader("⚠️ 危险操作")
            
            st.markdown("""
            <div class="warning-box">
                <strong>警告:</strong> 以下操作不可逆，请谨慎操作！
            </div>
            """, unsafe_allow_html=True)
            
            # 删除实体
            st.write("**删除实体:**")
            
            if not st.session_state.show_confirmation:
                if st.button("🗑️ 删除实体", type="secondary"):
                    st.session_state.show_confirmation = True
                    st.rerun()
            else:
                st.warning(f"确定要删除实体 '{entity_name}' 吗？此操作将同时删除所有相关关系！")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ 确认删除", type="primary"):
                        try:
                            # 删除实体及其关系
                            delete_query = f"""
                            MATCH (n:{entity_type} {{name: $name}})
                            DETACH DELETE n
                            """
                            
                            db.query(delete_query, {"name": entity_name})
                            
                            st.success(f"实体 '{entity_name}' 已成功删除")
                            
                            # 重置状态
                            st.session_state.selected_entity = None
                            st.session_state.selected_entity_type = None
                            st.session_state.show_confirmation = False
                            st.session_state.management_mode = "browse"
                            
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"删除失败: {str(e)}")
                
                with col2:
                    if st.button("❌ 取消"):
                        st.session_state.show_confirmation = False
                        st.rerun()
        
        # 返回浏览模式按钮
        if st.button("← 返回浏览模式"):
            st.session_state.management_mode = "browse"
            st.session_state.selected_entity = None
            st.session_state.selected_entity_type = None
            st.rerun()
    
    else:
        st.info("请先在浏览模式中选择要编辑的实体")
        if st.button("← 返回浏览模式"):
            st.session_state.management_mode = "browse"
            st.rerun()

elif management_mode == "batch":
    # 批量操作模式
    st.subheader("📦 批量操作")
    
    # 使用实体详情组件的批量操作功能
    entity_detail.manage_entity_batch_operations(selected_entity_type)

elif management_mode == "create":
    # 创建实体模式
    st.subheader("➕ 创建新实体")
    
    with st.form("create_entity_form"):
        st.write(f"**创建新的{entity_type_options[selected_entity_type]}:**")
        
        # 基本信息
        new_name = st.text_input("名称*", help="实体的唯一名称")
        new_description = st.text_area("描述", help="实体的详细描述")
        
        # 其他属性
        st.write("**其他属性:**")
        col1, col2 = st.columns(2)
        
        additional_props = {}
        for i in range(3):  # 允许添加3个额外属性
            with col1 if i % 2 == 0 else col2:
                prop_key = st.text_input(f"属性名 {i+1}", key=f"prop_key_{i}")
                prop_value = st.text_input(f"属性值 {i+1}", key=f"prop_value_{i}")
                
                if prop_key and prop_value:
                    additional_props[prop_key] = prop_value
        
        # 提交按钮
        submitted = st.form_submit_button("✅ 创建实体")
        
        if submitted:
            if not new_name:
                st.error("请输入实体名称")
            else:
                try:
                    # 检查实体是否已存在
                    check_query = f"""
                    MATCH (n:{selected_entity_type} {{name: $name}})
                    RETURN count(n) as count
                    """
                    
                    check_results = db.query(check_query, {"name": new_name})
                    
                    if check_results and check_results[0]["count"] > 0:
                        st.error(f"实体 '{new_name}' 已存在")
                    else:
                        # 创建实体
                        props = {"name": new_name}
                        if new_description:
                            props["description"] = new_description
                        props.update(additional_props)
                        
                        # 构建CREATE语句
                        prop_assignments = []
                        params = {}
                        
                        for key, value in props.items():
                            param_key = f"prop_{key}"
                            prop_assignments.append(f"{key}: ${param_key}")
                            params[param_key] = value
                        
                        create_query = f"""
                        CREATE (n:{selected_entity_type} {{{', '.join(prop_assignments)}}})
                        RETURN n
                        """
                        
                        results = db.query(create_query, params)
                        
                        if results:
                            st.success(f"✅ 成功创建{entity_type_options[selected_entity_type]} '{new_name}'")
                            
                            # 清除表单
                            st.rerun()
                        else:
                            st.error("创建失败，请重试")
                            
                except Exception as e:
                    st.error(f"创建实体失败: {str(e)}")

# 显示选中实体的详细信息（在浏览模式下）
if management_mode == "browse" and st.session_state.selected_entity:
    st.markdown("---")
    
    entity_name = st.session_state.selected_entity
    entity_type = st.session_state.selected_entity_type or selected_entity_type
    
    # 显示实体详情
    entity_detail.display_entity_info(entity_name, entity_type, editable=False)
    
    # 显示关系信息
    entity_detail.display_entity_relationships(entity_name, entity_type, editable=False)
    
    # 操作按钮
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("✏️ 编辑此实体"):
            st.session_state.management_mode = "edit"
            st.rerun()
    
    with col2:
        if st.button("🔍 查找相似实体"):
            similar_entities = search_engine.get_similar_entities(entity_name, entity_type)
            if similar_entities:
                st.write("**相似实体:**")
                for sim in similar_entities[:5]:
                    st.write(f"- {sim['entity_name']} (相似度: {sim['similarity_score']:.3f})")
            else:
                st.info("未找到相似实体")
    
    with col3:
        if st.button("❌ 关闭详情"):
            st.session_state.selected_entity = None
            st.session_state.selected_entity_type = None
            st.rerun()

# 显示统计信息
if st.session_state.get("show_statistics", False):
    st.markdown("---")
    st.subheader("📊 实体统计")
    
    try:
        # 获取各类型实体数量
        stats_query = """
        CALL {
            MATCH (c:company) RETURN 'company' as type, count(c) as count
            UNION ALL
            MATCH (i:industry) RETURN 'industry' as type, count(i) as count
            UNION ALL
            MATCH (p:product) RETURN 'product' as type, count(p) as count
        }
        RETURN type, count
        ORDER BY count DESC
        """
        
        stats_results = db.query(stats_query)
        
        if stats_results:
            col1, col2, col3 = st.columns(3)
            
            for i, result in enumerate(stats_results):
                entity_type_name = entity_type_options.get(result["type"], result["type"])
                count = result["count"]
                
                with [col1, col2, col3][i]:
                    st.metric(entity_type_name, f"{count:,}")
        
        # 关闭统计按钮
        if st.button("关闭统计"):
            st.session_state.show_statistics = False
            st.rerun()
            
    except Exception as e:
        st.error(f"获取统计信息失败: {str(e)}")

# 页脚
st.markdown("---")
st.caption(f"实体管理系统 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 帮助信息
with st.sidebar:
    st.markdown("---")
    st.subheader("📖 使用帮助")
    
    with st.expander("管理模式说明"):
        st.markdown("""
        - **🔍 浏览模式**: 查看和搜索实体
        - **✏️ 编辑模式**: 编辑实体信息和关系
        - **📦 批量操作**: 批量管理多个实体
        - **➕ 创建实体**: 创建新的实体
        """)
    
    with st.expander("操作提示"):
        st.markdown("""
        - 在浏览模式下点击"查看详情"可查看完整信息
        - 编辑模式下可以修改实体属性和关系
        - 删除操作不可逆，请谨慎操作
        - 使用搜索功能快速找到目标实体
        """)