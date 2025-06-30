@echo off
chcp 65001 > nul
title 知识图谱数据导入可视化工具

:: 跳过函数定义部分直接到主程序
goto :main_program

:: 函数定义部分
:log_func
echo %*
if defined LOG_FILE echo %* >> "%LOG_FILE%"
goto :eof

:main_program
echo ======================================================
echo           知识图谱数据导入可视化工具 - 启动器
echo ======================================================
echo.

:: 设置环境变量
set CONDA_ENV_NAME=pChainKnowledgeGraph
set VENV_NAME=kg_env
set VENV_PATH=%CD%\%VENV_NAME%
set NEO4J_PATH=C:\Program Files\Neo4j Desktop\Neo4j Desktop.exe
set NEO4J_SERVICE=neo4j
set NEO4J_HOME=C:\Users\franc\Downloads\neo4j-chs-community-5.26.0-windows
set NEO4J_USER=neo4j
set NEO4J_PASSWORD=neo4j
set STREAMLIT_PORT=8501

:: 创建日志目录
if not exist "logs\" mkdir logs

:: 设置日志文件名 (使用更安全的日期时间格式)
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YYYY=%dt:~0,4%"
set "MM=%dt:~4,2%"
set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%"
set "Min=%dt:~10,2%"
set "Sec=%dt:~12,2%"
set "LOG_FILE=logs\startup_%YYYY%%MM%%DD%_%HH%%Min%%Sec%.log"

:: 记录启动信息到日志
echo [%date% %time%] 启动脚本开始执行 > "%LOG_FILE%"

:: 检查Python是否已安装
python --version > nul 2>&1
if %errorlevel% neq 0 (
    call :log_func [错误] 未检测到Python，请安装Python 3.8或更高版本。
    call :log_func 您可以从 https://www.python.org/downloads/ 下载安装。
    pause
    exit /b 1
)

:: 先尝试使用conda环境
echo 正在检查conda环境...
where conda >nul 2>&1
if %errorlevel% equ 0 (
    call :log_func [信息] 检测到conda，尝试激活conda环境: %CONDA_ENV_NAME%
    
    :: 使用call确保命令正常执行后继续
    call conda activate %CONDA_ENV_NAME% 2>nul
    if %errorlevel% equ 0 (
        call :log_func [成功] 已激活conda环境: %CONDA_ENV_NAME%
        goto :dependencies_check
    ) else (
        call :log_func [警告] 无法激活conda环境: %CONDA_ENV_NAME%
        call :log_func [信息] 尝试初始化conda并重新激活...
        
        :: 尝试初始化conda并重新激活
        call conda init cmd.exe >nul 2>&1
        call conda activate %CONDA_ENV_NAME% 2>nul
        if %errorlevel% equ 0 (
            call :log_func [成功] 已激活conda环境: %CONDA_ENV_NAME%
            goto :dependencies_check
        ) else (
            call :log_func [警告] 仍然无法激活conda环境，尝试其他方法...
        )
    )
) else (
    call :log_func [信息] 未检测到conda，尝试使用标准虚拟环境...
)

:: 如果conda环境不可用，尝试使用已有的虚拟环境或创建新的
echo 正在检查虚拟环境...
if exist "%VENV_PATH%\Scripts\activate.bat" (
    call :log_func [信息] 检测到虚拟环境: %VENV_PATH%
) else (
    call :log_func [信息] 虚拟环境不存在，尝试创建...
    python -m venv "%VENV_PATH%" 2>nul
    if %errorlevel% neq 0 (
        call :log_func [警告] 使用venv创建虚拟环境失败，尝试使用virtualenv...
        pip install virtualenv -q
        python -m virtualenv "%VENV_PATH%" 2>nul
        if %errorlevel% neq 0 (
            call :log_func [警告] 创建虚拟环境失败，将使用系统Python环境。
            goto :dependencies_check
        )
    )
    call :log_func [成功] 虚拟环境已创建: %VENV_PATH%
)

:: 激活标准虚拟环境
echo 正在激活虚拟环境: %VENV_NAME%
call "%VENV_PATH%\Scripts\activate.bat"
if %errorlevel% neq 0 (
    call :log_func [警告] 无法激活虚拟环境，将使用系统Python环境。
) else (
    call :log_func [成功] 已激活虚拟环境: %VENV_NAME%
)

:dependencies_check
:: 安装必要的依赖
call :log_func 正在检查并安装必要的依赖...

