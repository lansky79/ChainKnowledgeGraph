@echo off
chcp 65001 > nul
title 知识图谱数据导入可视化工具 - 启动器
color 0A
cls

echo ======================================================
echo           知识图谱数据导入可视化工具 - 启动器
echo ======================================================
echo.
echo 正在检查环境...

:: 设置虚拟环境路径
set VENV_NAME=pChainKnowledgeGraph

:: 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo [错误] Python未安装或未添加到PATH环境变量中。
    echo 请访问 https://www.python.org/downloads/ 下载并安装Python 3.8或更高版本。
    echo 安装时请勾选"Add Python to PATH"选项。
    echo.
    pause
    exit /b 1
)

:: 检查Neo4j是否运行 - 简化检查方式
echo 正在检查Neo4j数据库连接...
echo 注意：如果Neo4j未启动，应用可能无法正常工作。

:: 检查指定的虚拟环境是否存在
if not exist "%VENV_NAME%\Scripts\activate.bat" (
    color 0E
    echo [警告] 指定的虚拟环境不存在: %VENV_NAME%
    echo 是否要创建此虚拟环境？(Y/N): 
    set /p create_venv=
    if /i "%create_venv%" == "Y" (
        echo 正在创建虚拟环境 %VENV_NAME%...
        python -m venv %VENV_NAME%
        if %errorlevel% neq 0 (
            color 0C
            echo [错误] 创建虚拟环境失败。
            pause
            exit /b 1
        )
    ) else (
        echo 操作已取消。
        pause
        exit /b 1
    )
)

:: 激活指定的虚拟环境
echo 正在激活虚拟环境: %VENV_NAME%
call "%VENV_NAME%\Scripts\activate.bat"
if %errorlevel% neq 0 (
    color 0C
    echo [错误] 激活虚拟环境失败。
    pause
    exit /b 1
)

:: 检查是否已安装依赖
pip show streamlit >nul 2>&1
if %errorlevel% neq 0 (
    echo 正在安装依赖包...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        color 0C
        echo [错误] 安装依赖包失败。
        echo 详细错误信息：
        pip install -r requirements.txt
        pause
        exit /b 1
    )
)

:: 检查配置文件是否存在
if not exist "config_windows.json" (
    echo 配置文件不存在，正在创建Windows专用配置...
    (
        echo {
        echo     "neo4j": {
        echo         "uri": "bolt://127.0.0.1:7687",
        echo         "username": "neo4j",
        echo         "password": "12345678"
        echo     },
        echo     "app": {
        echo         "title": "知识图谱数据导入可视化工具 - Windows版",
        echo         "theme": "light",
        echo         "batch_size_default": 10000,
        echo         "batch_size_min": 1000,
        echo         "batch_size_max": 50000,
        echo         "refresh_interval": 60,
        echo         "show_logo": true,
        echo         "windows_mode": true
        echo     },
        echo     "data_paths": {
        echo         "import_state": "data\\import_state.pkl",
        echo         "company": "data\\company.json",
        echo         "industry": "data\\industry.json",
        echo         "product": "data\\product.json",
        echo         "company_industry": "data\\company_industry.json",
        echo         "industry_industry": "data\\industry_industry.json",
        echo         "company_product": "data\\company_product.json",
        echo         "product_product": "data\\product_product.json"
        echo     },
        echo     "windows_settings": {
        echo         "use_cmd": true,
        echo         "browser_path": "",
        echo         "neo4j_path": "C:\\Program Files\\Neo4j Desktop\\Neo4j Desktop.exe",
        echo         "log_path": "logs\\app.log",
        echo         "auto_start_browser": true,
        echo         "auto_start_neo4j": false,
        echo         "theme_color": "#4CAF50",
        echo         "disable_progress_animation": true
        echo     }
        echo }
    ) > config_windows.json
)

:: 检查数据目录是否存在
if not exist "data\" (
    echo 创建数据目录...
    mkdir data
)

:: 检查日志目录是否存在
if not exist "logs\" (
    echo 创建日志目录...
    mkdir logs
)

:: 启动Streamlit应用
cls
color 0A
echo ======================================================
echo           知识图谱数据导入可视化工具 - 启动中
echo ======================================================
echo.
echo 正在启动应用，请稍候...
echo 应用启动后将自动打开浏览器。
echo.
echo 如果浏览器没有自动打开，请手动访问: http://localhost:8501
echo.
echo 按 Ctrl+C 可以停止应用运行。
echo ======================================================
echo.

:: 使用start命令启动浏览器
timeout /t 3 >nul
start "" http://localhost:8501

:: 直接在当前窗口运行Python脚本
echo 正在启动应用，如果出现错误将显示在下方...
python -u kg_import_dashboard_windows.py
set ERRORLEVEL_PYTHON=%errorlevel%

:: 如果应用异常退出
if %ERRORLEVEL_PYTHON% neq 0 (
    color 0C
    echo.
    echo [错误] 应用启动失败，错误代码: %ERRORLEVEL_PYTHON%
    echo.
    echo 请检查以上错误信息并解决问题。
) else (
    color 0E
    echo.
    echo 应用已退出。
)

echo.
echo 按任意键关闭此窗口...
pause > nul 