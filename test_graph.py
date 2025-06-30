from py2neo import Graph

# 连接Neo4j
g = Graph("bolt://127.0.0.1:7687", auth=("neo4j", "12345678"))

# 清空当前数据库（谨慎操作！）
g.run("MATCH (n) DETACH DELETE n")

# 创建测试节点
g.run("CREATE (c:company {name: '测试公司'}) RETURN c")
g.run("CREATE (p:product {name: '测试产品'}) RETURN p")
g.run("CREATE (i:industry {name: '测试行业'}) RETURN i")

# 创建关系
g.run("MATCH (c:company), (p:product) WHERE c.name='测试公司' AND p.name='测试产品' CREATE (c)-[r:主营产品]->(p)")

print("测试节点和关系已创建，请在浏览器中查询: MATCH (n) RETURN n")
