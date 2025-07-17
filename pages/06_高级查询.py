"""
高级查询页面
提供可视化查询构建、Cypher编辑器、查询模板管理等功能
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import json

# 导入自定义模块
from utils.db_connector import Neo4jConnector
from utils.query_builder import QueryBuilder
from utils.logger import setup_logger
from visualizers.network_viz import display_network

# 设置日志
logger = setup_logger("KG_Advanced_Query")

# 页面配置
st.set_page_config(
    page_title="高级查询",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
    .query-builder-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        background-color: #f8f9fa;
    }
    .template-card {
        border: 1px solid #e0e0e0;
        border-radius: 6px;
        padding: 12px;
        margin: 8px 0;
        background-color: #ffffff;
    }
    .predefined-template {
        border-left: 4px solid #28a745;
    }
    .custom-template {
        border-left: 4px solid #007bff;
    }
    .cypher-editor {
        font-family: 'Courier New', monospace;
        background-color: #f8f8f8;
        border: 1px solid #ddd;
        border-radius: 4px;
        padding: 10px;
    }
    .query-result {
        max-height: 400px;
        overflow-y: auto;
        border: 1px solid #ddd;
        border-radius: 4px;
        padding: 10px;
        background-color: #f9f9f9;
    }
</style>
""", unsafe_allow_html=True)

# 初始化组件
@st.cache_resource
def get_query_builder():
    """获取查询构建器实例（缓存资源）"""
    db = Neo4jConnector()
    return QueryBuilder(db)

query_builder = get_query_builder()

# 初始化会话状态
if "current_query" not in st.session_state:
    st.session_state.current_query = ""

if "query_results" not in st.session_state:
    st.session_state.query_results = []

if "selected_template" not in st.session_state:
    st.session_state.selected_template = None

# 页面标题
st.title("🔧 高级查询")

# 创建选项卡
tab1, tab2, tab3, tab4 = st.tabs(["可视化构建", "Cypher编辑器", "查询模板", "查询历史"])

