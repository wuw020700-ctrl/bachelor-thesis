#!/usr/bin/env bash
# 在 WSL 的 Ubuntu 里一键装好 openEMS + FEniCSx
#
# 用法:
#   wsl -d Ubuntu-22.04 -- bash -lc "cd /mnt/c/Users/ww/Documents/Codex/2026-10-09/ai && bash scripts/bootstrap-ubuntu.sh"
#
# 全程不需要 sudo（都装到 $HOME）。步骤：
#   1) apt 装编译依赖            <-- 这一步需要 sudo，脚本会提示
#   2) 走镜像拉取 openEMS 子模块
#   3) 编译安装 openEMS 到 ~/openems-install
#   4) 用 conda-forge 装 FEniCSx 到 ~/miniforge3/envs/fenicsx

set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPS=(build-essential cmake git wget libhdf5-dev libboost-all-dev libcgal-dev
      libvtk9-dev libtinyxml-dev python3-dev python3-pip python3-venv curl)

echo "============================================================"
echo " openEMS + FEniCSx 一键安装"
echo "============================================================"
echo

# ---------- 1. apt 依赖（唯一需要 sudo 的地方）----------
echo "== [1/4] 检查编译依赖 =="
missing=()
for p in "${DEPS[@]}"; do
    dpkg -s "$p" >/dev/null 2>&1 || missing+=("$p")
done

if [ "${#missing[@]}" -eq 0 ]; then
    echo "  依赖齐全"
else
    echo "  缺: ${missing[*]}"
    echo "  现在执行 apt-get install（会要你的 Linux 密码，输入时不显示字符）"
    sudo apt-get update
    sudo apt-get install -y "${missing[@]}" || {
        echo "[X] apt 安装失败"; exit 1; }
fi

# ---------- 2. 拉子模块 ----------
echo
echo "== [2/4] 拉取 openEMS 源码（走镜像，GitHub 直连常断）=="
if [ -d "$HOME/openems-src/.git" ]; then
    bash "$HERE/fix-openems-clone.sh" || true
    bash "$HERE/finish-openems-submodules.sh" || true
else
    echo "  浅克隆主仓库 ..."
    git clone --depth 1 \
        https://gh-proxy.com/https://github.com/thliebig/openEMS-Project.git \
        "$HOME/openems-src"
    bash "$HERE/fix-openems-clone.sh" || true
    bash "$HERE/finish-openems-submodules.sh" || true
fi

# ---------- 3. 编译 openEMS ----------
echo
echo "== [3/4] 编译安装 openEMS =="
if [ -x "$HOME/openems-install/bin/openEMS" ]; then
    echo "  已安装: $("$HOME/openems-install/bin/openEMS" --version 2>&1 | grep -o 'v[0-9.]*' | head -1)"
else
    bash "$HERE/build-openems.sh" || {
        echo "[!] openEMS 编译未完全成功，但核心库通常已装好，继续。"
        echo "    仅 GUI(AppCSXCAD) 需要: sudo apt install -y libvtk9-qt-dev"
    }
fi

# ---------- 4. FEniCSx ----------
echo
echo "== [4/4] 安装 FEniCSx（conda-forge）=="
if [ -x "$HOME/miniforge3/envs/fenicsx/bin/python" ]; then
    echo "  已安装"
else
    bash "$HERE/install-fenicsx-conda.sh"
fi

echo
echo "============================================================"
echo " 完成情况"
echo "============================================================"
export PATH="$HOME/openems-install/bin:$HOME/miniforge3/bin:$PATH"
export LD_LIBRARY_PATH="$HOME/openems-install/lib:${LD_LIBRARY_PATH:-}"

if command -v openEMS >/dev/null 2>&1; then
    echo "  openEMS  : $(command -v openEMS)"
    openEMS --version 2>&1 | grep -o 'version v[0-9.]*' | head -1 | sed 's/^/             /'
else
    echo "  openEMS  : 未就绪"
fi

if "$HOME/miniforge3/envs/fenicsx/bin/python" -c "import dolfinx" 2>/dev/null; then
    v=$("$HOME/miniforge3/envs/fenicsx/bin/python" -c "import dolfinx;print(dolfinx.__version__)")
    echo "  FEniCSx  : dolfinx $v"
else
    echo "  FEniCSx  : 未就绪"
fi

echo
echo "环境变量已写入 ~/.bashrc，新开终端生效；当前会话可执行:  source ~/.bashrc"
