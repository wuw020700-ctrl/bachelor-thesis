#!/usr/bin/env bash
# 跑 openEMS 官方角锥喇叭教程，验证整条链路（也正好是我们要的馈源）

export LD_LIBRARY_PATH="$HOME/openems-install/lib:${LD_LIBRARY_PATH:-}"
PY="$HOME/openems-install/venv/bin/python"
T="$HOME/openems-install/share/openEMS/python/Tutorials"
WORK="$HOME/openems-tutorials"

mkdir -p "$WORK"

echo "==== 教程清单 ===="
ls -1 "$T" | sed 's/^/  /'

echo
echo "==== 复制 Horn_Antenna.py 到工作目录 ===="
cp "$T/Horn_Antenna.py" "$WORK/"
wc -l "$WORK/Horn_Antenna.py"

echo
echo "==== 运行（最多 15 分钟）===="
cd "$WORK"
timeout 900 "$PY" Horn_Antenna.py 2>&1 | tail -30
echo "退出码: $?"
