#!/usr/bin/env bash
# 查看 openEMS / CSXCAD Python 绑定的实际 API

export LD_LIBRARY_PATH="$HOME/openems-install/lib:${LD_LIBRARY_PATH:-}"
PY="$HOME/openems-install/venv/bin/python"
T="$HOME/openems-install/share/openEMS/python/Tutorials"

echo "==== 教程里用到的 Add* 方法 ===="
grep -ohE '\.Add[A-Za-z]+' "$T"/*.py 2>/dev/null | sort -u | head -30

echo
echo "==== 教程里端口/激励的写法 ===="
grep -nE 'Port|Excite|Excitation' "$T"/Simple_Patch_Antenna.py 2>/dev/null | head -12

echo
echo "==== ContinuousStructure 的 Add* 方法（运行时反射） ===="
"$PY" - <<'PYEOF'
from CSXCAD import ContinuousStructure
csx = ContinuousStructure()
names = [n for n in dir(csx) if n.startswith("Add")]
print("  " + "\n  ".join(sorted(names)))
print()
print("==== 网格对象方法 ====")
mesh = csx.GetGrid()
print("  " + "\n  ".join(sorted(n for n in dir(mesh) if not n.startswith("_"))[:25]))
PYEOF

echo
echo "==== openEMS 对象的方法 ===="
"$PY" - <<'PYEOF'
from openEMS import openEMS
f = openEMS()
names = [n for n in dir(f) if not n.startswith("_")]
print("  " + "\n  ".join(sorted(names)[:35]))
PYEOF
