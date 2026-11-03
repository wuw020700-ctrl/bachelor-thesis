# 配置 FEniCSx 运行环境（在当前 PowerShell 会话生效）
# 用法:  . .\scripts\setup-fenics-env.ps1      (注意前面的点，表示在当前会话生效)
#
# 作用：把 conda 环境里的 Library\bin 放进 PATH。
# 不做这一步，Intel MPI 会因为找不到 impi.dll / libfabric.dll 而报：
#   MPIDI_OFI_mpi_init_hook: OFI fi_getinfo() failed
#   internal_Init_thread: MPI_Init_thread failed

param(
    [string]$EnvPath = 'C:\Users\ww\.conda\envs\fenicsx'
)

if (-not (Test-Path "$EnvPath\python.exe")) {
    Write-Host "[X] 找不到 FEniCSx 环境: $EnvPath" -ForegroundColor Red
    Write-Host "    请先执行:" -ForegroundColor Yellow
    Write-Host "    conda create -y -n fenicsx -c conda-forge --override-channels python=3.11 fenics-dolfinx=0.11 fenics-basix mpi4py gmsh pyvista" -ForegroundColor White
    return
}

# Intel MPI 的 DLL 都在 Library\bin
$env:PATH = "$EnvPath\Library\bin;$EnvPath\Scripts;$EnvPath;$env:PATH"
$env:FI_PROVIDER_PATH = "$EnvPath\Library\bin"

Write-Host "[OK] FEniCSx 环境已就绪" -ForegroundColor Green
Write-Host "     python : $EnvPath\python.exe"
Write-Host ""

& "$EnvPath\python.exe" -c "from mpi4py import MPI; print('MPI    :', MPI.Get_library_version().splitlines()[0])" 2>&1 | Select-Object -First 3
& "$EnvPath\python.exe" -c "import dolfinx; print('dolfinx:', dolfinx.__version__)" 2>&1 | Select-Object -First 3

Write-Host ""
Write-Host "用法示例：" -ForegroundColor Cyan
Write-Host "  & '$EnvPath\python.exe' your_script.py" -ForegroundColor White
