"""Minimal repro: isolate the basix type-mapping failure."""

import traceback

from mpi4py import MPI
from dolfinx import mesh, fem
import ufl
import basix

print("dolfinx:", __import__("dolfinx").__version__)
print("basix :", basix.__version__)
print("ufl   :", ufl.__version__)

m = mesh.create_unit_square(MPI.COMM_WORLD, 4, 4)
print("cell name:", m.basix_cell())

V = fem.functionspace(m, ("Lagrange", 1))
u = ufl.TrialFunction(V)
v = ufl.TestFunction(V)

try:
    dx = ufl.Measure("dx", domain=m)
    print("measure ok:", dx)
    a = ufl.inner(ufl.grad(u), ufl.grad(v)) * dx
    print("form built:", type(a).__name__)
except Exception:
    traceback.print_exc()

try:
    a = fem.form(ufl.inner(ufl.grad(u), ufl.grad(v)) * ufl.Measure("dx", domain=m))
    print("fem.form ok")
    A = fem.assemble_matrix(a)
    A.scatter_reverse()
    print("assemble_matrix ok")
except Exception:
    traceback.print_exc()
