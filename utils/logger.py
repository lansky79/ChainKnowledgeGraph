"""
日志工具，用于配置和管理应用日志
"""
import logging
import os
from datetime import datetime

def setup_logger(name="KnowledgeGraph", log_level=logging.INFO):
    """
    设置应用日志
    
    参数:
    - name: 日志记录器名称
    - log_level: 日志级别
    
    返回:
    - 配置好的日志记录器
    """
    # 确保日志目录存在
    os.makedirs("logs", exist_ok=True)
    
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # 如果已经有处理器，则不再添加
    if logger.handlers:
        return logger
    
    # 创建日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建文件处理器，使用日期作为文件名
    log_file = os.path.join("logs", f"{name}_{datetime.now().strftime('%Y%m%d')}.log")
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # 添加处理器到记录器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger 