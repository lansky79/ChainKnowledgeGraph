import json
import os

# 确保data目录存在
os.makedirs('data', exist_ok=True)

# 公司数据 - 华为
companies = [
    {"name": "华为", "fullname": "华为技术有限公司", "description": "全球领先的通信设备制造商"}
]

# 行业数据 - 互联网
industries = [
    {"name": "互联网", "code": "900000", "description": "提供互联网服务和产品的行业"}
]

# 产品数据 - 华为手机系列 (减少数量，按类型分组)
products = [
    {"name": f"华为Mate {i}", "type": "Mate系列", "description": f"华为Mate系列第{i}代旗舰手机"} for i in range(10, 15)
] + [
    {"name": f"华为P {i}", "type": "P系列", "description": f"华为P系列第{i}代拍照手机"} for i in range(20, 25)
] + [
    {"name": f"华为nova {i}", "type": "nova系列", "description": f"华为nova系列第{i}代时尚手机"} for i in range(5, 10)
]

# 公司-行业关系数据 - 使用company_name和industry_name字段
company_industry_relations = [
    {"company_name": "华为", "industry_name": "互联网", "relation_type": "所属行业"}
]

# 公司-产品关系数据 - 使用company_name和product_name字段
company_product_relations = [
    {"company_name": "华为", "product_name": p["name"], "relation_type": "主营产品"} for p in products
]

def write_jsonl(filename, data):
    """将数据写入JSONL文件（每行一个JSON对象）"""
    with open(filename, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

def write_json_array(filename, data):
    """将数据写入JSON数组文件（整个文件是一个JSON数组）"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    # 写入各类数据文件 - 使用JSON数组格式（前端可能需要这种格式）
    write_json_array('data/company.json', companies)
    write_json_array('data/industry.json', industries)
    write_json_array('data/product.json', products)
    write_json_array('data/company_industry.json', company_industry_relations)
    write_json_array('data/company_product.json', company_product_relations)
    
    # 同时生成JSONL格式的文件，以便与其他导入的数据兼容
    write_jsonl('data/company.jsonl', companies)
    write_jsonl('data/industry.jsonl', industries)
    write_jsonl('data/product.jsonl', products)
    write_jsonl('data/company_industry.jsonl', company_industry_relations)
    write_jsonl('data/company_product.jsonl', company_product_relations)
    
    # 输出文件信息
    print(f"已生成以下数据文件:")
    print(f"- 公司数据: data/company.json ({len(companies)}个节点)")
    print(f"- 行业数据: data/industry.json ({len(industries)}个节点)")
    print(f"- 产品数据: data/product.json ({len(products)}个节点)")
    print(f"- 公司-行业关系: data/company_industry.json ({len(company_industry_relations)}条关系)")
    print(f"- 公司-产品关系: data/company_product.json ({len(company_product_relations)}条关系)")
    print("\n同时生成了对应的JSONL格式文件（.jsonl后缀），可以用于与其他JSONL格式数据兼容。")
    print("\n这些文件可以在前端'数据导入'页面上传。")