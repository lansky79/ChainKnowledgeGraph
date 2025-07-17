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
        },
        "search": {
            "max_results": 50,
            "similarity_threshold": 0.7,
            "cache_ttl": 300
        },
        "export": {
            "max_file_size": "50MB",
            "allowed_formats": ["png", "svg", "pdf", "json", "csv", "xlsx"],
            "export_dir": "static/exports"
        },
        "analytics": {
            "cache_ttl": 600,
            "max_nodes_for_analysis": 10000
        },
        "share": {
            "link_expiry_days": 7,
            "max_share_links": 100
        }
    }

# 加载配置
CONFIG = load_config()
DB_CONFIG = CONFIG.get("neo4j", {})
APP_CONFIG = CONFIG.get("app", {})
SEARCH_CONFIG = CONFIG.get("search", {})
EXPORT_CONFIG = CONFIG.get("export", {})
ANALYTICS_CONFIG = CONFIG.get("analytics", {})
SHARE_CONFIG = CONFIG.get("share", {}) 