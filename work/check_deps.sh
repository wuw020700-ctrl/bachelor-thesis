#!/usr/bin/env bash
# 检查 openEMS 编译依赖是否齐备

echo "==== 关键编译依赖 ===="
missing=0
for p in build-essential cmake git libhdf5-dev libboost-all-dev libcgal-dev \
         libvtk9-dev libtinyxml-dev qtbase5-dev qttools5-dev-tools \
         python3-dev python3-pip python3-venv; do
    if dpkg -s "$p" >/dev/null 2>&1; then
        printf '  [OK] %s\n' "$p"
    else
        printf '  [缺] %s\n' "$p"
        missing=$((missing + 1))
    fi
done
echo "  缺失 $missing 个"

echo
echo "==== 工具版本 ===="
cmake --version 2>/dev/null | head -1 || echo "  cmake 缺失"
g++ --version 2>/dev/null | head -1 || echo "  g++ 缺失"
python3 --version 2>/dev/null

echo
echo "==== 机器资源 ===="
echo "  CPU 核数: $(nproc)"
free -h | head -2 | sed 's/^/  /'
df -h "$HOME" | tail -1 | sed 's/^/  磁盘: /'
