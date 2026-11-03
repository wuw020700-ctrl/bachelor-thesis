# 建立项目 Python 虚拟环境并安装依赖（不需要管理员）
# 用法:  .\scripts\setup-python-env.ps1

param(
    [string]$Python = 'C:\Users\ww\AppData\Local\Programs\Python\Python311\python.exe',
    [string]$Index  = 'https://pypi.tuna.tsinghua.edu.cn/simple'
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $root '.venv'

if (-not (Test-Path $Python)) {
    Write-Host "[X] 找不到 Python: $Python" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $venv)) {
    Write-Host "== 创建虚拟环境 $venv ==" -ForegroundColor Cyan
    & $Python -m venv $venv
} else {
    Write-Host "== 虚拟环境已存在，复用 ==" -ForegroundColor Cyan
}

$vpy = Join-Path $venv 'Scripts\python.exe'

# 本机环境设了 PIP_NO_INDEX=1，会禁用索引，所以显式指定镜像源
$env:PIP_NO_INDEX = '0'

Write-Host "== 升级 pip ==" -ForegroundColor Cyan
& $vpy -m pip install --upgrade pip --index-url $Index

Write-Host "== 安装 requirements.txt ==" -ForegroundColor Cyan
& $vpy -m pip install -r (Join-Path $root 'requirements.txt') --index-url $Index

Write-Host ""
Write-Host "== 完成。验证 ==" -ForegroundColor Green
& $vpy -c "import numpy, scipy, matplotlib; print('numpy', numpy.__version__); print('scipy', scipy.__version__); print('matplotlib', matplotlib.__version__)"
Write-Host ""
Write-Host "之后激活环境:  .\.venv\Scripts\Activate.ps1"
