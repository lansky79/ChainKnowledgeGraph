import streamlit as st
import pandas as pd
import os
import json
from build_graph import MedicalGraph

# 设置页面配置
st.set_page_config(
    page_title="Streamlit测试应用",
    page_icon="🔍",
    layout="wide"
)

# 主标题
st.title("Streamlit测试应用")
st.write("这是一个简化版的测试应用，用于检查Streamlit是否能正常启动和显示")

# 创建选项卡
tab1, tab2, tab3 = st.tabs(["基本信息", "Neo4j连接", "数据文件"])

with tab1:
    st.header("基本信息")
    st.write("Python版本:", st.secrets.get("python_version", "未知"))
    st.write("运行平台:", st.secrets.get("platform", "未知"))
    st.write("当前工作目录:", os.getcwd())
    
    # 显示配置信息
    if os.path.exists('config_windows.json'):
        with st.expander("配置文件内容"):
            try:
                with open('config_windows.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    st.json(config)
            except Exception as e:
                st.error(f"读取配置文件失败: {e}")
    else:
        st.warning("未找到配置文件 config_windows.json")

with tab2:
    st.header("Neo4j连接测试")
    
    if st.button("测试Neo4j连接"):
        with st.spinner("正在连接Neo4j..."):
            try:
                # 尝试初始化MedicalGraph
                handler = MedicalGraph()
                
                if handler.g is None:
                    st.error("Neo4j连接失败，请确保Neo4j服务已启动")
                else:
                    # 尝试执行一个简单的查询
                    try:
                        result = handler.g.run("RETURN 1 AS test").data()
                        st.success(f"Neo4j连接成功，测试查询结果: {result}")
                    except Exception as e:
                        st.error(f"Neo4j查询失败: {e}")
            except Exception as e:
                st.error(f"MedicalGraph初始化失败: {e}")

with tab3:
    st.header("数据文件检查")
    
    # 检查数据目录
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    
    if not os.path.exists(data_dir):
        st.error(f"数据目录不存在: {data_dir}")
    else:
        st.success(f"数据目录存在: {data_dir}")
        
        # 列出预期的数据文件
        expected_files = [
            'company.json', 
            'industry.json', 
            'product.json',
            'company_industry.json',
            'company_product.json',
            'industry_industry.json',
            'product_product.json'
        ]
        
        # 创建数据框显示文件状态
        file_status = []
        for file in expected_files:
            file_path = os.path.join(data_dir, file)
            status = "存在" if os.path.exists(file_path) else "不存在"
            size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            file_status.append({
                "文件名": file,
                "状态": status,
                "大小(字节)": size
            })
        
        # 显示文件状态表格
        st.dataframe(pd.DataFrame(file_status))

# 页脚
st.markdown("---")
st.markdown("Streamlit测试应用 | 用于诊断问题") 