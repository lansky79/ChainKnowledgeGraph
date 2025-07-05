from src.neo4j_handler import Neo4jHandler
handler = Neo4jHandler()
print(handler.g.run('MATCH (n) RETURN count(n) as count').data()[0]['count'])