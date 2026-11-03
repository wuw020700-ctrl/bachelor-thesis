# 环境自检脚本
# 用法:  .\scripts\verify-env.ps1
# 逐项检查本机环境；打印通过/失败清单。不需要管理员权限。

$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent $PSScriptRoot

$results = New-Object System.Collections.Generic.List[object]

function Check {
    param([string]$Name, [scriptblock]$Test, [string]$Expect)
    $ok = $false
    try { $ok = [bool](& $Test) } catch { $ok = $false }
    $results.Add([pscustomobject]@{
        项目 = $Name
        结果 = $(if ($ok) { 'PASS' } else { 'FAIL' })
        期望 = $Expect
    })
}

Write-Host "==== 天线仿真毕设环境自检 ====" -ForegroundColor Cyan
Write-Host ""

# ---------- 1. Python 科学计算栈 ----------
Write-Host "[1/4] Python 科学计算栈" -ForegroundColor Yellow
$vpy = Join-Path $root '.venv\Scripts\python.exe'
Check 'Python venv' { Test-Path $vpy } $vpy

if (Test-Path $vpy) {
    $probe = Join-Path $env:TEMP 'dsh_env_probe.py'
    @'
import importlib
mods = ['numpy','scipy','matplotlib','h5py','pandas','pyvista','meshio','gmsh']
ok, bad = [], []
for m in mods:
    try:
        importlib.import_module(m)
        ok.append(m)
    except Exception:
        bad.append(m)
print('OK:' + ','.join(ok))
print('BAD:' + ','.join(bad))
'@ | Set-Content -Path $probe -Encoding UTF8

    $output = & $vpy $probe 2>&1
    $okLine = ($output | Select-String '^OK:' | Select-Object -First 1).Line
    $badLine = ($output | Select-String '^BAD:' | Select-Object -First 1).Line
    Write-Host "    $okLine"
    if ($badLine -and $badLine -ne 'BAD:') {
        Write-Host "    $badLine" -ForegroundColor Red
        Check 'Python 依赖齐全' { $false } '全部可导入'
    } else {
        Check 'Python 依赖齐全' { $true } '全部可导入'
    }
} else {
    Write-Host "    未找到 .venv" -ForegroundColor Red
}

# ---------- 2. Qt 工具链 ----------
Write-Host ""
Write-Host "[2/4] Qt 工具链" -ForegroundColor Yellow
$qt = 'C:\Qt\6.8.3\mingw_64'
$mingw = 'C:\Qt\Tools\mingw1310_64'
Check 'qmake.exe'     { Test-Path "$qt\bin\qmake.exe" }             'Qt 6.8.3'
Check 'Qt6Charts'     { Test-Path "$qt\lib\cmake\Qt6Charts" }        'qtcharts 模块'
Check 'Qt6SerialPort' { Test-Path "$qt\lib\cmake\Qt6SerialPort" }    'qtserialport 模块'
Check 'windeployqt'   { Test-Path "$qt\bin\windeployqt.exe" }        '部署工具'
Check 'Qt MinGW g++'  { Test-Path "$mingw\bin\g++.exe" }             'GCC 13.1.0'
Check 'CMake'         { Test-Path 'C:\Program Files\CMake\bin\cmake.exe' } 'CMake 4.x'
Check 'Qt 验证程序'   { Test-Path (Join-Path $root 'work\qt_probe\build\qt_probe.exe') } 'work\qt_probe'

# ---------- 3. FEniCSx ----------
Write-Host ""
Write-Host "[3/4] FEniCSx 结构有限元" -ForegroundColor Yellow
$fe = 'C:\Users\ww\.conda\envs\fenicsx'
$fepy = "$fe\python.exe"
Check 'fenicsx 环境'  { Test-Path $fepy }                          $fe
Check 'impi.dll'      { Test-Path "$fe\Library\bin\impi.dll" }     'Intel MPI'
Check 'libfabric.dll' { Test-Path "$fe\Library\bin\libfabric.dll" } 'OFI provider'

