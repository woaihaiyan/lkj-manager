# -*- coding: utf-8 -*-
"""安卓版打包脚本
将 Flask Web 应用用 PyInstaller 打包为 EXE，PC 运行后手机浏览器访问。
"""

import subprocess
import sys
import os

APP_NAME = "LKJ数据管理-手机版"
ENTRY = "app.py"

def main():
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", APP_NAME,
        "--windowed",
        "--noconfirm",
        "--clean",
        "--add-data", os.path.join("templates", ";templates"),
        "--add-data", os.path.join("static", ";static"),
        ENTRY,
    ]
    print("正在打包手机版服务端...")
    print("执行:", " ".join(cmd))
    result = subprocess.run(cmd)
    if result.returncode == 0:
        print(f"\n打包成功!")
        print(f"可执行文件: dist/{APP_NAME}/{APP_NAME}.exe")
        print(f"运行后用手机浏览器访问显示的 IP 地址即可")
    else:
        print("\n打包失败")
        sys.exit(1)

if __name__ == "__main__":
    main()