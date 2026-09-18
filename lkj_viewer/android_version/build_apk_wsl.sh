#!/bin/bash
# WSL 中执行: wsl bash /mnt/k/huawei/keshihua/demo/lkj_viewer/android_version/build_apk_wsl.sh

set -e

echo "================================================================"
echo "    LKJ 数据管理 - Android APK 打包脚本 (WSL)"
echo "================================================================"
echo ""

# 1. 检查并安装 Python3
if ! command -v python3 &> /dev/null; then
    echo "[1/6] 安装 Python3..."
    sudo apt-get update -qq
    sudo apt-get install -y -qq python3 python3-pip python3-venv
else
    echo "[1/6] Python3 已安装"
fi

# 2. 安装系统依赖
echo "[2/6] 安装系统依赖..."
sudo apt-get update -qq
sudo apt-get install -y -qq \
    git zip unzip openjdk-17-jdk \
    python3-setuptools python3-wheel python3-dev \
    autoconf libtool pkg-config \
    zlib1g-dev libncurses5-dev libncursesw5-dev \
    cmake libffi-dev libssl-dev
# libtinfo5 在新版 Ubuntu 中可能不存在，忽略错误
sudo apt-get install -y -qq libtinfo5 2>/dev/null || true

# 3. 创建虚拟环境
VENV_PATH="$HOME/p4a_env"
if [ ! -d "$VENV_PATH" ]; then
    echo "[3/6] 创建虚拟环境..."
    python3 -m venv "$VENV_PATH"
fi
source "$VENV_PATH/bin/activate"
echo "[3/6] 虚拟环境已激活"

# 4. 安装 Python 依赖
echo "[4/6] 安装 buildozer / p4a / 依赖..."
pip install --upgrade pip
pip install --upgrade buildozer Cython==0.29.36 python-for-android sh jinja2

# 5. 配置环境变量
export JAVA_HOME=$(dirname $(dirname $(readlink -f $(which java))))
export PATH="$JAVA_HOME/bin:$PATH"
echo "[5/6] JAVA_HOME=$JAVA_HOME"

# 进入项目目录
cd /mnt/k/huawei/keshihua/demo/lkj_viewer/android_version
cp ../excel_handler.py . 2>/dev/null || true

echo ""
echo "================================================================"
echo "   开始打包 APK"
echo "   首次需下载 SDK/NDK (~1-2GB)，耗时 20-40 分钟"
echo "================================================================"
echo ""

# 6. 运行 buildozer
buildozer android debug

echo ""
echo "================================================================"

APK_FILE=$(find bin/ -name "*.apk" 2>/dev/null | head -1)
if [ -n "$APK_FILE" ]; then
    echo "成功! APK: $APK_FILE"
    echo "大小: $(du -h "$APK_FILE" | cut -f1)"
    cp "$APK_FILE" /mnt/k/huawei/keshihua/demo/
    echo "已复制到: K:\\huawei\\keshihua\\demo\\$(basename "$APK_FILE")"
else
    echo "警告: 未找到 APK，请检查构建日志"
fi
echo ""
echo "将 APK 传到手机安装，Excel 放到 /sdcard/LKJ数据/ 目录"
echo "================================================================"
