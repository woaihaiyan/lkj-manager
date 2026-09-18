#!/bin/bash
J=/home/adminuser/lkj_build/.buildozer/android/platform/build-arm64-v8a/build/bootstrap_builds/sdl2/jni
for m in SDL2_image SDL2_mixer SDL2_ttf; do
  echo "===== $m ====="
  if [ -f "$J/$m/.gitmodules" ]; then
    grep -E "path =|url =|branch =" "$J/$m/.gitmodules"
  else
    echo "(no .gitmodules)"
  fi
done