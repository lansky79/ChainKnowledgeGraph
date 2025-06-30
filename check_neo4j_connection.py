#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Neo4j连接检查脚本
用于检查Neo4j数据库连接是否可用
"""

import sys
import json
import os

# 设置默认编码为UTF-8，防止中文问题
if sys.platform.startswith('win'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def load_config():
    """加载Neo4j连接配置"""
    try:
        # 尝试加载Windows专用配置
        if os.path.exists('config_windows.json'):
            with open('config_windows.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                if 'neo4j' in config:
                    return config['neo4j']
        
        # 尝试加载通用配置
        if os.path.exists('config.json'):
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                if 'neo4j' in config:
                    return config['neo4j']
        
        # 使用默认配置
        return {
            "uri": "bolt://127.0.0.1:7687",
            "username": "neo4j",
            "password": "12345678"
        }
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        return {
            "uri": "bolt://127.0.0.1:7687",
            "username": "neo4j",
            "password": "12345678"
        }

def check_neo4j_connection():
    """检查Neo4j连接状态"""
    config = load_config()
    
    try:
        from py2neo import Graph
        g = Graph(
            config["uri"],
            user=config["username"],
            password=config["password"]
        )
        
        # 尝试执行简单查询来验证连接
        g.run("RETURN 1").data()
        
        print("Neo4j连接成功!")
        print(f"连接地址: {config['uri']}")
        return True
    except Exception as e:
        print(f"Neo4j连接失败: {e}")
        print("请确保Neo4j数据库已启动并且连接参数正确:")
        print(f"  - 地址: {config['uri']}")
        print(f"  - 用户名: {config['username']}")
        print(f"  - 密码: {'*' * len(config['password'])}")
        return False

if __name__ == "__main__":
    success = check_neo4j_connection()
    sys.exit(0 if success else 1) 