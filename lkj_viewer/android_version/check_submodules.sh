#!/bin/bash
APK=/home/adminuser/lkj_build/bin/lkjmanager-1.0.0-arm64-v8a-debug.apk
echo "=== pybundle 内 Python 模块 ==="
cd /tmp && unzip -o -q "$APK" "lib/arm64-v8a/libpybundle.so" -d /tmp/apk_check 2>/dev/null
strings /tmp/apk_check/lib/arm64-v8a/libpybundle.so 2>/dev/null | grep -E "^main\.py|^excel_handler\.py|^app\.py|sitecustomize" | head -8
echo "=== aapt 包信息 ==="
AAPT=$(find /home/adminuser/.buildozer/android/platform/android-sdk/build-tools -name aapt2 -type f 2>/dev/null | sort -V | tail -1)
echo "aapt2: $AAPT"
"$AAPT" dump badging "$APK" 2>/dev/null | grep -E "package:|launchable-activity|application-label|sdkVersion|targetSdkVersion|native-code" | head -8