#!/usr/bin/env bash
# 探测 openEMS / FEniCSx 的实际可用接口，供写使用文档参考

export PATH="$HOME/openems-install/bin:$HOME/miniforge3/bin:$PATH"
export LD_LIBRARY_PATH="$HOME/openems-install/lib:${LD_LIBRARY_PATH:-}"

echo "==== openEMS 安装的 Python 相关文件 ===="
find "$HOME/openems-install" -name "*.py" -path "*python*" 2>/dev/null | head -10
echo
echo "==== 有没有 CSXCAD / openEMS python 模块 ===="
python3 -c "import CSXCAD; print('CSXCAD OK', CSXCAD.__file__)" 2>&1 | head -2
python3 -c "import openEMS; print('openEMS OK', openEMS.__file__)" 2>&1 | head -2

echo
echo "==== 教程目录 ===="
ls -1 "$HOME/openems-install/share/openEMS/python/Tutorials" 2>/dev/null | head -20

echo
echo "==== 教程用到的 import ===="
if [ -f "$HOME/openems-install/share/openEMS/python/Tutorials/Horn_Antenna.py" ]; then
    grep -nE '^(import|from)' "$HOME/openems-install/share/openEMS/python/Tutorials/Horn_Antenna.py" | head -12
fi

echo
echo "==== python3 版本与 pip 包 ===="
python3 --version
python3 -m pip list 2>/dev/null | grep -iE 'csxcad|openems|h5py|numpy|matplotlib' || echo "  (系统 python 里没有相关包)"

echo
echo "==== conda 环境里的 openEMS 相关包 ===="
"$HOME/miniforge3/envs/fenicsx/bin/pip" list 2>/dev/null | grep -iE 'csxcad|openems' || echo "  (没有)"
