"""
查询构建器模块
提供可视化查询构建、Cypher查询生成、查询模板管理等功能
"""
import logging
import json
import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from utils.db_connector import Neo4jConnector

logger = logging.getLogger(__name__)

class QueryBuilder:
    """查询构建器类"""
    
    def __init__(self, db_connector: Neo4jConnector):
        self.db = db_connector
        
        # 预定义的查询模板
        self.predefined_templates = {
            "基础节点查询": {
                "description": "查询指定类型的所有节点",
                "cypher": "MATCH (n:{node_type}) RETURN n LIMIT {limit}",
                "parameters": ["node_type", "limit"],
                "category": "基础查询"
            },
            "关系查询": {
                "description": "查询两个节点之间的关系",
                "cypher": "MATCH (a:{node_type1})-[r]->(b:{node_type2}) RETURN a, r, b LIMIT {limit}",
                "parameters": ["node_type1", "node_type2", "limit"],
                "category": "关系查询"
            },
            "路径查询": {
                "description": "查询两个节点之间的最短路径",
                "cypher": "MATCH path = shortestPath((a:{node_type1} {name: '{name1}'})-[*]-(b:{node_type2} {name: '{name2}'})) RETURN path",
                "parameters": ["node_type1", "node_type2", "name1", "name2"],
                "category": "路径查询"
            },
            "度中心性查询": {
                "description": "查询连接数最多的节点",
                "cypher": "MATCH (n:{node_type})-[r]-() WITH n, count(r) as degree RETURN n, degree ORDER BY degree DESC LIMIT {limit}",
                "parameters": ["node_type", "limit"],
                "category": "分析查询"
            },
            "邻居查询": {
                "description": "查询指定节点的所有邻居",
                "cypher": "MATCH (n:{node_type} {name: '{name}'})-[r]-(neighbor) RETURN n, r, neighbor",
                "parameters": ["node_type", "name"],
                "category": "邻居查询"
            }
        }
    
    def build_visual_query(self, query_config: Dict) -> Tuple[bool, str, str]:
        """
        根据可视化配置构建查询
        
        Args:
            query_config: 查询配置字典
            
        Returns:
            (成功标志, 消息, Cypher查询)
        """
        try:
            query_type = query_config.get("query_type", "")
            
            if query_type == "node_query":
                return self._build_node_query(query_config)
            elif query_type == "relationship_query":
                return self._build_relationship_query(query_config)
            elif query_type == "path_query":
                return self._build_path_query(query_config)
            elif query_type == "aggregation_query":
                return self._build_aggregation_query(query_config)
            elif query_type == "filter_query":
                return self._build_filter_query(query_config)
            else:
                return False, f"不支持的查询类型: {query_type}", ""
                
        except Exception as e:
            logger.error(f"构建可视化查询失败: {str(e)}")
            return False, f"构建查询失败: {str(e)}", ""
    
    def _build_node_query(self, config: Dict) -> Tuple[bool, str, str]:
        """构建节点查询"""
        node_type = config.get("node_type", "")
        properties = config.get("properties", {})
        limit = config.get("limit", 100)
        
        if not node_type:
            return False, "请指定节点类型", ""
        
        # 构建WHERE子句
        where_clauses = []
        for key, value in properties.items():
            if value:
                where_clauses.append(f"n.{key} = '{value}'")
        
        where_clause = " AND ".join(where_clauses)
        if where_clause:
            where_clause = f"WHERE {where_clause}"
        
        cypher = f"MATCH (n:{node_type}) {where_clause} RETURN n LIMIT {limit}"
        
        return True, "节点查询构建成功", cypher
    
    def _build_relationship_query(self, config: Dict) -> Tuple[bool, str, str]:
        """构建关系查询"""
        source_type = config.get("source_type", "")
        target_type = config.get("target_type", "")
        relationship_type = config.get("relationship_type", "")
        limit = config.get("limit", 100)
        
        if not source_type or not target_type:
            return False, "请指定源节点和目标节点类型", ""
        
        # 构建关系部分
        if relationship_type:
            rel_part = f"[r:{relationship_type}]"
        else:
            rel_part = "[r]"
        
        cypher = f"MATCH (a:{source_type})-{rel_part}->(b:{target_type}) RETURN a, r, b LIMIT {limit}"
        
        return True, "关系查询构建成功", cypher
    
    def _build_path_query(self, config: Dict) -> Tuple[bool, str, str]:
        """构建路径查询"""
        source_type = config.get("source_type", "")
        target_type = config.get("target_type", "")
        source_name = config.get("source_name", "")
        target_name = config.get("target_name", "")
        max_depth = config.get("max_depth", 5)
        path_type = config.get("path_type", "shortest")
        
        if not all([source_type, target_type, source_name, target_name]):
            return False, "请指定完整的路径查询参数", ""
        
        if path_type == "shortest":
            cypher = f"""
            MATCH path = shortestPath((a:{source_type} {{name: '{source_name}'}})-[*..{max_depth}]-(b:{target_type} {{name: '{target_name}'}}))
            RETURN path
            """
        else:  # all paths
            cypher = f"""
            MATCH path = (a:{source_type} {{name: '{source_name}'}})-[*..{max_depth}]-(b:{target_type} {{name: '{target_name}'}})
            RETURN path LIMIT 10
            """
        
        return True, "路径查询构建成功", cypher.strip()
    
    def _build_aggregation_query(self, config: Dict) -> Tuple[bool, str, str]:
        """构建聚合查询"""
        node_type = config.get("node_type", "")
        aggregation_type = config.get("aggregation_type", "count")
        group_by = config.get("group_by", "")
        
        if not node_type:
            return False, "请指定节点类型", ""
        
        if aggregation_type == "count":
            if group_by:
                cypher = f"MATCH (n:{node_type}) RETURN n.{group_by} as {group_by}, count(n) as count ORDER BY count DESC"
            else:
                cypher = f"MATCH (n:{node_type}) RETURN count(n) as total_count"
        elif aggregation_type == "degree":
            cypher = f"MATCH (n:{node_type})-[r]-() WITH n, count(r) as degree RETURN n.name as name, degree ORDER BY degree DESC LIMIT 20"
        else:
            return False, f"不支持的聚合类型: {aggregation_type}", ""
        
        return True, "聚合查询构建成功", cypher
    
    def _build_filter_query(self, config: Dict) -> Tuple[bool, str, str]:
        """构建过滤查询"""
        node_type = config.get("node_type", "")
        filters = config.get("filters", [])
        logic_operator = config.get("logic_operator", "AND")
        limit = config.get("limit", 100)
        
        if not node_type:
            return False, "请指定节点类型", ""
        
        if not filters:
            return False, "请添加至少一个过滤条件", ""
        
        # 构建过滤条件
        filter_clauses = []
        for filter_item in filters:
            field = filter_item.get("field", "")
            operator = filter_item.get("operator", "=")
            value = filter_item.get("value", "")
            
            if field and value:
                if operator == "=":
                    filter_clauses.append(f"n.{field} = '{value}'")
                elif operator == "!=":
                    filter_clauses.append(f"n.{field} <> '{value}'")
                elif operator == "contains":
                    filter_clauses.append(f"toLower(n.{field}) CONTAINS toLower('{value}')")
                elif operator == "starts_with":
                    filter_clauses.append(f"toLower(n.{field}) STARTS WITH toLower('{value}')")
                elif operator == "ends_with":
                    filter_clauses.append(f"toLower(n.{field}) ENDS WITH toLower('{value}')")
        
        if not filter_clauses:
            return False, "没有有效的过滤条件", ""
        
        where_clause = f" {logic_operator} ".join(filter_clauses)
        cypher = f"MATCH (n:{node_type}) WHERE {where_clause} RETURN n LIMIT {limit}"
        
        return True, "过滤查询构建成功", cypher
    
    def validate_cypher_query(self, cypher: str) -> Tuple[bool, str]:
        """
        验证Cypher查询语法
        
        Args:
            cypher: Cypher查询字符串
            
        Returns:
            (是否有效, 错误信息)
        """
        try:
            # 基本语法检查
            cypher = cypher.strip()
            
            if not cypher:
                return False, "查询不能为空"
            
            # 检查是否包含危险操作
            dangerous_keywords = ["DELETE", "REMOVE", "SET", "CREATE", "MERGE", "DROP"]
            cypher_upper = cypher.upper()
            
            for keyword in dangerous_keywords:
                if keyword in cypher_upper:
                    return False, f"为了安全起见，不允许使用 {keyword} 操作"
            
            # 检查基本语法结构
            if not any(keyword in cypher_upper for keyword in ["MATCH", "RETURN"]):
                return False, "查询必须包含 MATCH 和 RETURN 子句"
            
            # 尝试执行查询验证（限制结果数量）
            test_query = f"{cypher} LIMIT 1"
            try:
                self.db.query(test_query)
                return True, "查询语法正确"
            except Exception as e:
                return False, f"查询语法错误: {str(e)}"
                
        except Exception as e:
            logger.error(f"验证Cypher查询失败: {str(e)}")
            return False, f"验证失败: {str(e)}"
    
    def execute_custom_query(self, cypher: str, limit: int = 100) -> Tuple[bool, str, List[Dict]]:
        """
        执行自定义查询
        
        Args:
            cypher: Cypher查询字符串
            limit: 结果限制数量
            
        Returns:
            (成功标志, 消息, 查询结果)
        """
        try:
            # 验证查询
            is_valid, error_msg = self.validate_cypher_query(cypher)
            if not is_valid:
                return False, error_msg, []
            
            # 添加LIMIT限制（如果查询中没有）
            if "LIMIT" not in cypher.upper():
                cypher = f"{cypher} LIMIT {limit}"
            
            # 执行查询
            results = self.db.query(cypher)
            
            logger.info(f"执行自定义查询成功，返回 {len(results)} 条结果")
            return True, f"查询执行成功，返回 {len(results)} 条结果", results
            
        except Exception as e:
            logger.error(f"执行自定义查询失败: {str(e)}")
            return False, f"查询执行失败: {str(e)}", []
    
    def save_query_template(self, name: str, cypher: str, description: str = "", 
                           category: str = "自定义", is_public: bool = False) -> Tuple[bool, str]:
        """
        保存查询模板
        
        Args:
            name: 模板名称
            cypher: Cypher查询
            description: 模板描述
            category: 模板分类
            is_public: 是否公开
            
        Returns:
            (成功标志, 消息)
        """
        try:
            # 验证查询
            is_valid, error_msg = self.validate_cypher_query(cypher)
            if not is_valid:
                return False, f"查询模板无效: {error_msg}"
            
            # 检查模板名称是否已存在
            check_query = """
            MATCH (qt:QueryTemplate {name: $name})
            RETURN count(qt) as count
            """
            
            check_results = self.db.query(check_query, {"name": name})
            if check_results and check_results[0]["count"] > 0:
                return False, f"模板名称 '{name}' 已存在"
            
            # 保存模板
            save_query = """
            CREATE (qt:QueryTemplate {
                name: $name,
                cypher: $cypher,
                description: $description,
                category: $category,
                is_public: $is_public,
                created_time: datetime(),
                created_by: 'system'
            })
            RETURN qt
            """
            
            self.db.query(save_query, {
                "name": name,
                "cypher": cypher,
                "description": description,
                "category": category,
                "is_public": is_public
            })
            
            logger.info(f"保存查询模板成功: {name}")
            return True, f"查询模板 '{name}' 保存成功"
            
        except Exception as e:
            logger.error(f"保存查询模板失败: {str(e)}")
            return False, f"保存模板失败: {str(e)}"
    
    def get_query_templates(self, category: str = None) -> List[Dict]:
        """
        获取查询模板列表
        
        Args:
            category: 模板分类过滤
            
        Returns:
            模板列表
        """
        try:
            # 获取预定义模板
            templates = []
            
            for name, template in self.predefined_templates.items():
                if category is None or template["category"] == category:
                    templates.append({
                        "name": name,
                        "cypher": template["cypher"],
                        "description": template["description"],
                        "category": template["category"],
                        "is_predefined": True,
                        "created_time": None
                    })
            
            # 获取用户自定义模板
            if category:
                query = """
                MATCH (qt:QueryTemplate {category: $category})
                RETURN qt.name as name, qt.cypher as cypher, qt.description as description,
                       qt.category as category, qt.created_time as created_time
                ORDER BY qt.created_time DESC
                """
                results = self.db.query(query, {"category": category})
            else:
                query = """
                MATCH (qt:QueryTemplate)
                RETURN qt.name as name, qt.cypher as cypher, qt.description as description,
                       qt.category as category, qt.created_time as created_time
                ORDER BY qt.created_time DESC
                """
                results = self.db.query(query)
            
            # 添加用户模板
            for result in results:
                templates.append({
                    "name": result["name"],
                    "cypher": result["cypher"],
                    "description": result["description"],
                    "category": result["category"],
                    "is_predefined": False,
                    "created_time": result["created_time"]
                })
            
            return templates
            
        except Exception as e:
            logger.error(f"获取查询模板失败: {str(e)}")
            return []
    
    def delete_query_template(self, name: str) -> Tuple[bool, str]:
        """
        删除查询模板
        
        Args:
            name: 模板名称
            
        Returns:
            (成功标志, 消息)
        """
        try:
            # 检查是否为预定义模板
            if name in self.predefined_templates:
                return False, "不能删除预定义模板"
            
            # 删除模板
            delete_query = """
            MATCH (qt:QueryTemplate {name: $name})
            DELETE qt
            RETURN count(qt) as deleted_count
            """
            
            results = self.db.query(delete_query, {"name": name})
            
            if results and results[0]["deleted_count"] > 0:
                logger.info(f"删除查询模板成功: {name}")
                return True, f"模板 '{name}' 删除成功"
            else:
                return False, f"未找到模板 '{name}'"
                
        except Exception as e:
            logger.error(f"删除查询模板失败: {str(e)}")
            return False, f"删除模板失败: {str(e)}"
    
    def get_query_suggestions(self, partial_query: str) -> List[str]:
        """
        获取查询建议
        
        Args:
            partial_query: 部分查询字符串
            
        Returns:
            建议列表
        """
        suggestions = []
        
        # Cypher关键词建议
        keywords = [
            "MATCH", "RETURN", "WHERE", "WITH", "ORDER BY", "LIMIT",
            "CREATE", "MERGE", "DELETE", "SET", "REMOVE",
            "OPTIONAL MATCH", "UNION", "UNWIND", "CALL"
        ]
        
        partial_upper = partial_query.upper()
        
        for keyword in keywords:
            if keyword.startswith(partial_upper):
                suggestions.append(keyword)
        
        # 节点类型建议
        node_types = ["company", "industry", "product"]
        for node_type in node_types:
            if node_type.startswith(partial_query.lower()):
                suggestions.append(f":{node_type}")
        
        # 关系类型建议
        relationship_types = ["所属行业", "主营产品", "上级行业", "上游材料"]
        for rel_type in relationship_types:
            if rel_type.startswith(partial_query):
                suggestions.append(f":{rel_type}")
        
        return suggestions[:10]  # 限制建议数量
    
    def get_query_statistics(self) -> Dict:
        """
        获取查询统计信息
        
        Returns:
            统计信息字典
        """
        try:
            # 获取模板统计
            template_stats_query = """
            MATCH (qt:QueryTemplate)
            RETURN count(qt) as total_templates,
                   count(CASE WHEN qt.is_public = true THEN 1 END) as public_templates
            """
            
            template_results = self.db.query(template_stats_query)
            
            stats = {
                "total_templates": len(self.predefined_templates),
                "custom_templates": 0,
                "public_templates": 0,
                "predefined_templates": len(self.predefined_templates),
                "template_categories": list(set(t["category"] for t in self.predefined_templates.values()))
            }
            
            if template_results:
                result = template_results[0]
                stats["custom_templates"] = result.get("total_templates", 0)
                stats["public_templates"] = result.get("public_templates", 0)
                stats["total_templates"] += stats["custom_templates"]
            
            return stats
            
        except Exception as e:
            logger.error(f"获取查询统计失败: {str(e)}")
            return {}