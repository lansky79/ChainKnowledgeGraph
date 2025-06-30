#!/usr/bin/env python3
# coding: utf-8
# File: MedicalGraph.py
# Author: lhy<lhy_in_blcu@126.com,https://liuhuangyong.github.io>
# Date: 18-10-3

import os
import sys
import json
import time
import pickle
from tqdm import tqdm
from py2neo import Graph, Node, Relationship
from py2neo.bulk import create_nodes, merge_nodes, create_relationships

# 设置默认编码为UTF-8，防止中文问题
if sys.platform.startswith('win'):
    # 在Windows系统上特别设置
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 配置tqdm使用简单ASCII字符，避免PowerShell解析错误
tqdm.monitor_interval = 0
tqdm.ncols = 80
ASCII_BAR = '#'
ASCII_BLANK = '.'

class MedicalGraph:
    def __init__(self):
        # 使用os.path.dirname获取当前文件所在目录，避免斜杠问题
        cur_dir = os.path.dirname(os.path.abspath(__file__))
        
        # 使用os.path.join确保路径分隔符在不同操作系统下正确
        self.company_path = os.path.join(cur_dir, 'data', 'company.json')
        self.industry_path = os.path.join(cur_dir, 'data', 'industry.json')
        self.product_path = os.path.join(cur_dir, 'data', 'product.json')
        self.company_industry_path = os.path.join(cur_dir, 'data', 'company_industry.json')
        self.company_product_path = os.path.join(cur_dir, 'data', 'company_product.json')
        self.industry_industry = os.path.join(cur_dir, 'data', 'industry_industry.json')
        self.product_product = os.path.join(cur_dir, 'data', 'product_product.json')
        
        # 导入状态记录文件
        self.import_state_file = os.path.join(cur_dir, 'data', 'import_state.pkl')
        
        # 读取配置文件中的Neo4j连接信息
        neo4j_config = self._load_neo4j_config()
        
        # 使用Bolt协议连接Neo4j，更适合大批量数据导入
        try:
            self.g = Graph(
                neo4j_config["uri"],
                user=neo4j_config["username"],
                password=neo4j_config["password"])
            print(f"成功连接到Neo4j数据库: {neo4j_config['uri']}")
        except Exception as e:
            print(f"连接Neo4j数据库时出错: {e}")
            print(f"尝试连接的数据库: {neo4j_config['uri']}")
            print("请确保Neo4j数据库已启动并且可以访问")
            self.g = None
        
        # 设置批量导入的批次大小
        self.batch_size = 5000
        
        # 确保data目录存在
        data_dir = os.path.join(cur_dir, 'data')
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            print(f"创建数据目录: {data_dir}")
        
        # 初始化或加载导入状态
        self.import_state = self._load_import_state()
        
        # 数据文件总行数缓存
        self._file_total_lines = {}
        
        # 确保所有数据文件存在
        self.ensure_data_files_exist()
        print("已完成数据文件检查，准备就绪")

    '''创建知识图谱实体节点 - 主要接口'''
    def create_graphnodes(self, batch_size=None):
        """创建知识图谱节点的主要接口函数
        
        Args:
            batch_size: 每批处理的数据量，默认使用类实例中的batch_size
            
        Returns:
            int: 成功导入的节点数量
        """
        if batch_size:
            self.batch_size = batch_size
        
        try:
            return self.create_graphnodes_incremental(self.batch_size)
        except Exception as e:
            print(f"创建知识图谱节点失败: {e}")
            raise
        
    '''创建实体关系边 - 主要接口'''
    def create_graphrels(self, batch_size=None):
        """创建知识图谱关系的主要接口函数
        
        Args:
            batch_size: 每批处理的数据量，默认使用类实例中的batch_size
            
        Returns:
            int: 成功导入的关系数量
        """
        if batch_size:
            self.batch_size = batch_size
            
        try:
            return self.create_graphrels_incremental(self.batch_size)
        except Exception as e:
            print(f"创建知识图谱关系失败: {e}")
            raise

    def _load_import_state(self):
        """加载导入状态，如果不存在则初始化"""
        if os.path.exists(self.import_state_file):
            try:
                with open(self.import_state_file, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                print(f"加载导入状态失败: {e}，将创建新的导入状态")
        
        # 初始化导入状态
        return {
            'company': 0,
            'industry': 0,
            'product': 0,
            'company_industry': 0,
            'industry_industry': 0,
            'company_product': 0,
            'product_product': 0,
            'last_import_time': None
        }
    
    def _save_import_state(self):
        """保存当前导入状态"""
        self.import_state['last_import_time'] = time.time()
        try:
            with open(self.import_state_file, 'wb') as f:
                pickle.dump(self.import_state, f)
            print("导入状态已保存")
        except Exception as e:
            print(f"保存导入状态失败: {e}")
            
    def ensure_data_files_exist(self):
        """确保所有数据文件存在，如果不存在则创建示例数据"""
        data_files = {
            'company': self.company_path,
            'industry': self.industry_path,
            'product': self.product_path,
            'company_industry': self.company_industry_path,
            'company_product': self.company_product_path,
            'industry_industry': self.industry_industry,
            'product_product': self.product_product
        }
        
        # 检查并创建数据文件
        for file_type, file_path in data_files.items():
            if not os.path.exists(file_path):
                print(f"数据文件不存在: {file_path}，创建示例数据...")
                self._create_sample_data(file_type, file_path)
    
    def _create_sample_data(self, file_type, file_path):
        """为不同类型的数据文件创建示例数据"""
        sample_data = []
        
        # 根据文件类型创建不同的示例数据
        if file_type == 'company':
            sample_data = [
                {"name": "阿里巴巴", "description": "电子商务公司"},
                {"name": "腾讯", "description": "互联网服务提供商"},
                {"name": "百度", "description": "搜索引擎公司"},
                {"name": "华为", "description": "通信设备制造商"},
                {"name": "小米", "description": "智能手机制造商"}
            ]
        elif file_type == 'industry':
            sample_data = [
                {"name": "互联网", "description": "互联网行业"},
                {"name": "电子商务", "description": "电子商务行业"},
                {"name": "人工智能", "description": "人工智能行业"},
                {"name": "通信", "description": "通信行业"},
                {"name": "智能硬件", "description": "智能硬件行业"}
            ]
        elif file_type == 'product':
            sample_data = [
                {"name": "淘宝", "description": "电子商务平台"},
                {"name": "微信", "description": "社交通讯软件"},
                {"name": "百度搜索", "description": "搜索引擎"},
                {"name": "华为手机", "description": "智能手机"},
                {"name": "小米手机", "description": "智能手机"}
            ]
        elif file_type == 'company_industry':
            sample_data = [
                {"company_name": "阿里巴巴", "industry_name": "电子商务", "rel": "属于"},
                {"company_name": "腾讯", "industry_name": "互联网", "rel": "属于"},
                {"company_name": "百度", "industry_name": "互联网", "rel": "属于"},
                {"company_name": "华为", "industry_name": "通信", "rel": "属于"},
                {"company_name": "小米", "industry_name": "智能硬件", "rel": "属于"}
            ]
        elif file_type == 'industry_industry':
            sample_data = [
                {"from_industry": "互联网", "to_industry": "电子商务", "rel": "包含"},
                {"from_industry": "互联网", "to_industry": "人工智能", "rel": "相关"},
                {"from_industry": "电子商务", "to_industry": "互联网", "rel": "属于"},
                {"from_industry": "通信", "to_industry": "互联网", "rel": "相关"},
                {"from_industry": "智能硬件", "to_industry": "通信", "rel": "相关"}
            ]
        elif file_type == 'company_product':
            sample_data = [
                {"company_name": "阿里巴巴", "product_name": "淘宝", "rel": "拥有", "rel_weight": 1.0},
                {"company_name": "腾讯", "product_name": "微信", "rel": "拥有", "rel_weight": 1.0},
                {"company_name": "百度", "product_name": "百度搜索", "rel": "拥有", "rel_weight": 1.0},
                {"company_name": "华为", "product_name": "华为手机", "rel": "生产", "rel_weight": 0.9},
                {"company_name": "小米", "product_name": "小米手机", "rel": "生产", "rel_weight": 0.9}
            ]
        elif file_type == 'product_product':
            sample_data = [
                {"from_entity": "淘宝", "to_entity": "微信", "rel": "竞争"},
                {"from_entity": "微信", "to_entity": "百度搜索", "rel": "合作"},
                {"from_entity": "百度搜索", "to_entity": "淘宝", "rel": "合作"},
                {"from_entity": "华为手机", "to_entity": "小米手机", "rel": "竞争"},
                {"from_entity": "小米手机", "to_entity": "华为手机", "rel": "竞争"}
            ]
        
        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # 写入示例数据
        with open(file_path, 'w', encoding='utf-8') as f:
            for item in sample_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
                
        print(f"已创建示例数据文件: {file_path}，包含 {len(sample_data)} 条记录")
            
    def _count_file_lines(self, filepath):
        """计算文件总行数"""
        if filepath in self._file_total_lines:
            return self._file_total_lines[filepath]
        
        # 如果文件不存在，创建示例数据
        if not os.path.exists(filepath):
            file_type = os.path.basename(filepath).split('.')[0]
            self._create_sample_data(file_type, filepath)
            
        count = 0
        try:
            # 明确指定UTF-8编码
            with open(filepath, 'r', encoding='utf-8') as f:
                for _ in f:
                    count += 1
            self._file_total_lines[filepath] = count
            return count
        except UnicodeDecodeError as e:
            print(f"计算文件行数时出现编码错误: {e}")
            print(f"尝试使用不同编码重新读取文件: {filepath}")
            # 尝试不同的编码
            try:
                with open(filepath, 'r', encoding='gbk') as f:
                    for _ in f:
                        count += 1
                self._file_total_lines[filepath] = count
                return count
            except Exception as e2:
                print(f"使用GBK编码读取文件也失败: {e2}")
                return 0
        except Exception as e:
            print(f"计算文件行数时出错: {e}")
            return 0

    def _ensure_constraints(self):
        """确保数据库中有必要的约束和索引"""
        # 创建唯一性约束
        constraints = [
            "CREATE CONSTRAINT ON (c:company) ASSERT c.name IS UNIQUE IF NOT EXISTS",
            "CREATE CONSTRAINT ON (i:industry) ASSERT i.name IS UNIQUE IF NOT EXISTS",
            "CREATE CONSTRAINT ON (p:product) ASSERT p.name IS UNIQUE IF NOT EXISTS"
        ]
        
        for constraint in constraints:
            try:
                self.g.run(constraint)
            except Exception as e:
                print(f"创建约束失败: {e}")

    """加载数据"""
    def load_data(self, filepath):
        datas = []
        try:
            # 明确指定UTF-8编码
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    obj = json.loads(line)
                    if not obj:
                        continue
                    datas.append(obj)
            return datas
        except UnicodeDecodeError as e:
            print(f"加载数据时出现编码错误: {e}")
            print(f"尝试使用不同编码重新读取文件: {filepath}")
            # 尝试不同的编码
            try:
                with open(filepath, 'r', encoding='gbk') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        obj = json.loads(line)
                        if not obj:
                            continue
                        datas.append(obj)
                return datas
            except Exception as e2:
                print(f"使用GBK编码读取文件也失败: {e2}")
                return []
        except Exception as e:
            print(f"加载数据时出错: {e}")
            return []
    
    def load_data_incremental(self, filepath, offset, limit=None):
        """增量加载数据，从offset开始，最多加载limit条"""
        datas = []
        count = 0
        try:
            # 明确指定UTF-8编码
            with open(filepath, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    if i < offset:
                        continue
                        
                    line = line.strip()
                    if not line:
                        continue
                        
                    obj = json.loads(line)
                    if not obj:
                        continue
                        
                    datas.append(obj)
                    count += 1
                    
                    if limit and count >= limit:
                        break
            return datas
        except UnicodeDecodeError as e:
            print(f"增量加载数据时出现编码错误: {e}")
            print(f"尝试使用不同编码重新读取文件: {filepath}")
            # 尝试不同的编码
            try:
                with open(filepath, 'r', encoding='gbk') as f:
                    for i, line in enumerate(f):
                        if i < offset:
                            continue
                            
                        line = line.strip()
                        if not line:
                            continue
                            
                        obj = json.loads(line)
                        if not obj:
                            continue
                            
                        datas.append(obj)
                        count += 1
                        
                        if limit and count >= limit:
                            break
                return datas
            except Exception as e2:
                print(f"使用GBK编码读取文件也失败: {e2}")
                return []
        except Exception as e:
            print(f"增量加载数据时出错: {e}")
            return []

    '''建立节点 - 增量批量优化版'''
    def create_node_incremental(self, label, filepath, limit=None):
        # 获取已处理的偏移量
        offset = self.import_state[label.lower()]
        
        # 加载增量数据
        nodes = self.load_data_incremental(filepath, offset, limit)
        
        if not nodes:
            print(f"没有新的 {label} 数据需要导入")
            return 0
            
        total = len(nodes)
        batch = []
        count = 0
        
        print(f"开始增量创建 {label} 节点，从偏移量 {offset} 开始，共 {total} 个")
        
        # 确保有唯一性约束
        self._ensure_constraints()
        
        # 使用安全的方式处理节点，不使用tqdm
        for node in nodes:
            batch.append(node)
            count += 1
            
            # 当批次达到指定大小或处理到最后一个节点时执行批量导入
            if len(batch) >= self.batch_size or count == total:
                try:
                    # 使用merge_nodes而不是create_nodes，避免重复
                    merge_nodes(self.g.auto(), batch, "name", labels={label})
                    batch = []
                    # 打印进度
                    if count % 1000 == 0 or count == total:
                        print(f"已处理 {count}/{total} 个 {label} 节点")
                except Exception as e:
                    print(f"批量创建节点出错: {e}")
        
        # 更新导入状态
        self.import_state[label.lower()] += total
        self._save_import_state()
                    
        return count

    '''创建实体关系边 - 增量批量优化版'''
    def create_relationship_incremental(self, start_node, end_node, filepath, from_key, end_key, rel_key="rel", limit=None):
        # 获取关系类型的导入状态键
        rel_type = f"{start_node.lower()}_{end_node.lower()}"
        if rel_type not in self.import_state:
            rel_type = f"{end_node.lower()}_{end_node.lower()}"
        
        # 获取已处理的偏移量
        offset = self.import_state[rel_type]
        
        # 加载增量数据
        edges = self.load_data_incremental(filepath, offset, limit)
        
        if not edges:
            print(f"没有新的 {start_node}->{end_node} 关系数据需要导入")
            return 0
            
        count = 0
        total = len(edges)
        
        print(f"开始增量创建关系: {start_node}->{end_node}，从偏移量 {offset} 开始，共 {total} 条")
        
        # 按关系类型分组处理
        rel_groups = {}
        
        # 首先将边按关系类型分组
        for edge in edges:  # 移除tqdm
            try:
                p = edge[from_key]
                q = edge[end_key]
                rel = edge[rel_key]
                
                if rel not in rel_groups:
                    rel_groups[rel] = []
                
                rel_groups[rel].append((p, q))
                count += 1
                
                # 打印进度
                if count % 1000 == 0 or count == total:
                    print(f"已分组 {count}/{total} 条 {start_node}->{end_node} 关系")
            except Exception as e:
                print(f"处理关系分组时出错: {e}")
        
        # 然后按关系类型批量处理
        for rel, pairs in rel_groups.items():
            batch_data = []
            batch_count = 0
            batch_total = len(pairs)
            
            for p, q in pairs:  # 移除tqdm
                batch_data.append((p, q))
                batch_count += 1
                
                # 当批次达到指定大小或处理到最后一个关系时执行批量导入
                if len(batch_data) >= self.batch_size or batch_count == batch_total:
                    try:
                        query = f"""
                        UNWIND $data AS row
                        MATCH (p:{start_node} {{name: row[0]}}), (q:{end_node} {{name: row[1]}})
                        MERGE (p)-[:{rel}]->(q)
                        """
                        self.g.run(query, data=batch_data)
                        batch_data = []
                        
                        # 打印进度
                        if batch_count % 1000 == 0 or batch_count == batch_total:
                            print(f"已创建 {batch_count}/{batch_total} 条 {rel} 关系")
                    except Exception as e:
                        print(f"批量创建关系时出错: {e}")
        
        # 更新导入状态
        self.import_state[rel_type] += total
        self._save_import_state()
                
        return count

    '''创建带属性的实体关系边 - 增量批量优化版'''
    def create_relationship_attr_incremental(self, start_node, end_node, filepath, from_key, end_key, rel_key="rel", attr_key="rel_weight", attr_name="权重", limit=None):
        # 获取关系类型的导入状态键
        rel_type = f"{start_node.lower()}_{end_node.lower()}"
        
        # 获取已处理的偏移量
        offset = self.import_state[rel_type]
        
        # 加载增量数据
        edges = self.load_data_incremental(filepath, offset, limit)
        
        if not edges:
            print(f"没有新的 {start_node}->{end_node} 带属性关系数据需要导入")
            return 0
            
        count = 0
        total = len(edges)
        
        print(f"开始增量创建带属性关系: {start_node}->{end_node}，从偏移量 {offset} 开始，共 {total} 条")
        
        # 按关系类型分组处理
        rel_groups = {}
        
        # 首先将边按关系类型分组
        for edge in edges:  # 移除tqdm
            try:
                p = edge[from_key]
                q = edge[end_key]
                rel = edge[rel_key]
                weight = edge[attr_key]
                
                if rel not in rel_groups:
                    rel_groups[rel] = []
                
                rel_groups[rel].append((p, q, weight))
                count += 1
                
                # 打印进度
                if count % 1000 == 0 or count == total:
                    print(f"已分组 {count}/{total} 条带属性关系")
            except Exception as e:
                print(f"处理带属性关系分组时出错: {e}")
        
        # 然后按关系类型批量处理
        for rel, triples in rel_groups.items():
            batch_data = []
            batch_count = 0
            batch_total = len(triples)
            
            for p, q, weight in triples:  # 移除tqdm
                batch_data.append((p, q, weight))
                batch_count += 1
                
                # 当批次达到指定大小或处理到最后一个关系时执行批量导入
                if len(batch_data) >= self.batch_size or batch_count == batch_total:
                    try:
                        query = f"""
                        UNWIND $data AS row
                        MATCH (p:{start_node} {{name: row[0]}}), (q:{end_node} {{name: row[1]}})
                        MERGE (p)-[r:{rel}]->(q)
                        SET r.{attr_name} = row[2]
                        """
                        self.g.run(query, data=batch_data)
                        batch_data = []
                        
                        # 打印进度
                        if batch_count % 1000 == 0 or batch_count == batch_total:
                            print(f"已创建 {batch_count}/{batch_total} 条带属性 {rel} 关系")
                    except Exception as e:
                        print(f"批量创建带属性关系时出错: {e}")
        
        # 更新导入状态
        self.import_state[rel_type] += total
        self._save_import_state()
                
        return count

    '''增量创建知识图谱实体节点'''
    def create_graphnodes_incremental(self, limit=None):
        total_nodes = 0
        print("开始增量创建实体节点...")
        
        total_nodes += self.create_node_incremental('company', self.company_path, limit)
        total_nodes += self.create_node_incremental('industry', self.industry_path, limit)
        total_nodes += self.create_node_incremental('product', self.product_path, limit)
        
        print(f"实体节点增量创建完成，共创建 {total_nodes} 个新节点")
        return total_nodes

    '''增量创建实体关系边'''
    def create_graphrels_incremental(self, limit=None):
        total_rels = 0
        print("开始增量创建实体关系...")
        
        total_rels += self.create_relationship_incremental(
            'company', 'industry', 
            self.company_industry_path, 
            "company_name", "industry_name", 
            limit=limit
        )
        
        total_rels += self.create_relationship_incremental(
            'industry', 'industry', 
            self.industry_industry, 
            "from_industry", "to_industry", 
            limit=limit
        )
        
        total_rels += self.create_relationship_attr_incremental(
            'company', 'product', 
            self.company_product_path, 
            "company_name", "product_name", 
            limit=limit
        )
        
        total_rels += self.create_relationship_incremental(
            'product', 'product', 
            self.product_product, 
            "from_entity", "to_entity", 
            limit=limit
        )
        
        print(f"实体关系增量创建完成，共创建 {total_rels} 条新关系")
        return total_rels
    
    '''增量导入指定数量的数据并记录时间'''
    def incremental_import(self, limit=10000):
        print(f"开始增量导入数据，批次大小: {limit}...")
        print(f"当前导入状态: {self.import_state}")
        
        # 记录开始时间
        start_time = time.time()
        
        # 创建节点
        node_start_time = time.time()
        nodes_count = self.create_graphnodes_incremental(limit)
        node_end_time = time.time()
        node_duration = node_end_time - node_start_time
        
        # 创建关系
        rel_start_time = time.time()
        rels_count = self.create_graphrels_incremental(limit)
        rel_end_time = time.time()
        rel_duration = rel_end_time - rel_start_time
        
        # 计算总时间
        total_duration = time.time() - start_time
        
        # 打印结果
        print("\n" + "="*50)
        print("增量导入结果统计")
        print("="*50)
        print(f"总导入时间: {total_duration:.2f} 秒 ({total_duration/60:.2f} 分钟)")
        print(f"节点导入时间: {node_duration:.2f} 秒 ({node_duration/60:.2f} 分钟)")
        print(f"关系导入时间: {rel_duration:.2f} 秒 ({rel_duration/60:.2f} 分钟)")
        print(f"导入节点总数: {nodes_count}")
        print(f"导入关系总数: {rels_count}")
        
        if nodes_count > 0:
            print(f"节点导入速度: {nodes_count/node_duration:.2f} 个/秒")
        if rels_count > 0:
            print(f"关系导入速度: {rels_count/rel_duration:.2f} 个/秒")
            
        print(f"当前导入状态: {self.import_state}")
        print("="*50)
        
        return {
            "total_time": total_duration,
            "nodes_time": node_duration,
            "rels_time": rel_duration,
            "nodes_count": nodes_count,
            "rels_count": rels_count
        }
    
    '''显示导入状态信息'''
    def show_import_status(self):
        print("\n" + "="*50)
        print("当前导入状态")
        print("="*50)
        
        for key, value in self.import_state.items():
            if key == 'last_import_time' and value:
                import datetime
                time_str = datetime.datetime.fromtimestamp(value).strftime('%Y-%m-%d %H:%M:%S')
                print(f"{key}: {time_str}")
            else:
                print(f"{key}: {value}")
                
        print("="*50)
    
    '''显示详细导入进度'''
    def show_detailed_import_progress(self):
        print("\n" + "="*50)
        print("详细导入进度")
        print("="*50)
        
        # 节点数据
        node_files = {
            'company': self.company_path,
            'industry': self.industry_path,
            'product': self.product_path
        }
        
        # 关系数据
        rel_files = {
            'company_industry': self.company_industry_path,
            'industry_industry': self.industry_industry,
            'company_product': self.company_product_path,
            'product_product': self.product_product
        }
        
        # 显示节点导入进度
        print("节点导入进度:")
        total_nodes = 0
        imported_nodes = 0
        for node_type, file_path in node_files.items():
            total = self._count_file_lines(file_path)
            imported = self.import_state[node_type]
            progress = (imported / total * 100) if total > 0 else 0
            remaining = total - imported
            
            total_nodes += total
            imported_nodes += imported
            
            print(f"  {node_type.ljust(10)}: {imported}/{total} ({progress:.2f}%) - 剩余: {remaining}")
        
        # 显示关系导入进度
        print("\n关系导入进度:")
        total_rels = 0
        imported_rels = 0
        for rel_type, file_path in rel_files.items():
            total = self._count_file_lines(file_path)
            imported = self.import_state[rel_type]
            progress = (imported / total * 100) if total > 0 else 0
            remaining = total - imported
            
            total_rels += total
            imported_rels += imported
            
            print(f"  {rel_type.ljust(15)}: {imported}/{total} ({progress:.2f}%) - 剩余: {remaining}")
        
        # 显示总体进度
        total_all = total_nodes + total_rels
        imported_all = imported_nodes + imported_rels
        overall_progress = (imported_all / total_all * 100) if total_all > 0 else 0
        remaining_all = total_all - imported_all
        
        print("\n总体进度:")
        print(f"  总数据量: {total_all}")
        print(f"  已导入: {imported_all} ({overall_progress:.2f}%)")
        print(f"  剩余: {remaining_all}")
        
        # 显示最后导入时间
        if self.import_state['last_import_time']:
            import datetime
            time_str = datetime.datetime.fromtimestamp(self.import_state['last_import_time']).strftime('%Y-%m-%d %H:%M:%S')
            print(f"\n最后导入时间: {time_str}")
            
        print("="*50)
    
    '''重置导入状态'''
    def reset_import_state(self):
        if os.path.exists(self.import_state_file):
            os.remove(self.import_state_file)
        self.import_state = self._load_import_state()
        print("导入状态已重置")

    def _load_neo4j_config(self):
        """从配置文件加载Neo4j连接参数"""
        # 默认连接参数
        default_config = {
            "uri": "bolt://127.0.0.1:7687",
            "username": "neo4j",
            "password": "12345678"
        }
        
        try:
            # 尝试加载Windows专用配置
            config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config_windows.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if 'neo4j' in config:
                        return config['neo4j']
            
            # 尝试加载通用配置
            config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if 'neo4j' in config:
                        return config['neo4j']
                    
            print("未找到Neo4j配置，使用默认连接参数")
            return default_config
            
        except Exception as e:
            print(f"加载Neo4j配置出错: {e}，使用默认连接参数")
            return default_config


if __name__ == '__main__':
    handler = MedicalGraph()
    
    # 显示当前导入状态
    handler.show_import_status()
    
    # 显示详细导入进度
    handler.show_detailed_import_progress()
    
    # 增量导入10000条数据
    # handler.incremental_import(10000)
    
    # 如果需要重置导入状态（慎用）
    # handler.reset_import_state()