if (Test-Path $fepy) {
    # 关键：必须把 Library\bin 加进 PATH，否则 MPI_Init 失败
    $oldPath = $env:PATH
    $env:PATH = "$fe\Library\bin;$env:PATH"

    $mpiOut = & $fepy -c "from mpi4py import MPI; print(MPI.Get_library_version().splitlines()[0])" 2>&1

    $mpiLine = $mpiOut | Where-Object { $_ -match 'Intel\(R\) MPI' } | Select-Object -First 1
    if ($mpiLine) {
        Write-Host "    $mpiLine"
        Check 'MPI 初始化' { $true } 'Intel MPI 可启动'
    } else {
        Write-Host "    MPI 初始化失败（需把 <env>\Library\bin 加入 PATH）" -ForegroundColor Red
        Check 'MPI 初始化' { $false } 'Intel MPI 可启动'
    }

    # NOTE: keep Library\bin on PATH for this import too - dolfinx loads
    # MPI/PETSc DLLs from there. (Restoring PATH before this line made the
    # check report a false failure.)
    $dfxOut = & $fepy -c "import dolfinx; print('DOLFINX=' + dolfinx.__version__)" 2>&1
    $env:PATH = $oldPath
    $dfxLine = $dfxOut | Where-Object { $_ -match 'DOLFINX=' } | Select-Object -First 1
    if ($dfxLine) {
        $ver = ($dfxLine -replace '.*DOLFINX=', '').Trim()
        Write-Host "    dolfinx $ver"
        Check 'dolfinx' { $true } $ver
    } else {
        Write-Host "    dolfinx 导入失败" -ForegroundColor Red
        Check 'dolfinx' { $false } '导入失败'
    }
    $uflOut = & $fepy -c "import ufl, ffcx; print('UFL=' + ufl.__version__); print('FFCX=' + ffcx.__version__)" 2>&1
    $uflLine = $uflOut | Where-Object { $_ -match '^UFL=' } | Select-Object -First 1
    $ffcxLine = $uflOut | Where-Object { $_ -match '^FFCX=' } | Select-Object -First 1
    if ($uflLine -and $ffcxLine) {
        $uv = ($uflLine -replace '^UFL=', '').Trim()
        $fv = ($ffcxLine -replace '^FFCX=', '').Trim()
        Write-Host "    ufl $uv / ffcx $fv"
        Check 'UFL/FFCX 可导入' { $true } "ufl $uv, ffcx $fv"
    } else {
        Write-Host "    ufl/ffcx 导入失败" -ForegroundColor Red
        Check 'UFL/FFCX 可导入' { $false } '导入失败'
    }

    # Form compilation uses CFFI, which on Windows only drives MSVC (cl.exe).
    # MinGW cannot substitute here - this is the real blocker for native Windows.
    $clOk = $null -ne (Get-Command cl.exe -ErrorAction SilentlyContinue)
    Check 'MSVC cl.exe' { $clOk } '表单 JIT 编译必需；缺则 FEniCSx 只能走 WSL'
}

# ---------- 4. WSL 侧：openEMS / FEniCSx ----------
Write-Host ""
Write-Host "[4/4] WSL 侧 openEMS / FEniCSx" -ForegroundColor Yellow

$distro = $null
try {
    $list = (& wsl.exe -l -q 2>&1 | Out-String) -replace "`0", ""
    if ($list -match 'Ubuntu-22\.04') { $distro = 'Ubuntu-22.04' }
    elseif ($list -match 'Ubuntu') { $distro = 'Ubuntu' }
} catch { }

Check 'WSL 发行版' { $null -ne $distro } $(if ($distro) { $distro } else { '未装：见 HANDOFF.md' })

if ($distro) {
    $probe = Join-Path $root 'scripts\wsl-env-probe.sh'
    # C:\a\b -> /mnt/c/a/b  （盘符必须小写，Linux 区分大小写）
    $drive = $probe.Substring(0, 1).ToLower()
    $probeUnix = '/mnt/' + $drive + ($probe.Substring(2) -replace '\\', '/')

    $raw = (& wsl.exe -d $distro -- bash $probeUnix 2>&1 | Out-String) -replace "`0", ""
    $kv = @{}
    foreach ($line in ($raw -split "`r?`n")) {
        if ($line -match '^([A-Z0-9_]+)=(.*)$') { $kv[$Matches[1]] = $Matches[2].Trim() }
    }

    Check 'openEMS'  { [bool]$kv['OPENEMS_BIN'] } $(if ($kv['OPENEMS_VER']) { $kv['OPENEMS_VER'] } else { '未装' })
    Check 'libopenEMS' { [bool]$kv['OPENEMS_LIB'] } $(if ($kv['OPENEMS_LIB']) { $kv['OPENEMS_LIB'] } else { '缺' })
    Check 'dolfinx (WSL)'  { [bool]$kv['DOLFINX'] }  $(if ($kv['DOLFINX'])  { $kv['DOLFINX'] }  else { '未装' })
    Check 'petsc4py (WSL)' { [bool]$kv['PETSC4PY'] } $(if ($kv['PETSC4PY']) { $kv['PETSC4PY'] } else { '未装' })
}

# ---------- 汇总 ----------
Write-Host ""
Write-Host "==== 汇总 ====" -ForegroundColor Cyan
$results | Format-Table -AutoSize

$fail = @($results | Where-Object { $_.结果 -eq 'FAIL' }).Count
$pass = @($results | Where-Object { $_.结果 -eq 'PASS' }).Count
Write-Host "通过 $pass 项，失败 $fail 项" -ForegroundColor $(if ($fail -eq 0) { 'Green' } else { 'Yellow' })
Write-Host ""
if ($fail -gt 0) {
    Write-Host "说明：" -ForegroundColor Yellow
    Write-Host "  MSVC cl.exe   —— 原生 Windows 跑 FEniCSx 需要 Visual Studio；" -ForegroundColor Yellow
    Write-Host "                   已改用 WSL 的 FEniCSx，这一项不影响。" -ForegroundColor Yellow
    Write-Host "  其它 FAIL     —— 见 HANDOFF.md 的排查步骤。" -ForegroundColor Yellow
} else {
    Write-Host "全部通过。" -ForegroundColor Green
}
