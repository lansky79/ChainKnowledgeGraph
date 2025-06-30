@echo off
rem 设置控制台编码为UTF-8
chcp 65001 > nul
title 简化版知识图谱工具

echo ======================================================
echo     简化版知识图谱工具 - 启动脚本
echo ======================================================
echo.
echo 此脚本将启动简化版知识图谱查看工具，无需Neo4j连接
echo.

rem 设置环境变量
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSSTDIO=utf-8
set STREAMLIT_SERVER_PORT=8503

rem 检查端口占用情况
echo 检查端口占用情况...
netstat -ano | findstr :8503
if %errorlevel% equ 0 (
    echo 端口8503已被占用，尝试使用8504端口...
    set STREAMLIT_SERVER_PORT=8504
)

rem 检查文件是否存在
if not exist "simple_app.py" (
    echo [错误] simple_app.py 文件不存在
    echo 请确保该文件在当前目录中
    pause
    exit /b 1
)

rem 检查数据目录
if not exist "data" (
    echo 创建数据目录...
    mkdir data
)

rem 检查streamlit是否安装
echo 检查环境...
python -c "import streamlit" >nul 2>&1
if %errorlevel% neq 0 (
    echo 安装必要的包...
    pip install streamlit pandas tqdm
    if %errorlevel% neq 0 (
        echo [错误] 安装必要的包失败
        pause
        exit /b 1
    )
)

echo.
echo 启动简化版知识图谱工具，端口: %STREAMLIT_SERVER_PORT%
echo.
echo 启动后，请在浏览器中访问:
echo http://localhost:%STREAMLIT_SERVER_PORT%
echo.
echo 按Ctrl+C终止应用
echo.

rem 启动浏览器
timeout /t 2 > nul
start http://localhost:%STREAMLIT_SERVER_PORT%

rem 启动Streamlit应用
python -m streamlit run simple_app.py --server.port=%STREAMLIT_SERVER_PORT% --server.headless=true

echo.
echo 应用已关闭
echo.
pause
exit /b 0 