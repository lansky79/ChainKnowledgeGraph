from py2neo import Graph
import logging
import json
import os

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Neo4jHandler")

class Config:
    """配置类，用于管理Neo4j连接参数"""
    
    def __init__(self, uri="bolt://localhost:7687", username="neo4j", password="12345678"):
        self.uri = uri
        self.username = username
        self.password = password
    
    @classmethod
    def from_json(cls, config_file):
        """从JSON文件加载配置"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                neo4j_config = config_data.get('neo4j', {})
                return cls(
                    uri=neo4j_config.get('uri', "bolt://localhost:7687"),
                    username=neo4j_config.get('username', "neo4j"),
                    password=neo4j_config.get('password', "12345678")
                )
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return cls()  # 返回默认配置

class Neo4jHandler:
    """Neo4j处理器类，处理与Neo4j数据库的交互"""
    
    def __init__(self, config=None):
        """
        初始化Neo4j处理器
        
        Args:
            config: Config对象或配置字典
        """
        if config is None:
            # 尝试从配置文件加载
            if os.path.exists('config_windows.json'):
                config = Config.from_json('config_windows.json')
            elif os.path.exists('config.json'):
                config = Config.from_json('config.json')
            else:
                config = Config()
        elif isinstance(config, dict):
            config = Config(**config)
        
        self.config = config
        self.g = None
        self.import_state = {}
        
        # 数据文件路径
        self.company_path = "data/company.jsonl" if os.path.exists("data/company.jsonl") else "data/company.json"
        self.industry_path = "data/industry.jsonl" if os.path.exists("data/industry.jsonl") else "data/industry.json"
        self.product_path = "data/product.jsonl" if os.path.exists("data/product.jsonl") else "data/product.json"
        self.company_industry_path = "data/company_industry.jsonl" if os.path.exists("data/company_industry.jsonl") else "data/company_industry.json"
        self.industry_industry = "data/industry_industry.json"
        self.company_product_path = "data/company_product.jsonl" if os.path.exists("data/company_product.jsonl") else "data/company_product.json"
        self.product_product = "data/product_product.json"
        
        # 尝试加载导入状态
        self.load_import_state()
        
        # 连接数据库
        self._connect()
    
    def _connect(self):
        """连接到Neo4j数据库"""
        try:
            self.g = Graph(
                self.config.uri,
                auth=(self.config.username, self.config.password)
            )
            logger.info(f"成功连接到Neo4j数据库: {self.config.uri}")
            return True
        except Exception as e:
            logger.error(f"连接Neo4j数据库失败: {e}")
            self.g = None
            return False
    
    def run_query(self, query, **params):
        """
        执行Cypher查询
        
        Args:
            query: Cypher查询字符串
            **params: 查询参数
            
        Returns:
            查询结果列表
        """
        try:
            if not self.g:
                if not self._connect():
                    logger.error("数据库未连接，无法执行查询")
                    return []
            
            result = self.g.run(query, **params).data()
            return result
        except Exception as e:
            logger.error(f"执行查询失败: {e}")
            return []
    
    def create_index(self, label, property_name):
        """
        创建索引
        
        Args:
            label: 节点标签
            property_name: 属性名称
        """
        try:
            query = f"CREATE INDEX ON :{label}({property_name})"
            self.g.run(query)
            logger.info(f"创建索引: {label}({property_name})")
            return True
        except Exception as e:
            logger.error(f"创建索引失败: {e}")
            return False
    
    def clear_database(self):
        """清空数据库中的所有节点和关系"""
        try:
            self.g.run("MATCH (n) DETACH DELETE n")
            logger.info("已清空数据库")
            return True
        except Exception as e:
            logger.error(f"清空数据库失败: {e}")
            return False
    
    def get_node_count(self, label=None):
        """
        获取节点数量
        
        Args:
            label: 节点标签，如果为None则计算所有节点
            
        Returns:
            节点数量
        """
        try:
            if label:
                query = f"MATCH (n:{label}) RETURN count(n) as count"
            else:
                query = "MATCH (n) RETURN count(n) as count"
            
            result = self.g.run(query).data()
            return result[0]["count"] if result else 0
        except Exception as e:
            logger.error(f"获取节点数量失败: {e}")
            return 0
    
    def get_relationship_count(self, type=None):
        """
        获取关系数量
        
        Args:
            type: 关系类型，如果为None则计算所有关系
            
        Returns:
            关系数量
        """
        try:
            if type:
                query = f"MATCH ()-[r:{type}]->() RETURN count(r) as count"
            else:
                query = "MATCH ()-[r]->() RETURN count(r) as count"
            
            result = self.g.run(query).data()
            return result[0]["count"] if result else 0
        except Exception as e:
            logger.error(f"获取关系数量失败: {e}")
            return 0
    
    def save_import_state(self):
        """保存导入状态"""
        try:
            with open("import_state.json", "w", encoding="utf-8") as f:
                json.dump(self.import_state, f, ensure_ascii=False, indent=2)
            logger.info("已保存导入状态")
            return True
        except Exception as e:
            logger.error(f"保存导入状态失败: {e}")
            return False
    
    def load_import_state(self):
        """加载导入状态"""
        try:
            if os.path.exists("import_state.json"):
                with open("import_state.json", "r", encoding="utf-8") as f:
                    self.import_state = json.load(f)
                logger.info("已加载导入状态")
                return True
            else:
                logger.info("导入状态文件不存在，使用空状态")
                self.import_state = {}
                return False
        except Exception as e:
            logger.error(f"加载导入状态失败: {e}")
            self.import_state = {}
            return False
    
    def reset_import_state(self):
        """重置导入状态"""
        self.import_state = {}
        logger.info("已重置导入状态")
        return self.save_import_state()
    
    def _count_file_lines(self, file_path):
        """计算文件行数"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return sum(1 for _ in f)
        except Exception as e:
            logger.error(f"计算文件行数失败: {e}")
            return 0 

    def create_graphnodes(self, batch_size=10000):
        """
        创建图谱节点
        
        Args:
            batch_size: 批次大小
            
        Returns:
            创建的节点数量
        """
        try:
            node_count = 0
            
            # 导入公司节点
            company_count = self.import_nodes("company", self.company_path, batch_size)
            node_count += company_count
            
            # 导入行业节点
            industry_count = self.import_nodes("industry", self.industry_path, batch_size)
            node_count += industry_count
            
            # 导入产品节点
            product_count = self.import_nodes("product", self.product_path, batch_size)
            node_count += product_count
            
            # 保存导入状态
            self.save_import_state()
            
            logger.info(f"总共导入 {node_count} 个节点")
            return node_count
        except Exception as e:
            logger.error(f"创建图谱节点失败: {e}")
            return 0
    
    def create_graphrels(self, batch_size=10000):
        """
        创建图谱关系
        
        Args:
            batch_size: 批次大小
            
        Returns:
            创建的关系数量
        """
        try:
            rel_count = 0
            
            # 导入公司-行业关系
            ci_count = self.import_company_industry_rels(self.company_industry_path, batch_size)
            rel_count += ci_count
            
            # 导入行业-行业关系
            ii_count = self.import_industry_industry_rels(self.industry_industry, batch_size)
            rel_count += ii_count
            
            # 导入公司-产品关系
            cp_count = self.import_company_product_rels(self.company_product_path, batch_size)
            rel_count += cp_count
            
            # 导入产品-产品关系
            pp_count = self.import_product_product_rels(self.product_product, batch_size)
            rel_count += pp_count
            
            # 保存导入状态
            self.save_import_state()
            
            logger.info(f"总共导入 {rel_count} 条关系")
            return rel_count
        except Exception as e:
            logger.error(f"创建图谱关系失败: {e}")
            return 0
    
    def import_nodes(self, label, data, is_file=True, batch_size=10000):
        """
        导入节点
        
        Args:
            label: 节点标签
            data: 数据文件路径或数据列表
            is_file: 如果data是文件路径，则为True，否则为False
            batch_size: 批次大小
            
        Returns:
            导入的节点数量
        """
        try:
            if is_file:
                if not os.path.exists(data):
                    logger.warning(f"数据文件不存在: {data}")
                    return 0
                
                # 获取已导入数量
                imported = self.import_state.get(label, 0)
                logger.info(f"{label}节点已导入: {imported}")
                
                # 获取文件总行数
                total_lines = self._count_file_lines(data)
                if imported >= total_lines:
                    logger.info(f"{label}节点已全部导入")
                    return 0
                
                # 读取JSON文件
                with open(data, 'r', encoding='utf-8') as f:
                    # 跳过已导入的行
                    for _ in range(imported):
                        next(f)
                    
                    # 批量导入
                    count = 0
                    batch = []
                    
                    for line in f:
                        try:
                            line_data = json.loads(line.strip())
                            batch.append(line_data)
                            count += 1
                            
                            if len(batch) >= batch_size:
                                self._create_nodes_batch(label, batch)
                                imported += len(batch)
                                self.import_state[label] = imported
                                batch = []
                                
                                # 保存导入状态
                                self.save_import_state()
                        except json.JSONDecodeError:
                            logger.error(f"JSON解析错误: {line}")
                            continue
                        except Exception as e:
                            logger.error(f"处理行时出错: {e}")
                            continue
                    
                    # 处理剩余批次
                    if batch:
                        self._create_nodes_batch(label, batch)
                        imported += len(batch)
                        self.import_state[label] = imported
                        
                        # 保存导入状态
                        self.save_import_state()
                    
                    logger.info(f"导入 {count} 个 {label} 节点")
                    return count
            else:
                # 直接从数据列表导入
                self._create_nodes_batch(label, data)
                logger.info(f"从列表导入 {len(data)} 个 {label} 节点")
                return len(data)
        except Exception as e:
            logger.error(f"导入{label}节点失败: {e}")
            return 0
    
    def _create_nodes_batch(self, label, nodes_data):
        """
        批量创建节点
        
        Args:
            label: 节点标签
            nodes_data: 节点数据列表
        """
        try:
            # 构建批量创建节点的Cypher查询
            query = f"""
            UNWIND $nodes AS node
            MERGE (n:{label} {{name: node.name}})
            ON CREATE SET n += node
            """
            
            # 执行查询
            self.g.run(query, nodes=nodes_data)
        except Exception as e:
            logger.error(f"批量创建{label}节点失败: {e}")
            raise
    
    def import_company_industry_rels(self, file_path, batch_size=10000):
        """
        导入公司-行业关系
        
        Args:
            file_path: 数据文件路径
            batch_size: 批次大小
            
        Returns:
            导入的关系数量
        """
        try:
            return self._import_relationships(
                rel_key="company_industry", 
                data=file_path, 
                start_label="company", 
                end_label="industry",
                rel_type="属于",
                batch_size=batch_size
            )
        except Exception as e:
            logger.error(f"导入公司-行业关系失败: {e}")
            return 0
    
    def import_industry_industry_rels(self, file_path, batch_size=10000):
        """
        导入行业-行业关系
        
        Args:
            file_path: 数据文件路径
            batch_size: 批次大小
            
        Returns:
            导入的关系数量
        """
        try:
            return self._import_relationships(
                rel_key="industry_industry", 
                data=file_path, 
                start_label="industry", 
                end_label="industry",
                rel_type="上级行业",
                batch_size=batch_size
            )
        except Exception as e:
            logger.error(f"导入行业-行业关系失败: {e}")
            return 0
    
    def import_company_product_rels(self, file_path, batch_size=10000):
        """
        导入公司-产品关系
        
        Args:
            file_path: 数据文件路径
            batch_size: 批次大小
            
        Returns:
            导入的关系数量
        """
        try:
            return self._import_relationships(
                rel_key="company_product", 
                data=file_path, 
                start_label="company", 
                end_label="product",
                rel_type="拥有",
                batch_size=batch_size
            )
        except Exception as e:
            logger.error(f"导入公司-产品关系失败: {e}")
            return 0
    
    def import_product_product_rels(self, file_path, batch_size=10000):
        """
        导入产品-产品关系
        
        Args:
            file_path: 数据文件路径
            batch_size: 批次大小
            
        Returns:
            导入的关系数量
        """
        try:
            return self._import_relationships(
                rel_key="product_product", 
                data=file_path, 
                start_label="product", 
                end_label="product",
                rel_type="上游材料",
                batch_size=batch_size
            )
        except Exception as e:
            logger.error(f"导入产品-产品关系失败: {e}")
            return 0
    
    def _import_relationships(self, rel_key, data, start_label, end_label, rel_type, is_file=True, batch_size=10000):
        """
        导入关系通用方法
        
        Args:
            rel_key: 关系键名，用于导入状态记录
            data: 数据文件路径或数据列表
            start_label: 起始节点标签
            end_label: 结束节点标签
            rel_type: 关系类型
            is_file: 如果data是文件路径，则为True，否则为False
            batch_size: 批次大小
            
        Returns:
            导入的关系数量
        """
        try:
            if is_file:
                if not os.path.exists(data):
                    logger.warning(f"数据文件不存在: {data}")
                    return 0
                
                # 获取已导入数量
                imported = self.import_state.get(rel_key, 0)
                logger.info(f"{rel_key}关系已导入: {imported}")
                
                # 获取文件总行数
                total_lines = self._count_file_lines(data)
                if imported >= total_lines:
                    logger.info(f"{rel_key}关系已全部导入")
                    return 0
                
                # 读取JSON文件
                with open(data, 'r', encoding='utf-8') as f:
                    # 跳过已导入的行
                    for _ in range(imported):
                        next(f)
                    
                    # 批量导入
                    count = 0
                    batch = []
                    
                    for line in f:
                        try:
                            line_data = json.loads(line.strip())
                            batch.append(line_data)
                            count += 1
                            
                            if len(batch) >= batch_size:
                                self._create_relationships_batch(batch, start_label, end_label, rel_type)
                                imported += len(batch)
                                self.import_state[rel_key] = imported
                                batch = []
                                
                                # 保存导入状态
                                self.save_import_state()
                        except json.JSONDecodeError:
                            logger.error(f"JSON解析错误: {line}")
                            continue
                        except Exception as e:
                            logger.error(f"处理行时出错: {e}")
                            continue
                    
                    # 处理剩余批次
                    if batch:
                        self._create_relationships_batch(batch, start_label, end_label, rel_type)
                        imported += len(batch)
                        self.import_state[rel_key] = imported
                        
                        # 保存导入状态
                        self.save_import_state()
                    
                    logger.info(f"导入 {count} 条 {rel_key} 关系")
                    return count
            else:
                # 直接从数据列表导入
                self._create_relationships_batch(data, start_label, end_label, rel_type)
                logger.info(f"从列表导入 {len(data)} 条 {rel_key} 关系")
                return len(data)
        except Exception as e:
            logger.error(f"导入{rel_key}关系失败: {e}")
            return 0
    
    def _create_relationships_batch(self, rels_data, start_label, end_label, rel_type):
        """
        批量创建关系
        
        Args:
            rels_data: 关系数据列表
            start_label: 起始节点标签
            end_label: 结束节点标签
            rel_type: 关系类型
        """
        try:
            # 构建批量创建关系的Cypher查询
            query = f"""
            UNWIND $rels AS rel
            MATCH (start:{start_label} {{name: rel.start_name}})
            MATCH (end:{end_label} {{name: rel.end_name}})
            MERGE (start)-[r:{rel_type}]->(end)
            ON CREATE SET r += rel.properties
            """
            
            # 准备关系数据
            formatted_rels = []
            for rel in rels_data:
                start_name = rel.get("start_name", "")
                end_name = rel.get("end_name", "")
                
                # 跳过缺少起始或结束节点名称的关系
                if not start_name or not end_name:
                    continue
                
                # 提取关系属性
                properties = {k: v for k, v in rel.items() 
                             if k not in ["start_name", "end_name"]}
                
                formatted_rels.append({
                    "start_name": start_name,
                    "end_name": end_name,
                    "properties": properties
                })
            
            # 执行查询
            if formatted_rels:
                self.g.run(query, rels=formatted_rels)
        except Exception as e:
            logger.error(f"批量创建关系失败: {e}")
            raise 