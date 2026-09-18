# -*- coding: utf-8 -*-
"""PyInstaller 打包脚本
运行: python build.py
生成 dist/LKJ数据管理工具/LKJ数据管理工具.exe
"""

import subprocess
import sys
import os

APP_NAME = "LKJ数据管理工具"
ENTRY = "main.py"

def main():
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--windowed",
        "--noconfirm",
        "--clean",
        ENTRY,
    ]
    print("正在打包，请稍候...")
    print("执行:", " ".join(cmd))
    result = subprocess.run(cmd)
    if result.returncode == 0:
        print(f"\n打包成功! 可执行文件位于: dist/{APP_NAME}/{APP_NAME}.exe")
    else:
        print("\n打包失败，请检查错误信息")
        sys.exit(1)

if __name__ == "__main__":
    main()