@echo off
rem 设置控制台编码为UTF-8
chcp 65001 > nul
title Streamlit Only - Knowledge Graph Tool

echo ======================================================
echo     Streamlit Only - Knowledge Graph Tool
echo ======================================================
echo.
echo This script will ONLY start the Streamlit application
echo without checking Neo4j connection.
echo.
echo NOTE: Some features requiring Neo4j will not work
echo       until Neo4j is properly connected.
echo.

rem 设置环境变量
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSSTDIO=utf-8
set STREAMLIT_SERVER_PORT=8502

rem 检查端口占用情况
echo Checking if port 8502 is already in use...
netstat -ano | findstr :8502
if %errorlevel% equ 0 (
    echo Port 8502 is already in use.
    echo Using alternative port: 8503
    set STREAMLIT_SERVER_PORT=8503
)

rem 检查文件是否存在
if not exist "kg_import_dashboard_windows.py" (
    echo [ERROR] kg_import_dashboard_windows.py not found
    echo Please ensure this file exists in the current directory
    pause
    exit /b 1
)

rem 检查streamlit是否安装
python -c "import streamlit" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing Streamlit and required packages...
    pip install streamlit pandas numpy plotly py2neo tqdm pillow watchdog
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install required packages
        pause
        exit /b 1
    )
)

echo.
echo Starting Streamlit application on port %STREAMLIT_SERVER_PORT%...
echo.
echo Once started, open your browser and go to:
echo http://localhost:%STREAMLIT_SERVER_PORT%
echo.
echo Press Ctrl+C to stop the application when done
echo.

rem 启动浏览器
start http://localhost:%STREAMLIT_SERVER_PORT%

rem 启动Streamlit
python -m streamlit run kg_import_dashboard_windows.py --server.port=%STREAMLIT_SERVER_PORT% --server.headless=true

echo.
echo Streamlit application has exited.
echo.
pause
exit /b 0 