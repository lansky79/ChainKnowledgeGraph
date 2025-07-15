from src.neo4j_handler import Neo4jHandler
handler = Neo4jHandler()
result = handler.g.run('MATCH (c:company {name: "华为"}) RETURN c').data()
print(result)