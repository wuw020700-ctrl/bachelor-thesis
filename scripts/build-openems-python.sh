#!/usr/bin/env bash
# 补装 openEMS 的 Python 绑定（CSXCAD / openEMS 模块）
#
# 只装编译好的 C++ 部分是不够的：那些教程脚本 `from CSXCAD import ...`
# 需要 Python 绑定，而 --python 选项才会构建它。

set -uo pipefail

SRC="$HOME/openems-src"
PREFIX="$HOME/openems-install"
VENV="$PREFIX/venv"
LOG="$HOME/openems-python-build.log"

[ -x "$SRC/update_openEMS.sh" ] || { echo "[X] 没找到 $SRC/update_openEMS.sh"; exit 1; }

cd "$SRC"

echo "==== 构建 openEMS Python 绑定 ===="
echo "  安装前缀: $PREFIX"
echo "  venv    : $VENV"
echo "  日志    : $LOG"
echo

if ./update_openEMS.sh --njobs="$(nproc)" --python \
        --disable-GUI \
        --skip-dep-check \
        --python-venv-mode venv \
        --python-venv-dir "$VENV" \
        "$PREFIX" 2>&1 | tee "$LOG"; then
    echo
    echo "[OK] 构建完成"
else
    echo
    echo "[!] 构建返回非零，看日志尾部和下面的验证结果"
    tail -25 "$LOG"
fi

echo
echo "==== 验证 Python 绑定 ===="
PY="$VENV/bin/python"
if [ ! -x "$PY" ]; then
    echo "  [X] 没生成 venv: $VENV"
    exit 1
fi

export LD_LIBRARY_PATH="$PREFIX/lib:${LD_LIBRARY_PATH:-}"
"$PY" - <<'PYEOF'
for name in ["CSXCAD", "openEMS"]:
    try:
        mod = __import__(name)
        print(f"  [OK] {name:<8} {getattr(mod, '__file__', '?')}")
    except Exception as exc:
        print(f"  [FAIL] {name:<8} {type(exc).__name__}: {exc}")

try:
    from CSXCAD import ContinuousStructure
    from openEMS import openEMS
    from openEMS.physical_constants import C0
    csx = ContinuousStructure()
    FDTD = openEMS()
    print("  [OK] 能创建 ContinuousStructure / openEMS 对象")
    print(f"  [OK] physical_constants.C0 = {C0}")
except Exception as exc:
    import traceback
    traceback.print_exc()
    print("  [FAIL] 接口不可用")
PYEOF

echo
echo "用法:"
echo "  source $VENV/bin/activate"
echo "  或 $VENV/bin/python <脚本>"