# 可视化查询构建选项卡
with tab1:
    st.header("🎨 可视化查询构建")
    
    # 查询类型选择
    query_type = st.selectbox(
        "选择查询类型",
        ["node_query", "relationship_query", "path_query", "aggregation_query", "filter_query"],
        format_func=lambda x: {
            "node_query": "节点查询",
            "relationship_query": "关系查询", 
            "path_query": "路径查询",
            "aggregation_query": "聚合查询",
            "filter_query": "过滤查询"
        }.get(x, x)
    )
    
    # 根据查询类型显示不同的配置界面
    if query_type == "node_query":
        st.subheader("节点查询配置")
        
        col1, col2 = st.columns(2)
        
        with col1:
            node_type = st.selectbox(
                "节点类型",
                ["company", "industry", "product"],
                format_func=lambda x: {"company": "公司", "industry": "行业", "product": "产品"}.get(x, x)
            )
            
            limit = st.number_input("结果限制", min_value=1, max_value=1000, value=100)
        
        with col2:
            st.write("**属性过滤:**")
            prop_name = st.text_input("属性名", placeholder="例如: name")
            prop_value = st.text_input("属性值", placeholder="例如: 阿里巴巴")
        
        # 构建查询配置
        query_config = {
            "query_type": "node_query",
            "node_type": node_type,
            "limit": limit,
            "properties": {prop_name: prop_value} if prop_name and prop_value else {}
        }
    
    elif query_type == "relationship_query":
        st.subheader("关系查询配置")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            source_type = st.selectbox(
                "源节点类型",
                ["company", "industry", "product"],
                format_func=lambda x: {"company": "公司", "industry": "行业", "product": "产品"}.get(x, x)
            )
        
        with col2:
            target_type = st.selectbox(
                "目标节点类型",
                ["company", "industry", "product"],
                format_func=lambda x: {"company": "公司", "industry": "行业", "product": "产品"}.get(x, x)
            )
        
        with col3:
            relationship_type = st.selectbox(
                "关系类型（可选）",
                ["", "所属行业", "主营产品", "上级行业", "上游材料"],
                format_func=lambda x: "全部关系" if x == "" else x
            )
        
        limit = st.number_input("结果限制", min_value=1, max_value=1000, value=100, key="rel_limit")
        
        query_config = {
            "query_type": "relationship_query",
            "source_type": source_type,
            "target_type": target_type,
            "relationship_type": relationship_type,
            "limit": limit
        }
    
    elif query_type == "path_query":
        st.subheader("路径查询配置")
        
        col1, col2 = st.columns(2)
        
        with col1:
            source_type = st.selectbox(
                "源节点类型",
                ["company", "industry", "product"],
                format_func=lambda x: {"company": "公司", "industry": "行业", "product": "产品"}.get(x, x),
                key="path_source_type"
            )
            
            source_name = st.text_input("源节点名称", placeholder="例如: 阿里巴巴")
            
            max_depth = st.slider("最大路径深度", 1, 10, 5)
        
        with col2:
            target_type = st.selectbox(
                "目标节点类型",
                ["company", "industry", "product"],
                format_func=lambda x: {"company": "公司", "industry": "行业", "product": "产品"}.get(x, x),
                key="path_target_type"
            )
            
            target_name = st.text_input("目标节点名称", placeholder="例如: 华为")
            
            path_type = st.selectbox(
                "路径类型",
                ["shortest", "all"],
                format_func=lambda x: {"shortest": "最短路径", "all": "所有路径"}.get(x, x)
            )
        
        query_config = {
            "query_type": "path_query",
            "source_type": source_type,
            "target_type": target_type,
            "source_name": source_name,
            "target_name": target_name,
            "max_depth": max_depth,
            "path_type": path_type
        }
    
    elif query_type == "aggregation_query":
        st.subheader("聚合查询配置")
        
        col1, col2 = st.columns(2)
        
        with col1:
            node_type = st.selectbox(
                "节点类型",
                ["company", "industry", "product"],
                format_func=lambda x: {"company": "公司", "industry": "行业", "product": "产品"}.get(x, x),
                key="agg_node_type"
            )
            
            aggregation_type = st.selectbox(
                "聚合类型",
                ["count", "degree"],
                format_func=lambda x: {"count": "计数", "degree": "度中心性"}.get(x, x)
            )
        
        with col2:
            if aggregation_type == "count":
                group_by = st.text_input("分组字段（可选）", placeholder="例如: description")
            else:
                group_by = ""
        
        query_config = {
            "query_type": "aggregation_query",
            "node_type": node_type,
            "aggregation_type": aggregation_type,
            "group_by": group_by
        }
    
    elif query_type == "filter_query":
        st.subheader("过滤查询配置")
        
        node_type = st.selectbox(
            "节点类型",
            ["company", "industry", "product"],
            format_func=lambda x: {"company": "公司", "industry": "行业", "product": "产品"}.get(x, x),
            key="filter_node_type"
        )
        
        # 过滤条件
        st.write("**过滤条件:**")
        
        # 使用会话状态管理过滤条件
        if "filter_conditions" not in st.session_state:
            st.session_state.filter_conditions = [{"field": "", "operator": "=", "value": ""}]
        
        filters = []
        for i, condition in enumerate(st.session_state.filter_conditions):
            col1, col2, col3, col4 = st.columns([2, 1, 2, 1])
            
            with col1:
                field = st.text_input(f"字段 {i+1}", value=condition["field"], key=f"field_{i}")
            
            with col2:
                operator = st.selectbox(
                    f"操作符 {i+1}",
                    ["=", "!=", "contains", "starts_with", "ends_with"],
                    index=["=", "!=", "contains", "starts_with", "ends_with"].index(condition["operator"]),
                    key=f"operator_{i}"
                )
            
            with col3:
                value = st.text_input(f"值 {i+1}", value=condition["value"], key=f"value_{i}")
            
            with col4:
                if st.button("删除", key=f"remove_{i}"):
                    st.session_state.filter_conditions.pop(i)
                    st.rerun()
            
            if field and value:
                filters.append({"field": field, "operator": operator, "value": value})
        
        # 添加新条件按钮
        if st.button("➕ 添加条件"):
            st.session_state.filter_conditions.append({"field": "", "operator": "=", "value": ""})
            st.rerun()
        
        # 逻辑操作符
        logic_operator = st.selectbox(
            "条件逻辑",
            ["AND", "OR"],
            format_func=lambda x: {"AND": "且", "OR": "或"}.get(x, x)
        )
        
        limit = st.number_input("结果限制", min_value=1, max_value=1000, value=100, key="filter_limit")
        
        query_config = {
            "query_type": "filter_query",
            "node_type": node_type,
            "filters": filters,
            "logic_operator": logic_operator,
            "limit": limit
        }
    
    # 生成查询按钮
    if st.button("🔨 生成查询", key="build_visual_query"):
        with st.spinner("正在构建查询..."):
            success, message, cypher = query_builder.build_visual_query(query_config)
            
            if success:
                st.success(message)
                st.session_state.current_query = cypher
                
                # 显示生成的查询
                st.subheader("生成的Cypher查询:")
                st.code(cypher, language="cypher")
                
                # 执行查询按钮
                if st.button("▶️ 执行查询", key="execute_visual_query"):
                    exec_success, exec_message, results = query_builder.execute_custom_query(cypher)
                    
                    if exec_success:
                        st.success(exec_message)
                        st.session_state.query_results = results
                        
                        # 显示结果
                        if results:
                            st.subheader("查询结果:")
                            
                            # 尝试转换为DataFrame显示
                            try:
                                df = pd.DataFrame(results)
                                st.dataframe(df, use_container_width=True)
                            except:
                                # 如果无法转换为DataFrame，显示JSON
                                st.json(results[:10])  # 只显示前10条
                                
                                if len(results) > 10:
                                    st.info(f"显示前10条结果，总共{len(results)}条")
                        else:
                            st.info("查询未返回结果")
                    else:
                        st.error(exec_message)
            else:
                st.error(message)

