# 知识图谱数据导入可视化工具 - Windows版使用指南

## 系统要求

- Windows 10或更高版本
- Python 3.8或更高版本
- Neo4j数据库 (社区版或企业版)

## 快速开始

我们提供了多种启动方式，满足不同用户的需求：

### 方式1: 一键启动（推荐新用户）

双击运行 `start_all.bat` 批处理文件，该文件会：
1. 自动启动Neo4j数据库（如果未运行）
2. 启动知识图谱数据导入可视化工具
3. 自动打开浏览器访问应用程序

### 方式2: 分步启动（适合高级用户）

1. 首先运行 `start_neo4j.bat` 启动Neo4j数据库
2. 然后运行 `direct_run.bat` 启动应用程序

### 方式3: 简化启动（适合已经启动Neo4j的用户）

如果您已经手动启动了Neo4j数据库，可以直接运行 `direct_run.bat` 启动应用程序。

## 批处理文件说明

### start_all.bat
- 一键启动批处理文件
- 自动启动Neo4j和应用程序
- 适合大多数用户

### start_neo4j.bat
- 专门用于启动Neo4j数据库
- 支持三种启动方式：Windows服务、Neo4j Desktop和命令行
- 会检测Neo4j连接是否成功

### direct_run.bat
- 直接启动知识图谱数据导入可视化工具
- 检查Neo4j连接状态，但不会自动启动Neo4j
- 会自动打开浏览器

### run_streamlit_simple.bat
- 简化版启动器
- 适合已经熟悉系统的用户

## Neo4j连接配置

默认配置：
- URL: `bolt://127.0.0.1:7687`
- 用户名: `neo4j`
- 密码: `12345678`

如需修改连接配置，请编辑 `config_windows.json` 文件中的 `neo4j` 部分。

## 常见问题

### 无法启动Neo4j

如果自动启动Neo4j失败，请尝试以下方法：

1. **通过Neo4j Desktop启动**
   - 打开Neo4j Desktop应用
   - 选择您的数据库，点击"Start"按钮

2. **通过Windows服务启动**
   - 按Win+R打开运行对话框
   - 输入`services.msc`并按回车
   - 找到Neo4j服务，右键选择"启动"

3. **通过命令行启动**
   - 打开命令提示符或PowerShell
   - 导航到Neo4j安装目录的bin文件夹
   - 执行`neo4j.bat console`命令

### 应用程序无法连接到Neo4j

请确保：
1. Neo4j数据库已经成功启动
2. 连接参数（URL、用户名、密码）正确
3. 没有防火墙或安全软件阻止连接

### 其他问题

如遇其他问题，请查看 `logs/app.log` 日志文件，了解详细错误信息。

## 高级配置

可以通过编辑 `config_windows.json` 文件来自定义应用程序行为，包括：

- Neo4j连接参数
- 批量导入大小
- 界面主题
- 自动启动选项
- 日志配置

## 注意事项

- 使用命令行方式启动Neo4j时，需要保持Neo4j控制台窗口打开
- 关闭应用程序时，记得同时关闭Neo4j（如果不再需要）
- 首次运行可能需要等待较长时间安装依赖

## 功能特点

1. **导入进度仪表盘**
   - 总体导入进度显示
   - 节点和关系的详细导入状态
   - 各类型数据的导入进度可视化

2. **数据分布统计**
   - 节点类型分布饼图
   - 关系类型分布饼图
   - 已导入/未导入数据对比图

3. **导入历史记录**
   - 导入操作历史表格
   - 导入数据量趋势图
   - 导入速度趋势图

4. **操作控制面板**
   - 批次大小控制
   - 导入操作执行
   - 导入状态重置
   - 日志查看

## 配置说明

Windows版本使用专用的配置文件 `config_windows.json`：

```json
{
    "neo4j": {
        "uri": "bolt://127.0.0.1:7687",
        "username": "neo4j",
        "password": "12345678"
    },
    "app": {
        "title": "知识图谱数据导入可视化工具 - Windows版",
        "theme": "light",
        "batch_size_default": 10000,
        "batch_size_min": 1000,
        "batch_size_max": 50000,
        "refresh_interval": 60,
        "show_logo": true,
        "windows_mode": true
    },
    "data_paths": {
        "import_state": "data\\import_state.pkl",
        "company": "data\\company.json",
        "industry": "data\\industry.json",
        "product": "data\\product.json",
        "company_industry": "data\\company_industry.json",
        "industry_industry": "data\\industry_industry.json",
        "company_product": "data\\company_product.json",
        "product_product": "data\\product_product.json"
    },
    "windows_settings": {
        "use_cmd": true,
        "browser_path": "",
        "neo4j_path": "C:\\Program Files\\Neo4j Desktop\\Neo4j Desktop.exe",
        "log_path": "logs\\app.log",
        "auto_start_browser": true,
        "auto_start_neo4j": false,
        "theme_color": "#4CAF50",
        "disable_progress_animation": true
    }
}
```

## 目录结构

```
知识图谱数据导入可视化工具/
│
├── build_graph.py           # 图谱构建核心代码
├── kg_import_dashboard.py   # 通用仪表盘
├── kg_import_dashboard_windows.py  # Windows专用仪表盘
├── config.json              # 通用配置文件
├── config_windows.json      # Windows专用配置文件
├── requirements.txt         # 依赖包列表
├── README.md                # 通用说明文档
├── README_WINDOWS.md        # Windows专用说明文档
├── start_dashboard.bat      # 通用启动脚本
├── start_dashboard_windows.bat  # Windows专用启动脚本
├── install_windows.bat      # Windows安装向导
│
├── data/                    # 数据目录
│   ├── company.json
│   ├── industry.json
│   ├── product.json
│   ├── company_industry.json
│   ├── industry_industry.json
│   ├── company_product.json
│   ├── product_product.json
│   └── import_state.pkl     # 导入状态记录
│
└── logs/                    # 日志目录
    └── app.log              # 应用日志
```

## 常见问题解答

### 1. 应用启动失败，提示"Python未安装"

确保已安装Python 3.8或更高版本，并且已将Python添加到PATH环境变量中。可以通过在命令提示符中运行`python --version`来验证。

### 2. 无法连接到Neo4j数据库

确保Neo4j数据库已启动并且可以访问。默认配置使用`bolt://127.0.0.1:7687`连接本地Neo4j数据库。如果您的Neo4j数据库使用不同的地址或凭据，请修改`config_windows.json`文件。

### 3. 导入过程中出现错误

查看应用日志（`logs/app.log`）以获取详细的错误信息。常见的错误原因包括：
- 数据文件格式不正确
- Neo4j数据库连接问题
- 内存不足

### 4. PowerShell中运行脚本时出现特殊字符解析错误

Windows版本专门解决了这个问题。请使用提供的`start_dashboard_windows.bat`脚本启动应用，而不是直接在PowerShell中运行Python脚本。

### 5. 如何重置导入状态

在应用的"操作控制面板"标签页中，点击"重置导入状态"按钮，然后确认操作。这将清除所有导入进度记录。

## 许可证

MIT 