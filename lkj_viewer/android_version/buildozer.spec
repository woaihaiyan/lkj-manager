[app]

title = LKJ数据管理
package.name = lkjmanager
package.domain = org.lkj
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt,json,xlsx
source.exclude_dirs = tests,bin,build,dist,__pycache__,templates,static,.buildozer,python-for-android,.github
source.exclude_patterns = app.py,build_android.py,doc_parser.py,build_apk_wsl.sh
android.accept_all_licenses = True
version = 1.0.0

requirements = python3,kivy,openpyxl

orientation = portrait

fullscreen = 0

permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

android.api = 31
android.minapi = 24
# 如需兼容老 32 位手机，改为: android.archs = arm64-v8a,armeabi-v7a
android.archs = arm64-v8a
android.allow_backup = 1

[buildozer]

log_level = 2
warn_on_root = 1
