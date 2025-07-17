"""
数据分析工具模块
提供节点统计、关系分析、中心性计算等功能
"""
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from utils.db_connector import Neo4jConnector
from config import ANALYTICS_CONFIG

logger = logging.getLogger(__name__)

class Analytics:
    """数据分析工具类"""
    
    def __init__(self, db_connector: Neo4jConnector):
        self.db = db_connector
        self.cache_ttl = ANALYTICS_CONFIG.get("cache_ttl", 600)
        self.max_nodes = ANALYTICS_CONFIG.get("max_nodes_for_analysis", 10000)
    
    def get_node_statistics(self) -> Dict:
        """
        获取节点统计信息
        
        Returns:
            节点统计数据字典
        """
        try:
            # 基础节点统计
            basic_stats_query = """
            CALL {
                MATCH (c:company) RETURN 'company' as type, count(c) as count
                UNION ALL
                MATCH (i:industry) RETURN 'industry' as type, count(i) as count
                UNION ALL
                MATCH (p:product) RETURN 'product' as type, count(p) as count
            }
            RETURN type, count
            ORDER BY count DESC
            """
            
            basic_results = self.db.query(basic_stats_query)
            
            # 详细统计
            detailed_stats = {}
            total_nodes = 0
            
            for result in basic_results:
                node_type = result["type"]
                count = result["count"]
                detailed_stats[node_type] = count
                total_nodes += count
            
            # 计算百分比
            percentages = {}
            for node_type, count in detailed_stats.items():
                percentages[node_type] = (count / total_nodes * 100) if total_nodes > 0 else 0
            
            # 获取节点属性统计
            attribute_stats = self._get_node_attribute_stats()
            
            return {
                "total_nodes": total_nodes,
                "node_counts": detailed_stats,
                "node_percentages": percentages,
                "attribute_stats": attribute_stats,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取节点统计失败: {str(e)}")
            return {}
    
    def get_relationship_statistics(self) -> Dict:
        """
        获取关系统计信息
        
        Returns:
            关系统计数据字典
        """
        try:
            # 关系类型统计
            relationship_stats_query = """
            CALL {
                MATCH ()-[r:所属行业]->() RETURN '所属行业' as type, count(r) as count
                UNION ALL
                MATCH ()-[r:主营产品]->() RETURN '主营产品' as type, count(r) as count
                UNION ALL
                MATCH ()-[r:上级行业]->() RETURN '上级行业' as type, count(r) as count
                UNION ALL
                MATCH ()-[r:上游材料]->() RETURN '上游材料' as type, count(r) as count
            }
            RETURN type, count
            ORDER BY count DESC
            """
            
            relationship_results = self.db.query(relationship_stats_query)
            
            # 处理结果
            relationship_counts = {}
            total_relationships = 0
            
            for result in relationship_results:
                rel_type = result["type"]
                count = result["count"]
                relationship_counts[rel_type] = count
                total_relationships += count
            
            # 计算百分比
            relationship_percentages = {}
            for rel_type, count in relationship_counts.items():
                relationship_percentages[rel_type] = (count / total_relationships * 100) if total_relationships > 0 else 0
            
            # 获取关系密度统计
            density_stats = self._get_relationship_density_stats()
            
            return {
                "total_relationships": total_relationships,
                "relationship_counts": relationship_counts,
                "relationship_percentages": relationship_percentages,
                "density_stats": density_stats,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取关系统计失败: {str(e)}")
            return {}
    
    def calculate_centrality_metrics(self, limit: int = 20) -> Dict:
        """
        计算中心性指标
        
        Args:
            limit: 返回结果数量限制
            
        Returns:
            中心性指标数据
        """
        try:
            # 度中心性（连接数最多的节点）
            degree_centrality_query = """
            CALL {
                MATCH (c:company)
                OPTIONAL MATCH (c)-[r]-()
                RETURN c.name as name, 'company' as type, count(r) as degree
                UNION ALL
                MATCH (i:industry)
                OPTIONAL MATCH (i)-[r]-()
                RETURN i.name as name, 'industry' as type, count(r) as degree
                UNION ALL
                MATCH (p:product)
                OPTIONAL MATCH (p)-[r]-()
                RETURN p.name as name, 'product' as type, count(r) as degree
            }
            RETURN name, type, degree
            ORDER BY degree DESC
            LIMIT $limit
            """
            
            degree_results = self.db.query(degree_centrality_query, {"limit": limit})
            
            # 入度中心性（被指向最多的节点）
            in_degree_query = """
            CALL {
                MATCH (c:company)
                OPTIONAL MATCH ()-[r]->(c)
                RETURN c.name as name, 'company' as type, count(r) as in_degree
                UNION ALL
                MATCH (i:industry)
                OPTIONAL MATCH ()-[r]->(i)
                RETURN i.name as name, 'industry' as type, count(r) as in_degree
                UNION ALL
                MATCH (p:product)
                OPTIONAL MATCH ()-[r]->(p)
                RETURN p.name as name, 'product' as type, count(r) as in_degree
            }
            RETURN name, type, in_degree
            ORDER BY in_degree DESC
            LIMIT $limit
            """
            
            in_degree_results = self.db.query(in_degree_query, {"limit": limit})
            
            # 出度中心性（指向其他节点最多的节点）
            out_degree_query = """
            CALL {
                MATCH (c:company)
                OPTIONAL MATCH (c)-[r]->()
                RETURN c.name as name, 'company' as type, count(r) as out_degree
                UNION ALL
                MATCH (i:industry)
                OPTIONAL MATCH (i)-[r]->()
                RETURN i.name as name, 'industry' as type, count(r) as out_degree
                UNION ALL
                MATCH (p:product)
                OPTIONAL MATCH (p)-[r]->()
                RETURN p.name as name, 'product' as type, count(r) as out_degree
            }
            RETURN name, type, out_degree
            ORDER BY out_degree DESC
            LIMIT $limit
            """
            
            out_degree_results = self.db.query(out_degree_query, {"limit": limit})
            
            return {
                "degree_centrality": [
                    {
                        "name": result["name"],
                        "type": result["type"],
                        "degree": result["degree"]
                    }
                    for result in degree_results
                ],
                "in_degree_centrality": [
                    {
                        "name": result["name"],
                        "type": result["type"],
                        "in_degree": result["in_degree"]
                    }
                    for result in in_degree_results
                ],
                "out_degree_centrality": [
                    {
                        "name": result["name"],
                        "type": result["type"],
                        "out_degree": result["out_degree"]
                    }
                    for result in out_degree_results
                ],
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"计算中心性指标失败: {str(e)}")
            return {}
    
    def generate_trend_data(self, days: int = 30) -> Dict:
        """
        生成趋势数据（模拟数据，实际项目中可以基于时间戳）
        
        Args:
            days: 天数
            
        Returns:
            趋势数据
        """
        try:
            # 获取当前数据作为基准
            current_stats = self.get_node_statistics()
            
            if not current_stats:
                return {}
            
            # 模拟历史趋势数据
            trend_data = []
            base_date = datetime.now() - timedelta(days=days)
            
            total_nodes = current_stats.get("total_nodes", 0)
            node_counts = current_stats.get("node_counts", {})
            
            for i in range(days + 1):
                date = base_date + timedelta(days=i)
                
                # 模拟增长趋势（实际项目中应该从数据库获取历史数据）
                growth_factor = 0.7 + (i / days) * 0.3  # 从70%增长到100%
                
                daily_data = {
                    "date": date.strftime("%Y-%m-%d"),
                    "total_nodes": int(total_nodes * growth_factor),
                    "companies": int(node_counts.get("company", 0) * growth_factor),
                    "industries": int(node_counts.get("industry", 0) * growth_factor),
                    "products": int(node_counts.get("product", 0) * growth_factor)
                }
                
                trend_data.append(daily_data)
            
            return {
                "trend_data": trend_data,
                "period_days": days,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"生成趋势数据失败: {str(e)}")
            return {}
    
    def get_network_analysis(self) -> Dict:
        """
        获取网络分析数据
        
        Returns:
            网络分析结果
        """
        try:
            # 连通性分析
            connectivity_query = """
            MATCH (n)
            OPTIONAL MATCH (n)-[r]-()
            WITH n, count(r) as connections
            RETURN 
                count(n) as total_nodes,
                count(CASE WHEN connections > 0 THEN 1 END) as connected_nodes,
                count(CASE WHEN connections = 0 THEN 1 END) as isolated_nodes,
                avg(connections) as avg_connections,
                max(connections) as max_connections,
                min(connections) as min_connections
            """
            
            connectivity_results = self.db.query(connectivity_query)
            
            if not connectivity_results:
                return {}
            
            connectivity = connectivity_results[0]
            
            # 计算连通率
            total_nodes = connectivity["total_nodes"]
            connected_nodes = connectivity["connected_nodes"]
            connectivity_rate = (connected_nodes / total_nodes * 100) if total_nodes > 0 else 0
            
            # 获取最活跃的实体
            most_active_query = """
            MATCH (n)-[r]-()
            WITH n, count(r) as connections, labels(n)[0] as node_type
            RETURN n.name as name, node_type, connections
            ORDER BY connections DESC
            LIMIT 10
            """
            
            most_active_results = self.db.query(most_active_query)
            
            return {
                "connectivity": {
                    "total_nodes": total_nodes,
                    "connected_nodes": connected_nodes,
                    "isolated_nodes": connectivity["isolated_nodes"],
                    "connectivity_rate": connectivity_rate,
                    "avg_connections": connectivity["avg_connections"],
                    "max_connections": connectivity["max_connections"],
                    "min_connections": connectivity["min_connections"]
                },
                "most_active_entities": [
                    {
                        "name": result["name"],
                        "type": result["node_type"],
                        "connections": result["connections"]
                    }
                    for result in most_active_results
                ],
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取网络分析失败: {str(e)}")
            return {}
    
    def get_industry_analysis(self) -> Dict:
        """
        获取行业分析数据
        
        Returns:
            行业分析结果
        """
        try:
            # 行业规模分析
            industry_size_query = """
            MATCH (i:industry)<-[:所属行业]-(c:company)
            WITH i, count(c) as company_count
            OPTIONAL MATCH (c:company)-[:所属行业]->(i)
            OPTIONAL MATCH (c)-[:主营产品]->(p:product)
            WITH i, company_count, count(DISTINCT p) as product_count
            RETURN i.name as industry_name,
                   company_count,
                   product_count,
                   (company_count + product_count) as total_entities
            ORDER BY total_entities DESC
            """
            
            industry_results = self.db.query(industry_size_query)
            
            # 行业关系分析
            industry_relations_query = """
            MATCH (i1:industry)-[r]-(i2:industry)
            WITH i1, i2, type(r) as relation_type, count(r) as relation_count
            RETURN i1.name as from_industry,
                   i2.name as to_industry,
                   relation_type,
                   relation_count
            ORDER BY relation_count DESC
            LIMIT 20
            """
            
            relations_results = self.db.query(industry_relations_query)
            
            return {
                "industry_sizes": [
                    {
                        "industry": result["industry_name"],
                        "companies": result["company_count"],
                        "products": result["product_count"],
                        "total_entities": result["total_entities"]
                    }
                    for result in industry_results
                ],
                "industry_relations": [
                    {
                        "from_industry": result["from_industry"],
                        "to_industry": result["to_industry"],
                        "relation_type": result["relation_type"],
                        "relation_count": result["relation_count"]
                    }
                    for result in relations_results
                ],
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取行业分析失败: {str(e)}")
            return {}
    
    def _get_node_attribute_stats(self) -> Dict:
        """获取节点属性统计"""
        try:
            # 检查描述字段的完整性
            description_stats_query = """
            CALL {
                MATCH (c:company)
                RETURN 'company' as type,
                       count(c) as total,
                       count(CASE WHEN c.description IS NOT NULL AND c.description <> '' THEN 1 END) as with_description
                UNION ALL
                MATCH (i:industry)
                RETURN 'industry' as type,
                       count(i) as total,
                       count(CASE WHEN i.description IS NOT NULL AND i.description <> '' THEN 1 END) as with_description
                UNION ALL
                MATCH (p:product)
                RETURN 'product' as type,
                       count(p) as total,
                       count(CASE WHEN p.description IS NOT NULL AND p.description <> '' THEN 1 END) as with_description
            }
            RETURN type, total, with_description,
                   (toFloat(with_description) / toFloat(total) * 100) as completion_rate
            """
            
            results = self.db.query(description_stats_query)
            
            return {
                result["type"]: {
                    "total": result["total"],
                    "with_description": result["with_description"],
                    "completion_rate": result["completion_rate"]
                }
                for result in results
            }
            
        except Exception as e:
            logger.error(f"获取节点属性统计失败: {str(e)}")
            return {}
    
    def _get_relationship_density_stats(self) -> Dict:
        """获取关系密度统计"""
        try:
            # 计算各类型节点间的关系密度
            density_query = """
            MATCH (c:company), (i:industry), (p:product)
            WITH count(c) as companies, count(i) as industries, count(p) as products
            MATCH ()-[r:所属行业]->()
            WITH companies, industries, products, count(r) as company_industry_rels
            MATCH ()-[r:主营产品]->()
            WITH companies, industries, products, company_industry_rels, count(r) as company_product_rels
            RETURN companies, industries, products,
                   company_industry_rels,
                   company_product_rels,
                   (toFloat(company_industry_rels) / (companies * industries)) as ci_density,
                   (toFloat(company_product_rels) / (companies * products)) as cp_density
            """
            
            results = self.db.query(density_query)
            
            if results:
                result = results[0]
                return {
                    "company_industry_density": result.get("ci_density", 0),
                    "company_product_density": result.get("cp_density", 0),
                    "total_possible_ci_relations": result["companies"] * result["industries"],
                    "total_possible_cp_relations": result["companies"] * result["products"],
                    "actual_ci_relations": result["company_industry_rels"],
                    "actual_cp_relations": result["company_product_rels"]
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"获取关系密度统计失败: {str(e)}")
            return {}
    
    def generate_summary_report(self) -> Dict:
        """
        生成综合分析报告
        
        Returns:
            综合报告数据
        """
        try:
            # 收集所有分析数据
            node_stats = self.get_node_statistics()
            relationship_stats = self.get_relationship_statistics()
            centrality_metrics = self.calculate_centrality_metrics(limit=5)
            network_analysis = self.get_network_analysis()
            industry_analysis = self.get_industry_analysis()
            
            # 生成关键洞察
            insights = []
            
            # 节点分布洞察
            if node_stats.get("node_counts"):
                max_type = max(node_stats["node_counts"], key=node_stats["node_counts"].get)
                max_count = node_stats["node_counts"][max_type]
                type_names = {"company": "公司", "industry": "行业", "product": "产品"}
                insights.append(f"数据中{type_names.get(max_type, max_type)}节点最多，共{max_count}个")
            
            # 连通性洞察
            if network_analysis.get("connectivity"):
                connectivity_rate = network_analysis["connectivity"]["connectivity_rate"]
                if connectivity_rate > 90:
                    insights.append(f"网络连通性很好，{connectivity_rate:.1f}%的节点都有连接")
                elif connectivity_rate > 70:
                    insights.append(f"网络连通性良好，{connectivity_rate:.1f}%的节点有连接")
                else:
                    insights.append(f"网络连通性有待提升，只有{connectivity_rate:.1f}%的节点有连接")
            
            # 中心性洞察
            if centrality_metrics.get("degree_centrality"):
                top_entity = centrality_metrics["degree_centrality"][0]
                insights.append(f"最活跃的实体是{top_entity['name']}，有{top_entity['degree']}个连接")
            
            return {
                "summary": {
                    "total_nodes": node_stats.get("total_nodes", 0),
                    "total_relationships": relationship_stats.get("total_relationships", 0),
                    "connectivity_rate": network_analysis.get("connectivity", {}).get("connectivity_rate", 0),
                    "most_active_entity": centrality_metrics.get("degree_centrality", [{}])[0].get("name", "未知")
                },
                "insights": insights,
                "detailed_analysis": {
                    "nodes": node_stats,
                    "relationships": relationship_stats,
                    "centrality": centrality_metrics,
                    "network": network_analysis,
                    "industry": industry_analysis
                },
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"生成综合报告失败: {str(e)}")
            return {}