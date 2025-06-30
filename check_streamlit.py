import sys
import pkg_resources
import subprocess
import socket
import time
import os
from pathlib import Path

def check_port_in_use(port):
    """检查指定端口是否被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def check_package_installed(package_name):
    """检查包是否已安装"""
    try:
        pkg_resources.get_distribution(package_name)
        return True
    except pkg_resources.DistributionNotFound:
        return False

def main():
    """主函数，检查Streamlit环境"""
    print("=" * 50)
    print("  Streamlit 环境诊断工具")
    print("=" * 50)
    print()
    
    # 检查Python版本
    print(f"Python版本: {sys.version}")
    
    # 检查必要的包
    required_packages = ["streamlit", "pandas", "numpy", "plotly", "py2neo", "tqdm", "pillow"]
    print("\n检查必要的包:")
    
    all_packages_installed = True
    for package in required_packages:
        is_installed = check_package_installed(package)
        status = "已安装" if is_installed else "未安装"
        print(f"  - {package}: {status}")
        if not is_installed:
            all_packages_installed = False
    
    # 检查主应用文件
    app_file = "kg_import_dashboard_windows.py"
    print(f"\n检查应用文件 ({app_file}):")
    if os.path.exists(app_file):
        print(f"  - 文件存在: 是")
        # 检查文件大小
        file_size = os.path.getsize(app_file)
        print(f"  - 文件大小: {file_size} 字节")
    else:
        print(f"  - 文件存在: 否")
        print(f"  - 错误: 找不到应用文件 {app_file}")
    
    # 检查端口
    test_port = 8501
    print(f"\n检查端口 {test_port}:")
    if check_port_in_use(test_port):
        print(f"  - 端口 {test_port} 已被占用")
    else:
        print(f"  - 端口 {test_port} 可用")
    
    # 检查临时启动Streamlit
    if all_packages_installed and os.path.exists(app_file):
        print("\n尝试启动Streamlit (不显示UI):")
        try:
            # 使用subprocess启动Streamlit，但设置超时为5秒
            process = subprocess.Popen(
                ["python", "-m", "streamlit", "run", app_file, "--server.headless=true", "--server.port=8599", "--server.baseUrlPath=/test"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 等待5秒后终止进程
            time.sleep(5)
            if process.poll() is None:  # 进程仍在运行
                print("  - Streamlit启动成功，进程正在运行")
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
            else:
                # 进程已经结束
                stdout, stderr = process.communicate()
                print(f"  - Streamlit启动失败，返回码: {process.returncode}")
                if stderr:
                    print("\n错误输出:")
                    print(stderr[:500] + "..." if len(stderr) > 500 else stderr)
        except Exception as e:
            print(f"  - 尝试启动Streamlit时出错: {str(e)}")
    
    print("\n诊断完成。")

if __name__ == "__main__":
    main() 