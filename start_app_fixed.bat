@echo off
echo ===================================
echo 知识图谱可视化系统启动脚本
echo ===================================

:: 检查Python环境
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Python未安装或不在PATH中，请安装Python 3.8+
    pause
    exit /b 1
)

:: 检查是否有虚拟环境
if exist kg_env\Scripts\activate.bat (
    echo 激活虚拟环境...
    call kg_env\Scripts\activate.bat
) else (
    echo 未找到虚拟环境，使用系统Python
)

:: 安装依赖
echo 检查并安装依赖...
pip install -r requirements.txt

:: 检查端口占用并选择可用端口
echo 检查端口占用情况...
netstat -ano | findstr :8501 >nul
if %ERRORLEVEL% equ 0 (
    echo 端口8501已被占用，尝试使用端口8502...
    netstat -ano | findstr :8502 >nul
    if %ERRORLEVEL% equ 0 (
        echo 端口8502也被占用，尝试使用端口8503...
        set PORT=8503
    ) else (
        set PORT=8502
    )
) else (
    set PORT=8501
)

:: 启动应用
echo 启动知识图谱可视化应用，使用端口 %PORT%...
echo 应用将在浏览器中自动打开: http://localhost:%PORT%
python -m streamlit run Home.py --server.port %PORT%

pause