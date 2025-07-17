# 知识图谱功能扩展设计文档

## 概述

本设计文档基于现有的知识图谱可视化系统架构，详细规划了六个主要功能扩展的技术实现方案。设计遵循现有的技术栈（Streamlit + Neo4j + Python），确保新功能与现有系统的无缝集成。

## 架构

### 现有架构分析
- **前端框架**: Streamlit (Python Web框架)
- **数据库**: Neo4j (图数据库)
- **可视化**: Pyvis, ECharts, Streamlit组件
- **项目结构**: 
  - `app.py` - 主应用入口
  - `pages/` - 多页面应用
  - `utils/` - 工具模块 (db_connector, data_processor, logger)
  - `visualizers/` - 可视化模块

### 扩展架构设计
```
knowledge-graph-system/
├── app.py (主页 - 重命名为"图谱主页")
├── pages/
│   ├── 01_数据导入.py
│   ├── 02_高级可视化.py
│   ├── 03_智能搜索.py (新增)
│   ├── 04_数据分析.py (新增)
│   ├── 05_实体管理.py (新增)
│   └── 06_高级查询.py (新增)
├── utils/
│   ├── search_engine.py (新增)
│   ├── analytics.py (新增)
│   ├── export_handler.py (新增)
│   └── query_builder.py (新增)
├── components/
│   ├── entity_detail.py (新增)
│   ├── search_widget.py (新增)
│   └── chart_components.py (新增)
└── static/ (新增)
    └── exports/ (导出文件存储)
```

## 组件和接口

### 1. 智能搜索与推荐系统

#### 核心组件
- **SearchEngine类** (`utils/search_engine.py`)
  - `fuzzy_search(query, entity_type=None)` - 模糊搜索
  - `get_recommendations(entity_name, limit=5)` - 获取推荐
  - `get_similar_entities(entity_name, similarity_threshold=0.7)` - 相似实体
  - `update_search_history(user_session, entity_name)` - 更新搜索历史

#### 数据模型
```python
# 搜索结果模型
SearchResult = {
    "entity_name": str,
    "entity_type": str,
    "relevance_score": float,
    "description": str
}

# 推荐结果模型
Recommendation = {
    "entity_name": str,
    "entity_type": str,
    "relation_type": str,
    "confidence_score": float
}
```

#### 实现策略
- 使用Neo4j的全文索引进行快速搜索
- 基于图结构计算实体相似度
- 利用关系权重进行推荐排序
- 使用Streamlit session_state存储搜索历史

### 2. 数据统计与分析面板

#### 核心组件
- **Analytics类** (`utils/analytics.py`)
  - `get_node_statistics()` - 节点统计
  - `get_relationship_statistics()` - 关系统计
  - `calculate_centrality_metrics()` - 中心性指标
  - `generate_trend_data()` - 趋势数据
  - `create_distribution_charts()` - 分布图表

#### 图表组件
- **ChartComponents类** (`components/chart_components.py`)
  - `create_pie_chart(data, title)` - 饼图
  - `create_bar_chart(data, title)` - 柱状图
  - `create_line_chart(data, title)` - 折线图
  - `create_heatmap(data, title)` - 热力图

#### 分析指标
- 节点度分布
- 关系类型分布
- 连通性分析
- 中心性排名
- 数据增长趋势

### 3. 导出与分享功能

#### 核心组件
- **ExportHandler类** (`utils/export_handler.py`)
  - `export_graph_image(nodes, edges, format='png')` - 导出图像
  - `export_data(query_result, format='json')` - 导出数据
  - `generate_report(entity_name, include_stats=True)` - 生成报告
  - `create_share_link(graph_config)` - 创建分享链接

#### 导出格式支持
- **图像**: PNG, SVG, PDF
- **数据**: JSON, CSV, Excel
- **报告**: HTML, PDF (包含图表和统计)

#### 分享机制
- 生成唯一的分享ID
- 将图谱配置存储到数据库
- 创建临时访问链接
- 支持链接过期设置

### 4. 实体详情与管理

#### 核心组件
- **EntityDetail类** (`components/entity_detail.py`)
  - `display_entity_info(entity_id)` - 显示实体信息
  - `edit_entity_form(entity_id)` - 编辑表单
  - `manage_relationships(entity_id)` - 关系管理
  - `batch_operations(entity_ids, operation)` - 批量操作

