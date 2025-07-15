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

:: 启动应用
echo 启动知识图谱可视化应用...
python -m streamlit run app.py

pause 