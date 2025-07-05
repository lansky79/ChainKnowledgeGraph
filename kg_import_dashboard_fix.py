import os
import sys
from py2neo import Graph
import logging
import json
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/dashboard_fix.log", mode='a'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("Dashboard_Fix")

# 加载Neo4j配置
def load_config():
    try:
        config_file = 'config_windows.json' if os.path.exists('config_windows.json') else 'config.json'
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"加载配置文件失败: {e}")
        return {
            "neo4j": {
                "uri": "bolt://127.0.0.1:7687",
                "username": "neo4j",
                "password": "12345678"
            }
        }

config = load_config()

# 连接Neo4j
try:
    graph = Graph(
        config["neo4j"]["uri"],
        auth=(config["neo4j"]["username"], config["neo4j"]["password"])
    )
    logger.info("Neo4j连接成功")
except Exception as e:
    logger.error(f"Neo4j连接失败: {e}")
    sys.exit(1)

def fix_dashboard_errors():
    """修复kg_import_dashboard.py中的错误"""
    # 1. 修复字典除以整数的类型错误
    logger.info("创建修复补丁")
    
    # 读取原始dashboard文件
    try:
        with open('kg_import_dashboard.py', 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"无法读取kg_import_dashboard.py: {e}")
        return False
    
    # 查找并修复错误行
    error_line = "high_strength_pairs = [item for item in analysis_data['results'] if item.get('strength', 0) > max(analysis_data['results'], key=lambda x: x.get('strength', 0)) / 2]"
    fixed_line = "high_strength_pairs = [item for item in analysis_data['results'] if item.get('strength', 0) > max([x.get('strength', 0) for x in analysis_data['results']]) / 2]"
    
    if error_line in content:
        content = content.replace(error_line, fixed_line)
        logger.info("找到并修复了类型错误")
    
    # 保存修复后的文件
    try:
        with open('kg_import_dashboard_fixed.py', 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info("修复后的文件已保存为kg_import_dashboard_fixed.py")
    except Exception as e:
        logger.error(f"无法保存修复后的文件: {e}")
        return False
    
    return True

def enhance_company_relationship_visualization():
    """为企业关系分析添加可视化增强"""
    logger.info("增强企业关系可视化")
    
    # 通过直接修改数据库来增强可视化效果
    # 1. 确保所有企业关系都有数值化的强度属性
    graph.run("""
    MATCH (c1:company)-[r]-(c2:company)
    WHERE EXISTS(r.strength) AND NOT EXISTS(r.strength_value)
    SET r.strength_value = CASE r.strength 
                         WHEN '强' THEN 3 
                         WHEN '中' THEN 2 
                         WHEN '弱' THEN 1 
                         ELSE 1 END
    """)
    
    # 2. 确保所有公司节点都有"公司"标签
    graph.run("""
    MATCH (c:company)
    WHERE NOT c:公司
    SET c:公司
    """)
    
    # 3. 添加"企业"标签，以便可以通过多种方式搜索
    graph.run("""
    MATCH (c:company)
    WHERE NOT c:企业
    SET c:企业
    """)
    
    logger.info("企业关系数据增强完成")
    return True

def create_visualization_examples():
    """创建示例图表展示如何分析企业竞争关系和关联关系"""
    
    st.title("企业关系分析图表示例")
    
    # 获取IT服务III行业的企业竞争关系数据
    compete_data = graph.run("""
    MATCH (c1:company {industry: 'IT服务III'})-[r:竞争对手]->(c2:company)
    RETURN c1.name as company1, c2.name as company2, r.strength as strength
    """).data()
    
    if compete_data:
        st.header("企业竞争关系分析")
        
        # 将数据转换为DataFrame
        df = pd.DataFrame(compete_data)
        
        # 显示数据表格
        st.subheader("竞争关系数据")
        st.dataframe(df)
        
        # 统计每个公司的竞争对手数量
        company_counts = {}
        for item in compete_data:
            company = item['company1']
            if company in company_counts:
                company_counts[company] += 1
            else:
                company_counts[company] = 1
        
        # 创建条形图
        fig, ax = plt.subplots(figsize=(10, 6))
        companies = list(company_counts.keys())
        counts = list(company_counts.values())
        
        ax.bar(companies, counts, color='skyblue')
        ax.set_xlabel('公司')
        ax.set_ylabel('竞争对手数量')
        ax.set_title('IT服务III行业公司竞争情况分析')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        st.pyplot(fig)
        
        # 创建竞争强度饼图
        strength_counts = {'强': 0, '中': 0, '弱': 0}
        for item in compete_data:
            strength = item['strength']
            if strength in strength_counts:
                strength_counts[strength] += 1
        
        fig2, ax2 = plt.subplots(figsize=(8, 8))
        ax2.pie(strength_counts.values(), labels=strength_counts.keys(), autopct='%1.1f%%', 
               colors=['red', 'orange', 'lightblue'])
        ax2.set_title('IT服务III行业竞争关系强度分布')
        
        st.pyplot(fig2)
    
    # 获取IT服务III行业的企业合作关系数据
    collab_data = graph.run("""
    MATCH (c1:company {industry: 'IT服务III'})-[r]->(c2:company)
    WHERE type(r) <> '竞争对手'
    RETURN c1.name as company1, c2.name as company2, type(r) as relation_type, r.strength as strength
    """).data()
    
    if collab_data:
        st.header("企业合作关系分析")
        
        # 将数据转换为DataFrame
        df = pd.DataFrame(collab_data)
        
        # 显示数据表格
        st.subheader("合作关系数据")
        st.dataframe(df)
        
        # 统计关系类型分布
        relation_counts = {}
        for item in collab_data:
            rel_type = item['relation_type']
            if rel_type in relation_counts:
                relation_counts[rel_type] += 1
            else:
                relation_counts[rel_type] = 1
        
        # 创建关系类型分布图
        fig3, ax3 = plt.subplots(figsize=(10, 6))
        rel_types = list(relation_counts.keys())
        counts = list(relation_counts.values())
        
        ax3.bar(rel_types, counts, color='lightgreen')
        ax3.set_xlabel('关系类型')
        ax3.set_ylabel('关系数量')
        ax3.set_title('IT服务III行业公司合作关系类型分布')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        st.pyplot(fig3)
    
    # 产品技术分析
    tech_data = graph.run("""
    MATCH (c:company {industry: 'IT服务III'})-[:生产]->(p:product)-[r]->(t:technology)
    RETURN p.name as product, collect(t.name) as technologies
    """).data()
    
    if tech_data:
        st.header("产品技术分析")
        
        # 展示产品-技术关联
        for item in tech_data:
            st.subheader(f"产品: {item['product']}")
            st.write("相关技术: " + ", ".join(item['technologies']))
        
        # 统计技术使用频率
        tech_counts = {}
        for item in tech_data:
            for tech in item['technologies']:
                if tech in tech_counts:
                    tech_counts[tech] += 1
                else:
                    tech_counts[tech] = 1
        
        # 创建技术使用频率图
        fig4, ax4 = plt.subplots(figsize=(12, 6))
        techs = list(tech_counts.keys())
        counts = list(tech_counts.values())
        
        # 按使用频率排序
        sorted_indices = sorted(range(len(counts)), key=lambda i: counts[i], reverse=True)
        sorted_techs = [techs[i] for i in sorted_indices]
        sorted_counts = [counts[i] for i in sorted_indices]
        
        ax4.bar(sorted_techs, sorted_counts, color='purple')
        ax4.set_xlabel('技术')
        ax4.set_ylabel('使用产品数量')
        ax4.set_title('IT服务III行业技术使用频率')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        st.pyplot(fig4)

def main():
    print("\nKG_Import_Dashboard 修复与增强工具")
    print("==============================")
    print("此工具将执行以下操作：")
    print("1. 修复kg_import_dashboard.py中的类型错误")
    print("2. 增强企业关系分析的图表功能")
    print("3. 确保所有企业节点都有'公司'标签")
    
    confirm = input("\n是否继续？(y/n): ")
    if confirm.lower() == 'y':
        # 修复错误
        if fix_dashboard_errors():
            print("成功修复dashboard文件中的错误")
        else:
            print("修复dashboard文件时出现问题")
        
        # 增强企业关系可视化
        if enhance_company_relationship_visualization():
            print("成功增强企业关系可视化")
        else:
            print("增强企业关系可视化时出现问题")
        
        print("\n修复与增强完成！")
        print("请运行 'streamlit run kg_import_dashboard_fixed.py' 来启动修复后的应用")
        print("或运行 'streamlit run kg_import_dashboard_fix.py' 来查看企业关系分析示例图表")
    else:
        print("操作已取消")

if __name__ == "__main__":
    if 'streamlit.runtime.scriptrunner.script_runner' in sys.modules:
        create_visualization_examples()
    else:
        main() 