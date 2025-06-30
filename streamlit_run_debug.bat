@echo off
rem 设置控制台编码为UTF-8
chcp 65001 > nul
title Streamlit Debug Launcher

echo ======================================================
echo      Streamlit Debug Launcher
echo ======================================================
echo.
echo This script will start the Streamlit application in debug mode
echo to help diagnose connection issues.
echo.

rem 设置环境变量
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSSTDIO=utf-8
set STREAMLIT_SERVER_PORT=8501

rem 检查端口占用情况
echo Checking if port 8501 is already in use...
netstat -ano | findstr :8501
if %errorlevel% equ 0 (
    echo Port 8501 is already in use. Trying to free it...
    echo You may need to manually close applications using this port.
    echo Alternatively, you can change the port in this script (STREAMLIT_SERVER_PORT).
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
echo Starting Streamlit in debug mode...
echo Once started, try accessing: http://localhost:8501
echo.
echo If you can't connect, check for any error messages in this window.
echo.

rem 启动Streamlit，显示详细日志
python -m streamlit run kg_import_dashboard_windows.py --server.port=%STREAMLIT_SERVER_PORT% --server.headless=false --server.enableCORS=false --server.enableXsrfProtection=false --logger.level=info

echo.
echo Streamlit application has exited.
echo.
pause
exit /b 0 