:: 创建依赖检查脚本
echo import sys > check_deps.py
echo required = ["streamlit", "pandas", "numpy", "matplotlib", "plotly", "py2neo", "tqdm", "PIL"] >> check_deps.py
echo missing = [] >> check_deps.py
echo for pkg in required: >> check_deps.py
echo     try: >> check_deps.py
echo         __import__(pkg) >> check_deps.py
echo     except ImportError: >> check_deps.py
echo         missing.append(pkg) >> check_deps.py
echo if missing: >> check_deps.py
echo     print("Missing dependencies:", ", ".join(missing)) >> check_deps.py
echo     sys.exit(1) >> check_deps.py
echo else: >> check_deps.py
echo     print("All dependencies installed") >> check_deps.py
echo     sys.exit(0) >> check_deps.py

:: 运行依赖检查脚本
python check_deps.py > deps_result.txt 2>&1
set /p DEPS_RESULT=<deps_result.txt
del deps_result.txt
del check_deps.py

call :log_func %DEPS_RESULT%
echo %DEPS_RESULT% | findstr /C:"Missing dependencies" > nul
if %errorlevel% equ 0 (
    call :log_func 正在安装缺失的依赖...
    pip install streamlit pandas numpy matplotlib plotly py2neo tqdm pillow
    if %errorlevel% neq 0 (
        call :log_func [错误] 安装依赖失败，请检查网络连接或手动安装。
        call :log_func pip install streamlit pandas numpy matplotlib plotly py2neo tqdm pillow
        pause
        exit /b 1
    )
    call :log_func [成功] 已安装所有必要的依赖
) else (
    call :log_func [信息] 所有必要的依赖已安装
)

:: 确保日志和数据目录存在
if not exist "logs\" mkdir logs
if not exist "data\" mkdir data

:: 检查是否有Neo4j进程正在运行
call :log_func 正在检查Neo4j进程状态...
tasklist /FI "IMAGENAME eq java.exe" | findstr /i "java.exe" > nul
if %errorlevel% equ 0 (
    call :log_func [警告] 检测到可能有Neo4j实例正在运行
    echo 是否终止所有Java进程以确保Neo4j可以正常启动? (Y/N)
    set /p kill_java=
    if /i "%kill_java%"=="Y" (
        call :log_func 正在终止Java进程...
        taskkill /F /IM java.exe > nul 2>&1
        call :log_func [信息] 已终止Java进程
        timeout /t 3 > nul
    )
)

:: 检查并清理锁文件
if exist "%NEO4J_HOME%\data\databases\store_lock" (
    call :log_func [警告] 检测到数据库锁文件，尝试清理...
    del /F "%NEO4J_HOME%\data\databases\store_lock" > nul 2>&1
    if %errorlevel% equ 0 (
        call :log_func [成功] 已清理数据库锁文件
    ) else (
        call :log_func [错误] 无法清理数据库锁文件，可能需要管理员权限
    )
)

:: 尝试启动Neo4j服务
call :log_func 正在检查Neo4j服务状态...

:: 方法3: 直接启动Neo4j服务器（独立安装版本）
if exist "%NEO4J_HOME%\bin\neo4j.bat" (
    call :log_func 检测到Neo4j独立安装，尝试直接启动服务器...
    call :log_func 正在启动Neo4j服务器，这可能需要几秒钟...
    
    :: 先尝试停止可能正在运行的实例
    call "%NEO4J_HOME%\bin\neo4j.bat" stop 2>nul
    timeout /t 5 >nul
    
    :: 启动Neo4j服务器
    start /b cmd /c ""%NEO4J_HOME%\bin\neo4j.bat" console"
    call :log_func [信息] Neo4j服务器启动命令已执行
    call :log_func 等待Neo4j服务器完全启动...
    timeout /t 25 >nul
    call :log_func [成功] Neo4j服务器应该已经启动
) else (
    call :log_func [警告] 未找到Neo4j独立安装版本，尝试其他方法...

    :: 方法1: 尝试启动Neo4j服务（如果作为Windows服务安装）
    sc query %NEO4J_SERVICE% >nul 2>&1
    if %errorlevel% equ 0 (
        call :log_func 检测到Neo4j服务，尝试启动...
        net start %NEO4J_SERVICE% >nul 2>&1
        if %errorlevel% equ 0 (
            call :log_func [成功] Neo4j服务已启动
        ) else (
            call :log_func [警告] 无法启动Neo4j服务，可能需要管理员权限
        )
    ) else (
        call :log_func [信息] 未检测到Neo4j服务
    )

    :: 方法2: 尝试启动Neo4j Desktop（如果已安装）
    if exist "%NEO4J_PATH%" (
        call :log_func 检测到Neo4j Desktop，尝试启动...
        start "" "%NEO4J_PATH%"
        call :log_func [信息] 已尝试启动Neo4j Desktop，请在其中手动启动数据库
        call :log_func 请等待Neo4j数据库完全启动后再继续...
        timeout /t 10 >nul
    ) else (
        call :log_func [警告] 未找到Neo4j Desktop，请手动启动Neo4j数据库
    )
)

