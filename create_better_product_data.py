#!/usr/bin/env python3
# coding: utf-8
# File: create_better_product_data.py
# 创建更好的产品数据结构，包括产品类别和产品间关系

from utils.db_connector import Neo4jConnector

def create_better_product_data():
    """创建更好的产品数据结构"""
    
    db = Neo4jConnector()
    
    try:
        print("开始创建更好的产品数据结构...")
        
        # 1. 创建产品类别和具体产品的层级结构
        products_data = [
            # 通用产品类别（父级产品）
            {"name": "手机", "category": "消费电子", "type": "产品类别", "description": "移动通信设备"},
            {"name": "电脑", "category": "消费电子", "type": "产品类别", "description": "个人计算设备"},
            {"name": "智能音箱", "category": "智能硬件", "type": "产品类别", "description": "语音交互设备"},
            {"name": "云服务", "category": "云计算", "type": "产品类别", "description": "云计算服务"},
            {"name": "搜索引擎", "category": "互联网服务", "type": "产品类别", "description": "信息检索服务"},
            {"name": "社交软件", "category": "互联网服务", "type": "产品类别", "description": "社交通讯应用"},
            {"name": "电商平台", "category": "互联网服务", "type": "产品类别", "description": "在线购物平台"},
            {"name": "支付服务", "category": "金融科技", "type": "产品类别", "description": "移动支付解决方案"},
            {"name": "地图导航", "category": "互联网服务", "type": "产品类别", "description": "位置服务和导航"},
            {"name": "视频平台", "category": "互联网服务", "type": "产品类别", "description": "在线视频服务"},
            {"name": "游戏", "category": "数字娱乐", "type": "产品类别", "description": "电子游戏产品"},
            {"name": "操作系统", "category": "软件系统", "type": "产品类别", "description": "设备操作系统"},
            
            # 具体产品实例（子级产品）
            {"name": "华为手机", "category": "消费电子", "type": "具体产品", "description": "华为品牌智能手机", "parent": "手机"},
            {"name": "小米手机", "category": "消费电子", "type": "具体产品", "description": "小米品牌智能手机", "parent": "手机"},
            {"name": "OPPO手机", "category": "消费电子", "type": "具体产品", "description": "OPPO品牌智能手机", "parent": "手机"},
            {"name": "vivo手机", "category": "消费电子", "type": "具体产品", "description": "vivo品牌智能手机", "parent": "手机"},
            
            {"name": "华为笔记本", "category": "消费电子", "type": "具体产品", "description": "华为MateBook系列", "parent": "电脑"},
            {"name": "小米笔记本", "category": "消费电子", "type": "具体产品", "description": "小米笔记本电脑", "parent": "电脑"},
            
            {"name": "小米音箱", "category": "智能硬件", "type": "具体产品", "description": "小米AI音箱", "parent": "智能音箱"},
            {"name": "小度音箱", "category": "智能硬件", "type": "具体产品", "description": "百度小度音箱", "parent": "智能音箱"},
            
            {"name": "阿里云", "category": "云计算", "type": "具体产品", "description": "阿里巴巴云服务", "parent": "云服务"},
            {"name": "腾讯云", "category": "云计算", "type": "具体产品", "description": "腾讯云服务", "parent": "云服务"},
            {"name": "百度云", "category": "云计算", "type": "具体产品", "description": "百度云服务", "parent": "云服务"},
            {"name": "京东云", "category": "云计算", "type": "具体产品", "description": "京东云服务", "parent": "云服务"},
            
            {"name": "百度搜索", "category": "互联网服务", "type": "具体产品", "description": "百度搜索引擎", "parent": "搜索引擎"},
            
            {"name": "微信", "category": "互联网服务", "type": "具体产品", "description": "腾讯微信", "parent": "社交软件"},
            {"name": "QQ", "category": "互联网服务", "type": "具体产品", "description": "腾讯QQ", "parent": "社交软件"},
            
            {"name": "淘宝", "category": "互联网服务", "type": "具体产品", "description": "阿里巴巴淘宝", "parent": "电商平台"},
            {"name": "天猫", "category": "互联网服务", "type": "具体产品", "description": "阿里巴巴天猫", "parent": "电商平台"},
            {"name": "京东商城", "category": "互联网服务", "type": "具体产品", "description": "京东电商平台", "parent": "电商平台"},
            
            {"name": "支付宝", "category": "金融科技", "type": "具体产品", "description": "阿里巴巴支付宝", "parent": "支付服务"},
            {"name": "微信支付", "category": "金融科技", "type": "具体产品", "description": "腾讯微信支付", "parent": "支付服务"},
            
            {"name": "百度地图", "category": "互联网服务", "type": "具体产品", "description": "百度地图服务", "parent": "地图导航"},
            
            {"name": "腾讯视频", "category": "互联网服务", "type": "具体产品", "description": "腾讯视频平台", "parent": "视频平台"},
            
            {"name": "王者荣耀", "category": "数字娱乐", "type": "具体产品", "description": "腾讯手机游戏", "parent": "游戏"},
            {"name": "网易游戏", "category": "数字娱乐", "type": "具体产品", "description": "网易游戏产品", "parent": "游戏"},
            
            {"name": "鸿蒙OS", "category": "软件系统", "type": "具体产品", "description": "华为鸿蒙操作系统", "parent": "操作系统"},
            {"name": "MIUI", "category": "软件系统", "type": "具体产品", "description": "小米MIUI系统", "parent": "操作系统"},
            {"name": "ColorOS", "category": "软件系统", "type": "具体产品", "description": "OPPO ColorOS", "parent": "操作系统"},
        ]
        
        # 批量创建产品节点
        create_products_query = """
        UNWIND $products AS product
        MERGE (p:product {name: product.name})
        ON CREATE SET 
            p.category = product.category,
            p.type = product.type,
            p.description = product.description
        ON MATCH SET 
            p.category = product.category,
            p.type = product.type,
            p.description = product.description
        """
        db.query(create_products_query, {"products": products_data})
        print(f"创建了 {len(products_data)} 个产品节点")
        
        # 2. 创建产品层级关系（父子关系）
        hierarchy_relations = []
        for product in products_data:
            if "parent" in product:
                hierarchy_relations.append({
                    "child": product["name"],
                    "parent": product["parent"]
                })
        
        create_hierarchy_query = """
        UNWIND $relations AS rel
        MATCH (child:product {name: rel.child})
        MATCH (parent:product {name: rel.parent})
        MERGE (child)-[r:属于类别]->(parent)
        """
        db.query(create_hierarchy_query, {"relations": hierarchy_relations})
        print(f"创建了 {len(hierarchy_relations)} 个产品层级关系")
        
        # 3. 创建产品间的其他关系
        product_relations = [
            # 竞争关系
            {"from": "华为手机", "to": "小米手机", "relation": "竞争", "description": "同类产品竞争"},
            {"from": "小米手机", "to": "OPPO手机", "relation": "竞争", "description": "同类产品竞争"},
            {"from": "OPPO手机", "to": "vivo手机", "relation": "竞争", "description": "同类产品竞争"},
            {"from": "vivo手机", "to": "华为手机", "relation": "竞争", "description": "同类产品竞争"},
            
            {"from": "阿里云", "to": "腾讯云", "relation": "竞争", "description": "云服务竞争"},
            {"from": "腾讯云", "to": "百度云", "relation": "竞争", "description": "云服务竞争"},
            {"from": "百度云", "to": "京东云", "relation": "竞争", "description": "云服务竞争"},
            
            {"from": "淘宝", "to": "京东商城", "relation": "竞争", "description": "电商平台竞争"},
            {"from": "天猫", "to": "京东商城", "relation": "竞争", "description": "电商平台竞争"},
            
            {"from": "支付宝", "to": "微信支付", "relation": "竞争", "description": "支付服务竞争"},
            
            {"from": "微信", "to": "QQ", "relation": "互补", "description": "同公司产品互补"},
            {"from": "淘宝", "to": "天猫", "relation": "互补", "description": "同公司产品互补"},
            
            # 依赖关系
            {"from": "华为手机", "to": "鸿蒙OS", "relation": "依赖", "description": "硬件依赖操作系统"},
            {"from": "小米手机", "to": "MIUI", "relation": "依赖", "description": "硬件依赖操作系统"},
            {"from": "OPPO手机", "to": "ColorOS", "relation": "依赖", "description": "硬件依赖操作系统"},
            
            {"from": "淘宝", "to": "支付宝", "relation": "依赖", "description": "电商依赖支付服务"},
            {"from": "天猫", "to": "支付宝", "relation": "依赖", "description": "电商依赖支付服务"},
            
            # 集成关系
            {"from": "微信", "to": "微信支付", "relation": "集成", "description": "社交软件集成支付"},
            {"from": "王者荣耀", "to": "微信支付", "relation": "集成", "description": "游戏集成支付"},
            
            # 技术支撑关系
            {"from": "阿里云", "to": "淘宝", "relation": "支撑", "description": "云服务支撑电商平台"},
            {"from": "阿里云", "to": "天猫", "relation": "支撑", "description": "云服务支撑电商平台"},
            {"from": "腾讯云", "to": "微信", "relation": "支撑", "description": "云服务支撑社交平台"},
            {"from": "腾讯云", "to": "王者荣耀", "relation": "支撑", "description": "云服务支撑游戏"},
        ]
        
        # 创建产品间关系
        create_relations_query = """
        UNWIND $relations AS rel
        MATCH (p1:product {name: rel.from})
        MATCH (p2:product {name: rel.to})
        MERGE (p1)-[r:产品关系 {type: rel.relation}]->(p2)
        ON CREATE SET r.description = rel.description
        ON MATCH SET r.description = rel.description
        """
        db.query(create_relations_query, {"relations": product_relations})
        print(f"创建了 {len(product_relations)} 个产品间关系")
        
        # 4. 验证数据
        print("\n验证产品数据...")
        
        # 查询产品类别统计
        category_stats = db.query("""
        MATCH (p:product)
        RETURN p.type as product_type, count(p) as count
        ORDER BY count DESC
        """)
        
        print("产品类型统计:")
        for stat in category_stats:
            print(f"  - {stat['product_type']}: {stat['count']}个")
        
        # 查询层级关系
        hierarchy_stats = db.query("""
        MATCH (child:product)-[:属于类别]->(parent:product)
        RETURN parent.name as category, collect(child.name) as products
        ORDER BY parent.name
        """)
        
        print(f"\n产品层级关系:")
        for stat in hierarchy_stats:
            products = stat['products'][:3]  # 只显示前3个
            more = f" 等{len(stat['products'])}个" if len(stat['products']) > 3 else ""
            print(f"  {stat['category']}: {', '.join(products)}{more}")
        
        # 查询产品间关系统计
        relation_stats = db.query("""
        MATCH (p1:product)-[r:产品关系]->(p2:product)
        RETURN r.type as relation_type, count(r) as count
        ORDER BY count DESC
        """)
        
        print(f"\n产品间关系统计:")
        for stat in relation_stats:
            print(f"  - {stat['relation_type']}: {stat['count']}条")
        
        print("\n更好的产品数据结构创建完成！")
        
        # 推荐测试产品
        print("\n推荐用于测试的产品:")
        print("1. 手机 - 有层级结构和竞争关系")
        print("2. 云服务 - 有竞争和支撑关系") 
        print("3. 电商平台 - 有竞争和依赖关系")
        print("4. 社交软件 - 有互补和集成关系")
        
    except Exception as e:
        print(f"创建产品数据时出错: {str(e)}")
        raise e

if __name__ == "__main__":
    create_better_product_data()