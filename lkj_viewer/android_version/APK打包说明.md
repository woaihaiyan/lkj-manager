# LKJ 数据管理 - Android APK 打包说明

## 方式一：本地 WSL 打包（推荐）

### 前提条件
- Windows 11（已启用 WSL 2）
- 如未安装 WSL，先运行：
  ```
  wsl --install -d Ubuntu
  ```
  然后**重启电脑**，打开 Ubuntu 设置用户名和密码

### 一键打包
双击 `build_apk.bat` 即可自动完成打包。

或手动在 WSL 中执行：
```bash
wsl bash /mnt/k/huawei/keshihua/demo/lkj_viewer/android_version/build_apk_wsl.sh
```

首次打包需要下载 Android SDK/NDK（约 2GB），耗时 20-30 分钟。
后续打包只需 2-3 分钟。

### 产物
APK 文件位于 `android_version/bin/lkjmanager-1.0.0-debug.apk`

---

## 方式二：GitHub Actions 在线打包

1. 将项目推送到 GitHub 仓库
2. GitHub Actions 自动触发构建（`.github/workflows/build-apk.yml`）
3. 构建完成后在 Actions → Artifacts 下载 APK

优点：无需本地安装任何工具链。

---

## 安装到手机

1. 将 APK 文件传到安卓手机
2. 手机设置 → 安全 → 允许安装未知来源应用
3. 点击 APK 文件安装
4. 打开"LKJ数据管理"应用

### 数据文件放置
将 Excel 文件放到手机存储的 `/sdcard/LKJ数据/` 目录下：
```
/sdcard/LKJ数据/兰州局工务类LKJ基础数据2026.2.24.xlsx
```

---

## Kivy 应用功能

- 工作簿分类列表（4大类13个工作簿）
- 数据表格浏览（分页显示）
- 搜索筛选
- 点击行编辑（整行编辑弹窗）
- 添加/删除行
- 保存回 Excel 文件