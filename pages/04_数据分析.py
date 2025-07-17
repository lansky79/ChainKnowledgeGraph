"""
数据分析页面
提供知识图谱的统计分析、趋势分析、网络分析等功能
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import json

# 导入自定义模块
from utils.db_connector import Neo4jConnector
from utils.analytics import Analytics
from utils.logger import setup_logger
from components.chart_components import ChartComponents, display_metrics_grid, display_chart_with_data

# 设置日志
logger = setup_logger("KG_Analytics")

# 页面配置
st.set_page_config(
    page_title="数据分析",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    .insight-card {
        background-color: #e8f4fd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #17a2b8;
        margin: 0.5rem 0;
    }
    .warning-card {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffc107;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# 初始化分析工具
@st.cache_resource
def get_analytics():
    """获取分析工具实例（缓存资源）"""
    db = Neo4jConnector()
    return Analytics(db)

analytics = get_analytics()
chart_components = ChartComponents()

# 页面标题
st.title("📊 数据分析")

# 创建侧边栏
st.sidebar.header("分析选项")

# 分析类型选择
analysis_type = st.sidebar.selectbox(
    "选择分析类型",
    ["概览分析", "节点分析", "关系分析", "网络分析", "行业分析", "趋势分析", "综合报告"]
)

# 刷新数据按钮
if st.sidebar.button("🔄 刷新数据", help="重新获取最新的分析数据"):
    st.cache_data.clear()
    st.rerun()

# 分析选项
st.sidebar.markdown("---")
st.sidebar.info("💡 需要导出分析数据？请前往 **数据管理** 页面的导出功能")

# 根据选择的分析类型显示内容
if analysis_type == "概览分析":
    st.subheader("📈 数据概览")
    
    # 获取基础统计数据
    with st.spinner("正在加载概览数据..."):
        node_stats = analytics.get_node_statistics()
        relationship_stats = analytics.get_relationship_statistics()
        network_analysis = analytics.get_network_analysis()
    
    if node_stats and relationship_stats:
        # 显示关键指标
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "总节点数", 
                f"{node_stats.get('total_nodes', 0):,}",
                help="知识图谱中的总节点数量"
            )
        
        with col2:
            st.metric(
                "总关系数", 
                f"{relationship_stats.get('total_relationships', 0):,}",
                help="知识图谱中的总关系数量"
            )
        
        with col3:
            connectivity_rate = network_analysis.get('connectivity', {}).get('connectivity_rate', 0)
            st.metric(
                "连通率", 
                f"{connectivity_rate:.1f}%",
                help="有连接的节点占总节点的百分比"
            )
        
        with col4:
            avg_connections = network_analysis.get('connectivity', {}).get('avg_connections', 0)
            st.metric(
                "平均连接数", 
                f"{avg_connections:.1f}",
                help="每个节点的平均连接数"
            )
        
        # 节点分布饼图
        st.subheader("节点类型分布")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            node_counts = node_stats.get('node_counts', {})
            if node_counts:
                # 转换为中文标签
                chinese_labels = {
                    'company': '公司',
                    'industry': '行业', 
                    'product': '产品'
                }
                chinese_data = {chinese_labels.get(k, k): v for k, v in node_counts.items()}
                
                fig = chart_components.create_pie_chart(
                    chinese_data, 
                    "节点类型分布"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.write("**详细统计:**")
            for node_type, count in node_counts.items():
                percentage = node_stats.get('node_percentages', {}).get(node_type, 0)
                chinese_type = {'company': '公司', 'industry': '行业', 'product': '产品'}.get(node_type, node_type)
                st.write(f"- {chinese_type}: {count:,} ({percentage:.1f}%)")
        
        # 关系分布柱状图
        st.subheader("关系类型分布")
        relationship_counts = relationship_stats.get('relationship_counts', {})
        if relationship_counts:
            fig = chart_components.create_bar_chart(
                relationship_counts,
                "关系类型分布"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.warning("无法获取统计数据，请检查数据库连接")

elif analysis_type == "节点分析":
    st.subheader("🔍 节点详细分析")
    
    with st.spinner("正在分析节点数据..."):
        node_stats = analytics.get_node_statistics()
        centrality_metrics = analytics.calculate_centrality_metrics(limit=15)
    
    if node_stats:
        # 节点属性完整性分析
        st.subheader("数据完整性分析")
        attribute_stats = node_stats.get('attribute_stats', {})
        
        if attribute_stats:
            completion_data = []
            for node_type, stats in attribute_stats.items():
                chinese_type = {'company': '公司', 'industry': '行业', 'product': '产品'}.get(node_type, node_type)
                completion_data.append({
                    'type': chinese_type,
                    'total': stats['total'],
                    'with_description': stats['with_description'],
                    'completion_rate': stats['completion_rate']
                })
            
            df = pd.DataFrame(completion_data)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # 完整性柱状图
                completion_dict = {row['type']: row['completion_rate'] for _, row in df.iterrows()}
                fig = chart_components.create_bar_chart(
                    completion_dict,
                    "描述字段完整性 (%)"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.write("**完整性详情:**")
                for _, row in df.iterrows():
                    st.write(f"**{row['type']}**")
                    st.write(f"- 总数: {row['total']:,}")
                    st.write(f"- 有描述: {row['with_description']:,}")
                    st.write(f"- 完整性: {row['completion_rate']:.1f}%")
                    st.write("")
    
    # 中心性分析
    if centrality_metrics:
        st.subheader("节点中心性分析")
        
        tab1, tab2, tab3 = st.tabs(["度中心性", "入度中心性", "出度中心性"])
        
        with tab1:
            degree_data = centrality_metrics.get('degree_centrality', [])
            if degree_data:
                st.write("**连接数最多的实体 (度中心性)**")
                
                # 创建数据框
                df = pd.DataFrame(degree_data)
                
                # 显示图表
                degree_dict = {f"{row['name']} ({row['type']})": row['degree'] for _, row in df.iterrows()}
                fig = chart_components.create_bar_chart(
                    degree_dict,
                    "度中心性排名",
                    orientation="horizontal"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # 显示表格
                df['类型'] = df['type'].map({'company': '公司', 'industry': '行业', 'product': '产品'})
                st.dataframe(
                    df[['name', '类型', 'degree']].rename(columns={
                        'name': '实体名称',
                        'degree': '连接数'
                    }),
                    use_container_width=True
                )
        
        with tab2:
            in_degree_data = centrality_metrics.get('in_degree_centrality', [])
            if in_degree_data:
                st.write("**被指向最多的实体 (入度中心性)**")
                
                df = pd.DataFrame(in_degree_data)
                
                in_degree_dict = {f"{row['name']} ({row['type']})": row['in_degree'] for _, row in df.iterrows()}
                fig = chart_components.create_bar_chart(
                    in_degree_dict,
                    "入度中心性排名",
                    orientation="horizontal"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                df['类型'] = df['type'].map({'company': '公司', 'industry': '行业', 'product': '产品'})
                st.dataframe(
                    df[['name', '类型', 'in_degree']].rename(columns={
                        'name': '实体名称',
                        'in_degree': '入度'
                    }),
                    use_container_width=True
                )
        
        with tab3:
            out_degree_data = centrality_metrics.get('out_degree_centrality', [])
            if out_degree_data:
                st.write("**指向其他实体最多的实体 (出度中心性)**")
                
                df = pd.DataFrame(out_degree_data)
                
                out_degree_dict = {f"{row['name']} ({row['type']})": row['out_degree'] for _, row in df.iterrows()}
                fig = chart_components.create_bar_chart(
                    out_degree_dict,
                    "出度中心性排名",
                    orientation="horizontal"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                df['类型'] = df['type'].map({'company': '公司', 'industry': '行业', 'product': '产品'})
                st.dataframe(
                    df[['name', '类型', 'out_degree']].rename(columns={
                        'name': '实体名称',
                        'out_degree': '出度'
                    }),
                    use_container_width=True
                )

elif analysis_type == "关系分析":
    st.subheader("🔗 关系详细分析")
    
    with st.spinner("正在分析关系数据..."):
        relationship_stats = analytics.get_relationship_statistics()
    
    if relationship_stats:
        # 关系分布
        st.subheader("关系类型分布")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            relationship_counts = relationship_stats.get('relationship_counts', {})
            if relationship_counts:
                fig = chart_components.create_pie_chart(
                    relationship_counts,
                    "关系类型分布"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.write("**关系统计:**")
            relationship_percentages = relationship_stats.get('relationship_percentages', {})
            for rel_type, count in relationship_counts.items():
                percentage = relationship_percentages.get(rel_type, 0)
                st.write(f"- {rel_type}: {count:,} ({percentage:.1f}%)")
        
        # 关系密度分析
        st.subheader("关系密度分析")
        density_stats = relationship_stats.get('density_stats', {})
        
        if density_stats:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                <div class="metric-card">
                    <h4>公司-行业关系密度</h4>
                    <p><strong>{:.4f}</strong></p>
                    <small>实际关系数: {:,} / 可能关系数: {:,}</small>
                </div>
                """.format(
                    density_stats.get('company_industry_density', 0),
                    density_stats.get('actual_ci_relations', 0),
                    density_stats.get('total_possible_ci_relations', 0)
                ), unsafe_allow_html=True)
            
            with col2:
                st.markdown("""
                <div class="metric-card">
                    <h4>公司-产品关系密度</h4>
                    <p><strong>{:.4f}</strong></p>
                    <small>实际关系数: {:,} / 可能关系数: {:,}</small>
                </div>
                """.format(
                    density_stats.get('company_product_density', 0),
                    density_stats.get('actual_cp_relations', 0),
                    density_stats.get('total_possible_cp_relations', 0)
                ), unsafe_allow_html=True)

