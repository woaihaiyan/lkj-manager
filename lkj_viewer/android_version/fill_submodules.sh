#!/bin/bash
T=/home/adminuser/lkj_build/.buildozer/android/platform/build-arm64-v8a/build/bootstrap_builds/sdl2/jni/SDL2_image/external/libjxl/third_party
LOG=/home/adminuser/lkj_build/submodules3.log
echo "=== codeload fill started $(date) ===" > "$LOG"

fill_zip() {
  local path="$1" url="$2" name="$3"
  if [ -d "$path" ] && [ -n "$(ls -A "$path" 2>/dev/null)" ] && [ ! -f "$path/.git" ]; then
    echo "EXISTS $name" >> "$LOG"
    return 0
  fi
  mkdir -p "$path"
  local tmp="/tmp/cd_$name"
  mkdir -p "$tmp"
  echo "DOWNLOAD $name" >> "$LOG"
  timeout 120 curl -sL -o "$tmp/pkg.zip" "$url" >> "$LOG" 2>&1
  if [ -s "$tmp/pkg.zip" ]; then
    (cd "$tmp" && unzip -q -o pkg.zip) >> "$LOG" 2>&1
    local inner=$(ls -d "$tmp"/*/ 2>/dev/null | head -1)
    if [ -n "$inner" ]; then
      mv "$path" "$path.old.$$" 2>/dev/null
      mkdir -p "$path"
      shopt -s dotglob
      mv "$inner"* "$path/" 2>/dev/null
      shopt -u dotglob
      if [ -n "$(ls -A "$path" 2>/dev/null)" ]; then
        echo "OK $name ($(ls -A "$path" | wc -l) items)" >> "$LOG"
      else
        echo "FAILED(empty) $name" >> "$LOG"
      fi
    else
      echo "FAILED(unzip) $name" >> "$LOG"
    fi
  else
    echo "FAILED(download) $name" >> "$LOG"
  fi
}

fill_zip "$T/lodepng"    "https://codeload.github.com/lvandeve/lodepng/zip/refs/heads/master"    lodepng
fill_zip "$T/lcms"       "https://codeload.github.com/mm2/Little-CMS/zip/refs/heads/master"     lcms
fill_zip "$T/googletest" "https://codeload.github.com/google/googletest/zip/refs/heads/main"    googletest
fill_zip "$T/sjpeg"      "https://codeload.github.com/webmproject/sjpeg/zip/refs/heads/master"  sjpeg
fill_zip "$T/brotli"     "https://codeload.github.com/libsdl-org/brotli/zip/refs/heads/v1.0.9-SDL" brotli
fill_zip "$T/highway"    "https://codeload.github.com/libsdl-org/highway/zip/refs/heads/0.15.0-SDL" highway

echo "=== done $(date) ===" >> "$LOG"
echo ALLDONE