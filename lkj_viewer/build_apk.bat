@echo off
chcp 65001 >nul
title LKJ数据管理 - APK打包工具

echo ============================================================
echo   LKJ数据管理 - Android APK 一键打包
echo ============================================================
echo.
echo 此脚本在 WSL 中自动打包 APK
echo.
echo 前提: 已安装 WSL+Ubuntu (如未安装请先运行 install_wsl.bat)
echo.
pause

echo.
echo [1/3] 检查 WSL...
wsl -l -v 2>nul
if errorlevel 1 (
    echo.
    echo 错误: WSL 未安装!
    echo 请先运行 install_wsl.bat 安装 WSL，然后重启电脑
    pause
    exit /b 1
)

echo.
echo [2/3] 在 WSL 中安装依赖并打包 APK...
echo 首次打包需下载 SDK/NDK (约1-2GB)，耗时20-40分钟
echo.
pause

wsl bash /mnt/k/huawei/keshihua/demo/lkj_viewer/android_version/build_apk_wsl.sh

if errorlevel 1 (
    echo.
    echo 打包过程中出现错误，请检查上方日志
    pause
    exit /b 1
)

echo.
echo [3/3] 完成!
echo.
echo APK 文件:
dir /b "k:\huawei\keshihua\demo\*.apk" 2>nul
echo.
echo 将 APK 传到手机安装，Excel 文件放到 /sdcard/LKJ数据/ 目录
echo.
pause
