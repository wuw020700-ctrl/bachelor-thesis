#!/usr/bin/env bash
# 编译并安装 openEMS 全家桶到用户目录（不需要 sudo）
#
# 用官方顶层驱动 update_openEMS.sh，它按依赖顺序构建：
#   fparser -> CSXCAD -> openEMS -> QCSXCAD -> AppCSXCAD
#
# 装到 $HOME/openems-install，然后把环境变量追加到 ~/.bashrc。

set -uo pipefail

SRC="$HOME/openems-src"
PREFIX="$HOME/openems-install"
LOG="$HOME/openems-build.log"
NJOBS="$(nproc)"

[ -x "$SRC/update_openEMS.sh" ] || { echo "[X] 找不到 $SRC/update_openEMS.sh"; exit 1; }

echo "==== 构建配置 ===="
echo "  源码:   $SRC"
echo "  前缀:   $PREFIX"
echo "  并行:   $NJOBS"
echo "  日志:   $LOG"
echo

cd "$SRC"

echo "==== 开始构建（耗时较长，日志实时写入 $LOG）===="
# 选项是 --njobs=N（不是 -j）；--verbose 让编译进度打到终端
if ./update_openEMS.sh --njobs="$NJOBS" --verbose "$PREFIX" 2>&1 | tee "$LOG"; then
    echo
    echo "[OK] 构建完成"
else
    echo
    echo "[X] 构建失败，日志尾部："
    tail -40 "$LOG"
    exit 1
fi

echo
echo "==== 写入环境变量到 ~/.bashrc ===="
MARK="# >>> openEMS local install >>>"
if ! grep -qF "$MARK" "$HOME/.bashrc" 2>/dev/null; then
    cat >> "$HOME/.bashrc" <<EOF

$MARK
export PATH="$PREFIX/bin:\$PATH"
export LD_LIBRARY_PATH="$PREFIX/lib:\${LD_LIBRARY_PATH:-}"
export CMAKE_PREFIX_PATH="$PREFIX:\${CMAKE_PREFIX_PATH:-}"
export PYTHONPATH="$PREFIX/lib:\${PYTHONPATH:-}"
# <<< openEMS local install <<<
EOF
    echo "  已追加"
else
    echo "  已存在，跳过"
fi

echo
echo "==== 验证 ===="
export PATH="$PREFIX/bin:$PATH"
export LD_LIBRARY_PATH="$PREFIX/lib:${LD_LIBRARY_PATH:-}"
if command -v openEMS >/dev/null 2>&1; then
    echo "  openEMS: $(command -v openEMS)"
    openEMS --version 2>&1 | head -3
else
    echo "  [X] PATH 里找不到 openEMS，检查 $PREFIX/bin"
    ls -la "$PREFIX/bin" 2>/dev/null | head
fi
