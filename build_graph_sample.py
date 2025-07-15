#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
from py2neo import Graph, Node, Relationship

# Neo4j连接配置
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "12345678"

def connect_to_neo4j():
    """连接到Neo4j数据库"""
    try:
        graph = Graph(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        print("成功连接到Neo4j数据库")
        return graph
    except Exception as e:
        print(f"连接Neo4j数据库失败: {str(e)}")
        return None

def clear_database(graph):
    """清空数据库中的所有节点和关系"""
    try:
        graph.run("MATCH (n) DETACH DELETE n")
        print("数据库已清空")
    except Exception as e:
        print(f"清空数据库失败: {str(e)}")

def load_json_data(file_path):
    """加载JSON数据文件"""
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            data = [json.loads(line) for line in f if line.strip()]
        print(f"成功加载数据文件: {file_path}")
        return data
    except Exception as e:
        print(f"加载数据文件失败 {file_path}: {str(e)}")
        return []

def create_industry_nodes(graph, data_path="data"):
    """创建行业节点"""
    industry_data = load_json_data(os.path.join(data_path, "company_industry.json"))
    
    # 获取已存在的行业节点
    existing_industries = {}
    try:
        result = graph.run("MATCH (i:industry) RETURN i.name as name").data()
        for record in result:
            existing_industries[record["name"]] = True
        print(f"已找到{len(existing_industries)}个现有行业节点")
    except Exception as e:
        print(f"获取现有行业节点失败: {str(e)}")
    
    # 创建行业节点和关系
    industries = {}
    for item in industry_data:
        industry_name = item["industry_name"]
        if industry_name not in industries:
            # 检查节点是否已存在
            if industry_name in existing_industries:
                # 获取已存在的节点
                industry_node = graph.nodes.match("industry", name=industry_name).first()
                if industry_node:
                    industries[industry_name] = industry_node
                    print(f"使用已存在的行业节点: {industry_name}")
                    continue
            
            # 创建新节点
            industry_node = Node("industry", name=industry_name, code=item["industry_code"])
            graph.create(industry_node)
            industries[industry_name] = industry_node
            print(f"创建行业节点: {industry_name}")
    
    # 添加行业之间的层级关系
    industry_hierarchy = [
        {"parent": "互联网", "child": "电子商务"},
        {"parent": "互联网", "child": "社交媒体"},
        {"parent": "互联网", "child": "云计算"},
        {"parent": "互联网", "child": "在线教育"},
        {"parent": "互联网", "child": "在线娱乐"},
        {"parent": "制造业", "child": "汽车制造"},
        {"parent": "制造业", "child": "电子设备"},
        {"parent": "制造业", "child": "机械设备"},
        {"parent": "金融业", "child": "银行"},
        {"parent": "金融业", "child": "保险"},
        {"parent": "金融业", "child": "证券"},
        {"parent": "医疗健康", "child": "医药研发"},
        {"parent": "医疗健康", "child": "医疗器械"},
        {"parent": "医疗健康", "child": "生物技术"},
        {"parent": "能源", "child": "新能源"},
        {"parent": "能源", "child": "传统能源"},
    ]
    
    for relation in industry_hierarchy:
        parent_name = relation["parent"]
        child_name = relation["child"]
        
        # 确保父行业节点存在
        if parent_name not in industries:
            # 检查是否已存在
            if parent_name in existing_industries:
                parent_node = graph.nodes.match("industry", name=parent_name).first()
                if parent_node:
                    industries[parent_name] = parent_node
                    print(f"使用已存在的父行业节点: {parent_name}")
                else:
                    parent_node = Node("industry", name=parent_name)
                    graph.create(parent_node)
                    industries[parent_name] = parent_node
                    print(f"创建父行业节点: {parent_name}")
            else:
                parent_node = Node("industry", name=parent_name)
                graph.create(parent_node)
                industries[parent_name] = parent_node
                print(f"创建父行业节点: {parent_name}")
        
        # 确保子行业节点存在
        if child_name not in industries:
            # 检查是否已存在
            if child_name in existing_industries:
                child_node = graph.nodes.match("industry", name=child_name).first()
                if child_node:
                    industries[child_name] = child_node
                    print(f"使用已存在的子行业节点: {child_name}")
                else:
                    child_node = Node("industry", name=child_name)
                    graph.create(child_node)
                    industries[child_name] = child_node
                    print(f"创建子行业节点: {child_name}")
            else:
                child_node = Node("industry", name=child_name)
                graph.create(child_node)
                industries[child_name] = child_node
                print(f"创建子行业节点: {child_name}")
        
        # 检查关系是否已存在
        try:
            rel_exists = graph.run(
                "MATCH (c:industry {name: $child})-[r:上级行业]->(p:industry {name: $parent}) RETURN count(r) > 0 as exists",
                {"child": child_name, "parent": parent_name}
            ).data()
            
            if rel_exists and rel_exists[0].get("exists", False):
                print(f"行业层级关系已存在: {child_name} -> {parent_name}")
                continue
        except Exception as e:
            print(f"检查行业层级关系失败: {str(e)}")
        
        # 创建层级关系
        try:
            rel = Relationship(industries[child_name], "上级行业", industries[parent_name])
            graph.create(rel)
            print(f"创建行业层级关系: {child_name} -> {parent_name}")
        except Exception as e:
            print(f"创建行业层级关系失败: {str(e)}")
    
    return industries

def create_company_nodes(graph, industries, data_path="data"):
    """创建公司节点"""
    try:
        company_data = load_json_data(os.path.join(data_path, "company_array.json"))
    except:
        print("无法加载company_array.json，使用手动创建的公司数据")
        company_data = []
    
    company_industry_data = load_json_data(os.path.join(data_path, "company_industry.json"))
    
    # 获取已存在的公司节点
    existing_companies = {}
    try:
        result = graph.run("MATCH (c:company) RETURN c.name as name").data()
        for record in result:
            existing_companies[record["name"]] = True
        print(f"已找到{len(existing_companies)}个现有公司节点")
    except Exception as e:
        print(f"获取现有公司节点失败: {str(e)}")
    
    # 创建公司节点
    companies = {}
    
    # 如果company_data加载失败，使用手动创建的公司数据
    if not company_data:
        manual_companies = [
            {"name": "阿里巴巴", "fullname": "阿里巴巴集团控股有限公司", "code": "BABA.N"},
            {"name": "腾讯控股", "fullname": "腾讯控股有限公司", "code": "00700.HK"},
            {"name": "百度", "fullname": "百度公司", "code": "BIDU.O"},
            {"name": "京东", "fullname": "京东集团股份有限公司", "code": "JD.O"},
            {"name": "网易", "fullname": "网易公司", "code": "NTES.O"},
            {"name": "美团", "fullname": "美团点评", "code": "03690.HK"},
            {"name": "拼多多", "fullname": "拼多多公司", "code": "PDD.O"},
            {"name": "字节跳动", "fullname": "北京字节跳动科技有限公司", "code": "未上市"},
            {"name": "华为", "fullname": "华为技术有限公司", "code": "未上市"},
            {"name": "小米集团", "fullname": "小米集团", "code": "01810.HK"},
            {"name": "中兴通讯", "fullname": "中兴通讯股份有限公司", "code": "000063.SZ"},
            {"name": "联想集团", "fullname": "联想集团有限公司", "code": "00992.HK"},
            {"name": "OPPO", "fullname": "广东欧珀移动通信有限公司", "code": "未上市"},
            {"name": "vivo", "fullname": "维沃移动通信有限公司", "code": "未上市"},
            {"name": "TCL科技", "fullname": "TCL科技集团股份有限公司", "code": "000100.SZ"},
            {"name": "创维数字", "fullname": "创维数字股份有限公司", "code": "000810.SZ"},
            {"name": "微博", "fullname": "微博公司", "code": "WB.O"},
            {"name": "搜狗", "fullname": "搜狗公司", "code": "已被腾讯收购"},
            {"name": "完美世界", "fullname": "完美世界股份有限公司", "code": "002624.SZ"},
            {"name": "三七互娱", "fullname": "芜湖三七互娱网络科技集团股份有限公司", "code": "002555.SZ"},
            {"name": "比亚迪", "fullname": "比亚迪股份有限公司", "code": "002594.SZ"},
            {"name": "蔚来", "fullname": "蔚来汽车", "code": "NIO.N"},
            {"name": "小鹏汽车", "fullname": "小鹏汽车有限公司", "code": "XPEV.N"},
            {"name": "理想汽车", "fullname": "理想汽车有限公司", "code": "LI.O"},
            {"name": "宁德时代", "fullname": "宁德时代新能源科技股份有限公司", "code": "300750.SZ"},
            {"name": "亿纬锂能", "fullname": "惠州亿纬锂能股份有限公司", "code": "300014.SZ"},
            {"name": "隆基绿能", "fullname": "隆基绿能科技股份有限公司", "code": "601012.SH"},
            {"name": "晶科能源", "fullname": "晶科能源控股有限公司", "code": "JKS.N"},
            {"name": "阳光电源", "fullname": "阳光电源股份有限公司", "code": "300274.SZ"},
            {"name": "中芯国际", "fullname": "中芯国际集成电路制造有限公司", "code": "688981.SH"},
            {"name": "韦尔股份", "fullname": "上海韦尔半导体股份有限公司", "code": "603501.SH"},
            {"name": "兆易创新", "fullname": "北京兆易创新科技股份有限公司", "code": "603986.SH"},
            {"name": "迈瑞医疗", "fullname": "深圳迈瑞生物医疗电子股份有限公司", "code": "300760.SZ"},
            {"name": "万东医疗", "fullname": "华润万东医疗装备股份有限公司", "code": "600055.SH"},
            {"name": "鱼跃医疗", "fullname": "江苏鱼跃医疗设备股份有限公司", "code": "002223.SZ"},
            {"name": "康泰生物", "fullname": "深圳康泰生物制品股份有限公司", "code": "300601.SZ"},
            {"name": "智飞生物", "fullname": "重庆智飞生物制品股份有限公司", "code": "300122.SZ"},
            {"name": "沃森生物", "fullname": "云南沃森生物技术股份有限公司", "code": "300142.SZ"},
            {"name": "恒瑞医药", "fullname": "江苏恒瑞医药股份有限公司", "code": "600276.SH"},
            {"name": "君实生物", "fullname": "上海君实生物医药科技股份有限公司", "code": "688180.SH"},
            {"name": "信达生物", "fullname": "信达生物制药", "code": "01801.HK"},
        ]
        company_data = manual_companies
    
    for item in company_data:
        company_name = item["name"]
        if company_name not in companies:
            # 检查节点是否已存在
            if company_name in existing_companies:
                # 获取已存在的节点
                company_node = graph.nodes.match("company", name=company_name).first()
                if company_node:
                    companies[company_name] = company_node
                    print(f"使用已存在的公司节点: {company_name}")
                    continue
            
            # 创建新节点
            company_node = Node("company", 
                               name=company_name, 
                               fullname=item.get("fullname", ""), 
                               code=item.get("code", ""))
            graph.create(company_node)
            companies[company_name] = company_node
            print(f"创建公司节点: {company_name}")
    
    # 创建公司与行业的关系
    # 手动添加一些公司与行业的关系
    industry_relations = [
        {"company": "阿里巴巴", "industry": "电子商务"},
        {"company": "阿里巴巴", "industry": "云计算"},
        {"company": "腾讯控股", "industry": "社交媒体"},
        {"company": "腾讯控股", "industry": "游戏Ⅲ"},
        {"company": "腾讯控股", "industry": "云计算"},
        {"company": "百度", "industry": "搜索引擎"},
        {"company": "百度", "industry": "人工智能"},
        {"company": "京东", "industry": "电子商务"},
        {"company": "京东", "industry": "物流"},
        {"company": "网易", "industry": "游戏Ⅲ"},
        {"company": "网易", "industry": "在线教育"},
        {"company": "美团", "industry": "生活服务"},
        {"company": "拼多多", "industry": "电子商务"},
        {"company": "字节跳动", "industry": "社交媒体"},
        {"company": "华为", "industry": "通信设备"},
        {"company": "华为", "industry": "智能手机"},
        {"company": "小米集团", "industry": "智能手机"},
        {"company": "小米集团", "industry": "智能家居"},
        {"company": "中兴通讯", "industry": "通信设备"},
        {"company": "联想集团", "industry": "电脑硬件"},
        {"company": "OPPO", "industry": "智能手机"},
        {"company": "vivo", "industry": "智能手机"},
        {"company": "TCL科技", "industry": "家电"},
        {"company": "创维数字", "industry": "家电"},
        {"company": "微博", "industry": "社交媒体"},
        {"company": "搜狗", "industry": "搜索引擎"},
        {"company": "完美世界", "industry": "游戏Ⅲ"},
        {"company": "三七互娱", "industry": "游戏Ⅲ"},
        {"company": "比亚迪", "industry": "新能源汽车"},
        {"company": "比亚迪", "industry": "电池"},
        {"company": "蔚来", "industry": "新能源汽车"},
        {"company": "小鹏汽车", "industry": "新能源汽车"},
        {"company": "理想汽车", "industry": "新能源汽车"},
        {"company": "宁德时代", "industry": "电池"},
        {"company": "亿纬锂能", "industry": "电池"},
        {"company": "隆基绿能", "industry": "光伏"},
        {"company": "晶科能源", "industry": "光伏"},
        {"company": "阳光电源", "industry": "光伏"},
        {"company": "中芯国际", "industry": "半导体"},
        {"company": "韦尔股份", "industry": "半导体"},
        {"company": "兆易创新", "industry": "半导体"},
        {"company": "迈瑞医疗", "industry": "医疗设备"},
        {"company": "万东医疗", "industry": "医疗设备"},
        {"company": "鱼跃医疗", "industry": "医疗设备"},
        {"company": "康泰生物", "industry": "疫苗"},
        {"company": "智飞生物", "industry": "疫苗"},
        {"company": "沃森生物", "industry": "疫苗"},
        {"company": "恒瑞医药", "industry": "制药"},
        {"company": "君实生物", "industry": "生物医药"},
        {"company": "信达生物", "industry": "生物医药"},
    ]
    
    # 从数据库中获取的关系
    for item in company_industry_data:
        company_name = item["company_name"]
        industry_name = item["industry_name"]
        
        if company_name in companies and industry_name in industries:
            # 检查关系是否已存在
            try:
                rel_exists = graph.run(
                    "MATCH (c:company {name: $company})-[r:所属行业]->(i:industry {name: $industry}) RETURN count(r) > 0 as exists",
                    {"company": company_name, "industry": industry_name}
                ).data()
                
                if rel_exists and rel_exists[0].get("exists", False):
                    print(f"公司行业关系已存在: {company_name} -> {industry_name}")
                    continue
            except Exception as e:
                print(f"检查公司行业关系失败: {str(e)}")
            
            # 创建关系
            rel = Relationship(companies[company_name], "所属行业", industries[industry_name])
            graph.create(rel)
            print(f"创建公司行业关系: {company_name} -> {industry_name}")
    
    # 手动添加的关系
    for relation in industry_relations:
        company_name = relation["company"]
        industry_name = relation["industry"]
        
        if company_name in companies and industry_name in industries:
            # 检查关系是否已存在
            try:
                rel_exists = graph.run(
                    "MATCH (c:company {name: $company})-[r:所属行业]->(i:industry {name: $industry}) RETURN count(r) > 0 as exists",
                    {"company": company_name, "industry": industry_name}
                ).data()
                
                if rel_exists and rel_exists[0].get("exists", False):
                    print(f"公司行业关系(手动)已存在: {company_name} -> {industry_name}")
                    continue
            except Exception as e:
                print(f"检查公司行业关系(手动)失败: {str(e)}")
            
            # 创建关系
            rel = Relationship(companies[company_name], "所属行业", industries[industry_name])
            graph.create(rel)
            print(f"创建公司行业关系(手动): {company_name} -> {industry_name}")
        elif company_name in companies and industry_name not in industries:
            # 如果行业不存在，创建行业节点
            industry_node = Node("industry", name=industry_name)
            graph.create(industry_node)
            industries[industry_name] = industry_node
            print(f"创建行业节点(手动): {industry_name}")
            
            # 创建关系
            rel = Relationship(companies[company_name], "所属行业", industries[industry_name])
            graph.create(rel)
            print(f"创建公司行业关系(手动): {company_name} -> {industry_name}")
    
    return companies

def create_product_nodes(graph, companies=None):
    """创建产品节点和关系"""
    # 获取已存在的产品节点
    existing_products = {}
    try:
        result = graph.run("MATCH (p:product) RETURN p.name as name").data()
        for record in result:
            existing_products[record["name"]] = True
        print(f"已找到{len(existing_products)}个现有产品节点")
        except Exception as e:
        print(f"获取现有产品节点失败: {str(e)}")
    
    # 获取已存在的材料节点
    existing_materials = {}
    try:
        result = graph.run("MATCH (m:material) RETURN m.name as name").data()
        for record in result:
            existing_materials[record["name"]] = True
        print(f"已找到{len(existing_materials)}个现有材料节点")
    except Exception as e:
        print(f"获取现有材料节点失败: {str(e)}")
    
    products = {}
    
    # 创建产品节点
    product_names = ["智能手机", "笔记本电脑", "智能电视", "云服务", "电商平台", 
                    "社交软件", "搜索引擎", "网络游戏", "新能源汽车", "电池", 
                    "光伏组件", "芯片", "医疗器械", "疫苗", "抗体药物"]
    
    for name in product_names:
        if name not in products:
            # 检查节点是否已存在
            if name in existing_products:
                # 获取已存在的节点
                product_node = graph.nodes.match("product", name=name).first()
                if product_node:
                    products[name] = product_node
                    print(f"使用已存在的产品节点: {name}")
                    continue
            
            # 创建新节点
            product_node = Node("product", name=name)
            graph.create(product_node)
            products[name] = product_node
            print(f"创建产品节点: {name}")
    
    # 创建产品上游关系
    upstream_relations = [
        {"product": "智能手机", "upstream": "芯片"},
        {"product": "智能手机", "upstream": "电池"},
        {"product": "笔记本电脑", "upstream": "芯片"},
        {"product": "笔记本电脑", "upstream": "电池"},
        {"product": "智能电视", "upstream": "芯片"},
        {"product": "新能源汽车", "upstream": "电池"}
    ]
    
    for relation in upstream_relations:
        product_name = relation["product"]
        upstream_name = relation["upstream"]
        
        if product_name in products and upstream_name in products:
            # 检查关系是否已存在
            try:
                rel_exists = graph.run(
                    "MATCH (p1:product {name: $product})-[r:上游材料]->(p2:product {name: $upstream}) RETURN count(r) > 0 as exists",
                    {"product": product_name, "upstream": upstream_name}
                ).data()
                
                if rel_exists and rel_exists[0].get("exists", False):
                    print(f"产品上游关系已存在: {product_name} -> {upstream_name}")
                    continue
            except Exception as e:
                print(f"检查产品上游关系失败: {str(e)}")
            
            # 创建关系
            rel = Relationship(products[product_name], "上游材料", products[upstream_name])
            graph.create(rel)
            print(f"创建产品上游关系: {product_name} -> {upstream_name}")
    
    # 创建基础材料节点
    materials = {}
    material_names = ["硅片", "铝材", "塑料", "稀土", "锂矿"]
    
    for name in material_names:
        if name not in materials:
            # 检查节点是否已存在
            if name in existing_materials:
                # 获取已存在的节点
                material_node = graph.nodes.match("material", name=name).first()
                if material_node:
                    materials[name] = material_node
                    print(f"使用已存在的材料节点: {name}")
                    continue
            
            # 创建新节点
            material_node = Node("material", name=name)
            graph.create(material_node)
            materials[name] = material_node
            print(f"创建基础材料节点: {name}")
    
    # 创建材料上游关系
    material_relations = [
        {"product": "电池", "material": "锂矿"},
        {"product": "芯片", "material": "硅片"}
    ]
    
    for relation in material_relations:
        product_name = relation["product"]
        material_name = relation["material"]
        
        if product_name in products and material_name in materials:
            # 检查关系是否已存在
            try:
                rel_exists = graph.run(
                    "MATCH (p:product {name: $product})-[r:上游材料]->(m:material {name: $material}) RETURN count(r) > 0 as exists",
                    {"product": product_name, "material": material_name}
                ).data()
                
                if rel_exists and rel_exists[0].get("exists", False):
                    print(f"材料上游关系已存在: {product_name} -> {material_name}")
                    continue
            except Exception as e:
                print(f"检查材料上游关系失败: {str(e)}")
            
            # 创建关系
            rel = Relationship(products[product_name], "上游材料", materials[material_name])
            graph.create(rel)
            print(f"创建材料上游关系: {product_name} -> {material_name}")
    
    # 如果提供了companies参数，创建公司与产品的关系
    if companies:
        company_product_relations = [
            {"company": "华为", "product": "智能手机"},
            {"company": "华为", "product": "笔记本电脑"},
            {"company": "小米集团", "product": "智能手机"},
            {"company": "小米集团", "product": "智能电视"},
            {"company": "OPPO", "product": "智能手机"},
            {"company": "vivo", "product": "智能手机"},
            {"company": "TCL科技", "product": "智能电视"},
            {"company": "创维数字", "product": "智能电视"},
            {"company": "阿里巴巴", "product": "云服务"},
            {"company": "阿里巴巴", "product": "电商平台"},
            {"company": "腾讯控股", "product": "社交软件"},
            {"company": "腾讯控股", "product": "网络游戏"},
            {"company": "百度", "product": "搜索引擎"},
            {"company": "京东", "product": "电商平台"},
            {"company": "比亚迪", "product": "新能源汽车"},
            {"company": "比亚迪", "product": "电池"},
            {"company": "蔚来", "product": "新能源汽车"},
            {"company": "小鹏汽车", "product": "新能源汽车"},
            {"company": "理想汽车", "product": "新能源汽车"},
            {"company": "宁德时代", "product": "电池"},
            {"company": "亿纬锂能", "product": "电池"},
            {"company": "隆基绿能", "product": "光伏组件"},
            {"company": "晶科能源", "product": "光伏组件"},
            {"company": "中芯国际", "product": "芯片"},
            {"company": "韦尔股份", "product": "芯片"},
            {"company": "迈瑞医疗", "product": "医疗器械"},
            {"company": "万东医疗", "product": "医疗器械"},
            {"company": "康泰生物", "product": "疫苗"},
            {"company": "智飞生物", "product": "疫苗"},
            {"company": "君实生物", "product": "抗体药物"},
            {"company": "信达生物", "product": "抗体药物"},
        ]
        
        for relation in company_product_relations:
            company_name = relation["company"]
            product_name = relation["product"]
            
            if company_name in companies and product_name in products:
                # 检查关系是否已存在
                try:
                    rel_exists = graph.run(
                        "MATCH (c:company {name: $company})-[r:主营产品]->(p:product {name: $product}) RETURN count(r) > 0 as exists",
                        {"company": company_name, "product": product_name}
                    ).data()
                    
                    if rel_exists and rel_exists[0].get("exists", False):
                        print(f"公司产品关系已存在: {company_name} -> {product_name}")
                        continue
                except Exception as e:
                    print(f"检查公司产品关系失败: {str(e)}")
                
                # 创建关系
                rel = Relationship(companies[company_name], "主营产品", products[product_name])
                graph.create(rel)
                print(f"创建公司产品关系: {company_name} -> {product_name}")
    
    return products

def main():
    """主函数"""
    graph = connect_to_neo4j()
    if not graph:
        return
    
    # 不再清空数据库，保留原有数据
    # clear_database(graph)
    print("保留原有数据，仅添加新节点和关系")
    
    # 创建行业节点
    industries = create_industry_nodes(graph)
    
    # 创建公司节点
    companies = create_company_nodes(graph, industries)
    
    # 创建产品节点
    create_product_nodes(graph, companies)
    
    print("示例数据导入成功")

if __name__ == "__main__":
    main() 