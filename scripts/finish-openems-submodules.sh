#!/usr/bin/env bash
# 修复「子模块 git 目录在、但工作区是空的」这种残状态
#
# 现象：CSXCAD 等目录里只剩一个 .git 文件，源码没检出。
#       git submodule status 却报告它们在正确 commit 上，所以
#       git submodule update 会跳过它们。
#
# 处理：先尝试 --force 重新检出；仍为空就对每个子模块单独 checkout -f。

set -uo pipefail

MIRROR="https://gh-proxy.com/https://github.com/"
SRC="$HOME/openems-src"
SUBS=(CSXCAD AppCSXCAD QCSXCAD CTB fparser hyp2mat openEMS)

[ -d "$SRC/.git" ] || { echo "[X] 没找到 $SRC"; exit 1; }

cd "$SRC"

GITOPTS=(
    -c "url.${MIRROR}.insteadOf=https://github.com/"
    -c http.version=HTTP/1.1
    -c http.lowSpeedLimit=0
    -c http.lowSpeedTime=999999
)

echo "==== 先试标准的 force 检出 ===="
git "${GITOPTS[@]}" submodule update --init --recursive --force --checkout || true

echo
echo "==== 逐个检查，仍为空的单独恢复 ===="
for d in "${SUBS[@]}"; do
    [ -d "$d" ] || { echo "  $d : 目录不存在，跳过"; continue; }
    n=$(ls -A "$d" 2>/dev/null | wc -l)
    if [ "$n" -gt 1 ]; then
        echo "  $d : 正常（$n 个条目）"
        continue
    fi
    echo "  $d : 空，执行 checkout -f ..."
    if git -C "$d" checkout -f >/dev/null 2>&1; then
        n2=$(ls -A "$d" 2>/dev/null | wc -l)
        echo "     -> 恢复后 $n2 个条目"
    else
        echo "     -> checkout 失败，尝试重新拉取"
        git "${GITOPTS[@]}" submodule update --init --force "$d" >/dev/null 2>&1 \
            && echo "     -> 重拉成功" || echo "     -> 重拉也失败"
    fi
done

echo
echo "==== 最终状态 ===="
git submodule status
echo
for d in "${SUBS[@]}"; do
    n=$(ls -A "$d" 2>/dev/null | wc -l)
    printf '  %-14s %s 个条目\n' "$d" "$n"
done

echo
echo "==== 关键文件抽查 ===="
for f in CSXCAD/CMakeLists.txt openEMS/CMakeLists.txt AppCSXCAD/CMakeLists.txt; do
    if [ -f "$f" ]; then echo "  [OK] $f"; else echo "  [缺] $f"; fi
done
