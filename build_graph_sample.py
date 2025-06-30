#!/usr/bin/env python3
# coding: utf-8
# File: build_graph_sample.py
# 基于原始build_graph.py修改，用于快速构建小规模样本知识图谱

import os
import json
import time

from py2neo import Graph, Node

class MedicalGraph:
    def __init__(self):
        cur_dir = '/'.join(os.path.abspath(__file__).split('/')[:-1])
        self.company_path = os.path.join(cur_dir, 'data/company.json')
        self.industry_path = os.path.join(cur_dir, 'data/industry.json')
        self.product_path = os.path.join(cur_dir, 'data/product.json')
        self.company_industry_path = os.path.join(cur_dir, 'data/company_industry.json')
        self.company_product_path = os.path.join(cur_dir, 'data/company_product.json')
        self.industry_industry = os.path.join(cur_dir, 'data/industry_industry.json')
        self.product_product = os.path.join(cur_dir, 'data/product_product.json')
        
        # 连接Neo4j数据库
        try:
            print("尝试连接Neo4j数据库...")
            self.g = Graph(
                "bolt://127.0.0.1:7687",
                auth=("neo4j", "12345678"))
            print("Neo4j数据库连接成功！")
            
            # 清空数据库，确保从干净环境开始
            print("清空现有数据...")
            self.g.run("MATCH (n) DETACH DELETE n")
            print("数据库已清空，准备构建样本知识图谱...")
        except Exception as e:
            print(f"连接Neo4j数据库失败: {e}")
            raise

    '''建立节点'''
    def create_node(self, label, nodes):
        count = 0
        for node in nodes:
            bodies = []
            for k, v in node.items():
                # 处理特殊字符，避免Cypher语法错误
                if isinstance(v, str):
                    v = v.replace("'", "\\'")
                body = k + ":" + "'%s'"% v
                bodies.append(body)
            query_body = ', '.join(bodies)
            try:
                sql = "CREATE (:%s{%s})"%(label, query_body)
                self.g.run(sql)
                count += 1
                print(f"已创建 {label} 节点: {count}/{len(nodes)}")
            except Exception as e:
                print(f"创建节点失败: {e}")
        return count

    """加载数据并限制数量"""
    def load_data(self, filepath, limit=50):
        datas = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                count = 0
                for line in f:
                    if count >= limit:
                        break
                    line = line.strip()
                    if not line:
                        continue
                    obj = json.loads(line)
                    if not obj:
                        continue
                    datas.append(obj)
                    count += 1
            print(f"从 {filepath} 加载了 {len(datas)} 条数据")
        except Exception as e:
            print(f"加载数据失败 {filepath}: {e}")
        return datas

    '''创建知识图谱实体节点类型schema'''
    def create_graphnodes(self):
        # 限制每种类型只加载少量数据
        print("加载公司数据...")
        company = self.load_data(self.company_path, 20)
        print("加载产品数据...")
        product = self.load_data(self.product_path, 30)
        print("加载行业数据...")
        industry = self.load_data(self.industry_path, 20)
        
        print("开始创建公司节点...")
        company_count = self.create_node('company', company)
        print(f"创建了 {company_count} 个公司节点")
        
        print("开始创建产品节点...")
        product_count = self.create_node('product', product)
        print(f"创建了 {product_count} 个产品节点")
        
        print("开始创建行业节点...")
        industry_count = self.create_node('industry', industry)
        print(f"创建了 {industry_count} 个行业节点")
        return

    '''创建实体关系边'''
    def create_graphrels(self):
        print("加载公司-行业关系数据...")
        company_industry = self.load_data(self.company_industry_path, 30)
        print("加载公司-产品关系数据...")
        company_product = self.load_data(self.company_product_path, 30)
        print("加载产品-产品关系数据...")
        product_product = self.load_data(self.product_product, 30)
        print("加载行业-行业关系数据...")
        industry_industry = self.load_data(self.industry_industry, 20)
        
        print("创建公司-行业关系...")
        self.create_relationship('company', 'industry', company_industry, "company_name", "industry_name")
        
        print("创建行业-行业关系...")
        self.create_relationship('industry', 'industry', industry_industry, "from_industry", "to_industry")
        
        print("创建公司-产品关系...")
        self.create_relationship_attr('company', 'product', company_product, "company_name", "product_name")
        
        print("创建产品-产品关系...")
        self.create_relationship('product', 'product', product_product, "from_entity", "to_entity")

    '''创建实体关联边'''
    def create_relationship(self, start_node, end_node, edges, from_key, end_key):
        count = 0
        total = len(edges)
        for edge in edges:
            try:
                p = edge[from_key]
                q = edge[end_key]
                # 处理特殊字符
                if isinstance(p, str):
                    p = p.replace("'", "\\'")
                if isinstance(q, str):
                    q = q.replace("'", "\\'")
                rel = edge["rel"]
                query = "match(p:%s),(q:%s) where p.name='%s'and q.name='%s' create (p)-[rel:%s]->(q)" % (
                start_node, end_node, p, q, rel)
                self.g.run(query)
                count += 1
                print(f"创建关系: {start_node}-[{rel}]->{end_node}, 进度: {count}/{total}")
            except Exception as e:
                print(f"创建关系失败: {e}")
        return count

    '''创建实体关联边'''
    def create_relationship_attr(self, start_node, end_node, edges, from_key, end_key):
        count = 0
        total = len(edges)
        for edge in edges:
            try:
                p = edge[from_key]
                q = edge[end_key]
                # 处理特殊字符
                if isinstance(p, str):
                    p = p.replace("'", "\\'")
                if isinstance(q, str):
                    q = q.replace("'", "\\'")
                rel = edge["rel"]
                weight = edge["rel_weight"]
                query = "match(p:%s),(q:%s) where p.name='%s'and q.name='%s' create (p)-[rel:%s{%s:'%s'}]->(q)" % (
                    start_node, end_node, p, q, rel, "权重", weight)
                self.g.run(query)
                count += 1
                print(f"创建带权重关系: {start_node}-[{rel}:{weight}]->{end_node}, 进度: {count}/{total}")
            except Exception as e:
                print(f"创建关系失败: {e}")
        return count

    '''查询样本图谱统计信息'''
    def show_graph_stats(self):
        try:
            # 查询节点数量
            node_count = self.g.run("MATCH (n) RETURN count(n) as count").data()[0]['count']
            # 查询关系数量
            rel_count = self.g.run("MATCH ()-[r]->() RETURN count(r) as count").data()[0]['count']
            # 查询各类型节点数量
            company_count = self.g.run("MATCH (n:company) RETURN count(n) as count").data()[0]['count']
            product_count = self.g.run("MATCH (n:product) RETURN count(n) as count").data()[0]['count']
            industry_count = self.g.run("MATCH (n:industry) RETURN count(n) as count").data()[0]['count']
            
            print("\n=== 样本知识图谱统计信息 ===")
            print(f"总节点数: {node_count}")
            print(f"总关系数: {rel_count}")
            print(f"公司节点数: {company_count}")
            print(f"产品节点数: {product_count}")
            print(f"行业节点数: {industry_count}")
            print("=========================\n")
            
            # 提供一些示例查询语句
            print("您可以在Neo4j浏览器中使用以下查询语句查看图谱:")
            print("1. 查看所有节点: MATCH (n) RETURN n LIMIT 100")
            print("2. 查看特定公司及其关系: MATCH (c:company)-[r]->(n) RETURN c, r, n")
            print("3. 查看产品上下游关系: MATCH (p1:product)-[r]->(p2:product) RETURN p1, r, p2 LIMIT 50")
            print("4. 查看行业层级关系: MATCH (i1:industry)-[r]->(i2:industry) RETURN i1, r, i2")
        except Exception as e:
            print(f"查询统计信息失败: {e}")


if __name__ == '__main__':
    try:
        print("开始构建样本知识图谱...")
        handler = MedicalGraph()
        handler.create_graphnodes()
        handler.create_graphrels()
        handler.show_graph_stats()
        print("样本知识图谱构建完成！请访问 http://127.0.0.1:7474 查看效果")
    except Exception as e:
        print(f"构建知识图谱过程中发生错误: {e}") 