:: 检查Neo4j是否成功启动
call :log_func 正在验证Neo4j是否成功启动...
powershell -Command "try { $client = New-Object System.Net.Sockets.TcpClient('localhost', 7687); $client.Close(); Write-Host '[成功] Neo4j服务器已成功启动并监听端口7687'; exit 0 } catch { Write-Host '[警告] 无法连接到Neo4j服务器端口7687'; exit 1 }"
set NEO4J_STATUS=%errorlevel%

if %NEO4J_STATUS% neq 0 (
    call :log_func [错误] Neo4j服务器可能未成功启动，请检查以下事项:
    call :log_func 1. 是否有其他程序占用7687端口
    call :log_func 2. Neo4j数据目录是否有写入权限
    call :log_func 3. 查看Neo4j日志获取详细错误信息: %NEO4J_HOME%\logs\
    echo.
    echo 是否仍要继续? (Y/N)
    set /p continue_anyway=
    if /i not "%continue_anyway%"=="Y" (
        call :log_func 操作已取消。
        pause
        exit /b 1
    )
)

:: 等待用户确认Neo4j已启动
echo.
call :log_func 请确保Neo4j数据库已启动，连接参数如下:
call :log_func - 地址: bolt://localhost:7687
call :log_func - 默认用户名: neo4j
call :log_func - 默认密码: neo4j (首次登录需要修改)
echo.

:: 询问用户名和密码
set /p NEO4J_USER=请输入Neo4j用户名 [默认:neo4j]: 
if "%NEO4J_USER%"=="" set NEO4J_USER=neo4j
call :log_func 使用Neo4j用户名: %NEO4J_USER%

set /p NEO4J_PASSWORD=请输入Neo4j密码 [默认:neo4j]: 
if "%NEO4J_PASSWORD%"=="" set NEO4J_PASSWORD=neo4j
call :log_func 使用Neo4j密码: [已设置]

:: 检查Neo4j连接
call :log_func 正在检查Neo4j连接...
call :log_func 使用认证信息: %NEO4J_USER%:[密码]

:: 创建临时Python脚本进行连接测试
echo from py2neo import Graph > neo4j_test.py
echo try: >> neo4j_test.py
echo     g = Graph("bolt://localhost:7687", auth=("%NEO4J_USER%", "%NEO4J_PASSWORD%")) >> neo4j_test.py
echo     print("[成功] Neo4j连接正常!") >> neo4j_test.py
echo     exit(0) >> neo4j_test.py
echo except Exception as e: >> neo4j_test.py
echo     print("[错误] 无法连接到Neo4j:", e) >> neo4j_test.py
echo     exit(1) >> neo4j_test.py

:: 运行测试脚本
python neo4j_test.py > neo4j_result.txt 2>&1
set /p NEO4J_RESULT=<neo4j_result.txt
call :log_func %NEO4J_RESULT%
set NEO4J_CONNECT_STATUS=%errorlevel%

:: 删除临时文件
del neo4j_test.py
del neo4j_result.txt

:: 检查连接结果
if %NEO4J_CONNECT_STATUS% neq 0 (
    color 0C
    echo.
    call :log_func [错误] 无法连接到Neo4j数据库，请检查:
    call :log_func 1. Neo4j是否已启动 (检查http://localhost:7474是否可访问)
    call :log_func 2. 用户名和密码是否正确
    call :log_func 3. 防火墙是否允许连接
    echo.
    echo 是否仍要继续? (Y/N):
    set /p force_continue=
    if /i not "%force_continue%"=="Y" (
        call :log_func 操作已取消。
        pause
        exit /b 1
    )
    call :log_func [警告] 强制继续，但应用可能无法正常工作!
)

:: 更新配置文件中的认证信息
call :log_func 更新Neo4j连接配置...
if exist "config_windows.json" (
    call :log_func 正在更新config_windows.json中的认证信息...
    powershell -Command "(Get-Content config_windows.json) -replace '\"username\": \"neo4j\"', '\"username\": \"%NEO4J_USER%\"' | Set-Content config_windows.json"
    powershell -Command "(Get-Content config_windows.json) -replace '\"password\": \"[^\"]*\"', '\"password\": \"%NEO4J_PASSWORD%\"' | Set-Content config_windows.json"
)

:: 检查kg_import_dashboard_windows.py是否存在
if not exist "kg_import_dashboard_windows.py" (
    call :log_func [错误] 未找到kg_import_dashboard_windows.py文件
    call :log_func 请确保该文件存在并位于当前目录
    pause
    exit /b 1
)

:: 检查端口8501是否被占用
call :log_func 正在检查端口%STREAMLIT_PORT%是否可用...
powershell -Command "if ((Get-NetTCPConnection -LocalPort %STREAMLIT_PORT% -ErrorAction SilentlyContinue).Count -gt 0) { Write-Host '[警告] 端口%STREAMLIT_PORT%已被占用'; exit 1 } else { Write-Host '[成功] 端口%STREAMLIT_PORT%可用'; exit 0 }"
if %errorlevel% neq 0 (
    call :log_func [警告] 端口%STREAMLIT_PORT%已被占用，尝试终止相关进程...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":%STREAMLIT_PORT%"') do (
        call :log_func 尝试终止进程: %%a
        taskkill /F /PID %%a >nul 2>&1
    )
    timeout /t 3 >nul
)

