@echo off
title 知识图谱数据导入可视化工具 - 安装向导
color 0A
cls

echo ======================================================
echo        知识图谱数据导入可视化工具 - 安装向导
echo ======================================================
echo.
echo 欢迎使用知识图谱数据导入可视化工具安装向导！
echo 本向导将帮助您设置运行环境。
echo.
echo 按任意键开始安装...
pause >nul

:: 检查Python是否安装
echo 正在检查Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo [错误] Python未安装或未添加到PATH环境变量中。
    echo 请访问 https://www.python.org/downloads/ 下载并安装Python 3.8或更高版本。
    echo 安装时请勾选"Add Python to PATH"选项。
    echo.
    echo 安装Python后，请重新运行此安装向导。
    pause
    exit /b 1
) else (
    echo [成功] 检测到Python已安装。
)

:: 检查pip是否可用
echo 正在检查pip...
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo [错误] pip未安装或不可用。
    echo 请确保您的Python安装包含pip。
    echo.
    pause
    exit /b 1
) else (
    echo [成功] 检测到pip已安装。
)

:: 创建虚拟环境
echo 正在创建虚拟环境...
if exist "venv\" (
    echo 虚拟环境已存在，是否重新创建？
    set /p recreate=重新创建虚拟环境？(Y/N): 
    if /i "%recreate%"=="Y" (
        echo 正在删除旧的虚拟环境...
        rmdir /s /q venv
        echo 正在创建新的虚拟环境...
        python -m venv venv
    )
) else (
    python -m venv venv
)

:: 激活虚拟环境
echo 正在激活虚拟环境...
call venv\Scripts\activate.bat

:: 安装依赖
echo 正在安装依赖包...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    color 0C
    echo [错误] 安装依赖包失败。
    echo 请检查您的网络连接或手动安装依赖：
    echo pip install -r requirements.txt
    pause
    exit /b 1
) else (
    echo [成功] 依赖包安装完成。
)

:: 创建必要的目录
echo 正在创建必要的目录...
if not exist "data\" (
    mkdir data
    echo 创建data目录成功。
)

if not exist "logs\" (
    mkdir logs
    echo 创建logs目录成功。
)

:: 检查Neo4j是否已安装
echo 正在检查Neo4j...
where neo4j >nul 2>&1
if %errorlevel% neq 0 (
    echo [提示] 未检测到Neo4j命令行工具。
    echo 请确保您已安装Neo4j数据库。
    echo 您可以从 https://neo4j.com/download/ 下载Neo4j Desktop或Neo4j Server。
    echo.
    echo 如果您已安装Neo4j，但未将其添加到PATH中，请忽略此提示。
) else (
    echo [成功] 检测到Neo4j已安装。
)

:: 检查配置文件
echo 正在检查配置文件...
if not exist "config_windows.json" (
    echo 创建Windows专用配置文件...
    echo {> config_windows.json
    echo     "neo4j": {>> config_windows.json
    echo         "uri": "bolt://127.0.0.1:7687",>> config_windows.json
    echo         "username": "neo4j",>> config_windows.json
    echo         "password": "12345678">> config_windows.json
    echo     },>> config_windows.json
    echo     "app": {>> config_windows.json
    echo         "title": "知识图谱数据导入可视化工具 - Windows版",>> config_windows.json
    echo         "theme": "light",>> config_windows.json
    echo         "batch_size_default": 10000,>> config_windows.json
    echo         "batch_size_min": 1000,>> config_windows.json
    echo         "batch_size_max": 50000,>> config_windows.json
    echo         "refresh_interval": 60,>> config_windows.json
    echo         "show_logo": true,>> config_windows.json
    echo         "windows_mode": true>> config_windows.json
    echo     },>> config_windows.json
    echo     "data_paths": {>> config_windows.json
    echo         "import_state": "data\\import_state.pkl",>> config_windows.json
    echo         "company": "data\\company.json",>> config_windows.json
    echo         "industry": "data\\industry.json",>> config_windows.json
    echo         "product": "data\\product.json",>> config_windows.json
    echo         "company_industry": "data\\company_industry.json",>> config_windows.json
    echo         "industry_industry": "data\\industry_industry.json",>> config_windows.json
    echo         "company_product": "data\\company_product.json",>> config_windows.json
    echo         "product_product": "data\\product_product.json">> config_windows.json
    echo     },>> config_windows.json
    echo     "windows_settings": {>> config_windows.json
    echo         "use_cmd": true,>> config_windows.json
    echo         "browser_path": "",>> config_windows.json
    echo         "neo4j_path": "C:\\Program Files\\Neo4j Desktop\\Neo4j Desktop.exe",>> config_windows.json
    echo         "log_path": "logs\\app.log",>> config_windows.json
    echo         "auto_start_browser": true,>> config_windows.json
    echo         "auto_start_neo4j": false,>> config_windows.json
    echo         "theme_color": "#4CAF50",>> config_windows.json
    echo         "disable_progress_animation": true>> config_windows.json
    echo     }>> config_windows.json
    echo }>> config_windows.json
    echo 配置文件创建成功。
) else (
    echo [成功] 配置文件已存在。
)

:: 创建桌面快捷方式
echo 是否创建桌面快捷方式？
set /p shortcut=创建桌面快捷方式？(Y/N): 
if /i "%shortcut%"=="Y" (
    echo 正在创建桌面快捷方式...
    set SCRIPT="%TEMP%\%RANDOM%-%RANDOM%-%RANDOM%-%RANDOM%.vbs"
    echo Set oWS = WScript.CreateObject("WScript.Shell") >> %SCRIPT%
    echo sLinkFile = "%USERPROFILE%\Desktop\知识图谱数据导入工具.lnk" >> %SCRIPT%
    echo Set oLink = oWS.CreateShortcut(sLinkFile) >> %SCRIPT%
    echo oLink.TargetPath = "%CD%\start_dashboard_windows.bat" >> %SCRIPT%
    echo oLink.WorkingDirectory = "%CD%" >> %SCRIPT%
    echo oLink.Description = "知识图谱数据导入可视化工具" >> %SCRIPT%
    echo oLink.IconLocation = "%SystemRoot%\System32\SHELL32.dll,13" >> %SCRIPT%
    echo oLink.Save >> %SCRIPT%
    cscript /nologo %SCRIPT%
    del %SCRIPT%
    echo 桌面快捷方式创建成功。
)

:: 安装完成
cls
color 0A
echo ======================================================
echo        知识图谱数据导入可视化工具 - 安装完成
echo ======================================================
echo.
echo 恭喜！知识图谱数据导入可视化工具已安装完成。
echo.
echo 您可以通过以下方式启动应用：
echo 1. 双击 start_dashboard_windows.bat 文件
if /i "%shortcut%"=="Y" echo 2. 双击桌面上的"知识图谱数据导入工具"快捷方式
echo.
echo 是否现在启动应用？
set /p start=启动应用？(Y/N): 
if /i "%start%"=="Y" (
    start "" start_dashboard_windows.bat
)

echo.
echo 感谢使用！
echo ======================================================
echo.
pause 