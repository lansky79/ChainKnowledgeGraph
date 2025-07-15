"""
数据库连接器，用于处理与Neo4j的连接和查询
"""
import logging
from py2neo import Graph
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_CONFIG

logger = logging.getLogger(__name__)

class Neo4jConnector:
    """Neo4j数据库连接器"""
    
    def __init__(self):
        """初始化连接器"""
        self.graph = None
        self.connect()
    
    def connect(self):
        """连接到Neo4j数据库"""
        try:
            self.graph = Graph(
                DB_CONFIG["uri"],
                auth=(DB_CONFIG["username"], DB_CONFIG["password"])
            )
            logger.info("成功连接到Neo4j数据库")
            return True
        except Exception as e:
            logger.error(f"连接Neo4j数据库失败: {e}")
            return False
    
    def query(self, cypher, params=None):
        """
        执行Cypher查询并返回结果
        
        参数:
        - cypher: Cypher查询字符串
        - params: 查询参数字典
        
        返回:
        - 查询结果列表
        """
        if not self.graph:
            if not self.connect():
                return []
        
        try:
            params = params or {}
            result = self.graph.run(cypher, **params).data()
            return result
        except Exception as e:
            logger.error(f"查询执行失败: {e}")
            return []
    
    def get_node_count(self, label=None):
        """获取节点数量"""
        try:
            if label:
                query = f"MATCH (n:{label}) RETURN count(n) as count"
            else:
                query = "MATCH (n) RETURN count(n) as count"
            
            result = self.query(query)
            return result[0]["count"] if result else 0
        except Exception as e:
            logger.error(f"获取节点数量失败: {e}")
            return 0
    
    def get_relationship_count(self, source_type=None, target_type=None, rel_type=None):
        """
        获取关系数量
        
        参数:
        - source_type: 源节点类型（可选）
        - target_type: 目标节点类型（可选）
        - rel_type: 关系类型（可选）
        
        返回:
        - 关系数量
        """
        try:
            if source_type and target_type and rel_type:
                query = f"MATCH (:{source_type})-[r:{rel_type}]->(:{target_type}) RETURN count(r) as count"
            elif rel_type:
                query = f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count"
            else:
                query = "MATCH ()-[r]->() RETURN count(r) as count"
            
            result = self.query(query)
            return result[0]["count"] if result else 0
        except Exception as e:
            logger.error(f"获取关系数量失败: {e}")
            return 0 