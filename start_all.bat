@echo off
rem 设置控制台编码为UTF-8
chcp 65001 > nul
title Knowledge Graph All-in-One Launcher

echo ======================================================
echo      Knowledge Graph All-in-One Launcher
echo ======================================================
echo.
echo This script will start both Neo4j database and the
echo Knowledge Graph application in sequence.
echo.
echo [Step 1/2] Starting Neo4j database...

rem 读取配置文件中的Neo4j路径
echo Reading configuration...
python -c "import json; config = json.load(open('config_windows.json', 'r', encoding='utf-8')); print(config['windows_settings']['neo4j_path'])" > neo4j_path.txt
set /p NEO4J_PATH=<neo4j_path.txt
del neo4j_path.txt

rem 设置Neo4j路径
set "NEO4J_HOME=C:\Users\franc\Downloads\neo4j-chs-community-5.26.0-windows"
set NEO4J_SERVICE=neo4j
set "NEO4J_DESKTOP=%NEO4J_PATH%"

rem 尝试连接Neo4j，检查是否已经运行
echo Checking if Neo4j is already running...
python check_neo4j_connection.py
set NEO4J_RUNNING_CODE=%errorlevel%

rem 如果Neo4j未运行，尝试启动
if %NEO4J_RUNNING_CODE% neq 0 (
    echo Neo4j is not running. Attempting to start...
    
    rem 方法1: 尝试通过Windows服务启动
    sc query %NEO4J_SERVICE% >nul 2>&1
    if %errorlevel% equ 0 (
        echo Starting Neo4j service...
        net start %NEO4J_SERVICE% >nul 2>&1
        if %errorlevel% equ 0 (
            echo Neo4j service started successfully!
            goto :neo4j_started
        )
    )
    
    rem 方法2: 尝试通过Neo4j Desktop启动
    if exist "%NEO4J_DESKTOP%" (
        echo Starting Neo4j via Desktop...
        start "" "%NEO4J_DESKTOP%"
        echo Waiting 15 seconds for you to start the database...
        timeout /t 15 /nobreak > nul
        goto :neo4j_started
    )
    
    rem 方法3: 尝试通过命令行启动
    if exist "%NEO4J_HOME%\bin\neo4j.bat" (
        echo Starting Neo4j via command line...
        start "Neo4j Server" cmd /c ""%NEO4J_HOME%\bin\neo4j.bat" console"
        echo Waiting 20 seconds for Neo4j to start...
        timeout /t 20 /nobreak > nul
        goto :neo4j_started
    )
    
    echo Could not start Neo4j automatically.
    echo Please run start_neo4j.bat first, then run direct_run.bat
    echo.
    echo Press any key to exit...
    pause > nul
    exit /b 1
)

:neo4j_started
echo.
echo [Step 2/2] Starting Knowledge Graph application...
echo.

rem 检查streamlit是否安装
python -c "import streamlit" >nul 2>&1
if %errorlevel% neq 0 (
    echo Streamlit not detected, installing required packages...
    pip install streamlit pandas numpy plotly py2neo tqdm pillow
)

rem 检查主应用文件是否存在
if not exist "kg_import_dashboard_windows.py" (
    echo Error: kg_import_dashboard_windows.py not found
    echo Please ensure this file exists in the current directory
    pause
    exit /b 1
)

rem 打开浏览器并启动应用
echo Opening browser and starting application...
start http://localhost:8501
echo.
echo Application starting...
echo Visit http://localhost:8501 in your browser
echo Press Ctrl+C in this window to stop the application when done
echo.

python -m streamlit run kg_import_dashboard_windows.py --server.headless=true

echo.
echo Application has exited.
echo IMPORTANT: If you started Neo4j via command line, make sure
echo            to close the Neo4j console window when done.
echo.
pause
exit /b 0 