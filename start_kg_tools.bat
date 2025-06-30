@echo off
rem 设置控制台编码为UTF-8
chcp 65001 > nul
title 知识图谱工具 - 启动器

:MENU
cls
echo ======================================================
echo        知识图谱工具 - 启动选项
echo ======================================================
echo.
echo 请选择要启动的功能:
echo.
echo  [1] 启动Neo4j数据库
echo  [2] 启动完整版应用 (需要Neo4j)
echo  [3] 启动简化版应用 (不需要Neo4j)
echo  [4] 运行诊断工具
echo  [5] 退出
echo.
set /p choice=请输入选项 [1-5]: 

if "%choice%"=="1" goto START_NEO4J
if "%choice%"=="2" goto START_FULL
if "%choice%"=="3" goto START_SIMPLE
if "%choice%"=="4" goto DIAGNOSTICS
if "%choice%"=="5" goto EXIT
goto MENU

:START_NEO4J
cls
echo ======================================================
echo        正在启动Neo4j数据库...
echo ======================================================
echo.
if exist "start_neo4j.bat" (
    call start_neo4j.bat
) else (
    echo [错误] 找不到 start_neo4j.bat 文件
    echo 按任意键返回主菜单...
    pause > nul
    goto MENU
)
echo.
echo 按任意键返回主菜单...
pause > nul
goto MENU

:START_FULL
cls
echo ======================================================
echo        正在启动完整版应用...
echo ======================================================
echo.
echo 该应用需要Neo4j数据库支持。确保Neo4j已经启动。
echo.
echo 1. 确认Neo4j已启动
echo 2. 启动完整版应用
echo 3. 返回主菜单
echo.
set /p fullchoice=请选择 [1-3]: 

if "%fullchoice%"=="1" goto START_NEO4J
if "%fullchoice%"=="2" (
    if exist "direct_run.bat" (
        start direct_run.bat
        echo 应用正在启动中...
        timeout /t 2 > nul
        goto MENU
    ) else if exist "run_dashboard.bat" (
        start run_dashboard.bat
        echo 应用正在启动中...
        timeout /t 2 > nul
        goto MENU
    ) else (
        echo [错误] 找不到启动脚本
        echo 按任意键返回...
        pause > nul
        goto START_FULL
    )
)
if "%fullchoice%"=="3" goto MENU
goto START_FULL

:START_SIMPLE
cls
echo ======================================================
echo        正在启动简化版应用...
echo ======================================================
echo.
if exist "run_simple_app.bat" (
    start run_simple_app.bat
    echo 简化版应用正在启动中...
    echo 启动后，请在浏览器中访问: http://localhost:8503
    echo.
    echo 按任意键返回主菜单...
    pause > nul
    goto MENU
) else (
    echo [错误] 找不到 run_simple_app.bat 文件
    echo 按任意键返回主菜单...
    pause > nul
    goto MENU
)

:DIAGNOSTICS
cls
echo ======================================================
echo        正在运行诊断工具...
echo ======================================================
echo.
echo 诊断选项:
echo.
echo  [1] 检查Streamlit环境
echo  [2] 检查Neo4j连接
echo  [3] 返回主菜单
echo.
set /p diagchoice=请选择 [1-3]: 

if "%diagchoice%"=="1" (
    if exist "check_streamlit.py" (
        python check_streamlit.py
    ) else (
        echo [错误] 找不到 check_streamlit.py 文件
    )
    echo.
    echo 按任意键返回诊断菜单...
    pause > nul
    goto DIAGNOSTICS
)
if "%diagchoice%"=="2" (
    if exist "check_neo4j_connection.py" (
        python check_neo4j_connection.py
    ) else (
        echo [错误] 找不到 check_neo4j_connection.py 文件
    )
    echo.
    echo 按任意键返回诊断菜单...
    pause > nul
    goto DIAGNOSTICS
)
if "%diagchoice%"=="3" goto MENU
goto DIAGNOSTICS

:EXIT
echo 感谢使用知识图谱工具，再见!
timeout /t 2 > nul
exit /b 0 