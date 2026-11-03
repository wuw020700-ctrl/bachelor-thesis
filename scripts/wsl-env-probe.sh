#!/usr/bin/env bash
# WSL 侧环境探测：输出 KEY=VALUE 行，供 verify-env.ps1 解析

export PATH="$HOME/openems-install/bin:$HOME/miniforge3/bin:$PATH"
export LD_LIBRARY_PATH="$HOME/openems-install/lib:${LD_LIBRARY_PATH:-}"

OPENEMS_BIN=$(command -v openEMS 2>/dev/null || true)
if [ -n "$OPENEMS_BIN" ]; then
    echo "OPENEMS_BIN=$OPENEMS_BIN"
    ver=$(openEMS --version 2>&1 | grep -o 'version v[0-9.]*' | head -1 | sed 's/version //')
    echo "OPENEMS_VER=${ver:-unknown}"
else
    echo "OPENEMS_BIN="
    echo "OPENEMS_VER="
fi

FX="$HOME/miniforge3/envs/fenicsx/bin/python"
if [ -x "$FX" ]; then
    out=$("$FX" - <<'PYEOF' 2>/dev/null
try:
    import dolfinx, petsc4py, mpi4py
    print(f"{dolfinx.__version__}|{petsc4py.__version__}|{mpi4py.__version__}")
except Exception:
    print("||")
PYEOF
    )
    IFS='|' read -r d p m <<< "$out"
    echo "DOLFINX=$d"
    echo "PETSC4PY=$p"
    echo "MPI4PY=$m"
else
    echo "DOLFINX="
    echo "PETSC4PY="
    echo "MPI4PY="
fi

if [ -d "$HOME/openems-install/lib" ]; then
    echo "OPENEMS_LIB=$(ls "$HOME/openems-install/lib"/libopenEMS.so.* 2>/dev/null | head -1 | xargs -r basename)"
else
    echo "OPENEMS_LIB="
fi
