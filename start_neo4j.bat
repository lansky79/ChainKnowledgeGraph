@echo off
rem 设置控制台编码为UTF-8
chcp 65001 > nul
title Neo4j Database Starter

echo ======================================================
echo              Neo4j Database Starter
echo ======================================================
echo.
echo This script will start your Neo4j database.
echo Please wait until the database is fully started before
echo running the knowledge graph application.
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

rem 如果Neo4j已经运行，询问是否重启
if %NEO4J_RUNNING_CODE% equ 0 (
    echo Neo4j is already running.
    choice /C YN /M "Do you want to restart Neo4j"
    if %errorlevel% equ 1 (
        echo Stopping Neo4j before restart...
        
        rem 尝试停止服务
        sc query %NEO4J_SERVICE% >nul 2>&1
        if %errorlevel% equ 0 (
            net stop %NEO4J_SERVICE% >nul 2>&1
        )
        
        rem 尝试停止命令行版本
        if exist "%NEO4J_HOME%\bin\neo4j.bat" (
            "%NEO4J_HOME%\bin\neo4j.bat" stop 2>nul
        )
        
        echo Neo4j stopped.
        goto :start_neo4j
    ) else (
        echo Neo4j will continue running.
        goto :check_connection
    )
)

:start_neo4j
echo Neo4j is not running. Starting Neo4j...

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
    echo Neo4j service not found or cannot be queried.
)

rem 方法2: 尝试通过Neo4j Desktop启动
echo Method 2: Trying to start via Neo4j Desktop...
if exist "%NEO4J_DESKTOP%" (
    echo Neo4j Desktop found at %NEO4J_DESKTOP%
    echo Starting Neo4j Desktop, please manually start your database...
    start "" "%NEO4J_DESKTOP%"
    echo Waiting for you to start the database...
    pause
    goto :check_connection
) else (
    echo Neo4j Desktop not found at %NEO4J_DESKTOP%
)

rem 方法3: 尝试通过命令行启动
echo Method 3: Trying to start via command line...
if exist "%NEO4J_HOME%\bin\neo4j.bat" (
    echo Neo4j installation found at %NEO4J_HOME%
    echo Starting Neo4j server in a new window...
    echo (The Neo4j server window must remain open for the database to run)
    start "Neo4j Server" cmd /c ""%NEO4J_HOME%\bin\neo4j.bat" console"
    echo Waiting 20 seconds for Neo4j to start...
    timeout /t 20 /nobreak > nul
    goto :check_connection
) else (
    echo Neo4j installation not found at %NEO4J_HOME%
)

echo All automatic startup methods failed.
echo.
echo Please try one of the following:
echo 1. Start Neo4j Desktop manually and start your database
echo 2. Start Neo4j service from Windows Services
echo 3. Navigate to your Neo4j installation and run 'bin\neo4j.bat console'
echo.
echo Press any key to exit...
pause > nul
exit /b 1

:check_connection
echo Checking final Neo4j connection...
python check_neo4j_connection.py
if %errorlevel% neq 0 (
    echo [WARNING] Cannot connect to Neo4j database.
    echo Please ensure Neo4j is properly configured with:
    echo   - URL: bolt://127.0.0.1:7687
    echo   - Username: neo4j
    echo   - Password: 12345678
    echo.
    echo You can now try to run the main application with direct_run.bat
    echo.
    echo Press any key to exit...
    pause > nul
    exit /b 1
)

echo.
echo ======================================================
echo Neo4j database is now running!
echo.
echo You can now run the main application:
echo   direct_run.bat
echo.
echo IMPORTANT: Keep this window open if you started Neo4j
echo           via command line (Method 3).
echo ======================================================
echo.
echo Press any key to exit this starter script...
pause > nul
exit /b 0 