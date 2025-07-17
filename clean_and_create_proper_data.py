#!/usr/bin/env python3
# coding: utf-8
# File: clean_and_create_proper_data.py
# 清理不合适的产品数据，创建合理的公司-产品关系数据

from utils.db_connector import Neo4jConnector
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def clean_and_create_proper_data():
    """清理不合适的数据并创建合理的公司-产品关系"""
    
    # 连接数据库
    db = Neo4jConnector()
    
    try:
        print("开始清理不合适的产品数据...")
        
        # 1. 删除华为手机具体型号数据
        print("删除华为手机具体型号数据...")
        delete_huawei_models = """
        MATCH (p:product) 
        WHERE p.name =~ '华为(Mate|P|nova)\\s*\\d+.*' 
        DETACH DELETE p
        """
        result = db.query(delete_huawei_models)
        print(f"删除华为手机型号数据完成")
        
        # 2. 删除其他不合适的具体型号产品
        print("删除其他品牌的具体型号数据...")
        delete_other_models = """
        MATCH (p:product) 
        WHERE p.name =~ '.*(\\d+号|型号|版本\\d+).*' 
        DETACH DELETE p
        """
        result = db.query(delete_other_models)
        print(f"删除其他型号数据完成")
        
        # 3. 创建合理的产品数据
        print("创建合理的产品数据...")
        
        # 定义合理的产品数据
        products_data = [
            # 华为产品
            {"name": "智能手机", "category": "消费电子", "description": "智能手机产品"},
            {"name": "5G基站", "category": "通信设备", "description": "5G网络基础设施"},
            {"name": "交换机", "category": "网络设备", "description": "企业级网络交换设备"},
            {"name": "路由器", "category": "网络设备", "description": "网络路由设备"},
            {"name": "服务器", "category": "计算设备", "description": "企业级服务器"},
            {"name": "笔记本电脑", "category": "消费电子", "description": "便携式计算机"},
            {"name": "平板电脑", "category": "消费电子", "description": "平板计算设备"},
            {"name": "智能手表", "category": "可穿戴设备", "description": "智能穿戴设备"},
            {"name": "鸿蒙操作系统", "category": "软件系统", "description": "分布式操作系统"},
            {"name": "AI芯片", "category": "半导体", "description": "人工智能处理芯片"},
            
            # 阿里巴巴产品
            {"name": "淘宝", "category": "电商平台", "description": "在线购物平台"},
            {"name": "天猫", "category": "电商平台", "description": "品牌商城平台"},
            {"name": "支付宝", "category": "金融服务", "description": "移动支付平台"},
            {"name": "阿里云", "category": "云计算", "description": "云计算服务平台"},
            {"name": "钉钉", "category": "企业服务", "description": "企业协作平台"},
            {"name": "菜鸟物流", "category": "物流服务", "description": "智能物流网络"},
            
            # 腾讯产品
            {"name": "微信", "category": "社交软件", "description": "即时通讯软件"},
            {"name": "QQ", "category": "社交软件", "description": "即时通讯软件"},
            {"name": "微信支付", "category": "金融服务", "description": "移动支付服务"},
            {"name": "腾讯云", "category": "云计算", "description": "云计算服务"},
            {"name": "王者荣耀", "category": "游戏", "description": "手机游戏"},
            {"name": "腾讯视频", "category": "视频服务", "description": "在线视频平台"},
            
            # 百度产品
            {"name": "百度搜索", "category": "搜索引擎", "description": "网络搜索服务"},
            {"name": "百度地图", "category": "地图服务", "description": "地图导航服务"},
            {"name": "百度云", "category": "云计算", "description": "云存储服务"},
            {"name": "Apollo", "category": "自动驾驶", "description": "自动驾驶平台"},
            {"name": "小度音箱", "category": "智能硬件", "description": "智能语音助手"},
            {"name": "百度AI", "category": "人工智能", "description": "AI技术平台"},
            
            # 小米产品
            {"name": "小米手机", "category": "消费电子", "description": "智能手机"},
            {"name": "小米电视", "category": "消费电子", "description": "智能电视"},
            {"name": "小米路由器", "category": "网络设备", "description": "家用路由器"},
            {"name": "小米手环", "category": "可穿戴设备", "description": "智能手环"},
            {"name": "小米音箱", "category": "智能硬件", "description": "智能音响"},
            {"name": "MIUI", "category": "软件系统", "description": "手机操作系统"},
            
            # 字节跳动产品
            {"name": "抖音", "category": "短视频", "description": "短视频社交平台"},
            {"name": "今日头条", "category": "资讯平台", "description": "个性化资讯推荐"},
            {"name": "TikTok", "category": "短视频", "description": "国际版短视频平台"},
            {"name": "飞书", "category": "企业服务", "description": "企业协作平台"},
            {"name": "剪映", "category": "视频编辑", "description": "视频编辑软件"},
            
            # 美团产品
            {"name": "美团外卖", "category": "生活服务", "description": "外卖配送平台"},
            {"name": "美团打车", "category": "出行服务", "description": "网约车服务"},
            {"name": "美团酒店", "category": "生活服务", "description": "酒店预订服务"},
            {"name": "美团买菜", "category": "生活服务", "description": "生鲜配送服务"},
            
            # 滴滴产品
            {"name": "滴滴出行", "category": "出行服务", "description": "网约车平台"},
            {"name": "滴滴货运", "category": "物流服务", "description": "货运配送服务"},
            {"name": "滴滴金融", "category": "金融服务", "description": "金融服务平台"},
            
            # 京东产品
            {"name": "京东商城", "category": "电商平台", "description": "综合电商平台"},
            {"name": "京东物流", "category": "物流服务", "description": "物流配送服务"},
            {"name": "京东金融", "category": "金融服务", "description": "金融科技服务"},
            {"name": "京东云", "category": "云计算", "description": "云计算服务"},
            
            # 网易产品
            {"name": "网易邮箱", "category": "通讯服务", "description": "电子邮件服务"},
            {"name": "网易云音乐", "category": "音乐服务", "description": "在线音乐平台"},
            {"name": "网易游戏", "category": "游戏", "description": "游戏开发运营"},
            {"name": "网易有道", "category": "教育服务", "description": "在线教育平台"},
            
            # OPPO产品
            {"name": "OPPO手机", "category": "消费电子", "description": "智能手机"},
            {"name": "OPPO手表", "category": "可穿戴设备", "description": "智能手表"},
            {"name": "OPPO耳机", "category": "消费电子", "description": "无线耳机"},
            {"name": "ColorOS", "category": "软件系统", "description": "手机操作系统"},
            
            # vivo产品
            {"name": "vivo手机", "category": "消费电子", "description": "智能手机"},
            {"name": "vivo手表", "category": "可穿戴设备", "description": "智能手表"},
            {"name": "vivo耳机", "category": "消费电子", "description": "无线耳机"},
            {"name": "OriginOS", "category": "软件系统", "description": "手机操作系统"},
        ]
        
        # 批量创建产品节点
        create_products_query = """
        UNWIND $products AS product
        MERGE (p:product {name: product.name})
        ON CREATE SET 
            p.category = product.category,
            p.description = product.description
        ON MATCH SET 
            p.category = product.category,
            p.description = product.description
        """
        db.query(create_products_query, {"products": products_data})
        print(f"创建了 {len(products_data)} 个产品节点")
        
        # 4. 创建公司节点（如果不存在）
        print("创建公司节点...")
        
        companies_data = [
            {"name": "华为", "description": "全球领先的ICT基础设施和智能终端提供商"},
            {"name": "阿里巴巴", "description": "中国最大的电子商务公司"},
            {"name": "腾讯", "description": "中国领先的互联网增值服务提供商"},
            {"name": "百度", "description": "全球最大的中文搜索引擎"},
            {"name": "小米", "description": "以手机、智能硬件和IoT平台为核心的互联网公司"},
            {"name": "字节跳动", "description": "全球化的移动互联网平台"},
            {"name": "美团", "description": "中国领先的生活服务电子商务平台"},
            {"name": "滴滴", "description": "全球领先的移动出行平台"},
            {"name": "京东", "description": "中国领先的技术驱动的电商和零售基础设施服务商"},
            {"name": "网易", "description": "中国领先的互联网技术公司"},
            {"name": "OPPO", "description": "全球领先的智能终端制造商和移动互联网服务提供商"},
            {"name": "vivo", "description": "专注于智能手机领域的品牌"},
        ]
        
        # 批量创建公司节点
        create_companies_query = """
        UNWIND $companies AS company
        MERGE (c:company {name: company.name})
        ON CREATE SET 
            c.description = company.description
        ON MATCH SET 
            c.description = company.description
        """
        db.query(create_companies_query, {"companies": companies_data})
        print(f"创建了 {len(companies_data)} 个公司节点")
        
        # 5. 创建合理的公司-产品关系
        print("创建公司-产品关系...")
        
        company_product_relations = [
            # 华为
            {"company": "华为", "product": "智能手机", "relation": "主营产品"},
            {"company": "华为", "product": "5G基站", "relation": "主营产品"},
            {"company": "华为", "product": "交换机", "relation": "主营产品"},
            {"company": "华为", "product": "路由器", "relation": "主营产品"},
            {"company": "华为", "product": "服务器", "relation": "主营产品"},
            {"company": "华为", "product": "笔记本电脑", "relation": "主营产品"},
            {"company": "华为", "product": "平板电脑", "relation": "主营产品"},
            {"company": "华为", "product": "智能手表", "relation": "主营产品"},
            {"company": "华为", "product": "鸿蒙操作系统", "relation": "主营产品"},
            {"company": "华为", "product": "AI芯片", "relation": "主营产品"},
            
            # 阿里巴巴
            {"company": "阿里巴巴", "product": "淘宝", "relation": "主营产品"},
            {"company": "阿里巴巴", "product": "天猫", "relation": "主营产品"},
            {"company": "阿里巴巴", "product": "支付宝", "relation": "主营产品"},
            {"company": "阿里巴巴", "product": "阿里云", "relation": "主营产品"},
            {"company": "阿里巴巴", "product": "钉钉", "relation": "主营产品"},
            {"company": "阿里巴巴", "product": "菜鸟物流", "relation": "主营产品"},
            
            # 腾讯
            {"company": "腾讯", "product": "微信", "relation": "主营产品"},
            {"company": "腾讯", "product": "QQ", "relation": "主营产品"},
            {"company": "腾讯", "product": "微信支付", "relation": "主营产品"},
            {"company": "腾讯", "product": "腾讯云", "relation": "主营产品"},
            {"company": "腾讯", "product": "王者荣耀", "relation": "主营产品"},
            {"company": "腾讯", "product": "腾讯视频", "relation": "主营产品"},
            
            # 百度
            {"company": "百度", "product": "百度搜索", "relation": "主营产品"},
            {"company": "百度", "product": "百度地图", "relation": "主营产品"},
            {"company": "百度", "product": "百度云", "relation": "主营产品"},
            {"company": "百度", "product": "Apollo", "relation": "主营产品"},
            {"company": "百度", "product": "小度音箱", "relation": "主营产品"},
            {"company": "百度", "product": "百度AI", "relation": "主营产品"},
            
            # 小米
            {"company": "小米", "product": "小米手机", "relation": "主营产品"},
            {"company": "小米", "product": "小米电视", "relation": "主营产品"},
            {"company": "小米", "product": "小米路由器", "relation": "主营产品"},
            {"company": "小米", "product": "小米手环", "relation": "主营产品"},
            {"company": "小米", "product": "小米音箱", "relation": "主营产品"},
            {"company": "小米", "product": "MIUI", "relation": "主营产品"},
            
            # 字节跳动
            {"company": "字节跳动", "product": "抖音", "relation": "主营产品"},
            {"company": "字节跳动", "product": "今日头条", "relation": "主营产品"},
            {"company": "字节跳动", "product": "TikTok", "relation": "主营产品"},
            {"company": "字节跳动", "product": "飞书", "relation": "主营产品"},
            {"company": "字节跳动", "product": "剪映", "relation": "主营产品"},
            
            # 美团
            {"company": "美团", "product": "美团外卖", "relation": "主营产品"},
            {"company": "美团", "product": "美团打车", "relation": "主营产品"},
            {"company": "美团", "product": "美团酒店", "relation": "主营产品"},
            {"company": "美团", "product": "美团买菜", "relation": "主营产品"},
            
            # 滴滴
            {"company": "滴滴", "product": "滴滴出行", "relation": "主营产品"},
            {"company": "滴滴", "product": "滴滴货运", "relation": "主营产品"},
            {"company": "滴滴", "product": "滴滴金融", "relation": "主营产品"},
            
            # 京东
            {"company": "京东", "product": "京东商城", "relation": "主营产品"},
            {"company": "京东", "product": "京东物流", "relation": "主营产品"},
            {"company": "京东", "product": "京东金融", "relation": "主营产品"},
            {"company": "京东", "product": "京东云", "relation": "主营产品"},
            
            # 网易
            {"company": "网易", "product": "网易邮箱", "relation": "主营产品"},
            {"company": "网易", "product": "网易云音乐", "relation": "主营产品"},
            {"company": "网易", "product": "网易游戏", "relation": "主营产品"},
            {"company": "网易", "product": "网易有道", "relation": "主营产品"},
            
            # OPPO
            {"company": "OPPO", "product": "OPPO手机", "relation": "主营产品"},
            {"company": "OPPO", "product": "OPPO手表", "relation": "主营产品"},
            {"company": "OPPO", "product": "OPPO耳机", "relation": "主营产品"},
            {"company": "OPPO", "product": "ColorOS", "relation": "主营产品"},
            
            # vivo
            {"company": "vivo", "product": "vivo手机", "relation": "主营产品"},
            {"company": "vivo", "product": "vivo手表", "relation": "主营产品"},
            {"company": "vivo", "product": "vivo耳机", "relation": "主营产品"},
            {"company": "vivo", "product": "OriginOS", "relation": "主营产品"},
        ]
        
        # 创建公司-产品关系
        create_relations_query = """
        UNWIND $relations AS rel
        MATCH (c:company {name: rel.company})
        MATCH (p:product {name: rel.product})
        MERGE (c)-[r:主营产品]->(p)
        """
        db.query(create_relations_query, {"relations": company_product_relations})
        print(f"创建了 {len(company_product_relations)} 个公司-产品关系")
        
        # 5. 验证数据
        print("\n验证数据...")
        
        # 查询华为的产品
        huawei_products = db.query("""
        MATCH (c:company {name: '华为'})-[:主营产品]->(p:product)
        RETURN p.name as product_name, p.category as category
        ORDER BY p.name
        """)
        
        print(f"华为的产品 ({len(huawei_products)}个):")
        for product in huawei_products:
            print(f"  - {product['product_name']} ({product['category']})")
        
        # 查询所有公司的产品数量
        company_stats = db.query("""
        MATCH (c:company)-[:主营产品]->(p:product)
        RETURN c.name as company, count(p) as product_count
        ORDER BY product_count DESC
        """)
        
        print(f"\n各公司产品数量:")
        for stat in company_stats:
            print(f"  - {stat['company']}: {stat['product_count']}个产品")
        
        print("\n数据清理和创建完成！")
        
    except Exception as e:
        logger.error(f"处理数据时出错: {str(e)}")
        raise e
    finally:
        # Neo4jConnector 不需要手动关闭连接
        pass

if __name__ == "__main__":
    clean_and_create_proper_data()