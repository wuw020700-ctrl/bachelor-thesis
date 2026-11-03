"""Probe the FEniCSx environment and report what actually works.

Run with the conda env python:
    C:\\Users\\ww\\.conda\\envs\\fenicsx\\python.exe src\\fenics\\check_env.py
"""

import sys

print("python:", sys.version.split()[0])

results = {}

def probe(name, fn):
    try:
        value = fn()
        results[name] = ("OK", value)
    except Exception as exc:  # noqa: BLE001 - diagnostic script
        results[name] = ("FAIL", f"{type(exc).__name__}: {exc}")


probe("mpi4py", lambda: __import__("mpi4py").__version__)
probe("dolfinx", lambda: __import__("dolfinx").__version__)
probe("basix", lambda: __import__("basix").__version__)
probe("ufl", lambda: __import__("ufl").__version__)
probe("petsc4py", lambda: __import__("petsc4py").__version__)
probe("gmsh", lambda: __import__("gmsh").__version__ if hasattr(__import__("gmsh"), "__version__") else "imported")
probe("pyvista", lambda: __import__("pyvista").__version__)


def build_mesh():
    from mpi4py import MPI
    from dolfinx import mesh

    m = mesh.create_unit_square(MPI.COMM_WORLD, 8, 8)
    return f"cells={m.topology.index_map(m.topology.dim).size_local}"


probe("mesh.create_unit_square", build_mesh)


def function_space():
    from mpi4py import MPI
    from dolfinx import mesh, fem

    m = mesh.create_unit_square(MPI.COMM_WORLD, 8, 8)
    V = fem.functionspace(m, ("Lagrange", 1))
    return f"dofs={V.dofmap.index_map.size_global}"


probe("fem.functionspace", function_space)


def assemble_matrix():
    from mpi4py import MPI
    from dolfinx import mesh, fem, default_scalar_type
    from dolfinx.fem import form
    import ufl

    m = mesh.create_unit_square(MPI.COMM_WORLD, 8, 8)
    V = fem.functionspace(m, ("Lagrange", 1))
    u, v = ufl.TrialFunction(V), ufl.TestFunction(V)
    a = form(ufl.inner(ufl.grad(u), ufl.grad(v)) * ufl.dx)
    A = fem.assemble_matrix(a)
    A.scatter_reverse()
    return f"matrix assembled, nnz={A.squared_norm() is not None}"


probe("assemble_matrix", assemble_matrix)

print()
width = max(len(k) for k in results)
for name, (status, detail) in results.items():
    mark = "OK  " if status == "OK" else "FAIL"
    print(f"[{mark}] {name:<{width}}  {detail}")

print()
missing = [k for k, (s, _) in results.items() if s == "FAIL"]
if missing:
    print("missing/broken:", ", ".join(missing))
else:
    print("all probes passed")
