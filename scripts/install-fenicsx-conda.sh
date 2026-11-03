#!/usr/bin/env bash
# 用 conda-forge 装 FEniCSx（不需要 sudo）
#
#   1) 从清华镜像下载 Miniforge3
#   2) 装到 ~/miniforge3
#   3) 配好清华 conda-forge 镜像（不可达则回退官方源）
#   4) 建 fenicsx 环境装 fenics-dolfinx

set -uo pipefail

MF_URL="https://mirrors.tuna.tsinghua.edu.cn/github-release/conda-forge/miniforge/LatestRelease/Miniforge3-26.7.2-0-Linux-x86_64.sh"
MF_SH="$HOME/miniforge-installer.sh"
MF_DIR="$HOME/miniforge3"
ENV_NAME="fenicsx"

# ---------- 1. 下载 ----------
if [ ! -x "$MF_DIR/bin/conda" ]; then
    if [ ! -s "$MF_SH" ]; then
        echo "==== 下载 Miniforge3 ===="
        curl -L --fail --retry 3 --connect-timeout 20 -o "$MF_SH" "$MF_URL" 2>&1 | tail -2
    fi
    ls -lh "$MF_SH"

    echo
    echo "==== 静默安装到 $MF_DIR ===="
    bash "$MF_SH" -b -p "$MF_DIR" 2>&1 | tail -8
else
    echo "==== Miniforge 已存在: $MF_DIR ===="
fi

CONDA="$MF_DIR/bin/conda"
[ -x "$CONDA" ] || { echo "[X] conda 安装失败"; exit 1; }
"$CONDA" --version

# ---------- 2. 配镜像 ----------
echo
echo "==== 配置 conda 源 ===="
TUNA="https://mirrors.tuna.tsinghua.edu.cn/anaconda"
if timeout 25 curl -s -o /dev/null -w '%{http_code}' "$TUNA/cloud/conda-forge/linux-64/repodata.json" | grep -q 200; then
    echo "  清华 conda-forge 可达，使用镜像"
    "$CONDA" config --set show_channel_urls yes >/dev/null
    cat > "$HOME/.condarc" <<EOF
channels:
  - conda-forge
default_channels:
  - $TUNA/pkgs/main
  - $TUNA/pkgs/r
custom_channels:
  conda-forge: $TUNA/cloud/conda-forge
  bioconda: $TUNA/cloud/bioconda
show_channel_urls: true
channel_priority: flexible
EOF
else
    echo "  清华源不可达，使用官方 conda-forge"
fi

# ---------- 3. 建环境 ----------
echo
echo "==== 创建 $ENV_NAME 环境（这一步下载量较大）===="
"$CONDA" create -y -n "$ENV_NAME" -c conda-forge \
    python=3.11 \
    fenics-dolfinx \
    fenics-basix \
    fenics-ufl \
    fenics-ffcx \
    petsc4py \
    mpi4py \
    mpich \
    pyvista \
    gmsh \
    numpy scipy matplotlib h5py meshio 2>&1 | tail -20

PY="$MF_DIR/envs/$ENV_NAME/bin/python"
[ -x "$PY" ] || { echo "[X] 环境创建失败"; exit 1; }

# ---------- 4. 验证 ----------
echo
echo "==== 验证 ===="
"$PY" - <<'PYEOF'
import sys
print("python:", sys.version.split()[0])
mods = ["numpy", "scipy", "matplotlib", "h5py", "mpi4py",
        "dolfinx", "basix", "ufl", "ffcx", "petsc4py", "gmsh", "pyvista", "meshio"]
bad = []
for m in mods:
    try:
        mod = __import__(m)
        print(f"  [OK]   {m:<10} {getattr(mod, '__version__', '?')}")
    except Exception as exc:
        print(f"  [FAIL] {m:<10} {type(exc).__name__}: {exc}")
        bad.append(m)
print()
print("失败:", ", ".join(bad) if bad else "无")
PYEOF

echo
echo "==== 最小求解测试 ===="
"$PY" - <<'PYEOF'
try:
    from mpi4py import MPI
    from dolfinx import mesh, fem
    import ufl
    m = mesh.create_unit_square(MPI.COMM_WORLD, 8, 8)
    V = fem.functionspace(m, ("Lagrange", 1))
    u, v = ufl.TrialFunction(V), ufl.TestFunction(V)
    A = fem.assemble_matrix(fem.form(ufl.inner(ufl.grad(u), ufl.grad(v)) * ufl.dx))
    A.scatter_reverse()
    print("  [OK] 网格 + 函数空间 + 矩阵装配全部通过")
except Exception:
    import traceback
    traceback.print_exc()
    print("  [FAIL] 求解链路未打通")
PYEOF

echo
echo "用法: $MF_DIR/bin/conda activate $ENV_NAME"
