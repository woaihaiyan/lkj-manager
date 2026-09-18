# LKJ 数据管理 - APK 打包成功记录（2026-09-18）

## 产物

| 项目 | 值 |
|------|-----|
| APK 文件 | `K:\huawei\keshihua\demo\lkjmanager-1.0.0-arm64-v8a-debug.apk` |
| 大小 | 20.3 MB |
| 包名 | `org.lkj.lkjmanager` |
| 版本 | 1.0.0 |
| 应用名 | LKJ数据管理 |
| 架构 | arm64-v8a（64 位，2018 年后手机均支持） |
| minSdk / targetSdk | 24 / 31 |

副本：`K:\huawei\keshihua\demo\lkj_viewer\android_version\bin\lkjmanager-1.0.0-arm64-v8a-debug.apk`

## 之前 WSL 打包一直报错的原因（已全部解决）

### 1. git 代理失效（最根本原因）
WSL 的 `~/.gitconfig` 里配置了 `http.proxy = http://192.168.1.34:7890`（指向 Windows 上的代理软件），但代理软件没有运行、7890 端口无监听，导致 WSL 里**所有** GitHub 访问全部失败（`Failed to connect to github.com port 443 via 192.168.1.34`）。
- 处理：移除该代理配置（备份在 `~/.gitconfig.bak`），实测 WSL 直连 GitHub 正常。

### 2. GitHub 直连不稳定（时好时坏）
小文件下载能成，大仓库 git clone 会被掐断（134 秒超时 / HTTP2 framing 错误）。
- 处理：python-for-android 源码改从 **gitee 镜像** clone（`gitee.com/mirrors/python-for-android`），remote 指回官方地址通过 buildozer 检查。
- SDL2_image / SDL2_mixer / SDL2_ttf 的 19 个第三方子模块，git clone 失败的改用 **codeload.github.com 下载 zip 解压**补齐（该通道稳定）。skia.googlesource.com（被墙）的 skcms 用 GitHub 官方镜像 `github.com/google/skcms` 替代。

### 3. kivy 强制拉入网络库导致 pip 平台校验失败
kivy recipe 的 `python_depends` 包含 `requests/chardet/urllib3/idna/certifi/filetype`，其传递依赖 charset_normalizer 的 android wheel 被 pip 判为平台不兼容（p4a 与新版 pip 的兼容问题）。
- 处理：本应用是离线工具，不需要网络库。修改 WSL 构建目录内 p4a 源码：
  `python-for-android/pythonforandroid/recipes/kivy/__init__.py` 第 37 行
  `python_depends = ['certifi', 'chardet', 'idna', 'requests', 'urllib3', 'filetype']`
  → `python_depends = []  # network deps removed for offline app`
  （原文件备份为 `__init__.py.bak.orig`）

### 4. build venv 的 pip 损坏
之前构建中断导致 `build/venv` 里的 pip 内部模块版本不一致（`ImportError: cannot import name 'BuildDependencyInstallError'`）。
- 处理：将该 venv 移走，p4a 自动重建。

## 成功打包的环境与命令

构建在 **WSL 内部文件系统**进行（`/home/adminuser/lkj_build`），不在 /mnt/k 挂载盘上（避免 IO 慢和兼容问题）：

```bash
# 1. 准备构建目录（只复制干净源码）
mkdir -p ~/lkj_build
cp /mnt/k/huawei/keshihua/demo/lkj_viewer/android_version/{main.py,excel_handler.py,buildozer.spec} ~/lkj_build/

# 2. 配置环境并构建
cd ~/lkj_build
export JAVA_HOME=$(dirname $(dirname $(readlink -f $(which java))))
source ~/p4a_env/bin/activate
buildozer android debug
```

## buildozer.spec 的改动（相对原配置）

- `android.archs`：`arm64-v8a,armeabi-v7a` → `arm64-v8a`（只打 64 位，构建时间减半；如需兼容老 32 位手机，改回双架构即可，但耗时更长）
- `source.exclude_dirs`：追加 `python-for-android,.github`（防止把 p4a 源码误打包进 APK）

## 后续重新打包（改代码后）

```bash
# 在 Windows 执行
wsl bash /mnt/k/huawei/keshihua/demo/lkj_viewer/android_version/build_fixed.sh
# 产物在 ~/lkj_build/bin/lkjmanager-1.0.0-arm64-v8a-debug.apk，手动复制回 Windows
```

注意：
- 如果重新 clone 了 python-for-android，需重新执行上面的 kivy recipe 修改（问题 3）。
- 如果换了 WSL 发行版或清空 ~/p4a_env，需重新安装 buildozer/python-for-android 依赖。
- 新 APK 是 debug 签名，仅用于内部安装使用；正式分发建议配置 release 签名（`buildozer android release` + keystore）。

## 手机安装

1. 将 APK 传到手机，允许"安装未知来源应用"后安装。
2. 将 Excel 数据文件放到 `/sdcard/LKJ数据/` 目录（文件名：`兰州局工务类LKJ基础数据2026.2.24.xlsx`）。
