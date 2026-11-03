#!/usr/bin/env bash
# 补齐 gmsh python 模块，并对 FEniCSx 做一次真实求解验证（Poisson）

export PATH="$HOME/miniforge3/bin:$PATH"
PY="$HOME/miniforge3/envs/fenicsx/bin/python"
PIP="$HOME/miniforge3/envs/fenicsx/bin/pip"
INDEX="https://pypi.tuna.tsinghua.edu.cn/simple"

echo "==== 补装 gmsh python 模块 ===="
"$PIP" install gmsh --index-url "$INDEX" --timeout 90 2>&1 | tail -4

echo
echo "==== 导入检查 ===="
"$PY" - <<'PYEOF'
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
print("失败:", ", ".join(bad) if bad else "无")
PYEOF

echo
echo "==== 真实求解：二维 Poisson -Δu = 1, u=0 on boundary ===="
"$PY" - <<'PYEOF'
import numpy as np
from mpi4py import MPI
from dolfinx import mesh, fem, default_scalar_type
from dolfinx.fem.petsc import LinearProblem
import ufl

m = mesh.create_unit_square(MPI.COMM_WORLD, 32, 32)
V = fem.functionspace(m, ("Lagrange", 1))

# 必须加 Dirichlet 边界条件，否则 Laplacian 奇异（常数在零空间里），
# 解会漂移到任意大的值。
tdim = m.topology.dim
fdim = tdim - 1
m.topology.create_connectivity(fdim, tdim)
facets = mesh.exterior_facet_indices(m.topology)
dofs = fem.locate_dofs_topological(V, fdim, facets)
bc = fem.dirichletbc(default_scalar_type(0.0), dofs, V)

u = ufl.TrialFunction(V)
v = ufl.TestFunction(V)
f = fem.Constant(m, default_scalar_type(1.0))
a = ufl.inner(ufl.grad(u), ufl.grad(v)) * ufl.dx
L = f * v * ufl.dx

problem = LinearProblem(a, L, bcs=[bc], petsc_options_prefix="poisson_",
                        petsc_options={"ksp_type": "cg", "pc_type": "jacobi"})
uh = problem.solve()

arr = uh.x.array
print(f"  自由度        : {arr.size}")
print(f"  解的范围      : {arr.min():.6f} .. {arr.max():.6f}")
print(f"  峰值理论值    : 0.0736 (单位方域 Poisson 的解析中心值)")
print(f"  误差          : {abs(arr.max() - 0.0736):.2e}")
print("  [OK] FEniCSx 完整求解链路可用" if abs(arr.max() - 0.0736) < 5e-3
      else "  [FAIL] 数值不对")
PYEOF

echo
echo "==== 环境激活方式 ===="
echo "  export PATH=\"\$HOME/miniforge3/bin:\$PATH\""
echo "  conda activate fenicsx"