elif analysis_type == "网络分析":
    st.subheader("🌐 网络结构分析")
    
    with st.spinner("正在分析网络结构..."):
        network_analysis = analytics.get_network_analysis()
    
    if network_analysis:
        # 连通性分析
        st.subheader("网络连通性")
        connectivity = network_analysis.get('connectivity', {})
        
        if connectivity:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("总节点数", f"{connectivity.get('total_nodes', 0):,}")
            
            with col2:
                st.metric("连通节点数", f"{connectivity.get('connected_nodes', 0):,}")
            
            with col3:
                st.metric("孤立节点数", f"{connectivity.get('isolated_nodes', 0):,}")
            
            with col4:
                st.metric("连通率", f"{connectivity.get('connectivity_rate', 0):.1f}%")
            
            # 连接数分布
            col1, col2 = st.columns(2)
            
            with col1:
                # 连通性仪表盘
                connectivity_rate = connectivity.get('connectivity_rate', 0)
                fig = chart_components.create_gauge_chart(
                    connectivity_rate,
                    "网络连通率 (%)",
                    max_value=100,
                    color="green" if connectivity_rate > 80 else "orange" if connectivity_rate > 60 else "red"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.write("**连接统计:**")
                st.write(f"- 平均连接数: {connectivity.get('avg_connections', 0):.2f}")
                st.write(f"- 最大连接数: {connectivity.get('max_connections', 0):,}")
                st.write(f"- 最小连接数: {connectivity.get('min_connections', 0):,}")
                
                # 连通性评估
                if connectivity_rate > 90:
                    st.success("🟢 网络连通性优秀")
                elif connectivity_rate > 70:
                    st.info("🟡 网络连通性良好")
                else:
                    st.warning("🔴 网络连通性需要改善")
        
        # 最活跃实体
        st.subheader("最活跃实体")
        most_active = network_analysis.get('most_active_entities', [])
        
        if most_active:
            # 创建活跃度图表
            active_dict = {f"{entity['name']} ({entity['type']})": entity['connections'] 
                          for entity in most_active}
            
            fig = chart_components.create_bar_chart(
                active_dict,
                "最活跃实体排名",
                orientation="horizontal"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # 显示详细表格
            df = pd.DataFrame(most_active)
            df['类型'] = df['type'].map({'company': '公司', 'industry': '行业', 'product': '产品'})
            st.dataframe(
                df[['name', '类型', 'connections']].rename(columns={
                    'name': '实体名称',
                    'connections': '连接数'
                }),
                use_container_width=True
            )

elif analysis_type == "行业分析":
    st.subheader("🏭 行业深度分析")
    
    with st.spinner("正在分析行业数据..."):
        industry_analysis = analytics.get_industry_analysis()
    
    if industry_analysis:
        # 行业规模分析
        st.subheader("行业规模排名")
        industry_sizes = industry_analysis.get('industry_sizes', [])
        
        if industry_sizes:
            df = pd.DataFrame(industry_sizes)
            
            # 行业规模图表
            size_dict = {row['industry']: row['total_entities'] for _, row in df.iterrows()}
            fig = chart_components.create_bar_chart(
                size_dict,
                "行业实体总数排名"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # 详细表格
            st.dataframe(
                df.rename(columns={
                    'industry': '行业名称',
                    'companies': '公司数量',
                    'products': '产品数量',
                    'total_entities': '实体总数'
                }),
                use_container_width=True
            )
        
        # 行业关系网络
        st.subheader("行业关系网络")
        industry_relations = industry_analysis.get('industry_relations', [])
        
        if industry_relations:
            st.write("**行业间关系:**")
            
            relations_df = pd.DataFrame(industry_relations)
            st.dataframe(
                relations_df.rename(columns={
                    'from_industry': '源行业',
                    'to_industry': '目标行业',
                    'relation_type': '关系类型',
                    'relation_count': '关系数量'
                }),
                use_container_width=True
            )

elif analysis_type == "趋势分析":
    st.subheader("📈 数据趋势分析")
    
    # 趋势分析参数
    col1, col2 = st.columns([1, 3])
    
    with col1:
        days = st.selectbox("分析周期", [7, 14, 30, 60, 90], index=2)
    
    with st.spinner(f"正在生成{days}天的趋势数据..."):
        trend_data = analytics.generate_trend_data(days=days)
    
    if trend_data:
        trend_list = trend_data.get('trend_data', [])
        
        if trend_list:
            # 总体趋势图
            st.subheader("节点增长趋势")
            fig = chart_components.create_line_chart(
                trend_list,
                'date',
                'total_nodes',
                "节点总数增长趋势"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # 分类趋势图
            st.subheader("各类型节点增长趋势")
            
            # 重构数据用于多线图
            trend_df = pd.DataFrame(trend_list)
            
            fig = chart_components.create_line_chart(
                pd.melt(trend_df, id_vars=['date'], 
                       value_vars=['companies', 'industries', 'products'],
                       var_name='type', value_name='count').to_dict('records'),
                'date',
                'count',
                "各类型节点增长趋势",
                color_field='type'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # 趋势统计
            st.subheader("趋势统计")
            
            if len(trend_list) >= 2:
                start_total = trend_list[0]['total_nodes']
                end_total = trend_list[-1]['total_nodes']
                growth_rate = ((end_total - start_total) / start_total * 100) if start_total > 0 else 0
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("起始节点数", f"{start_total:,}")
                
                with col2:
                    st.metric("当前节点数", f"{end_total:,}")
                
                with col3:
                    st.metric("增长率", f"{growth_rate:.1f}%")

elif analysis_type == "综合报告":
    st.subheader("📋 综合分析报告")
    
    with st.spinner("正在生成综合报告..."):
        report = analytics.generate_summary_report()
    
    if report:
        # 报告摘要
        st.subheader("📊 报告摘要")
        summary = report.get('summary', {})
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("总节点数", f"{summary.get('total_nodes', 0):,}")
        
        with col2:
            st.metric("总关系数", f"{summary.get('total_relationships', 0):,}")
        
        with col3:
            st.metric("连通率", f"{summary.get('connectivity_rate', 0):.1f}%")
        
        with col4:
            st.metric("最活跃实体", summary.get('most_active_entity', '未知'))
        
        # 关键洞察
        st.subheader("💡 关键洞察")
        insights = report.get('insights', [])
        
        for insight in insights:
            st.markdown(f"""
            <div class="insight-card">
                <p>💡 {insight}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # 详细分析数据
        with st.expander("📈 查看详细分析数据"):
            detailed_analysis = report.get('detailed_analysis', {})
            
            for section, data in detailed_analysis.items():
                st.subheader(f"{section.upper()} 数据")
                if isinstance(data, dict):
                    st.json(data)
                else:
                    st.write(data)
        
        # 导出报告
        st.subheader("📤 导出报告")
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            if st.button("导出完整报告"):
                # 生成报告文件
                report_json = json.dumps(report, ensure_ascii=False, indent=2)
                st.download_button(
                    label="下载 JSON 报告",
                    data=report_json,
                    file_name=f"knowledge_graph_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )

# 页脚
st.markdown("---")
st.caption(f"数据分析系统 | 最后更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 添加帮助信息
with st.sidebar:
    st.markdown("---")
    st.subheader("📖 帮助信息")
    
    with st.expander("分析类型说明"):
        st.markdown("""
        - **概览分析**: 整体数据概况和基础统计
        - **节点分析**: 节点类型分布和中心性分析
        - **关系分析**: 关系类型分布和密度分析
        - **网络分析**: 网络连通性和结构分析
        - **行业分析**: 行业规模和关系网络分析
        - **趋势分析**: 数据增长趋势和变化分析
        - **综合报告**: 完整的分析报告和洞察
        """)
    
    with st.expander("指标说明"):
        st.markdown("""
        - **度中心性**: 节点的连接数量
        - **入度中心性**: 指向该节点的连接数
        - **出度中心性**: 该节点指向其他节点的连接数
        - **连通率**: 有连接的节点占总节点的比例
        - **关系密度**: 实际关系数与可能关系数的比值
        """)