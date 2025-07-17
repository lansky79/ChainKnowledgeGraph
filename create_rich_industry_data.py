#!/usr/bin/env python3
# coding: utf-8
# File: create_rich_industry_data.py
# 创建丰富的行业数据和行业间关系

from utils.db_connector import Neo4jConnector

def create_rich_industry_data():
    """创建丰富的行业数据和行业间关系"""
    
    db = Neo4jConnector()
    
    try:
        print("开始创建丰富的行业数据...")
        
        # 1. 创建更多行业节点
        industries_data = [
            {"name": "互联网", "level": "一级行业", "description": "基于互联网技术的各种服务和应用"},
            {"name": "人工智能", "level": "一级行业", "description": "机器学习、深度学习等AI技术应用"},
            {"name": "电子商务", "level": "二级行业", "description": "在线交易和电商平台服务"},
            {"name": "云计算", "level": "二级行业", "description": "云服务和云基础设施"},
            {"name": "大数据", "level": "二级行业", "description": "数据分析和数据处理服务"},
            {"name": "物联网", "level": "二级行业", "description": "设备互联和智能感知技术"},
            {"name": "区块链", "level": "二级行业", "description": "分布式账本和加密货币技术"},
            {"name": "5G通信", "level": "二级行业", "description": "第五代移动通信技术"},
            {"name": "智能制造", "level": "二级行业", "description": "工业4.0和智能生产"},
            {"name": "新能源", "level": "一级行业", "description": "清洁能源和可再生能源"},
            {"name": "生物医药", "level": "一级行业", "description": "生物技术和医药研发"},
            {"name": "金融科技", "level": "二级行业", "description": "金融服务的技术创新"},
            {"name": "教育科技", "level": "二级行业", "description": "在线教育和教育信息化"},
            {"name": "智能交通", "level": "二级行业", "description": "交通智能化和自动驾驶"},
            {"name": "智慧城市", "level": "二级行业", "description": "城市信息化和智能管理"},
            {"name": "网络安全", "level": "二级行业", "description": "信息安全和网络防护"},
            {"name": "虚拟现实", "level": "二级行业", "description": "VR/AR技术和应用"},
            {"name": "游戏娱乐", "level": "二级行业", "description": "电子游戏和数字娱乐"},
        ]
        
        # 批量创建行业节点
        create_industries_query = """
        UNWIND $industries AS industry
        MERGE (i:industry {name: industry.name})
        ON CREATE SET 
            i.level = industry.level,
            i.description = industry.description
        ON MATCH SET 
            i.level = industry.level,
            i.description = industry.description
        """
        db.query(create_industries_query, {"industries": industries_data})
        print(f"创建了 {len(industries_data)} 个行业节点")
        
        # 2. 创建行业间的关系
        industry_relations = [
            # 互联网作为核心，与多个行业相关
            {"from": "互联网", "to": "电子商务", "relation": "包含", "description": "电子商务是互联网的重要应用领域"},
            {"from": "互联网", "to": "云计算", "relation": "依赖", "description": "互联网服务依赖云计算基础设施"},
            {"from": "互联网", "to": "大数据", "relation": "产生", "description": "互联网应用产生大量数据"},
            {"from": "互联网", "to": "人工智能", "relation": "融合", "description": "互联网与AI技术深度融合"},
            {"from": "互联网", "to": "金融科技", "relation": "催生", "description": "互联网推动金融服务创新"},
            {"from": "互联网", "to": "教育科技", "relation": "催生", "description": "互联网推动教育模式创新"},
            {"from": "互联网", "to": "游戏娱乐", "relation": "包含", "description": "网络游戏是互联网重要应用"},
            
            # 人工智能与其他行业的关系
            {"from": "人工智能", "to": "大数据", "relation": "依赖", "description": "AI需要大数据支撑"},
            {"from": "人工智能", "to": "云计算", "relation": "依赖", "description": "AI计算需要云计算资源"},
            {"from": "人工智能", "to": "智能制造", "relation": "赋能", "description": "AI技术赋能制造业"},
            {"from": "人工智能", "to": "智能交通", "relation": "赋能", "description": "AI技术推动交通智能化"},
            {"from": "人工智能", "to": "生物医药", "relation": "赋能", "description": "AI辅助药物研发"},
            {"from": "人工智能", "to": "金融科技", "relation": "赋能", "description": "AI提升金融服务效率"},
            
            # 5G通信与其他行业的关系
            {"from": "5G通信", "to": "物联网", "relation": "支撑", "description": "5G为物联网提供高速连接"},
            {"from": "5G通信", "to": "智能交通", "relation": "支撑", "description": "5G支撑车联网发展"},
            {"from": "5G通信", "to": "智慧城市", "relation": "支撑", "description": "5G是智慧城市基础设施"},
            {"from": "5G通信", "to": "虚拟现实", "relation": "支撑", "description": "5G提供VR/AR所需带宽"},
            
            # 云计算与其他行业的关系
            {"from": "云计算", "to": "大数据", "relation": "支撑", "description": "云计算为大数据提供计算资源"},
            {"from": "云计算", "to": "物联网", "relation": "支撑", "description": "云计算处理物联网数据"},
            {"from": "云计算", "to": "区块链", "relation": "支撑", "description": "云计算支撑区块链网络"},
            
            # 大数据与其他行业的关系
            {"from": "大数据", "to": "金融科技", "relation": "赋能", "description": "大数据支撑金融风控"},
            {"from": "大数据", "to": "智慧城市", "relation": "赋能", "description": "大数据支撑城市治理"},
            {"from": "大数据", "to": "生物医药", "relation": "赋能", "description": "大数据辅助医药研发"},
            
            # 物联网与其他行业的关系
            {"from": "物联网", "to": "智能制造", "relation": "赋能", "description": "物联网实现设备互联"},
            {"from": "物联网", "to": "智慧城市", "relation": "赋能", "description": "物联网是智慧城市感知层"},
            {"from": "物联网", "to": "新能源", "relation": "赋能", "description": "物联网优化能源管理"},
            
            # 区块链与其他行业的关系
            {"from": "区块链", "to": "金融科技", "relation": "赋能", "description": "区块链创新金融服务"},
            {"from": "区块链", "to": "网络安全", "relation": "增强", "description": "区块链提升数据安全"},
            
            # 网络安全与其他行业的关系
            {"from": "网络安全", "to": "金融科技", "relation": "保障", "description": "网络安全保障金融系统"},
            {"from": "网络安全", "to": "智慧城市", "relation": "保障", "description": "网络安全保障城市系统"},
        ]
        
        # 创建行业间关系
        create_relations_query = """
        UNWIND $relations AS rel
        MATCH (i1:industry {name: rel.from})
        MATCH (i2:industry {name: rel.to})
        MERGE (i1)-[r:相关行业 {type: rel.relation}]->(i2)
        ON CREATE SET r.description = rel.description
        ON MATCH SET r.description = rel.description
        """
        db.query(create_relations_query, {"relations": industry_relations})
        print(f"创建了 {len(industry_relations)} 个行业间关系")
        
        # 3. 验证数据
        print("\n验证数据...")
        
        # 查询所有行业
        all_industries = db.query("""
        MATCH (i:industry)
        RETURN i.name as name, i.level as level
        ORDER BY i.name
        """)
        
        print(f"\n所有行业 ({len(all_industries)}个):")
        for industry in all_industries:
            print(f"  - {industry['name']} ({industry['level']})")
        
        # 查询互联网相关的行业关系
        internet_relations = db.query("""
        MATCH (i1:industry {name: '互联网'})-[r:相关行业]->(i2:industry)
        RETURN i2.name as related_industry, r.type as relation_type
        ORDER BY i2.name
        """)
        
        print(f"\n互联网相关的行业关系 ({len(internet_relations)}个):")
        for rel in internet_relations:
            print(f"  - 互联网 --{rel['relation_type']}--> {rel['related_industry']}")
        
        # 查询所有行业间关系统计
        all_relations = db.query("""
        MATCH (i1:industry)-[r:相关行业]->(i2:industry)
        RETURN count(r) as total_relations
        """)
        
        print(f"\n总行业间关系数量: {all_relations[0]['total_relations']}")
        
        print("\n丰富的行业数据创建完成！")
        
    except Exception as e:
        print(f"创建行业数据时出错: {str(e)}")
        raise e

if __name__ == "__main__":
    create_rich_industry_data()