#!/bin/bash
cd /home/adminuser/lkj_build || exit 1
export JAVA_HOME=$(dirname $(dirname $(readlink -f $(which java))))
export PATH="$JAVA_HOME/bin:$PATH"
source /home/adminuser/p4a_env/bin/activate
echo "=== build started $(date) ===" > /home/adminuser/lkj_build/build.log
buildozer android debug >> /home/adminuser/lkj_build/build.log 2>&1
echo "=== BUILD_EXIT=$? $(date) ===" >> /home/adminuser/lkj_build/build.log