#!/usr/bin/env python3
"""
构建脚本：将前后端代码打包成一个可执行文件
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def build_backend():
    """构建Python后端"""
    print("正在构建Python后端...")
    
    # 创建dist目录
    dist_dir = Path("dist")
    dist_dir.mkdir(exist_ok=True)
    
    # 使用PyInstaller打包Python后端
    cmd = [
        "pyinstaller",
        "--onefile",
        "--name", "vspeech_backend",
        "--add-data", "database.py:.",
        "--add-data", "video_searcher.py:.",
        "--add-data", "wishper.py:.",
        "--add-data", "model.py:.",
        "--add-data", "preprocess.py:.",
        "--add-data", "retrieve.py:.",
        "--add-data", "utils.py:.",
        "--add-data", "video_edit.py:.",
        "--add-data", "vstore.py:.",
        "--hidden-import", "flask",
        "--hidden-import", "flask_cors",
        "--hidden-import", "uuid",
        "--hidden-import", "threading",
        "api.py"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("Python后端构建成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Python后端构建失败: {e}")
        return False

def build_frontend():
    """构建Electron前端"""
    print("正在构建Electron前端...")
    
    # 使用electron-builder打包
    cmd = ["npm", "run", "dist"]
    
    try:
        subprocess.run(cmd, check=True)
        print("Electron前端构建成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Electron前端构建失败: {e}")
        return False

def main():
    """主构建函数"""
    print("开始构建vspeech_searcher应用...")
    
    # 检查依赖
    if not shutil.which("pyinstaller"):
        print("错误: 未找到pyinstaller，请先安装: pip install pyinstaller")
        return False
    
    if not shutil.which("npm"):
        print("错误: 未找到npm，请先安装Node.js")
        return False
    
    # 构建后端
    if not build_backend():
        return False
    
    # 构建前端
    if not build_frontend():
        return False
    
    print("应用构建完成!")
    print("可执行文件位于 release/ 目录中")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
