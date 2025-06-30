#!/usr/bin/env python3
# coding: utf-8
# 调试脚本，用于检查应用启动问题

import os
import sys
import json
import traceback
from build_graph import MedicalGraph

def load_config():
    """加载配置文件"""
    try:
        # 优先加载Windows专用配置
        if os.path.exists('config_windows.json'):
            print("加载Windows专用配置文件")
            with open('config_windows.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        # 如果没有Windows专用配置，加载通用配置
        elif os.path.exists('config.json'):
            print("加载通用配置文件")
            with open('config.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            print("配置文件不存在，使用默认配置")
            return {
                "neo4j": {
                    "uri": "bolt://127.0.0.1:7687",
                    "username": "neo4j",
                    "password": "12345678"
                }
            }
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        return {}

def check_neo4j_connection(config):
    """检查Neo4j连接"""
    try:
        from py2neo import Graph
        
        neo4j_config = config.get('neo4j', {})
        uri = neo4j_config.get('uri', 'bolt://127.0.0.1:7687')
        username = neo4j_config.get('username', 'neo4j')
        password = neo4j_config.get('password', '12345678')
        
        print(f"尝试连接Neo4j: {uri}")
        g = Graph(uri, user=username, password=password)
        
        # 执行简单查询测试连接
        result = g.run("RETURN 1 AS test").data()
        print(f"Neo4j连接成功，测试查询结果: {result}")
        return True
    except Exception as e:
        print(f"Neo4j连接失败: {str(e)}")
        print(traceback.format_exc())
        return False

def check_medical_graph():
    """检查MedicalGraph初始化"""
    try:
        print("尝试初始化MedicalGraph...")
        handler = MedicalGraph()
        
        if handler.g is None:
            print("MedicalGraph初始化成功，但Neo4j连接失败")
            return False
        else:
            print("MedicalGraph初始化成功，Neo4j连接正常")
            return True
    except Exception as e:
        print(f"MedicalGraph初始化失败: {str(e)}")
        print(traceback.format_exc())
        return False

def check_data_files():
    """检查数据文件"""
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    
    if not os.path.exists(data_dir):
        print(f"数据目录不存在: {data_dir}")
        return False
    
    expected_files = [
        'company.json', 
        'industry.json', 
        'product.json',
        'company_industry.json',
        'company_product.json',
        'industry_industry.json',
        'product_product.json'
    ]
    
    missing_files = []
    for file in expected_files:
        file_path = os.path.join(data_dir, file)
        if not os.path.exists(file_path):
            missing_files.append(file)
    
    if missing_files:
        print(f"缺少以下数据文件: {', '.join(missing_files)}")
        return False
    else:
        print("所有数据文件都存在")
        return True

def main():
    """主函数"""
    print("=" * 50)
    print("知识图谱应用诊断工具")
    print("=" * 50)
    print()
    
    # 检查Python版本
    print(f"Python版本: {sys.version}")
    print(f"运行平台: {sys.platform}")
    print()
    
    # 检查配置文件
    print("检查配置文件...")
    config = load_config()
    print()
    
    # 检查Neo4j连接
    print("检查Neo4j连接...")
    neo4j_ok = check_neo4j_connection(config)
    print()
    
    # 检查数据文件
    print("检查数据文件...")
    data_ok = check_data_files()
    print()
    
    # 检查MedicalGraph初始化
    print("检查MedicalGraph初始化...")
    mg_ok = check_medical_graph()
    print()
    
    # 总结
    print("=" * 50)
    print("诊断结果:")
    print(f"配置文件: {'正常' if config else '异常'}")
    print(f"Neo4j连接: {'正常' if neo4j_ok else '异常'}")
    print(f"数据文件: {'正常' if data_ok else '异常'}")
    print(f"MedicalGraph初始化: {'正常' if mg_ok else '异常'}")
    print()
    
    if neo4j_ok and data_ok and mg_ok:
        print("诊断结果: 所有检查都通过，应用应该可以正常启动")
    else:
        print("诊断结果: 存在问题，请解决上述问题后再尝试启动应用")
    
    print("=" * 50)

if __name__ == "__main__":
    main() 