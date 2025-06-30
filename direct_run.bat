@echo off
rem 设置控制台编码为UTF-8
chcp 65001 > nul
title Knowledge Graph Import Tool - Direct Launch

rem 设置环境变量
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSSTDIO=utf-8

echo ======================================================
echo     Knowledge Graph Import Tool - Direct Launch
echo ======================================================
echo.
echo This script will directly launch the Streamlit app
echo.

rem 读取配置文件中的Neo4j路径
echo Reading configuration...
python -c "import json; config = json.load(open('config_windows.json', 'r', encoding='utf-8')); print(config['windows_settings']['neo4j_path'])" > neo4j_path.txt
set /p NEO4J_PATH=<neo4j_path.txt
del neo4j_path.txt

rem 设置Neo4j默认路径
if "%NEO4J_PATH%"=="" (
    echo Neo4j path not found in config, using default paths...
    set "NEO4J_DESKTOP=C:\Program Files\Neo4j Desktop\Neo4j Desktop.exe"
    set "NEO4J_HOME=C:\Users\franc\Downloads\neo4j-chs-community-5.26.0-windows"
    set NEO4J_SERVICE=neo4j
) else (
    echo Using Neo4j path from config: %NEO4J_PATH%
    set "NEO4J_DESKTOP=%NEO4J_PATH%"
    set "NEO4J_HOME=C:\Users\franc\Downloads\neo4j-chs-community-5.26.0-windows"
    set NEO4J_SERVICE=neo4j
)

rem 尝试连接Neo4j，检查是否已经运行
echo Checking if Neo4j is already running...
python check_neo4j_connection.py
set NEO4J_RUNNING_CODE=%errorlevel%

rem 如果Neo4j未运行，尝试启动它
if %NEO4J_RUNNING_CODE% neq 0 (
    echo Neo4j is not running. Attempting to start...
    
    rem 方法1: 尝试通过Windows服务启动
    echo Method 1: Trying to start via Windows Service...
    sc query %NEO4J_SERVICE% >nul 2>&1
    if %errorlevel% equ 0 (
        echo Neo4j service found, attempting to start...
        net start %NEO4J_SERVICE% >nul 2>&1
        if %errorlevel% equ 0 (
            echo Neo4j service started successfully!
            goto :check_connection
        ) else (
            echo Failed to start Neo4j service.
        )
    ) else (
        echo Neo4j service not found.
    )
    
    rem 方法2: 尝试通过Neo4j Desktop启动
    echo Method 2: Trying to start via Neo4j Desktop...
    if exist "%NEO4J_DESKTOP%" (
        echo Neo4j Desktop found at %NEO4J_DESKTOP%
        echo Starting Neo4j Desktop, please manually start your database...
        start "" "%NEO4J_DESKTOP%"
        echo Waiting 10 seconds for you to start the database...
        timeout /t 10 /nobreak > nul
        goto :check_connection
    ) else (
        echo Neo4j Desktop not found at %NEO4J_DESKTOP%
    )
    
    rem 方法3: 尝试通过命令行启动
    echo Method 3: Trying to start via command line...
    if exist "%NEO4J_HOME%\bin\neo4j.bat" (
        echo Neo4j installation found at %NEO4J_HOME%
        echo Stopping any running Neo4j instances...
        "%NEO4J_HOME%\bin\neo4j.bat" stop 2>nul
        echo Starting Neo4j server...
        start "Neo4j Server" cmd /c ""%NEO4J_HOME%\bin\neo4j.bat" console"
        echo Waiting 20 seconds for Neo4j to start...
        timeout /t 20 /nobreak > nul
        goto :check_connection
    ) else (
        echo Neo4j installation not found at %NEO4J_HOME%
    )
    
    echo All automatic startup methods failed.
    echo Please start Neo4j manually before continuing.
    choice /C YN /M "Do you want to continue without Neo4j"
    if %errorlevel% equ 2 (
        echo Operation cancelled.
        exit /b 1
    )
)

:check_connection
echo Checking Neo4j connection...
python check_neo4j_connection.py
if %errorlevel% neq 0 (
    echo [WARNING] Cannot connect to Neo4j database. Make sure Neo4j is running.
    echo.
    echo Note: The application can still be launched, but you will not be able
    echo       to import data until Neo4j is running and accessible.
    echo.
    echo Do you want to continue anyway? (Y/N)
    set /p continue_choice=
    if /i not "%continue_choice%"=="Y" (
        echo Operation cancelled
        pause
        exit /b 1
    )
)

rem 检查streamlit是否安装
python -c "import streamlit" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Streamlit not detected, attempting to install...
    pip install streamlit pandas numpy plotly py2neo tqdm pillow
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install Streamlit
        pause
        exit /b 1
    )
)

rem 检查文件是否存在
if not exist "kg_import_dashboard_windows.py" (
    echo [ERROR] kg_import_dashboard_windows.py not found
    echo Please ensure this file exists in the current directory
    pause
    exit /b 1
)

echo After launch, please visit: http://localhost:8501
echo Press Ctrl+C to stop the application
echo.

rem 打开浏览器
echo Opening browser...
start http://localhost:8501

rem 直接启动Streamlit
echo Launching application...
python -m streamlit run kg_import_dashboard_windows.py --server.headless=true

rem 如果Streamlit退出，等待用户按键
echo Application has exited
pause
exit /b 0 