# Cypher编辑器选项卡
with tab2:
    st.header("💻 Cypher查询编辑器")
    
    # 查询编辑器
    cypher_query = st.text_area(
        "输入Cypher查询:",
        value=st.session_state.current_query,
        height=200,
        help="输入您的Cypher查询语句",
        key="cypher_editor"
    )
    
    # 查询操作按钮
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("✅ 验证查询"):
            if cypher_query:
                is_valid, error_msg = query_builder.validate_cypher_query(cypher_query)
                if is_valid:
                    st.success("✅ 查询语法正确")
                else:
                    st.error(f"❌ {error_msg}")
            else:
                st.warning("请输入查询语句")
    
    with col2:
        if st.button("▶️ 执行查询"):
            if cypher_query:
                with st.spinner("正在执行查询..."):
                    success, message, results = query_builder.execute_custom_query(cypher_query)
                    
                    if success:
                        st.success(message)
                        st.session_state.query_results = results
                        st.session_state.current_query = cypher_query
                    else:
                        st.error(message)
            else:
                st.warning("请输入查询语句")
    
    with col3:
        if st.button("💾 保存为模板"):
            if cypher_query:
                st.session_state.show_save_template = True
            else:
                st.warning("请输入查询语句")
    
    with col4:
        if st.button("🗑️ 清空编辑器"):
            st.session_state.current_query = ""
            st.rerun()
    
    # 保存模板对话框
    if st.session_state.get("show_save_template", False):
        with st.form("save_template_form"):
            st.subheader("保存查询模板")
            
            template_name = st.text_input("模板名称*", placeholder="输入模板名称")
            template_description = st.text_area("模板描述", placeholder="描述模板的用途")
            template_category = st.selectbox(
                "模板分类",
                ["自定义", "基础查询", "关系查询", "路径查询", "分析查询"]
            )
            is_public = st.checkbox("设为公开模板")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.form_submit_button("💾 保存"):
                    if template_name:
                        success, message = query_builder.save_query_template(
                            template_name, cypher_query, template_description, 
                            template_category, is_public
                        )
                        
                        if success:
                            st.success(message)
                            st.session_state.show_save_template = False
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.error("请输入模板名称")
            
            with col2:
                if st.form_submit_button("❌ 取消"):
                    st.session_state.show_save_template = False
                    st.rerun()
    
    # 显示查询结果
    if st.session_state.query_results:
        st.subheader("查询结果")
        
        results = st.session_state.query_results
        
        # 结果统计
        st.info(f"共返回 {len(results)} 条结果")
        
        # 结果显示选项
        display_format = st.selectbox(
            "结果显示格式",
            ["表格", "JSON", "图谱"],
            key="result_display_format"
        )
        
        if display_format == "表格":
            try:
                df = pd.DataFrame(results)
                st.dataframe(df, use_container_width=True)
            except Exception as e:
                st.error(f"无法转换为表格格式: {str(e)}")
                st.json(results[:20])
        
        elif display_format == "JSON":
            # 分页显示JSON结果
            page_size = 10
            total_pages = (len(results) + page_size - 1) // page_size
            
            if total_pages > 1:
                page = st.selectbox("选择页面", range(1, total_pages + 1)) - 1
                start_idx = page * page_size
                end_idx = min(start_idx + page_size, len(results))
                page_results = results[start_idx:end_idx]
            else:
                page_results = results
            
            st.json(page_results)
        
        elif display_format == "图谱":
            # 尝试将结果转换为图谱格式
            try:
                nodes = []
                edges = []
                node_ids = set()
                
                for result in results:
                    # 处理节点
                    for key, value in result.items():
                        if hasattr(value, 'labels') and hasattr(value, 'identity'):  # Neo4j节点
                            node_id = value.identity
                            if node_id not in node_ids:
                                nodes.append({
                                    "id": node_id,
                                    "label": value.get("name", f"Node_{node_id}"),
                                    "group": list(value.labels)[0] if value.labels else "unknown"
                                })
                                node_ids.add(node_id)
                        
                        elif hasattr(value, 'start_node') and hasattr(value, 'end_node'):  # Neo4j关系
                            edges.append({
                                "from": value.start_node.identity,
                                "to": value.end_node.identity,
                                "label": value.type
                            })
                
                if nodes and edges:
                    st.subheader("图谱可视化")
                    display_network(nodes, edges, "查询结果图谱")
                else:
                    st.info("查询结果无法转换为图谱格式")
                    
            except Exception as e:
                st.error(f"图谱可视化失败: {str(e)}")

