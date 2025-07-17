"""
图表组件库
提供各种数据可视化图表组件
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any

class ChartComponents:
    """图表组件类"""
    
    @staticmethod
    def create_pie_chart(data: Dict[str, int], title: str = "饼图", 
                        colors: Optional[List[str]] = None) -> go.Figure:
        """
        创建饼图
        
        Args:
            data: 数据字典 {标签: 数值}
            title: 图表标题
            colors: 自定义颜色列表
            
        Returns:
            Plotly图表对象
        """
        if not data:
            return go.Figure()
        
        labels = list(data.keys())
        values = list(data.values())
        
        # 默认颜色方案
        if not colors:
            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8']
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.3,
            marker_colors=colors[:len(labels)],
            textinfo='label+percent',
            textposition='outside'
        )])
        
        fig.update_layout(
            title={
                'text': title,
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18}
            },
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.01
            ),
            margin=dict(t=60, b=20, l=20, r=120),
            height=400
        )
        
        return fig
    
    @staticmethod
    def create_bar_chart(data: Dict[str, int], title: str = "柱状图",
                        orientation: str = "vertical", colors: Optional[List[str]] = None) -> go.Figure:
        """
        创建柱状图
        
        Args:
            data: 数据字典 {标签: 数值}
            title: 图表标题
            orientation: 方向 ("vertical" 或 "horizontal")
            colors: 自定义颜色列表
            
        Returns:
            Plotly图表对象
        """
        if not data:
            return go.Figure()
        
        labels = list(data.keys())
        values = list(data.values())
        
        # 默认颜色方案
        if not colors:
            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8']
        
        if orientation == "horizontal":
            fig = go.Figure(data=[go.Bar(
                y=labels,
                x=values,
                orientation='h',
                marker_color=colors[:len(labels)],
                text=values,
                textposition='outside'
            )])
            
            fig.update_layout(
                xaxis_title="数值",
                yaxis_title="类别"
            )
        else:
            fig = go.Figure(data=[go.Bar(
                x=labels,
                y=values,
                marker_color=colors[:len(labels)],
                text=values,
                textposition='outside'
            )])
            
            fig.update_layout(
                xaxis_title="类别",
                yaxis_title="数值"
            )
        
        fig.update_layout(
            title={
                'text': title,
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18}
            },
            showlegend=False,
            margin=dict(t=60, b=60, l=60, r=60),
            height=400
        )
        
        return fig
    
    @staticmethod
    def create_line_chart(data: List[Dict], x_field: str, y_field: str, 
                         title: str = "折线图", color_field: Optional[str] = None) -> go.Figure:
        """
        创建折线图
        
        Args:
            data: 数据列表
            x_field: X轴字段名
            y_field: Y轴字段名
            title: 图表标题
            color_field: 颜色分组字段名
            
        Returns:
            Plotly图表对象
        """
        if not data:
            return go.Figure()
        
        df = pd.DataFrame(data)
        
        if color_field and color_field in df.columns:
            fig = px.line(df, x=x_field, y=y_field, color=color_field,
                         title=title, markers=True)
        else:
            fig = px.line(df, x=x_field, y=y_field, title=title, markers=True)
        
        fig.update_layout(
            title={
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18}
            },
            margin=dict(t=60, b=60, l=60, r=60),
            height=400
        )
        
        return fig
    
    @staticmethod
    def create_heatmap(data: List[List], x_labels: List[str], y_labels: List[str],
                      title: str = "热力图", colorscale: str = "Blues") -> go.Figure:
        """
        创建热力图
        
        Args:
            data: 二维数据数组
            x_labels: X轴标签
            y_labels: Y轴标签
            title: 图表标题
            colorscale: 颜色方案
            
        Returns:
            Plotly图表对象
        """
        if not data:
            return go.Figure()
        
        fig = go.Figure(data=go.Heatmap(
            z=data,
            x=x_labels,
            y=y_labels,
            colorscale=colorscale,
            showscale=True,
            text=data,
            texttemplate="%{text}",
            textfont={"size": 10}
        ))
        
        fig.update_layout(
            title={
                'text': title,
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18}
            },
            margin=dict(t=60, b=60, l=60, r=60),
            height=400
        )
        
        return fig
    
    @staticmethod
    def create_scatter_plot(data: List[Dict], x_field: str, y_field: str,
                           size_field: Optional[str] = None, color_field: Optional[str] = None,
                           title: str = "散点图") -> go.Figure:
        """
        创建散点图
        
        Args:
            data: 数据列表
            x_field: X轴字段名
            y_field: Y轴字段名
            size_field: 点大小字段名
            color_field: 颜色字段名
            title: 图表标题
            
        Returns:
            Plotly图表对象
        """
        if not data:
            return go.Figure()
        
        df = pd.DataFrame(data)
        
        fig = px.scatter(df, x=x_field, y=y_field,
                        size=size_field if size_field else None,
                        color=color_field if color_field else None,
                        title=title,
                        hover_data=df.columns.tolist())
        
        fig.update_layout(
            title={
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18}
            },
            margin=dict(t=60, b=60, l=60, r=60),
            height=400
        )
        
        return fig
    
    @staticmethod
    def create_gauge_chart(value: float, title: str = "仪表盘", 
                          max_value: float = 100, color: str = "blue") -> go.Figure:
        """
        创建仪表盘图表
        
        Args:
            value: 当前值
            title: 图表标题
            max_value: 最大值
            color: 颜色
            
        Returns:
            Plotly图表对象
        """
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=value,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': title, 'font': {'size': 18}},
            delta={'reference': max_value * 0.8},
            gauge={
                'axis': {'range': [None, max_value]},
                'bar': {'color': color},
                'steps': [
                    {'range': [0, max_value * 0.5], 'color': "lightgray"},
                    {'range': [max_value * 0.5, max_value * 0.8], 'color': "gray"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': max_value * 0.9
                }
            }
        ))
        
        fig.update_layout(
            margin=dict(t=60, b=20, l=20, r=20),
            height=300
        )
        
        return fig
    
    @staticmethod
    def create_multi_metric_chart(metrics: Dict[str, float], title: str = "多指标对比") -> go.Figure:
        """
        创建多指标对比图表
        
        Args:
            metrics: 指标字典 {指标名: 值}
            title: 图表标题
            
        Returns:
            Plotly图表对象
        """
        if not metrics:
            return go.Figure()
        
        # 标准化数据到0-100范围
        values = list(metrics.values())
        max_val = max(values) if values else 1
        normalized_values = [(v / max_val) * 100 for v in values]
        
        labels = list(metrics.keys())
        
        fig = go.Figure()
        
        # 添加雷达图
        fig.add_trace(go.Scatterpolar(
            r=normalized_values,
            theta=labels,
            fill='toself',
            name='指标值',
            line_color='rgb(32, 201, 151)'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )),
            showlegend=True,
            title={
                'text': title,
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18}
            },
            margin=dict(t=60, b=20, l=20, r=20),
            height=400
        )
        
        return fig
    
    @staticmethod
    def create_treemap(data: List[Dict], values_field: str, labels_field: str,
                      parents_field: Optional[str] = None, title: str = "树状图") -> go.Figure:
        """
        创建树状图
        
        Args:
            data: 数据列表
            values_field: 数值字段名
            labels_field: 标签字段名
            parents_field: 父级字段名
            title: 图表标题
            
        Returns:
            Plotly图表对象
        """
        if not data:
            return go.Figure()
        
        df = pd.DataFrame(data)
        
        fig = go.Figure(go.Treemap(
            labels=df[labels_field],
            values=df[values_field],
            parents=df[parents_field] if parents_field else [""] * len(df),
            textinfo="label+value+percent parent"
        ))
        
        fig.update_layout(
            title={
                'text': title,
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18}
            },
            margin=dict(t=60, b=20, l=20, r=20),
            height=400
        )
        
        return fig
    
    @staticmethod
    def create_sunburst(data: List[Dict], values_field: str, labels_field: str,
                       parents_field: str, title: str = "旭日图") -> go.Figure:
        """
        创建旭日图
        
        Args:
            data: 数据列表
            values_field: 数值字段名
            labels_field: 标签字段名
            parents_field: 父级字段名
            title: 图表标题
            
        Returns:
            Plotly图表对象
        """
        if not data:
            return go.Figure()
        
        df = pd.DataFrame(data)
        
        fig = go.Figure(go.Sunburst(
            labels=df[labels_field],
            parents=df[parents_field],
            values=df[values_field],
            branchvalues="total"
        ))
        
        fig.update_layout(
            title={
                'text': title,
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18}
            },
            margin=dict(t=60, b=20, l=20, r=20),
            height=400
        )
        
        return fig

# Streamlit专用图表函数
def display_metrics_grid(metrics: Dict[str, Any], columns: int = 4):
    """
    显示指标网格
    
    Args:
        metrics: 指标字典
        columns: 列数
    """
    if not metrics:
        st.info("暂无指标数据")
        return
    
    # 创建列布局
    cols = st.columns(columns)
    
    for i, (key, value) in enumerate(metrics.items()):
        with cols[i % columns]:
            if isinstance(value, (int, float)):
                st.metric(label=key, value=f"{value:,.0f}" if isinstance(value, int) else f"{value:.2f}")
            else:
                st.metric(label=key, value=str(value))

def display_chart_with_data(chart_func, data, title: str, show_data: bool = False):
    """
    显示图表并可选显示原始数据
    
    Args:
        chart_func: 图表创建函数
        data: 数据
        title: 标题
        show_data: 是否显示原始数据
    """
    try:
        fig = chart_func(data, title)
        st.plotly_chart(fig, use_container_width=True)
        
        if show_data:
            with st.expander("查看原始数据"):
                if isinstance(data, dict):
                    st.json(data)
                elif isinstance(data, list):
                    if data and isinstance(data[0], dict):
                        st.dataframe(pd.DataFrame(data))
                    else:
                        st.write(data)
                else:
                    st.write(data)
                    
    except Exception as e:
        st.error(f"图表显示失败: {str(e)}")

def create_comparison_chart(data1: Dict, data2: Dict, labels: List[str], 
                          title: str = "对比图表") -> go.Figure:
    """
    创建对比图表
    
    Args:
        data1: 第一组数据
        data2: 第二组数据
        labels: 标签列表
        title: 图表标题
        
    Returns:
        Plotly图表对象
    """
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name=labels[0],
        x=list(data1.keys()),
        y=list(data1.values()),
        marker_color='#FF6B6B'
    ))
    
    fig.add_trace(go.Bar(
        name=labels[1],
        x=list(data2.keys()),
        y=list(data2.values()),
        marker_color='#4ECDC4'
    ))
    
    fig.update_layout(
        title={
            'text': title,
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18}
        },
        barmode='group',
        margin=dict(t=60, b=60, l=60, r=60),
        height=400
    )
    
    return fig