"""
数据处理模块，用于处理Neo4j查询结果并转换为可视化所需的格式
"""
import logging
import traceback

logger = logging.getLogger(__name__)

def process_neo4j_results(results, entity_name):
    """
    处理Neo4j查询结果，转换为标准的节点和边格式
    
    参数:
    - results: Neo4j查询结果
    - entity_name: 中心实体名称
    
    返回:
    - nodes: 节点列表
    - edges: 边列表
    """
    try:
        logger.info(f"开始处理查询结果，结果数量: {len(results)}")
        logger.info(f"结果示例: {results[0] if results else 'No results'}")
        
        nodes = []
        edges = []
        node_ids = {}  # 用于去重
        
        for record in results:
            logger.info(f"处理记录: {record.keys()}")
            path = record.get("path", {})
            
            # 调试路径结构
            if path:
                logger.info(f"路径包含以下键: {dir(path)}")
                logger.info(f"路径节点数量: {len(path.nodes) if hasattr(path, 'nodes') else 'Unknown'}")
                logger.info(f"路径关系数量: {len(path.relationships) if hasattr(path, 'relationships') else 'Unknown'}")
            
            # 处理节点
            if hasattr(path, 'nodes'):
                for node in path.nodes:
                    node_id = node.identity
                    if node_id not in node_ids:
                        node_type = list(node.labels)[0]
                        group = 0 if node_type == "industry" else 1 if node_type == "company" else 2
                        
                        nodes.append({
                            "id": node_id,
                            "label": node.get("name", "未命名"),
                            "group": group
                        })
                        node_ids[node_id] = True
                        logger.info(f"添加节点: {node.get('name', 'Unknown')}, 类型: {node_type}")
            
            # 处理关系
            if hasattr(path, 'relationships'):
                for rel in path.relationships:
                    edges.append({
                        "from": rel.start_node.identity,
                        "to": rel.end_node.identity,
                        "label": type(rel).__name__
                    })
                    logger.info(f"添加关系: {rel.start_node.get('name', 'Unknown')} -> {rel.end_node.get('name', 'Unknown')}, 类型: {type(rel).__name__}")
        
        # 处理companies（如果有）
        if results and "companies" in results[0]:
            for record in results:
                companies = record.get("companies", [])
                logger.info(f"处理公司集合，数量: {len(companies)}")
                for company in companies:
                    if company and hasattr(company, 'identity'):
                        company_id = company.identity
                        if company_id not in node_ids and company.get("name"):
                            nodes.append({
                                "id": company_id,
                                "label": company.get("name", "未命名公司"),
                                "group": 1  # 公司
                            })
                            node_ids[company_id] = True
                            logger.info(f"添加公司节点: {company.get('name', 'Unknown')}")
        
        logger.info(f"处理完成，共 {len(nodes)} 个节点和 {len(edges)} 条边")
        return nodes, edges
    
    except Exception as e:
        logger.error(f"处理Neo4j结果失败: {e}")
        logger.error(traceback.format_exc())
        return [], []

def get_entity_options(db_connector, entity_type, search_term=""):
    """
    获取实体选项列表
    
    参数:
    - db_connector: 数据库连接器
    - entity_type: 实体类型
    - search_term: 搜索词
    
    返回:
    - 实体名称列表
    """
    try:
        query_parts = [f"MATCH (n:{entity_type})"]
        params = {}

        if search_term:
            query_parts.append("WHERE toLower(n.name) CONTAINS toLower($search_term)")
            params["search_term"] = search_term
        
        query_parts.append("RETURN n.name AS name ORDER BY name LIMIT 100")
        query = " ".join(query_parts)

        results = db_connector.query(query, params)
        return [record["name"] for record in results]
    except Exception as e:
        logger.error(f"获取实体列表失败: {e}")
        return [] 