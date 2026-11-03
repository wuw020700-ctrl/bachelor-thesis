#!/usr/bin/env bash
# 检查 openEMS 源码树的克隆状态

SRC="$HOME/openems-src"

echo "==== 目录: $SRC ===="
if [ ! -d "$SRC" ]; then
    echo "  不存在"
    exit 1
fi
ls -la "$SRC" | head -25

echo
echo "==== 各子目录文件数 ===="
for d in "$SRC"/*/; do
    [ -d "$d" ] || continue
    n=$(find "$d" -type f 2>/dev/null | wc -l)
    echo "  $(basename "$d") : $n 个文件"
done

echo
echo "==== git submodule status ===="
cd "$SRC" && git submodule status 2>&1 | head -20

echo
echo "==== 网络: GitHub 可达性 ===="
timeout 15 curl -sI https://github.com 2>&1 | head -1 || echo "  github.com 直连失败/超时"

echo
echo "==== 网络: 镜像可达性 ===="
for m in https://gh-proxy.com https://ghfast.top https://gitclone.com; do
    code=$(timeout 12 curl -s -o /dev/null -w '%{http_code}' "$m" 2>/dev/null)
    echo "  $m -> HTTP ${code:-timeout}"
done
