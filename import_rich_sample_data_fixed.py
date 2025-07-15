import json
import os
import logging
from src.neo4j_handler import Neo4jHandler

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def main():
    # 连接Neo4j数据库
    handler = Neo4jHandler()
    
    # 创建知名公司节点
    companies = [
        {"name": "华为", "fullname": "华为技术有限公司", "description": "全球领先的通信设备制造商"},
        {"name": "小米", "fullname": "小米科技有限责任公司", "description": "智能手机和智能硬件制造商"},
        {"name": "腾讯", "fullname": "腾讯控股有限公司", "description": "中国领先的互联网和科技企业"},
        {"name": "阿里巴巴", "fullname": "阿里巴巴集团控股有限公司", "description": "全球最大的电子商务平台之一"},
        {"name": "百度", "fullname": "百度公司", "description": "中国领先的搜索引擎和AI企业"},
        {"name": "京东", "fullname": "京东集团", "description": "中国电子商务公司"},
        {"name": "字节跳动", "fullname": "北京字节跳动科技有限公司", "description": "开发了抖音、今日头条等产品的科技公司"},
        {"name": "美团", "fullname": "美团点评", "description": "中国领先的生活服务电子商务平台"},
        {"name": "网易", "fullname": "网易公司", "description": "中国互联网科技公司"},
        {"name": "联想", "fullname": "联想集团", "description": "全球个人电脑制造商"}
    ]
    
    # 创建行业节点
    industries = [
        {"name": "互联网", "code": "900000", "description": "提供互联网服务和产品的行业"},
        {"name": "通信", "code": "900001", "description": "提供通信设备和服务的行业"},
        {"name": "电子", "code": "900002", "description": "电子产品制造行业"},
        {"name": "软件", "code": "900003", "description": "软件开发和服务行业"},
        {"name": "人工智能", "code": "900004", "description": "人工智能技术研发和应用行业"},
        {"name": "电子商务", "code": "900005", "description": "通过互联网进行商品和服务交易的行业"},
        {"name": "云计算", "code": "900006", "description": "提供云服务和解决方案的行业"},
        {"name": "大数据", "code": "900007", "description": "数据处理和分析行业"}
    ]
    
    # 创建产品节点
    products = [
        {"name": "华为Mate系列", "type": "智能手机", "description": "华为高端旗舰智能手机系列"},
        {"name": "华为P系列", "type": "智能手机", "description": "华为摄影旗舰智能手机系列"},
        {"name": "华为nova系列", "type": "智能手机", "description": "华为年轻时尚智能手机系列"},
        {"name": "华为MateBook", "type": "笔记本电脑", "description": "华为笔记本电脑系列"},
        {"name": "华为智选生态", "type": "智能硬件", "description": "华为智能生态产品系列"},
        {"name": "鸿蒙OS", "type": "操作系统", "description": "华为自主研发的分布式操作系统"},
        {"name": "昇腾AI", "type": "AI芯片", "description": "华为自主研发的AI计算平台"},
        {"name": "华为云", "type": "云服务", "description": "华为提供的云计算服务"},
        
        {"name": "小米手机", "type": "智能手机", "description": "小米品牌智能手机"},
        {"name": "Redmi手机", "type": "智能手机", "description": "小米旗下Redmi品牌智能手机"},
        {"name": "MIUI", "type": "操作系统", "description": "小米基于Android开发的操作系统"},
        {"name": "小米电视", "type": "智能电视", "description": "小米品牌智能电视"},
        {"name": "小米生态链", "type": "智能硬件", "description": "小米生态系统中的智能硬件产品"},
        
        {"name": "微信", "type": "社交软件", "description": "腾讯开发的即时通讯软件"},
        {"name": "QQ", "type": "社交软件", "description": "腾讯开发的即时通讯软件"},
        {"name": "腾讯游戏", "type": "游戏", "description": "腾讯开发和代理的游戏产品"},
        {"name": "腾讯云", "type": "云服务", "description": "腾讯提供的云计算服务"},
        {"name": "腾讯视频", "type": "视频平台", "description": "腾讯旗下的在线视频平台"},
        
        {"name": "淘宝", "type": "电商平台", "description": "阿里巴巴旗下C2C电商平台"},
        {"name": "天猫", "type": "电商平台", "description": "阿里巴巴旗下B2C电商平台"},
        {"name": "阿里云", "type": "云服务", "description": "阿里巴巴提供的云计算服务"},
        {"name": "支付宝", "type": "支付服务", "description": "阿里巴巴旗下的支付平台"},
        {"name": "钉钉", "type": "办公软件", "description": "阿里巴巴旗下的企业协同办公平台"},
        
        {"name": "百度搜索", "type": "搜索引擎", "description": "百度提供的搜索引擎服务"},
        {"name": "百度地图", "type": "地图服务", "description": "百度提供的地图服务"},
        {"name": "百度智能云", "type": "云服务", "description": "百度提供的云计算服务"},
        {"name": "百度Apollo", "type": "自动驾驶", "description": "百度自动驾驶平台"},
        {"name": "百度文心大模型", "type": "AI模型", "description": "百度研发的大型语言模型"}
    ]
    
    # 公司与行业的关系
    company_industry_relations = [
        {"company": "华为", "industry": "通信", "relation_type": "belongs_to"},
        {"company": "华为", "industry": "电子", "relation_type": "belongs_to"},
        {"company": "华为", "industry": "人工智能", "relation_type": "belongs_to"},
        {"company": "华为", "industry": "云计算", "relation_type": "belongs_to"},
        
        {"company": "小米", "industry": "电子", "relation_type": "belongs_to"},
        {"company": "小米", "industry": "互联网", "relation_type": "belongs_to"},
        
        {"company": "腾讯", "industry": "互联网", "relation_type": "belongs_to"},
        {"company": "腾讯", "industry": "软件", "relation_type": "belongs_to"},
        {"company": "腾讯", "industry": "云计算", "relation_type": "belongs_to"},
        
        {"company": "阿里巴巴", "industry": "互联网", "relation_type": "belongs_to"},
        {"company": "阿里巴巴", "industry": "电子商务", "relation_type": "belongs_to"},
        {"company": "阿里巴巴", "industry": "云计算", "relation_type": "belongs_to"},
        
        {"company": "百度", "industry": "互联网", "relation_type": "belongs_to"},
        {"company": "百度", "industry": "人工智能", "relation_type": "belongs_to"},
        {"company": "百度", "industry": "大数据", "relation_type": "belongs_to"},
        
        {"company": "京东", "industry": "电子商务", "relation_type": "belongs_to"},
        {"company": "京东", "industry": "互联网", "relation_type": "belongs_to"},
        
        {"company": "字节跳动", "industry": "互联网", "relation_type": "belongs_to"},
        {"company": "字节跳动", "industry": "软件", "relation_type": "belongs_to"},
        
        {"company": "美团", "industry": "互联网", "relation_type": "belongs_to"},
        {"company": "美团", "industry": "电子商务", "relation_type": "belongs_to"},
        
        {"company": "网易", "industry": "互联网", "relation_type": "belongs_to"},
        {"company": "网易", "industry": "软件", "relation_type": "belongs_to"},
        
        {"company": "联想", "industry": "电子", "relation_type": "belongs_to"}
    ]
    
    # 公司与产品的关系
    company_product_relations = [
        {"company": "华为", "product": "华为Mate系列", "relation_type": "produces"},
        {"company": "华为", "product": "华为P系列", "relation_type": "produces"},
        {"company": "华为", "product": "华为nova系列", "relation_type": "produces"},
        {"company": "华为", "product": "华为MateBook", "relation_type": "produces"},
        {"company": "华为", "product": "华为智选生态", "relation_type": "produces"},
        {"company": "华为", "product": "鸿蒙OS", "relation_type": "produces"},
        {"company": "华为", "product": "昇腾AI", "relation_type": "produces"},
        {"company": "华为", "product": "华为云", "relation_type": "produces"},
        
        {"company": "小米", "product": "小米手机", "relation_type": "produces"},
        {"company": "小米", "product": "Redmi手机", "relation_type": "produces"},
        {"company": "小米", "product": "MIUI", "relation_type": "produces"},
        {"company": "小米", "product": "小米电视", "relation_type": "produces"},
        {"company": "小米", "product": "小米生态链", "relation_type": "produces"},
        
        {"company": "腾讯", "product": "微信", "relation_type": "produces"},
        {"company": "腾讯", "product": "QQ", "relation_type": "produces"},
        {"company": "腾讯", "product": "腾讯游戏", "relation_type": "produces"},
        {"company": "腾讯", "product": "腾讯云", "relation_type": "produces"},
        {"company": "腾讯", "product": "腾讯视频", "relation_type": "produces"},
        
        {"company": "阿里巴巴", "product": "淘宝", "relation_type": "produces"},
        {"company": "阿里巴巴", "product": "天猫", "relation_type": "produces"},
        {"company": "阿里巴巴", "product": "阿里云", "relation_type": "produces"},
        {"company": "阿里巴巴", "product": "支付宝", "relation_type": "produces"},
        {"company": "阿里巴巴", "product": "钉钉", "relation_type": "produces"},
        
        {"company": "百度", "product": "百度搜索", "relation_type": "produces"},
        {"company": "百度", "product": "百度地图", "relation_type": "produces"},
        {"company": "百度", "product": "百度智能云", "relation_type": "produces"},
        {"company": "百度", "product": "百度Apollo", "relation_type": "produces"},
        {"company": "百度", "product": "百度文心大模型", "relation_type": "produces"}
    ]
    
    # 行业间的关系
    industry_industry_relations = [
        {"source_industry": "互联网", "target_industry": "软件", "relation_type": "related_to"},
        {"source_industry": "互联网", "target_industry": "电子商务", "relation_type": "related_to"},
        {"source_industry": "通信", "target_industry": "电子", "relation_type": "related_to"},
        {"source_industry": "人工智能", "target_industry": "大数据", "relation_type": "related_to"},
        {"source_industry": "云计算", "target_industry": "大数据", "relation_type": "related_to"},
        {"source_industry": "云计算", "target_industry": "软件", "relation_type": "related_to"}
    ]
    
    # 产品间的关系
    product_product_relations = [
        {"source_product": "华为Mate系列", "target_product": "鸿蒙OS", "relation_type": "uses"},
        {"source_product": "华为P系列", "target_product": "鸿蒙OS", "relation_type": "uses"},
        {"source_product": "华为nova系列", "target_product": "鸿蒙OS", "relation_type": "uses"},
        {"source_product": "华为MateBook", "target_product": "华为智选生态", "relation_type": "compatible_with"},
        {"source_product": "小米手机", "target_product": "MIUI", "relation_type": "uses"},
        {"source_product": "Redmi手机", "target_product": "MIUI", "relation_type": "uses"},
        {"source_product": "小米电视", "target_product": "小米生态链", "relation_type": "part_of"},
        {"source_product": "微信", "target_product": "腾讯云", "relation_type": "runs_on"},
        {"source_product": "QQ", "target_product": "腾讯云", "relation_type": "runs_on"},
        {"source_product": "淘宝", "target_product": "阿里云", "relation_type": "runs_on"},
        {"source_product": "天猫", "target_product": "阿里云", "relation_type": "runs_on"},
        {"source_product": "支付宝", "target_product": "阿里云", "relation_type": "runs_on"},
        {"source_product": "百度搜索", "target_product": "百度智能云", "relation_type": "runs_on"},
        {"source_product": "百度地图", "target_product": "百度智能云", "relation_type": "runs_on"},
        {"source_product": "百度Apollo", "target_product": "百度文心大模型", "relation_type": "uses"}
    ]
    
    # 开始导入数据
    logger.info("开始导入丰富的示例数据...")
    
    # 创建公司节点
    for company in companies:
        handler.create_company_node(company["name"], company.get("fullname", ""), company.get("description", ""))
        logger.info(f"创建公司节点: {company[\"name\"]}")
    
    # 创建行业节点
    for industry in industries:
        handler.create_industry_node(industry["name"], industry.get("code", ""), industry.get("description", ""))
        logger.info(f"创建行业节点: {industry[\"name\"]}")
    
    # 创建产品节点
    for product in products:
        handler.create_product_node(product["name"], product.get("type", ""), product.get("description", ""))
        logger.info(f"创建产品节点: {product[\"name\"]}")
    
    # 创建公司与行业的关系
    for relation in company_industry_relations:
        handler.create_company_industry_relation(relation["company"], relation["industry"], relation["relation_type"])
        logger.info(f"创建公司-行业关系: {relation[\"company\"]} - {relation[\"industry\"]}")
    
    # 创建公司与产品的关系
    for relation in company_product_relations:
        handler.create_company_product_relation(relation["company"], relation["product"], relation["relation_type"])
        logger.info(f"创建公司-产品关系: {relation[\"company\"]} - {relation[\"product\"]}")
    
    # 创建行业间的关系
    for relation in industry_industry_relations:
        handler.create_industry_industry_relation(relation["source_industry"], relation["target_industry"], relation["relation_type"])
        logger.info(f"创建行业-行业关系: {relation[\"source_industry\"]} - {relation[\"target_industry\"]}")
    
    # 创建产品间的关系
    for relation in product_product_relations:
        handler.create_product_product_relation(relation["source_product"], relation["target_product"], relation["relation_type"])
        logger.info(f"创建产品-产品关系: {relation[\"source_product\"]} - {relation[\"target_product\"]}")
    
    logger.info("丰富的示例数据导入完成!")

if __name__ == "__main__":
    main()
