#!/usr/bin/env bash
# 修复 openEMS 子模块克隆失败（GitHub 直连不通，改走镜像）
#
# 用法:  bash scripts/fix-openems-clone.sh
#
# 说明：用 git 的 insteadOf 把 github.com 重写到 gh-proxy.com 镜像，
#       这个设置通过 -c 传下去，会一并作用于子模块，不写进全局配置。

set -uo pipefail

MIRROR="https://gh-proxy.com/https://github.com/"
SRC="$HOME/openems-src"

if [ ! -d "$SRC/.git" ]; then
    echo "[X] 没找到 $SRC，请先跑过 scripts/bootstrap-ubuntu.sh"
    exit 1
fi

echo "==== 镜像可用性 ===="
if ! timeout 30 git ls-remote "${MIRROR}thliebig/openEMS.git" HEAD >/dev/null 2>&1; then
    echo "[X] 镜像 $MIRROR 不可用，换一个："
    echo "    ghfast.top  /  gitclone.com"
    exit 1
fi
echo "[OK] $MIRROR 可用"

GITOPTS=(
    -c "url.${MIRROR}.insteadOf=https://github.com/"
    -c http.version=HTTP/1.1
    -c http.postBuffer=524288000
    -c http.lowSpeedLimit=0
    -c http.lowSpeedTime=999999
)

cd "$SRC"

echo
echo "==== 同步子模块 URL ===="
git "${GITOPTS[@]}" submodule sync --recursive

echo
echo "==== 拉取子模块（失败会自动重试 3 次）===="
ok=0
for attempt in 1 2 3; do
    echo "--- 第 $attempt 次 ---"
    if git "${GITOPTS[@]}" submodule update --init --recursive; then
        ok=1
        break
    fi
    echo "    第 $attempt 次失败，10 秒后重试..."
    sleep 10
done

echo
echo "==== 结果 ===="
git submodule status

echo
echo "==== 各子模块文件数 ===="
for d in "$SRC"/*/; do
    [ -d "$d" ] || continue
    n=$(find "$d" -type f 2>/dev/null | wc -l)
    printf '  %-14s %s 个文件\n' "$(basename "$d")" "$n"
done

if [ "$ok" -eq 1 ]; then
    echo
    echo "[OK] 子模块拉取完成，可以继续编译："
    echo "     cd ~/openems-src && ./update_openEMS.sh"
else
    echo
    echo "[X] 三次都失败。把上面的输出发我。"
    exit 1
fi
