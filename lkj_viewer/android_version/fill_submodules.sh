#!/bin/bash
J=/home/adminuser/lkj_build/.buildozer/android/platform/build-arm64-v8a/build/bootstrap_builds/sdl2/jni
LOG=/home/adminuser/lkj_build/submodules.log
echo "=== submodule fill started $(date) ===" > "$LOG"

clone_one() {
  local path="$1" url="$2" branch="$3"
  if [ -d "$path" ] && [ -n "$(ls -A "$path" 2>/dev/null)" ]; then
    echo "EXISTS $path" >> "$LOG"
    return 0
  fi
  mkdir -p "$(dirname "$path")"
  echo "CLONING $path <- ${url} ${branch:+@$branch}" >> "$LOG"
  if [ -n "$branch" ]; then
    git clone --depth 1 -b "$branch" "$url" "$path" >> "$LOG" 2>&1
  else
    git clone --depth 1 "$url" "$path" >> "$LOG" 2>&1
  fi
  if [ -d "$path" ] && [ -n "$(ls -A "$path" 2>/dev/null)" ]; then
    echo "OK $path" >> "$LOG"
  else
    echo "BRANCH-FAIL, retry without branch: $path" >> "$LOG"
    mv "$path" "$path.bad.$$" 2>/dev/null
    git clone --depth 1 "$url" "$path" >> "$LOG" 2>&1
    if [ -d "$path" ] && [ -n "$(ls -A "$path" 2>/dev/null)" ]; then
      echo "OK2 $path" >> "$LOG"
    else
      echo "FAILED $path" >> "$LOG"
    fi
  fi
}

I=$J/SDL2_image/external
T=$J/SDL2_image/external/libjxl/third_party
M=$J/SDL2_mixer/external
F=$J/SDL2_ttf/external

# SDL2_image
clone_one "$I/libavif"   https://github.com/libsdl-org/libavif.git  v1.0.3-SDL
clone_one "$I/dav1d"     https://github.com/libsdl-org/dav1d.git    1.2.1-SDL
# libjxl third_party
clone_one "$T/lodepng"   https://github.com/lvandeve/lodepng        ""
clone_one "$T/lcms"      https://github.com/mm2/Little-CMS         ""
clone_one "$T/googletest" https://github.com/google/googletest     ""
clone_one "$T/sjpeg"     https://github.com/webmproject/sjpeg.git  ""
clone_one "$T/skcms"     https://github.com/google/skcms           ""
clone_one "$T/brotli"    https://github.com/libsdl-org/brotli.git  v1.0.9-SDL
clone_one "$T/highway"   https://github.com/libsdl-org/highway.git 0.15.0-SDL
# SDL2_mixer
clone_one "$M/flac"      https://github.com/libsdl-org/flac.git     1.3.4-SDL
clone_one "$M/ogg"       https://github.com/libsdl-org/ogg.git      v1.3.5-SDL
clone_one "$M/vorbis"    https://github.com/libsdl-org/vorbis.git   v1.3.7-SDL
clone_one "$M/opus"      https://github.com/libsdl-org/opus.git     v1.3.1-SDL
clone_one "$M/opusfile"  https://github.com/libsdl-org/opusfile.git v0.12-SDL
clone_one "$M/tremor"    https://github.com/libsdl-org/tremor.git   v1.2.1-SDL
clone_one "$M/libmodplug" https://github.com/libsdl-org/libmodplug.git v0.8.9.0-SDL
clone_one "$M/mpg123"    https://github.com/libsdl-org/mpg123.git   v1.29.3-SDL
# SDL2_ttf
clone_one "$F/freetype"  https://github.com/libsdl-org/freetype.git  VER-2-13-2-SDL
clone_one "$F/harfbuzz"  https://github.com/libsdl-org/harfbuzz.git  8.1.1-SDL

echo "=== done $(date) ===" >> "$LOG"
echo ALLDONE