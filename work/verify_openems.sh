#!/usr/bin/env bash
# 验证 openEMS 安装

P="$HOME/openems-install"
export PATH="$P/bin:$PATH"
export LD_LIBRARY_PATH="$P/lib:${LD_LIBRARY_PATH:-}"

echo "==== 安装前缀 ===="
du -sh "$P" 2>/dev/null

echo
echo "==== bin/ ===="
ls -1 "$P/bin" 2>/dev/null | sed 's/^/  /' || echo "  无"

echo
echo "==== lib/ 主要库 ===="
ls -1 "$P/lib" 2>/dev/null | head -12 | sed 's/^/  /'

echo
echo "==== openEMS 版本 ===="
if command -v openEMS >/dev/null 2>&1; then
    openEMS --version 2>&1 | head -8
else
    echo "  [X] PATH 里没有 openEMS"
fi

echo
echo "==== openEMS 帮助 ===="
openEMS --help 2>&1 | head -15

echo
echo "==== CSXCAD / fparser 是否就位 ===="
for f in "$P/include/CSXCAD/CSXCAD.h" "$P/include/fparser/fparser.h" "$P/include/openEMS/openems.h"; do
    if [ -f "$f" ]; then echo "  [OK] $f"; else echo "  [缺] $f"; fi
done
