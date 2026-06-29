"""
RITUAL - 4-Tier MCP Memory Portal
Windows Executable Build Script

Copyright (c) 2024 Black Tiger Computing
Lead Developer: sonamcgoo
Lead Designer: OpenHands Agent
"""

import subprocess
import sys
import os
import shutil

def check_pyinstaller():
    """Ensure PyInstaller is installed."""
    try:
        import PyInstaller
        print(f"PyInstaller {PyInstaller.__version__} found")
        return True
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        return True

def clean_build():
    """Clean previous build artifacts."""
    dirs_to_clean = ["build", "dist"]
    for d in dirs_to_clean:
        if os.path.exists(d):
            shutil.rmtree(d)
            print(f"Removed {d}/")

def build_exe():
    """Build Windows executable."""
    print("Building Windows executable...")
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "-n", "RITUAL",
        "--add-data", "src/frontend;src/frontend",
        "src/backend/main.py"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print("Build successful!")
        if os.path.exists("dist/RITUAL.exe"):
            print(f"Executable: {os.path.abspath('dist/RITUAL.exe')}")
    else:
        print("Build output:")
        print(result.stdout)
        if result.stderr:
            print("Errors:")
            print(result.stderr)

def create_windows_launcher():
    """Create batch file for easy launching."""
    batch_content = '''@echo off
title RITUAL - MCP Memory Portal
echo Starting RITUAL...
cd /d "%~dp0"
if exist "dist\\RITUAL.exe" (
    start "" "dist\\RITUAL.exe"
) else (
    echo Error: RITUAL.exe not found. Run: python build_exe.py
    pause
)
'''
    with open("run_ritual.bat", "w") as f:
        f.write(batch_content)
    print("Created run_ritual.bat")

def main():
    print("=" * 50)
    print("RITUAL Windows Build Script")
    print("Copyright (c) 2024 Black Tiger Computing")
    print("=" * 50)
    
    check_pyinstaller()
    clean_build()
    create_windows_launcher()
    build_exe()
    
    print("\nBuild complete!")
    print("Run 'run_ritual.bat' or 'dist\\RITUAL.exe' to start RITUAL")

if __name__ == "__main__":
    main()