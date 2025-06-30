@echo off
rem 设置控制台编码为UTF-8
chcp 65001 > nul
title Knowledge Graph Import Tool - Simple Version

echo ======================================================
echo    Knowledge Graph Import Tool - Simple Version
echo ======================================================
echo.
echo Starting simplified Streamlit application...
echo This script will launch Streamlit directly, skipping complex environment checks
echo.

:: 设置环境变量，确保Python正确处理字符
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSSTDIO=utf-8

:: 检查Python是否可用
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not detected. Please install Python 3.8 or higher
    pause
    exit /b 1
)

:: 检查Neo4j连接
echo NOTE: Please ensure Neo4j database is running
echo - Neo4j address: bolt://localhost:7687
echo - Default username: neo4j
echo.

:: 检查是否可以直接启动Streamlit (跳过Python脚本，直接运行)
where streamlit >nul 2>&1
if %errorlevel% equ 0 (
    echo Streamlit command detected, attempting direct launch...
    echo.
    echo If application starts successfully, please visit: http://localhost:8501
    echo Press Ctrl+C to stop the application
    echo.
    start http://localhost:8501
    streamlit run kg_import_dashboard_windows.py --server.headless=true
) else (
    :: 使用Python脚本启动
    echo Streamlit command not found, using Python script to launch...
    python -X utf8 start_streamlit.py
    if %errorlevel% neq 0 (
        echo [ERROR] Application launch failed, error code: %errorlevel%
        pause
        exit /b 1
    )
)

exit /b 0 