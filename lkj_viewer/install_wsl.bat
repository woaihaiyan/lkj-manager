@echo off
chcp 65001 >nul
title 安装 WSL 并打包 APK

echo ============================================================
echo   第一步：安装 WSL（仅首次需要，需重启电脑一次）
echo ============================================================
echo.
echo 即将以管理员权限安装 WSL 和 Ubuntu
echo 安装完成后需要重启电脑
echo.
echo 重启后请运行 build_apk.bat 继续打包 APK
echo.
pause

echo 正在安装 WSL...
powershell -Command "Start-Process wsl -ArgumentList '--install','-d','Ubuntu','--no-launch' -Verb RunAs -Wait"

echo.
echo WSL 安装命令已执行
echo 如果提示需要重启，请重启电脑
echo 重启后打开 Ubuntu 设置用户名和密码
echo 然后运行 build_apk.bat 打包 APK
echo.
pause