#### 管理功能
- 实体属性编辑
- 关系添加/删除/修改
- 批量标签管理
- 数据验证和约束检查

#### 安全机制
- 操作确认对话框
- 数据备份机制
- 操作日志记录
- 权限验证（如需要）

### 5. 高级查询构建器

#### 核心组件
- **QueryBuilder类** (`utils/query_builder.py`)
  - `build_visual_query(conditions)` - 可视化查询构建
  - `validate_cypher_query(query)` - Cypher查询验证
  - `save_query_template(name, query)` - 保存查询模板
  - `execute_custom_query(query, params)` - 执行自定义查询

#### 查询界面
- 条件选择器（实体类型、属性、关系）
- 逻辑操作符（AND, OR, NOT）
- Cypher代码编辑器
- 查询结果预览

#### 模板管理
- 常用查询模板库
- 用户自定义模板
- 模板分享功能

### 6. 系统优化与用户体验

#### 性能优化
- **分页加载**: 大数据集分批加载
- **缓存机制**: 使用`@st.cache_data`缓存查询结果
- **异步处理**: 长时间操作使用进度条
- **索引优化**: 为常用查询字段创建索引

#### 用户体验
- **响应式设计**: 适配不同屏幕尺寸
- **加载状态**: 使用`st.spinner`和进度条
- **错误处理**: 友好的错误信息和建议
- **帮助系统**: 内置操作指南和提示

## 数据模型

### 扩展的Neo4j数据模型

```cypher
// 添加搜索历史节点
CREATE (sh:SearchHistory {
    session_id: string,
    entity_name: string,
    search_time: datetime,
    entity_type: string
})

// 添加查询模板节点
CREATE (qt:QueryTemplate {
    name: string,
    query: string,
    description: string,
    created_by: string,
    created_time: datetime,
    is_public: boolean
})

// 添加分享配置节点
CREATE (sc:ShareConfig {
    share_id: string,
    graph_config: string,
    created_time: datetime,
    expires_at: datetime,
    access_count: integer
})

// 为现有节点添加统计属性
ALTER (c:company) SET c.view_count = 0, c.last_accessed = datetime()
ALTER (i:industry) SET i.view_count = 0, i.last_accessed = datetime()
ALTER (p:product) SET p.view_count = 0, p.last_accessed = datetime()
```

### 新增索引

```cypher
// 创建全文搜索索引
CREATE FULLTEXT INDEX entity_search_index 
FOR (n:company|industry|product) 
ON EACH [n.name, n.description]

// 创建属性索引
CREATE INDEX entity_name_index FOR (n:company) ON (n.name)
CREATE INDEX entity_name_index FOR (n:industry) ON (n.name)
CREATE INDEX entity_name_index FOR (n:product) ON (n.name)
```

## 错误处理

### 错误类型和处理策略

1. **数据库连接错误**
   - 显示友好的连接失败信息
   - 提供重试机制
   - 记录详细错误日志

2. **查询执行错误**
   - 验证查询语法
   - 显示具体错误位置
   - 提供查询建议

3. **导出错误**
   - 检查文件权限
   - 验证数据格式
   - 提供备选方案

4. **性能问题**
   - 查询超时处理
   - 大数据集分页
   - 内存使用监控

## 测试策略

### 单元测试
- 各工具类的核心方法测试
- 数据处理逻辑测试
- 查询构建器测试

### 集成测试
- 数据库连接测试
- 页面功能测试
- 导出功能测试

### 性能测试
- 大数据集加载测试
- 复杂查询性能测试
- 并发访问测试

### 用户体验测试
- 界面响应性测试
- 错误处理测试
- 移动端适配测试

## 部署考虑

### 环境要求
- Python 3.8+
- Neo4j 4.0+
- 足够的磁盘空间用于导出文件
- 内存建议8GB+（处理大型图谱）

### 配置管理
- 扩展现有的`config.py`
- 添加新功能的配置选项
- 支持环境变量配置

### 监控和日志
- 扩展现有的日志系统
- 添加性能监控
- 用户操作审计日志