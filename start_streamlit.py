import os
import sys
import subprocess
import time

# Set default encoding to UTF-8 to prevent character encoding issues
if sys.platform.startswith('win'):
    # Special setting for Windows systems
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Simple logging function
def log(message):
    print(f"[{time.strftime('%H:%M:%S')}] {message}")

def main():
    log("Starting simplified Streamlit application...")
    
    # Check if file exists
    dashboard_file = "kg_import_dashboard_windows.py"
    if not os.path.exists(dashboard_file):
        log(f"Error: File {dashboard_file} not found")
        log("Please ensure this file exists in the current directory")
        input("Press any key to exit...")
        return
    
    log("Checking necessary dependencies...")
    try:
        import streamlit
        import pandas
        import numpy
        import plotly
        import py2neo
        log("All basic dependencies successfully imported")
    except ImportError as e:
        log(f"Missing dependency: {e}")
        log("Attempting to install missing dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "streamlit", "pandas", "numpy", "plotly", "py2neo", "tqdm", "pillow"])
    
    # Try to start Streamlit
    log("Starting Streamlit application...")
    log(f"Using command: streamlit run {dashboard_file}")
    log("After launch, please visit: http://localhost:8501")
    log("If the application is not accessible, check for error messages during startup")
    
    # Use subprocess to start Streamlit, displaying real-time output
    try:
        # Set environment variables to ensure correct encoding
        my_env = os.environ.copy()
        my_env["PYTHONIOENCODING"] = "utf-8"
        
        # On Windows, use a simpler, more direct way to start
        if sys.platform.startswith('win'):
            # First set console encoding
            subprocess.run("chcp 65001", shell=True, check=True)
            
            # Directly start streamlit without using shell=True
            log("Starting Streamlit using Windows-specific method...")
            process = subprocess.Popen(
                [sys.executable, "-m", "streamlit", "run", dashboard_file, "--server.headless=true"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                env=my_env
            )
        else:
            # Use normal method for other systems
            process = subprocess.Popen(
                [sys.executable, "-m", "streamlit", "run", dashboard_file, "--server.headless=true"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                env=my_env
            )
        
        # Display output in real-time
        log("Starting to monitor Streamlit output...")
        for line in process.stdout:
            line = line.strip()
            print(line)
            # If we see a message indicating successful startup, try to open the browser
            if "You can now view your Streamlit app in your browser" in line:
                log("Streamlit application successfully started!")
                # Optional: Automatically open browser
                try:
                    import webbrowser
                    webbrowser.open("http://localhost:8501")
                    log("Browser automatically opened")
                except:
                    log("Unable to automatically open browser, please manually visit http://localhost:8501")
                
        # Wait for process to end
        return_code = process.wait()
        log(f"Streamlit process has exited, return code: {return_code}")
        
    except Exception as e:
        log(f"Error during startup: {e}")
        import traceback
        log(traceback.format_exc())
    
    log("Application has exited")
    input("Press any key to close...")

if __name__ == "__main__":
    main() 