#!/usr/bin/env bash
# WSL 侧环境收尾：
#   1) 把 openEMS 的 PATH / LD_LIBRARY_PATH 写进 ~/.bashrc
#   2) 建 Python 虚拟环境并安装 FEniCSx（走 PyPI 的 Linux 轮子，不用 sudo）
#
# 用法: bash scripts/setup-wsl-env.sh

set -uo pipefail

PREFIX="$HOME/openems-install"
VENV="$HOME/fenicsx-venv"
PY="$VENV/bin/python"
INDEX="https://pypi.tuna.tsinghua.edu.cn/simple"

echo "==== 1. openEMS 环境变量 ===="
MARK="# >>> openEMS local install >>>"
if grep -qF "$MARK" "$HOME/.bashrc" 2>/dev/null; then
    echo "  已存在，跳过"
else
    cat >> "$HOME/.bashrc" <<EOF

$MARK
export PATH="$PREFIX/bin:\$PATH"
export LD_LIBRARY_PATH="$PREFIX/lib:\${LD_LIBRARY_PATH:-}"
export CMAKE_PREFIX_PATH="$PREFIX:\${CMAKE_PREFIX_PATH:-}"
# <<< openEMS local install <<<
EOF
    echo "  已写入 ~/.bashrc"
fi
export PATH="$PREFIX/bin:$PATH"
export LD_LIBRARY_PATH="$PREFIX/lib:${LD_LIBRARY_PATH:-}"

echo
echo "==== 2. 创建虚拟环境 ===="
if [ ! -x "$PY" ]; then
    python3 -m venv "$VENV"
    echo "  已创建 $VENV"
else
    echo "  已存在 $VENV"
fi
"$PY" -m pip install --upgrade pip --index-url "$INDEX" 2>&1 | tail -2

echo
echo "==== 3. 安装 FEniCSx 与配套包 ===="
"$PY" -m pip install \
    --index-url "$INDEX" \
    --timeout 120 \
    numpy scipy matplotlib h5py \
    fenics-dolfinx fenics-basix fenics-ufl fenics-ffcx petsc4py mpi4py \
    gmsh meshio pyvista 2>&1 | tail -12

echo
echo "==== 4. 验证 ===="
"$PY" - <<'PYEOF'
import sys
print("python:", sys.version.split()[0])
mods = ["numpy", "scipy", "matplotlib", "h5py", "mpi4py",
        "dolfinx", "basix", "ufl", "ffcx", "petsc4py", "gmsh", "pyvista", "meshio"]
bad = []
for m in mods:
    try:
        mod = __import__(m)
        v = getattr(mod, "__version__", "?")
        print(f"  [OK]   {m:<10} {v}")
    except Exception as exc:
        print(f"  [FAIL] {m:<10} {type(exc).__name__}: {exc}")
        bad.append(m)
print()
if bad:
    print("失败:", ", ".join(bad))
else:
    print("全部导入成功")
PYEOF

echo
echo "==== 5. 最小 FEniCSx 求解测试 ===="
"$PY" - <<'PYEOF'
try:
    from mpi4py import MPI
    from dolfinx import mesh, fem, la
    import ufl
    m = mesh.create_unit_square(MPI.COMM_WORLD, 8, 8)
    V = fem.functionspace(m, ("Lagrange", 1))
    u, v = ufl.TrialFunction(V), ufl.TestFunction(V)
    a = fem.form(ufl.inner(ufl.grad(u), ufl.grad(v)) * ufl.dx)
    A = fem.assemble_matrix(a)
    A.scatter_reverse()
    print("  [OK] 网格 + 函数空间 + 矩阵装配全部通过")
except Exception as exc:
    import traceback
    traceback.print_exc()
    print("  [FAIL] FEniCSx 求解链路未打通")
PYEOF

echo
echo "完成。之后用:  source ~/.bashrc && $PY <脚本>"