:: 启动应用
cls
color 0A
echo ======================================================
echo           知识图谱数据导入可视化工具 - 启动中
echo ======================================================
echo.
call :log_func 正在启动应用，请稍候...
echo 应用启动后将自动打开浏览器。
echo.
echo 如果浏览器没有自动打开，请手动访问: http://localhost:8501
echo.
echo 按 Ctrl+C 可以停止应用运行。
echo ======================================================
echo.

:: 创建详细的Streamlit启动脚本
echo @echo off > run_streamlit.bat
echo cd "%CD%" >> run_streamlit.bat

:: 根据实际环境选择不同的激活命令
where conda >nul 2>&1
if %errorlevel% equ 0 (
    echo call conda activate %CONDA_ENV_NAME% >> run_streamlit.bat
) else (
    if exist "%VENV_PATH%\Scripts\activate.bat" (
        echo call "%VENV_PATH%\Scripts\activate.bat" >> run_streamlit.bat
    )
)

echo echo 正在启动Streamlit应用... >> run_streamlit.bat
echo echo 启动命令: python -m streamlit run kg_import_dashboard_windows.py >> run_streamlit.bat
echo python -m streamlit run kg_import_dashboard_windows.py --server.headless=true --server.enableCORS=false >> run_streamlit.bat
echo if %%errorlevel%% neq 0 ( >> run_streamlit.bat
echo   echo [错误] Streamlit启动失败，错误代码: %%errorlevel%% >> run_streamlit.bat
echo   echo 请检查以下内容: >> run_streamlit.bat
echo   echo 1. kg_import_dashboard_windows.py文件是否存在语法错误 >> run_streamlit.bat
echo   echo 2. 所有依赖是否已正确安装 >> run_streamlit.bat
echo   echo 3. 端口8501是否被其他应用占用 >> run_streamlit.bat
echo   pause >> run_streamlit.bat
echo ) >> run_streamlit.bat

:: 使用独立窗口运行Streamlit，以便查看错误信息
call :log_func [信息] 在独立窗口中启动Streamlit...
start cmd /k "run_streamlit.bat"

:: 等待Streamlit启动
call :log_func 正在等待Streamlit启动，请稍候...
timeout /t 5 >nul

:: 尝试多次检查Streamlit是否成功启动
call :log_func 检查Streamlit是否已启动...
set MAX_RETRIES=6
set RETRY_COUNT=0

:retry_check
set /a RETRY_COUNT+=1
call :log_func 尝试 %RETRY_COUNT%/%MAX_RETRIES%...

powershell -Command "try { $response = Invoke-WebRequest -Uri http://localhost:%STREAMLIT_PORT% -UseBasicParsing -TimeoutSec 5; Write-Host '[成功] Streamlit已成功启动'; exit 0 } catch { Write-Host '[警告] 无法连接到Streamlit应用'; exit 1 }"
if %errorlevel% equ 0 (
    call :log_func [成功] Streamlit应用已成功启动!
    goto :streamlit_started
)

if %RETRY_COUNT% lss %MAX_RETRIES% (
    call :log_func 等待Streamlit启动，将在5秒后重试...
    timeout /t 5 >nul
    goto :retry_check
)

:streamlit_check_failed
call :log_func [警告] 多次尝试后仍无法连接到Streamlit应用
echo 请检查以下事项:
echo 1. 查看Streamlit启动窗口中的错误信息
echo 2. 确保已安装所有必要的Python依赖
echo 3. 检查kg_import_dashboard_windows.py文件是否有语法错误
echo 4. 检查端口%STREAMLIT_PORT%是否被其他应用占用
echo.
echo 您可以尝试手动运行以下命令启动应用:
echo python -m streamlit run kg_import_dashboard_windows.py
goto :continue_anyway

:streamlit_started
:: 使用start命令启动浏览器
call :log_func 正在打开浏览器...
start "" http://localhost:8501

:continue_anyway
echo.
echo 如果应用已成功启动，请访问: http://localhost:8501
echo 如果遇到问题，请查看Streamlit启动窗口中的错误信息
echo 完整日志已保存到: %LOG_FILE%
echo.
echo 按任意键关闭此窗口...
pause > nul 