#!/usr/bin/env bash
# 查找可用的 miniforge / micromamba 镜像，以及 conda-forge 镜像

echo "==== 清华 miniforge github-release 镜像 ===="
timeout 30 curl -s "https://mirrors.tuna.tsinghua.edu.cn/github-release/conda-forge/miniforge/LatestRelease/" 2>/dev/null \
    | grep -oE 'Miniforge3-[0-9.]+-[0-9]+-Linux-x86_64\.sh' | head -3

echo
echo "==== 清华 anaconda 镜像 (conda-forge) ===="
code=$(timeout 20 curl -s -o /dev/null -w '%{http_code}' "https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge/linux-64/repodata.json")
echo "  conda-forge linux-64 repodata -> HTTP $code"

echo
echo "==== 清华 anaconda 镜像里的 dolfinx ===="
timeout 60 curl -s "https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/conda-forge/linux-64/" 2>/dev/null \
    | grep -oE 'fenics-dolfinx-[0-9][^"<>]*\.conda' | tail -3

echo
echo "==== micromamba 官方源 ===="
code=$(timeout 20 curl -s -o /dev/null -w '%{http_code}' "https://micro.mamba.pm/api/micromamba/linux-64/latest")
echo "  micro.mamba.pm -> HTTP $code"

echo
echo "==== 系统是否已有 conda/mamba ===="
for c in conda mamba micromamba; do
    if command -v "$c" >/dev/null 2>&1; then echo "  [有] $c -> $(command -v $c)"; else echo "  [无] $c"; fi
done
