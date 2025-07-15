# 知识图谱可视化系统

一个基于Neo4j和Streamlit的知识图谱可视化系统，支持企业、行业、产品之间关系的可视化展示。

## 功能特点

- **多种可视化方式**：支持交互式网络图、ECharts网络图、层级树、关系矩阵、产业链等多种可视化方式
- **灵活的数据导入**：支持JSON格式的数据导入，可自定义实体和关系
- **示例数据**：内置示例数据，包括阿里巴巴、腾讯、百度、华为、小米等公司及其相关行业和产品
- **多页面应用**：包含主页、数据导入、高级可视化等多个功能页面

## 系统要求

- Python 3.8+
- Neo4j数据库 (4.0+)
- 相关Python库 (见requirements.txt)

## 安装步骤

1. 克隆或下载本仓库
2. 安装Neo4j数据库 (https://neo4j.com/download/)
3. 安装Python依赖：

    ```bash
    pip install -r requirements.txt
    ```

4. 配置Neo4j连接信息 (config.py)
5. 运行应用：

            ```bash
# Windows
start_app.bat

# Linux/Mac
python -m streamlit run app.py
```

## 使用说明

### 主页

主页提供基本的知识图谱可视化功能：

1. 在左侧选择实体类型（公司、行业、产品）
2. 搜索并选择具体实体
3. 设置关系深度（1-3）
4. 选择可视化类型（交互式网络图或ECharts网络图）
5. 点击"生成可视化"按钮查看知识图谱

### 数据导入页面

数据导入页面提供了导入自定义数据的功能：

1. 上传JSON格式的节点和关系数据
2. 点击"导入数据"按钮将数据导入到Neo4j数据库
3. 或者点击"导入示例数据"按钮导入预设的示例数据

### 高级可视化页面

高级可视化页面提供了更多可视化类型：

1. 网络图：显示实体间的关系网络
2. 层级树：显示行业的层级结构（仅支持行业类型）
3. 关系矩阵：以矩阵形式展示实体间的关系
4. 产业链：展示产业链结构（仅支持行业类型）

## 数据格式

系统支持以下JSON格式的数据：

### 节点数据

- 公司节点：
```json
[
    {"name": "阿里巴巴", "description": "中国领先的电子商务公司"},
    {"name": "腾讯", "description": "中国领先的互联网服务提供商"}
]
```

- 行业节点：
```json
[
    {"name": "互联网", "description": "互联网行业"},
    {"name": "电子商务", "description": "电子商务行业"}
]
```

- 产品节点：
```json
[
    {"name": "淘宝", "description": "阿里巴巴旗下电子商务平台"},
    {"name": "微信", "description": "腾讯旗下社交通讯软件"}
]
```

### 关系数据

- 公司-行业关系：
```json
[
    {"company_name": "阿里巴巴", "industry_name": "互联网"},
    {"company_name": "阿里巴巴", "industry_name": "电子商务"}
]
```

- 公司-产品关系：
        ```json
[
    {"company_name": "阿里巴巴", "product_name": "淘宝"},
    {"company_name": "腾讯", "product_name": "微信"}
]
```

- 行业-行业关系：
```json
[
    {"from_industry": "电子商务", "to_industry": "互联网"},
    {"from_industry": "人工智能", "to_industry": "互联网"}
]
```

## 项目结构

```
ChainKnowledgeGraph/
├── app.py                 # 主应用入口
├── config.py              # 配置文件
├── requirements.txt       # 依赖列表
├── start_app.bat          # Windows启动脚本
├── pages/                 # 多页面应用页面
│   ├── 01_数据导入.py       # 数据导入页面
│   └── 02_高级可视化.py      # 高级可视化页面
├── utils/                 # 工具函数
│   ├── db_connector.py    # 数据库连接器
│   ├── data_processor.py  # 数据处理函数
│   └── logger.py          # 日志工具
├── visualizers/           # 可视化工具
│   └── network_viz.py     # 网络可视化函数
└── data/                  # 示例数据
    ├── company.json       # 公司数据
    ├── industry.json      # 行业数据
    └── product.json       # 产品数据
```

## 注意事项

- 确保Neo4j数据库已启动并且可以连接
- 默认连接信息为：bolt://localhost:7687，用户名neo4j，密码12345678
- 可以在config.py中修改连接信息
- 导入示例数据会清除数据库中的所有现有数据

## 许可证

MIT

