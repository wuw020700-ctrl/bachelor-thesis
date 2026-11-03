# 需要以【管理员】身份运行 PowerShell，然后执行本脚本。
# 作用：启用 WSL2 + 安装 Ubuntu，并提示在 Ubuntu 内运行 bootstrap-ubuntu.sh

$ErrorActionPreference = 'Stop'

$id = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($id)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "[X] 需要管理员权限。" -ForegroundColor Red
    Write-Host "    请右键 PowerShell -> 以管理员身份运行，再执行本脚本。" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] 管理员权限已确认" -ForegroundColor Green

Write-Host ""
Write-Host "== 1. 启用 Windows 功能: WSL + 虚拟机平台 ==" -ForegroundColor Cyan
$features = @('Microsoft-Windows-Subsystem-Linux', 'VirtualMachinePlatform')
foreach ($f in $features) {
    $state = (Get-WindowsOptionalFeature -Online -FeatureName $f).State
    if ($state -ne 'Enabled') {
        Write-Host "   enabling $f ..."
        Enable-WindowsOptionalFeature -Online -FeatureName $f -All -NoRestart | Out-Null
    } else {
        Write-Host "   $f already enabled"
    }
}

Write-Host ""
Write-Host "== 2. 安装 Ubuntu 发行版 ==" -ForegroundColor Cyan
wsl.exe --set-default-version 2

# 若发行版已存在就跳过下载，避免重复拉包
$installed = (wsl.exe -l -q 2>$null) -replace "`0", ""
if ($installed -match 'Ubuntu') {
    Write-Host "   Ubuntu 已存在，跳过安装"
} else {
    wsl.exe --install -d Ubuntu-22.04
    if ($LASTEXITCODE -ne 0) {
        Write-Host "   [!] Ubuntu 安装未成功（exit $LASTEXITCODE）。" -ForegroundColor Yellow
        Write-Host "       常见原因是 WSL 功能刚启用、尚未重启。请先重启再重跑本脚本。" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "== 下一步 ==" -ForegroundColor Yellow
Write-Host "1) 如提示重启，先重启电脑。"
Write-Host "2) 首次进入 Ubuntu 时设置 Linux 用户名和密码。"
Write-Host "3) 然后运行下面这条命令，安装 openEMS 与 FEniCSx："
Write-Host ""
Write-Host '   wsl -d Ubuntu-22.04 -- bash -lc "cd /mnt/c/Users/ww/Documents/Codex/2026-10-09/ai && bash scripts/bootstrap-ubuntu.sh"' -ForegroundColor White
Write-Host ""
Write-Host "4) 验证："
Write-Host "   openEMS --version"
Write-Host '   python3 -c "import dolfinx; print(dolfinx.__version__)"'
