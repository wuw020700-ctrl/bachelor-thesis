"""openEMS 工具链冒烟测试：lambda/2 偶极子。

**用途**：确认 openEMS + Python 绑定 + nf2ff 后处理整条链路能跑通。
它几十秒就结束，适合装完环境先跑一遍。

**不要把它当物理基准**：网格约 lambda/30，对 1mm 线径和 1mm 馈电间隙
来说偏粗，算出的方向性和辐射功率不作数。要做真实天线，请以官方教程
（`Horn_Antenna.py` 等，见 docs/03-工具使用手册.md）为模板。

运行（在 WSL 里）：
    source ~/openems-install/venv/bin/activate
    python examples/openems/quickstart_dipole.py
"""

import os
import tempfile

import numpy as np

from CSXCAD import ContinuousStructure
from openEMS import openEMS as OpenEMS
from openEMS.physical_constants import C0

# ---------------------------------------------------------------- 参数
unit = 1e-3                      # 长度单位 mm
f0 = 2.4e9                       # 中心频率
lambda0 = C0 / f0 / unit         # 自由空间波长（mm）
print(f"f0 = {f0/1e9:.2f} GHz,  lambda0 = {lambda0:.2f} mm")

RES = lambda0 / 30               # 网格分辨率
dipole_len = 0.47 * lambda0      # 略短于 lambda/2
dipole_rad = 1.0                 # 线径 mm
air_gap = lambda0 / 4            # 天线到边界距离

# ---------------------------------------------------------------- FDTD
FDTD = OpenEMS(NrTS=8000, EndCriteria=1e-4)
FDTD.SetGaussExcite(f0, f0 / 2)
FDTD.SetBoundaryCond(["PML_8"] * 6)

CSX = ContinuousStructure()
FDTD.SetCSX(CSX)
mesh = CSX.GetGrid()
mesh.SetDeltaUnit(unit)

# ---------------------------------------------------------------- 几何
# 偶极子要在中心留出馈电间隙：整体分两段，中间 gap 处放集总端口。
# 如果画成一整根圆柱，端口会报 "only a 1D/line integration is allowed"，
# 结果是 Prad = 0、Dmax = nan。
gap = 1.0  # 馈电间隙（mm）

arm_lo = CSX.AddMetal("dipole_lo")
arm_lo.AddCylinder(
    np.array([0, 0, -dipole_len / 2]),
    np.array([0, 0, -gap]),
    dipole_rad,
)

arm_hi = CSX.AddMetal("dipole_hi")
arm_hi.AddCylinder(
    np.array([0, 0, gap]),
    np.array([0, 0, dipole_len / 2]),
    dipole_rad,
)

# ---------------------------------------------------------------- 网格
# 域要包住天线，并且 NF2FF 盒必须落在网格内部（线太稀会报
# "not enough lines in some direction"）。
half_xy = 0.6 * lambda0
half_z = 0.8 * lambda0

mesh.AddLine("x", [-half_xy, -5, 0, 5, half_xy])
mesh.AddLine("y", [-half_xy, -5, 0, 5, half_xy])
mesh.AddLine(
    "z",
    [-half_z, -dipole_len / 2 - 5, -dipole_len / 2, -gap, 0, gap,
     dipole_len / 2, dipole_len / 2 + 5, half_z],
)
mesh.SmoothMeshLines("all", RES, 1.5)
print(f"网格: x={mesh.GetQtyLines(0)} y={mesh.GetQtyLines(1)} z={mesh.GetQtyLines(2)} 条线")

# ---------------------------------------------------------------- 馈源
# 端口起止点必须只沿一个坐标轴变化（这里是 z），否则电压积分会失败。
# 另外：端口挂在 FDTD 对象上，CSX 对象上没有 AddLumpedPort。
port = FDTD.AddLumpedPort(
    1,  # 端口号
    50,  # 阻抗
    np.array([0, 0, -gap]),
    np.array([0, 0, gap]),
    "z",
    1.0,                    # 激励幅度
    priority=5,
)

# ---------------------------------------------------------------- 近远场
# opt_resolution 必须是长度 3 的序列，传标量会报 "object of type 'float' has no len()"
nf2ff = FDTD.CreateNF2FFBox(
    "nf2ff",
    opt_resolution=[RES, RES, RES],
    frequency=[f0],
)

# ---------------------------------------------------------------- 远场方向
theta = np.arange(0, 181, 5.0)
phi = np.arange(0, 361, 10.0)

# ---------------------------------------------------------------- 运行
sim_path = os.path.join(tempfile.gettempdir(), "openems_quickstart")
os.makedirs(sim_path, exist_ok=True)
print(f"工作目录: {sim_path}")

FDTD.Run(sim_path, cleanup=True, verbose=0)

# ---------------------------------------------------------------- 后处理
freq = np.array([f0])
port.CalcPort(sim_path, freq)

nf2ff_res = nf2ff.CalcNF2FF(
    sim_path,
    f0,
    np.deg2rad(theta),
    np.deg2rad(phi),
    outfile=os.path.join(sim_path, "nf2ff.h5"),
)

E_norm = np.squeeze(nf2ff_res.E_norm[0])
Prad = float(np.squeeze(nf2ff_res.Prad[0]))
Dmax = float(np.squeeze(nf2ff_res.Dmax[0]))
print()
print(f"辐射功率  Prad = {Prad:.4e} W")
print(f"最大方向性 D   = {Dmax:.3f} ({10*np.log10(Dmax):.2f} dBi)")
print(f"远场数据形状   = {E_norm.shape}  (theta x phi)")

out = os.path.join(tempfile.gettempdir(), "openems_quickstart_result.npz")
np.savez(out, theta=theta, phi=phi, E_norm=E_norm, Prad=Prad, Dmax=Dmax)
print(f"结果已保存: {out}")
print()
print("[OK] openEMS 完整链路（建模 -> FDTD -> 近远场变换）跑通")
