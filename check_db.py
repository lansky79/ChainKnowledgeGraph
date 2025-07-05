from build_graph import MedicalGraph

def check_database():
    # 初始化图谱处理器
    g = MedicalGraph()
    
    # 检查公司节点
    result = g.g.run('MATCH (n:company) RETURN count(n) as count').data()
    company_count = result[0]['count'] if result else 0
    print(f'数据库中的公司节点数量: {company_count}')
    
    # 获取示例公司节点
    sample = g.g.run('MATCH (n:company) RETURN n.name as name LIMIT 5').data()
    print('示例公司节点:')
    for item in sample:
        print(f'- {item["name"]}')
    
    # 检查行业节点
    result = g.g.run('MATCH (n:industry) RETURN count(n) as count').data()
    industry_count = result[0]['count'] if result else 0
    print(f'数据库中的行业节点数量: {industry_count}')
    
    # 检查产品节点
    result = g.g.run('MATCH (n:product) RETURN count(n) as count').data()
    product_count = result[0]['count'] if result else 0
    print(f'数据库中的产品节点数量: {product_count}')
    
    # 检查关系
    result = g.g.run('MATCH ()-[r]->() RETURN count(r) as count').data()
    rel_count = result[0]['count'] if result else 0
    print(f'数据库中的关系数量: {rel_count}')
    
    # 检查关系类型
    result = g.g.run('MATCH ()-[r]->() RETURN type(r) as type, count(r) as count').data()
    print('关系类型统计:')
    for item in result:
        print(f'- {item["type"]}: {item["count"]}')

if __name__ == "__main__":
    check_database() 