# 查询模板选项卡
with tab3:
    st.header("📚 查询模板管理")
    
    # 模板分类过滤
    col1, col2 = st.columns([2, 1])
    
    with col1:
        category_filter = st.selectbox(
            "模板分类",
            ["全部", "基础查询", "关系查询", "路径查询", "分析查询", "自定义"],
            key="template_category_filter"
        )
    
    with col2:
        if st.button("🔄 刷新模板"):
            st.cache_data.clear()
            st.rerun()
    
    # 获取模板列表
    if category_filter == "全部":
        templates = query_builder.get_query_templates()
    else:
        templates = query_builder.get_query_templates(category_filter)
    
    if templates:
        st.info(f"找到 {len(templates)} 个模板")
        
        # 显示模板
        for template in templates:
            template_class = "predefined-template" if template["is_predefined"] else "custom-template"
            
            with st.container():
                st.markdown(f"""
                <div class="template-card {template_class}">
                    <h4>{template['name']}</h4>
                    <p><strong>分类:</strong> {template['category']}</p>
                    <p><strong>描述:</strong> {template['description']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # 操作按钮
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if st.button("👀 查看", key=f"view_{template['name']}"):
                        st.session_state.selected_template = template
                
                with col2:
                    if st.button("📝 使用", key=f"use_{template['name']}"):
                        st.session_state.current_query = template["cypher"]
                        st.success(f"模板 '{template['name']}' 已加载到编辑器")
                
                with col3:
                    if st.button("📋 复制", key=f"copy_{template['name']}"):
                        st.code(template["cypher"], language="cypher")
                
                with col4:
                    if not template["is_predefined"]:
                        if st.button("🗑️ 删除", key=f"delete_{template['name']}"):
                            success, message = query_builder.delete_query_template(template["name"])
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
                
                st.markdown("---")
    else:
        st.info("暂无查询模板")
    
    # 显示选中模板的详情
    if st.session_state.selected_template:
        template = st.session_state.selected_template
        
        st.subheader(f"模板详情: {template['name']}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**分类:** {template['category']}")
            st.write(f"**类型:** {'预定义' if template['is_predefined'] else '自定义'}")
        
        with col2:
            if template['created_time']:
                st.write(f"**创建时间:** {template['created_time']}")
        
        st.write(f"**描述:** {template['description']}")
        
        st.subheader("Cypher查询:")
        st.code(template["cypher"], language="cypher")
        
        if st.button("关闭详情"):
            st.session_state.selected_template = None
            st.rerun()

# 查询历史选项卡
with tab4:
    st.header("📜 查询历史")
    
    # 查询统计
    stats = query_builder.get_query_statistics()
    
    if stats:
        st.subheader("📊 统计信息")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("总模板数", stats.get("total_templates", 0))
        
        with col2:
            st.metric("预定义模板", stats.get("predefined_templates", 0))
        
        with col3:
            st.metric("自定义模板", stats.get("custom_templates", 0))
        
        with col4:
            st.metric("公开模板", stats.get("public_templates", 0))
        
        # 模板分类分布
        categories = stats.get("template_categories", [])
        if categories:
            st.subheader("模板分类分布")
            category_counts = {}
            for template in query_builder.get_query_templates():
                category = template["category"]
                category_counts[category] = category_counts.get(category, 0) + 1
            
            df = pd.DataFrame(list(category_counts.items()), columns=["分类", "数量"])
            st.bar_chart(df.set_index("分类"))
    
    # 使用说明
    st.subheader("📖 使用说明")
    
    st.markdown("""
    ### 🎯 功能介绍
    
    **可视化构建:**
    - 通过图形界面构建常用查询
    - 支持节点、关系、路径、聚合、过滤查询
    - 自动生成Cypher语句
    
    **Cypher编辑器:**
    - 直接编写和执行Cypher查询
    - 语法验证和错误提示
    - 查询结果多格式显示
    
    **查询模板:**
    - 预定义常用查询模板
    - 保存和管理自定义模板
    - 模板分类和搜索
    
    ### 💡 使用技巧
    
    - 使用可视化构建器学习Cypher语法
    - 保存常用查询为模板提高效率
    - 结合图谱可视化查看查询结果
    - 注意查询性能，适当使用LIMIT限制结果
    """)

# 页脚
st.markdown("---")
st.caption(f"高级查询系统 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 侧边栏帮助信息
with st.sidebar:
    st.markdown("---")
    st.subheader("🔧 查询工具")
    
    with st.expander("Cypher语法提示"):
        st.markdown("""
        **基本语法:**
        ```cypher
        MATCH (n:Label)
        WHERE n.property = 'value'
        RETURN n
        LIMIT 10
        ```
        
        **关系查询:**
        ```cypher
        MATCH (a)-[r:RELATION]->(b)
        RETURN a, r, b
        ```
        
        **路径查询:**
        ```cypher
        MATCH path = (a)-[*1..3]-(b)
        RETURN path
        ```
        """)
    
    with st.expander("安全提示"):
        st.markdown("""
        - 本系统禁用了修改操作（CREATE、DELETE等）
        - 查询结果自动限制数量防止性能问题
        - 建议在大数据集上使用适当的过滤条件
        """)