#!/usr/bin/env bash
# 查 fenics-dolfinx 在各源的可用性

PY="$HOME/fenicsx-venv/bin/pip"

echo "==== 清华镜像 ===="
timeout 60 "$PY" index versions fenics-dolfinx \
    --index-url https://pypi.tuna.tsinghua.edu.cn/simple 2>&1 | head -4

echo
echo "==== 官方 PyPI ===="
timeout 60 "$PY" index versions fenics-dolfinx \
    --index-url https://pypi.org/simple 2>&1 | head -4

echo
echo "==== 官方 PyPI 上 dolfinx 相关包 ===="
for pkg in fenics-dolfinx dolfinx fenics-basix petsc4py; do
    code=$(timeout 40 curl -s -o /dev/null -w '%{http_code}' "https://pypi.org/pypi/$pkg/json")
    echo "  $pkg -> HTTP $code"
done

echo
echo "==== 本机 python 版本 ===="
"$HOME/fenicsx-venv/bin/python" --version

echo
echo "==== 系统 apt 里有没有 fenicsx ===="
apt-cache policy fenicsx 2>/dev/null | head -5
