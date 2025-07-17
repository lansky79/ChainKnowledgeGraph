#!/usr/bin/env python3
# coding: utf-8
# File: enrich_industry_relations.py
# 丰富行业间的交叉关系

from utils.db_connector import Neo4jConnector

def enrich_industry_relations():
    """添加更多行业间的交叉关系，让矩阵更丰富"""
    
    db = Neo4jConnector()
    
    try:
        print("开始添加更多行业间的交叉关系...")
        
        # 添加更多复杂的行业间关系
        additional_relations = [
            # 人工智能与其他行业的双向和多向关系
            {"from": "大数据", "to": "人工智能", "relation": "支撑", "description": "大数据为AI提供训练数据"},
            {"from": "云计算", "to": "人工智能", "relation": "支撑", "description": "云计算为AI提供计算资源"},
            {"from": "人工智能", "to": "教育科技", "relation": "赋能", "description": "AI个性化教学"},
            {"from": "人工智能", "to": "游戏娱乐", "relation": "赋能", "description": "AI提升游戏体验"},
            {"from": "人工智能", "to": "电子商务", "relation": "赋能", "description": "AI推荐系统"},
            
            # 云计算与其他行业的关系
            {"from": "电子商务", "to": "云计算", "relation": "依赖", "description": "电商平台依赖云服务"},
            {"from": "游戏娱乐", "to": "云计算", "relation": "依赖", "description": "游戏服务器依赖云计算"},
            {"from": "教育科技", "to": "云计算", "relation": "依赖", "description": "在线教育依赖云平台"},
            {"from": "金融科技", "to": "云计算", "relation": "依赖", "description": "金融服务依赖云基础设施"},
            
            # 大数据与其他行业的关系
            {"from": "电子商务", "to": "大数据", "relation": "产生", "description": "电商产生用户行为数据"},
            {"from": "游戏娱乐", "to": "大数据", "relation": "产生", "description": "游戏产生用户数据"},
            {"from": "教育科技", "to": "大数据", "relation": "产生", "description": "在线学习产生教育数据"},
            {"from": "金融科技", "to": "大数据", "relation": "依赖", "description": "金融风控需要大数据分析"},
            {"from": "大数据", "to": "电子商务", "relation": "赋能", "description": "数据分析优化电商运营"},
            {"from": "大数据", "to": "游戏娱乐", "relation": "赋能", "description": "数据分析优化游戏设计"},
            
            # 金融科技与其他行业的关系
            {"from": "电子商务", "to": "金融科技", "relation": "催生", "description": "电商推动支付创新"},
            {"from": "金融科技", "to": "电子商务", "relation": "支撑", "description": "支付服务支撑电商发展"},
            {"from": "人工智能", "to": "金融科技", "relation": "赋能", "description": "AI提升金融服务智能化"},
            {"from": "大数据", "to": "金融科技", "relation": "赋能", "description": "大数据支撑金融风控"},
            
            # 教育科技与其他行业的关系
            {"from": "游戏娱乐", "to": "教育科技", "relation": "融合", "description": "游戏化学习"},
            {"from": "教育科技", "to": "人工智能", "relation": "应用", "description": "教育场景应用AI技术"},
            {"from": "大数据", "to": "教育科技", "relation": "赋能", "description": "学习数据分析"},
            
            # 游戏娱乐与其他行业的关系
            {"from": "游戏娱乐", "to": "人工智能", "relation": "应用", "description": "游戏AI和NPC智能化"},
            {"from": "电子商务", "to": "游戏娱乐", "relation": "融合", "description": "游戏内购和虚拟商品交易"},
            
            # 电子商务内部生态关系
            {"from": "电子商务", "to": "教育科技", "relation": "拓展", "description": "电商平台拓展教育业务"},
            
            # 添加一些反向关系，形成更复杂的网络
            {"from": "云计算", "to": "大数据", "relation": "支撑", "description": "云计算支撑大数据处理"},
            {"from": "教育科技", "to": "游戏娱乐", "relation": "借鉴", "description": "教育借鉴游戏化设计"},
            {"from": "金融科技", "to": "人工智能", "relation": "应用", "description": "金融场景应用AI技术"},
            {"from": "电子商务", "to": "人工智能", "relation": "应用", "description": "电商应用AI推荐技术"},
            
            # 添加一些三角关系
            {"from": "云计算", "to": "电子商务", "relation": "支撑", "description": "云服务支撑电商平台"},
            {"from": "大数据", "to": "游戏娱乐", "relation": "优化", "description": "数据分析优化游戏体验"},
            {"from": "人工智能", "to": "云计算", "relation": "依赖", "description": "AI训练依赖云计算资源"},
            {"from": "教育科技", "to": "大数据", "relation": "应用", "description": "教育数据挖掘和分析"},
            {"from": "游戏娱乐", "to": "金融科技", "relation": "融合", "description": "游戏支付和虚拟货币"},
            {"from": "金融科技", "to": "教育科技", "relation": "支撑", "description": "教育分期和金融服务"},
        ]
        
        # 创建这些新的关系
        create_relations_query = """
        UNWIND $relations AS rel
        MATCH (i1:industry {name: rel.from})
        MATCH (i2:industry {name: rel.to})
        MERGE (i1)-[r:相关行业 {type: rel.relation}]->(i2)
        ON CREATE SET r.description = rel.description
        ON MATCH SET r.description = rel.description
        """
        db.query(create_relations_query, {"relations": additional_relations})
        print(f"添加了 {len(additional_relations)} 个新的行业间关系")
        
        # 验证结果
        print("\n验证新的关系网络...")
        
        # 查询每个行业的出度和入度
        industry_stats = db.query("""
        MATCH (i:industry)
        OPTIONAL MATCH (i)-[r_out:相关行业]->()
        OPTIONAL MATCH ()-[r_in:相关行业]->(i)
        RETURN i.name as industry, 
               count(distinct r_out) as outgoing_relations,
               count(distinct r_in) as incoming_relations,
               count(distinct r_out) + count(distinct r_in) as total_relations
        ORDER BY total_relations DESC
        """)
        
        print(f"\n行业关系统计 (按总关系数排序):")
        for stat in industry_stats:
            if stat['total_relations'] > 0:
                print(f"  {stat['industry']}: 出度={stat['outgoing_relations']}, 入度={stat['incoming_relations']}, 总计={stat['total_relations']}")
        
        # 查询总关系数
        total_relations = db.query("""
        MATCH ()-[r:相关行业]->()
        RETURN count(r) as total
        """)
        
        print(f"\n总行业间关系数量: {total_relations[0]['total']}")
        
        # 查询互联网相关的所有关系（包括作为目标的关系）
        internet_all_relations = db.query("""
        MATCH (i1:industry)-[r:相关行业]->(i2:industry)
        WHERE i1.name = '互联网' OR i2.name = '互联网'
        RETURN i1.name as from_industry, r.type as relation_type, i2.name as to_industry
        ORDER BY from_industry, to_industry
        """)
        
        print(f"\n互联网相关的所有关系 ({len(internet_all_relations)}个):")
        for rel in internet_all_relations:
            print(f"  {rel['from_industry']} --{rel['relation_type']}--> {rel['to_industry']}")
        
        # 查询形成的关系网络密度
        network_density = db.query("""
        MATCH (i:industry)
        WITH count(i) as node_count
        MATCH ()-[r:相关行业]->()
        WITH node_count, count(r) as edge_count
        RETURN node_count, edge_count, 
               round(100.0 * edge_count / (node_count * (node_count - 1)), 2) as density_percent
        """)
        
        if network_density:
            stats = network_density[0]
            print(f"\n网络统计:")
            print(f"  节点数: {stats['node_count']}")
            print(f"  边数: {stats['edge_count']}")
            print(f"  网络密度: {stats['density_percent']}%")
        
        print("\n行业关系网络丰富化完成！")
        
    except Exception as e:
        print(f"添加行业关系时出错: {str(e)}")
        raise e

if __name__ == "__main__":
    enrich_industry_relations()