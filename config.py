"""
配置文件，包含数据库连接和应用设置
"""
import os
import json

# 检测操作系统
import platform
IS_WINDOWS = platform.system() == "Windows"

# 加载配置文件
def load_config():
    config_file = None
    if IS_WINDOWS and os.path.exists('config_windows.json'):
        config_file = 'config_windows.json'
    elif os.path.exists('config.json'):
        config_file = 'config.json'
    
    if config_file:
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # 默认配置
    return {
        "neo4j": {
            "uri": "bolt://localhost:7687",
            "username": "neo4j",
            "password": "12345678"
        },
        "app": {
            "title": "知识图谱可视化工具",
            "batch_size_default": 10000
        }
    }

# 加载配置
CONFIG = load_config()
DB_CONFIG = CONFIG.get("neo4j", {})
APP_CONFIG = CONFIG.get("app", {}) 