"""
智能搜索引擎模块
提供模糊搜索、实体推荐、相似实体查找等功能
"""
import logging
from typing import List, Dict, Optional, Tuple
from utils.db_connector import Neo4jConnector
from config import SEARCH_CONFIG

logger = logging.getLogger(__name__)

class SearchEngine:
    """智能搜索引擎类"""
    
    def __init__(self, db_connector: Neo4jConnector):
        self.db = db_connector
        self.max_results = SEARCH_CONFIG.get("max_results", 50)
        self.similarity_threshold = SEARCH_CONFIG.get("similarity_threshold", 0.7)
        self.cache_ttl = SEARCH_CONFIG.get("cache_ttl", 300)
    
    def fuzzy_search(self, query: str, entity_type: Optional[str] = None, limit: int = None) -> List[Dict]:
        """
        模糊搜索实体
        
        Args:
            query: 搜索关键词
            entity_type: 实体类型过滤 ('company', 'industry', 'product')
            limit: 结果数量限制
            
        Returns:
            搜索结果列表
        """
        if not query or len(query.strip()) < 1:
            return []
        
        limit = limit or self.max_results
        query = query.strip()
        
        try:
            # 构建搜索查询
            if entity_type:
                # 特定类型搜索
                cypher_query = f"""
                MATCH (n:{entity_type})
                WHERE toLower(n.name) CONTAINS toLower($query) 
                   OR toLower(n.description) CONTAINS toLower($query)
                RETURN n.name as name, 
                       '{entity_type}' as type,
                       n.description as description,
                       CASE 
                           WHEN toLower(n.name) = toLower($query) THEN 1.0
                           WHEN toLower(n.name) STARTS WITH toLower($query) THEN 0.9
                           WHEN toLower(n.name) CONTAINS toLower($query) THEN 0.8
                           ELSE 0.6
                       END as relevance_score
                ORDER BY relevance_score DESC, n.name
                LIMIT $limit
                """
            else:
                # 全类型搜索
                cypher_query = """
                CALL {
                    MATCH (c:company)
                    WHERE toLower(c.name) CONTAINS toLower($query) 
                       OR toLower(c.description) CONTAINS toLower($query)
                    RETURN c.name as name, 'company' as type, c.description as description,
                           CASE 
                               WHEN toLower(c.name) = toLower($query) THEN 1.0
                               WHEN toLower(c.name) STARTS WITH toLower($query) THEN 0.9
                               WHEN toLower(c.name) CONTAINS toLower($query) THEN 0.8
                               ELSE 0.6
                           END as relevance_score
                    UNION ALL
                    MATCH (i:industry)
                    WHERE toLower(i.name) CONTAINS toLower($query) 
                       OR toLower(i.description) CONTAINS toLower($query)
                    RETURN i.name as name, 'industry' as type, i.description as description,
                           CASE 
                               WHEN toLower(i.name) = toLower($query) THEN 1.0
                               WHEN toLower(i.name) STARTS WITH toLower($query) THEN 0.9
                               WHEN toLower(i.name) CONTAINS toLower($query) THEN 0.8
                               ELSE 0.6
                           END as relevance_score
                    UNION ALL
                    MATCH (p:product)
                    WHERE toLower(p.name) CONTAINS toLower($query) 
                       OR toLower(p.description) CONTAINS toLower($query)
                    RETURN p.name as name, 'product' as type, p.description as description,
                           CASE 
                               WHEN toLower(p.name) = toLower($query) THEN 1.0
                               WHEN toLower(p.name) STARTS WITH toLower($query) THEN 0.9
                               WHEN toLower(p.name) CONTAINS toLower($query) THEN 0.8
                               ELSE 0.6
                           END as relevance_score
                }
                RETURN name, type, description, relevance_score
                ORDER BY relevance_score DESC, name
                LIMIT $limit
                """
            
            # 执行查询
            results = self.db.query(cypher_query, {"query": query, "limit": limit})
            
            # 格式化结果
            search_results = []
            for result in results:
                search_results.append({
                    "entity_name": result["name"],
                    "entity_type": result["type"],
                    "description": result.get("description", ""),
                    "relevance_score": result["relevance_score"]
                })
            
            logger.info(f"模糊搜索 '{query}' 返回 {len(search_results)} 个结果")
            return search_results
            
        except Exception as e:
            logger.error(f"模糊搜索失败: {str(e)}")
            return []
    
    def get_recommendations(self, entity_name: str, entity_type: str, limit: int = 5) -> List[Dict]:
        """
        获取实体推荐
        
        Args:
            entity_name: 实体名称
            entity_type: 实体类型
            limit: 推荐数量限制
            
        Returns:
            推荐结果列表
        """
        try:
            recommendations = []
            
            if entity_type == "company":
                # 公司推荐：同行业的其他公司
                query = """
                MATCH (c:company {name: $name})-[:所属行业]->(i:industry)<-[:所属行业]-(other:company)
                WHERE other.name <> $name
                RETURN other.name as entity_name, 'company' as entity_type, 
                       '同行业' as relation_type, 0.8 as confidence_score,
                       other.description as description
                LIMIT $limit
                """
                results = self.db.query(query, {"name": entity_name, "limit": limit})
                
                for result in results:
                    recommendations.append({
                        "entity_name": result["entity_name"],
                        "entity_type": result["entity_type"],
                        "relation_type": result["relation_type"],
                        "confidence_score": result["confidence_score"],
                        "description": result.get("description", "")
                    })
            
            elif entity_type == "industry":
                # 行业推荐：相关行业和该行业的主要公司
                query = """
                CALL {
                    MATCH (i:industry {name: $name})-[r]-(related:industry)
                    WHERE related.name <> $name
                    RETURN related.name as entity_name, 'industry' as entity_type,
                           type(r) as relation_type, 0.7 as confidence_score,
                           related.description as description
                    LIMIT 3
                    UNION ALL
                    MATCH (i:industry {name: $name})<-[:所属行业]-(c:company)
                    RETURN c.name as entity_name, 'company' as entity_type,
                           '所属行业' as relation_type, 0.9 as confidence_score,
                           c.description as description
                    LIMIT 2
                }
                RETURN entity_name, entity_type, relation_type, confidence_score, description
                ORDER BY confidence_score DESC
                LIMIT $limit
                """
                results = self.db.query(query, {"name": entity_name, "limit": limit})
                
                for result in results:
                    recommendations.append({
                        "entity_name": result["entity_name"],
                        "entity_type": result["entity_type"],
                        "relation_type": result["relation_type"],
                        "confidence_score": result["confidence_score"],
                        "description": result.get("description", "")
                    })
            
            elif entity_type == "product":
                # 产品推荐：同公司的其他产品和相关产品
                query = """
                CALL {
                    MATCH (p:product {name: $name})<-[:主营产品]-(c:company)-[:主营产品]->(other:product)
                    WHERE other.name <> $name
                    RETURN other.name as entity_name, 'product' as entity_type,
                           '同公司产品' as relation_type, 0.8 as confidence_score,
                           other.description as description
                    LIMIT 3
                    UNION ALL
                    MATCH (p:product {name: $name})-[r]-(related:product)
                    WHERE related.name <> $name
                    RETURN related.name as entity_name, 'product' as entity_type,
                           type(r) as relation_type, 0.7 as confidence_score,
                           related.description as description
                    LIMIT 2
                }
                RETURN entity_name, entity_type, relation_type, confidence_score, description
                ORDER BY confidence_score DESC
                LIMIT $limit
                """
                results = self.db.query(query, {"name": entity_name, "limit": limit})
                
                for result in results:
                    recommendations.append({
                        "entity_name": result["entity_name"],
                        "entity_type": result["entity_type"],
                        "relation_type": result["relation_type"],
                        "confidence_score": result["confidence_score"],
                        "description": result.get("description", "")
                    })
            
            logger.info(f"为 {entity_name} 生成了 {len(recommendations)} 个推荐")
            return recommendations
            
        except Exception as e:
            logger.error(f"获取推荐失败: {str(e)}")
            return []
    
    def get_similar_entities(self, entity_name: str, entity_type: str, 
                           similarity_threshold: float = None, limit: int = 5) -> List[Dict]:
        """
        获取相似实体
        
        Args:
            entity_name: 实体名称
            entity_type: 实体类型
            similarity_threshold: 相似度阈值
            limit: 结果数量限制
            
        Returns:
            相似实体列表
        """
        threshold = similarity_threshold or self.similarity_threshold
        
        try:
            # 基于关系结构计算相似度
            if entity_type == "company":
                query = """
                MATCH (c1:company {name: $name})-[:所属行业]->(i:industry)<-[:所属行业]-(c2:company)
                WHERE c2.name <> $name
                WITH c1, c2, count(i) as common_industries
                MATCH (c1)-[:主营产品]->(p1:product), (c2)-[:主营产品]->(p2:product)
                WITH c1, c2, common_industries, 
                     count(DISTINCT p1) as c1_products, 
                     count(DISTINCT p2) as c2_products
                OPTIONAL MATCH (c1)-[:主营产品]->(common_p:product)<-[:主营产品]-(c2)
                WITH c1, c2, common_industries, c1_products, c2_products, count(common_p) as common_products
                WITH c2, 
                     (toFloat(common_industries) + toFloat(common_products)) / 
                     (toFloat(c1_products) + toFloat(c2_products) - toFloat(common_products) + 1) as similarity
                WHERE similarity >= $threshold
                RETURN c2.name as entity_name, 'company' as entity_type, 
                       similarity as similarity_score, c2.description as description
                ORDER BY similarity DESC
                LIMIT $limit
                """
            elif entity_type == "industry":
                query = """
                MATCH (i1:industry {name: $name})<-[:所属行业]-(c:company)-[:所属行业]->(i2:industry)
                WHERE i2.name <> $name
                WITH i1, i2, count(c) as common_companies
                MATCH (i1)<-[:所属行业]-(c1:company), (i2)<-[:所属行业]-(c2:company)
                WITH i1, i2, common_companies,
                     count(DISTINCT c1) as i1_companies,
                     count(DISTINCT c2) as i2_companies
                WITH i2,
                     toFloat(common_companies) / 
                     (toFloat(i1_companies) + toFloat(i2_companies) - toFloat(common_companies) + 1) as similarity
                WHERE similarity >= $threshold
                RETURN i2.name as entity_name, 'industry' as entity_type,
                       similarity as similarity_score, i2.description as description
                ORDER BY similarity DESC
                LIMIT $limit
                """
            else:  # product
                query = """
                MATCH (p1:product {name: $name})<-[:主营产品]-(c:company)-[:主营产品]->(p2:product)
                WHERE p2.name <> $name
                WITH p1, p2, count(c) as common_companies
                MATCH (p1)<-[:主营产品]-(c1:company), (p2)<-[:主营产品]-(c2:company)
                WITH p1, p2, common_companies,
                     count(DISTINCT c1) as p1_companies,
                     count(DISTINCT c2) as p2_companies
                WITH p2,
                     toFloat(common_companies) / 
                     (toFloat(p1_companies) + toFloat(p2_companies) - toFloat(common_companies) + 1) as similarity
                WHERE similarity >= $threshold
                RETURN p2.name as entity_name, 'product' as entity_type,
                       similarity as similarity_score, p2.description as description
                ORDER BY similarity DESC
                LIMIT $limit
                """
            
            results = self.db.query(query, {
                "name": entity_name, 
                "threshold": threshold, 
                "limit": limit
            })
            
            similar_entities = []
            for result in results:
                similar_entities.append({
                    "entity_name": result["entity_name"],
                    "entity_type": result["entity_type"],
                    "similarity_score": result["similarity_score"],
                    "description": result.get("description", "")
                })
            
            logger.info(f"为 {entity_name} 找到 {len(similar_entities)} 个相似实体")
            return similar_entities
            
        except Exception as e:
            logger.error(f"获取相似实体失败: {str(e)}")
            return []
    
    def update_search_history(self, session_id: str, entity_name: str, entity_type: str) -> bool:
        """
        更新搜索历史
        
        Args:
            session_id: 会话ID
            entity_name: 实体名称
            entity_type: 实体类型
            
        Returns:
            是否成功
        """
        try:
            query = """
            MERGE (sh:SearchHistory {session_id: $session_id, entity_name: $entity_name})
            ON CREATE SET sh.entity_type = $entity_type, 
                         sh.search_time = datetime(),
                         sh.search_count = 1
            ON MATCH SET sh.search_time = datetime(),
                        sh.search_count = sh.search_count + 1
            """
            
            self.db.query(query, {
                "session_id": session_id,
                "entity_name": entity_name,
                "entity_type": entity_type
            })
            
            # 清理旧的搜索历史（保留最近50条）
            cleanup_query = """
            MATCH (sh:SearchHistory {session_id: $session_id})
            WITH sh ORDER BY sh.search_time DESC
            SKIP 50
            DETACH DELETE sh
            """
            
            self.db.query(cleanup_query, {"session_id": session_id})
            
            return True
            
        except Exception as e:
            logger.error(f"更新搜索历史失败: {str(e)}")
            return False
    
    def get_search_history(self, session_id: str, limit: int = 10) -> List[Dict]:
        """
        获取搜索历史
        
        Args:
            session_id: 会话ID
            limit: 结果数量限制
            
        Returns:
            搜索历史列表
        """
        try:
            query = """
            MATCH (sh:SearchHistory {session_id: $session_id})
            RETURN sh.entity_name as entity_name,
                   sh.entity_type as entity_type,
                   sh.search_time as search_time,
                   sh.search_count as search_count
            ORDER BY sh.search_time DESC
            LIMIT $limit
            """
            
            results = self.db.query(query, {"session_id": session_id, "limit": limit})
            
            history = []
            for result in results:
                history.append({
                    "entity_name": result["entity_name"],
                    "entity_type": result["entity_type"],
                    "search_time": result["search_time"],
                    "search_count": result["search_count"]
                })
            
            return history
            
        except Exception as e:
            logger.error(f"获取搜索历史失败: {str(e)}")
            return []
    
    def get_search_suggestions(self, partial_query: str, entity_type: Optional[str] = None, 
                             limit: int = 10) -> List[str]:
        """
        获取搜索建议
        
        Args:
            partial_query: 部分查询字符串
            entity_type: 实体类型过滤
            limit: 建议数量限制
            
        Returns:
            搜索建议列表
        """
        if not partial_query or len(partial_query.strip()) < 1:
            return []
        
        try:
            if entity_type:
                query = f"""
                MATCH (n:{entity_type})
                WHERE toLower(n.name) STARTS WITH toLower($query)
                RETURN n.name as suggestion
                ORDER BY length(n.name), n.name
                LIMIT $limit
                """
            else:
                query = """
                CALL {
                    MATCH (c:company)
                    WHERE toLower(c.name) STARTS WITH toLower($query)
                    RETURN c.name as suggestion
                    UNION ALL
                    MATCH (i:industry)
                    WHERE toLower(i.name) STARTS WITH toLower($query)
                    RETURN i.name as suggestion
                    UNION ALL
                    MATCH (p:product)
                    WHERE toLower(p.name) STARTS WITH toLower($query)
                    RETURN p.name as suggestion
                }
                RETURN DISTINCT suggestion
                ORDER BY length(suggestion), suggestion
                LIMIT $limit
                """
            
            results = self.db.query(query, {"query": partial_query.strip(), "limit": limit})
            
            suggestions = [result["suggestion"] for result in results]
            return suggestions
            
        except Exception as e:
            logger.error(f"获取搜索建议失败: {str(e)}")
            return []