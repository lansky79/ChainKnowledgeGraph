#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from src.neo4j_handler import Neo4jHandler, Config
import os
import json
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MedicalGraph")

class MedicalGraph:
    """医疗知识图谱构建类"""
    
    def __init__(self):
        """初始化图谱构建器"""
        self.handler = Neo4jHandler()
        self.g = self.handler.g
        
        # 直接使用handler的导入状态
        self.import_state = self.handler.import_state
        
        # 数据路径
        self.company_path = self.handler.company_path
        self.industry_path = self.handler.industry_path
        self.product_path = self.handler.product_path
        self.company_industry_path = self.handler.company_industry_path
        self.industry_industry = self.handler.industry_industry
        self.company_product_path = self.handler.company_product_path
        self.product_product = self.handler.product_product
    
    def create_graphnodes(self, batch_size=10000):
        """创建图谱节点"""
        return self.handler.create_graphnodes(batch_size)
    
    def create_graphrels(self, batch_size=10000):
        """创建图谱关系"""
        return self.handler.create_graphrels(batch_size)
    
    def import_nodes(self, label, data, is_file=True, batch_size=10000):
        """导入节点"""
        return self.handler.import_nodes(label, data, is_file, batch_size)

    def _import_relationships(self, rel_key, data, start_label, end_label, rel_type, is_file=True, batch_size=10000):
        """导入关系"""
        return self.handler._import_relationships(rel_key, data, start_label, end_label, rel_type, is_file, batch_size)

    def _count_file_lines(self, file_path):
        """计算文件行数"""
        return self.handler._count_file_lines(file_path)
    
    def reset_import_state(self):
        """重置导入状态"""
        self.handler.reset_import_state()
        self.import_state = self.handler.import_state
    
    def save_import_state(self):
        """保存导入状态"""
        self.handler.save_import_state()
        # 更新本地引用
        self.import_state = self.handler.import_state
        
    def run(self, query, **params):
        """执行Cypher查询"""
        if self.g:
            return self.g.run(query, **params)
        return None
        
    def run_query(self, query, **params):
        """执行Cypher查询（run方法的别名）"""
        return self.run(query, **params)
