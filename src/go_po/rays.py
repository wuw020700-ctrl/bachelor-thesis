"""几何光学 (GO) 射线追踪：馈源 -> 副面 -> 主面 -> 平行出射。

物理链条
--------
1. 馈源是位于双曲面**远焦点** z = z_focus_far 的点源（默认在主面顶点处）；
2. 射线打到副面（双曲面右支），反射后的出射线**反向延长线过近焦点**
   —— 近焦点与抛物面焦点 z = F 重合；
3. 射线打到主面（抛物面），反射后**平行于 z 轴**射出。

``collimation_error()`` 是一个物理自校验：双曲面取支、焦点位置或法向只要
有错，出射方向就不会平行于视轴，误差会立刻暴露（正确几何应达机器精度）。

注意
----
原版把馈源放在抛物面焦点 z = F、并按 馈源 -> 主面 -> 副面 追踪，那是错的：
卡塞格伦的路径必须是 馈源(远焦点) -> 副面 -> 主面。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from common.cassegrain import Cassegrain

__all__ = ["RayBundle", "trace_rays", "feed_half_angle_for_edge"]


@dataclass
class RayBundle:
    """一组射线的追踪结果。"""

    theta: np.ndarray
    """馈源出射角（相对视轴，弧度）。"""

    phi: np.ndarray
    """方位角（弧度）。"""

    p_sub: np.ndarray
    """副面落点 (N,3)。"""

    p_main: np.ndarray
    """主面落点 (N,3)。"""

    d_out: np.ndarray
    """出射方向 (N,3)；正确几何应为 (0,0,1)。"""

    r1: np.ndarray
    """馈源 -> 副面 的距离。"""

    r2: np.ndarray
    """副面 -> 主面 的距离。"""

    valid: np.ndarray
    """布尔掩码：该射线是否完整走完链路且落在主面口径内。"""

    @property
    def n_rays(self) -> int:
        return self.p_main.shape[0]

    @property
    def n_valid(self) -> int:
        return int(self.valid.sum())

    @property
    def aperture_radius(self) -> np.ndarray:
        """主面落点半径（口径坐标）。"""
        return np.hypot(self.p_main[:, 0], self.p_main[:, 1])

    def collimation_error(self) -> float:
        """出射方向偏离视轴的最大横向分量（理想应 ~1e-15）。"""
        d = self.d_out[self.valid]
        return float("nan") if d.size == 0 else float(np.max(np.abs(d[:, :2])))

    def collimation_rms(self) -> float:
        d = self.d_out[self.valid]
        return float("nan") if d.size == 0 else float(np.sqrt(np.mean(d[:, :2] ** 2)))

    def path_length_ripple(self) -> float:
        """光程起伏：起伏 ~0 表示几何正确。

        等光程的不变量是「馈源 -> 副面 -> 主面 -> 某垂直于视轴的平面」的总光程。
        出射线平行于 z，主面到该平面的距离是 (Z0 - z_main)，所以不变量为

            r1 + r2 - z_main = const

        （只算 r1 + r2 是错的，它本来就不该是常数。）
        """
        pl = (self.r1 + self.r2 - self.p_main[:, 2])[self.valid]
        return float("nan") if pl.size == 0 else float(np.max(pl) - np.min(pl))


def _reflect(d: np.ndarray, n: np.ndarray) -> np.ndarray:
    """矢量反射 d' = d - 2 (d.n) n。"""
    dn = np.sum(d * n, axis=-1, keepdims=True)
    out = d - 2.0 * dn * n
    return out / np.linalg.norm(out, axis=-1, keepdims=True)


def _first_root(o, d, f, t_lo, t_hi, n_scan=1500, n_bis=70):
    """在 [t_lo, t_hi] 上逐射线找 f(o + t d) 的首个变号点（向量化）。"""
    n = o.shape[0]
    frac = np.linspace(0.0, 1.0, n_scan)
    ts = t_lo[:, None] + frac[None, :] * (t_hi - t_lo)[:, None]
    vals = np.empty((n, n_scan))
    for j in range(n_scan):
        vals[:, j] = f(o + ts[:, j][:, None] * d)
    sgn = np.sign(vals)
    sgn[sgn == 0.0] = 1.0
    change = sgn[:, 1:] != sgn[:, :-1]
    found = change.any(axis=1)
    idx = np.argmax(change, axis=1)
    rows = np.arange(n)
    lo = ts[rows, idx].copy()
    hi = ts[rows, np.minimum(idx + 1, n_scan - 1)].copy()
    vlo = f(o + lo[:, None] * d)
    for _ in range(n_bis):
        mid = 0.5 * (lo + hi)
        vmid = f(o + mid[:, None] * d)
        same = np.sign(vmid) == np.sign(vlo)
        lo = np.where(same, mid, lo)
        hi = np.where(same, hi, mid)
    t = 0.5 * (lo + hi)
    return np.where(found, t, np.nan)


def _trace_one_direction(geo: Cassegrain, theta: np.ndarray, phi: np.ndarray):
    """给定 (theta, phi) 完成 馈源 -> 副面 -> 主面，返回各量。"""
    feed = np.array([0.0, 0.0, geo.z_focus_far])
    d0 = np.stack(
        [np.sin(theta) * np.cos(phi), np.sin(theta) * np.sin(phi), np.cos(theta)],
        axis=-1,
    )
    n = theta.size
    origin = np.tile(feed, (n, 1))

    # ---- 副面：双曲面右支 (z >= z_center) ----
    # 从射线到达 z = z_center 的位置开始扫，避开左支的伪解
    t_zc = (geo.z_center - geo.z_focus_far) / d0[:, 2]
    t_hi = 6.0 * (abs(geo.z_focus_far) + geo.F + abs(geo.z_center))

    def f_sub(p):
        r2 = p[:, 0] ** 2 + p[:, 1] ** 2
        return (p[:, 2] - geo.z_center) ** 2 / geo.a**2 - r2 / geo.b2 - 1.0

    t_sub = _first_root(origin, d0, f_sub, t_zc, np.full(n, t_hi))
    ok = np.isfinite(t_sub)
    p_sub = origin + np.where(ok, t_sub, 0.0)[:, None] * d0

    # ---- 副面法向（朝向来波侧） ----
    n_sub = np.stack(
        [-2.0 * p_sub[:, 0] / geo.b2,
         -2.0 * p_sub[:, 1] / geo.b2,
         2.0 * (p_sub[:, 2] - geo.z_center) / geo.a**2],
        axis=-1,
    )
    n_sub /= np.linalg.norm(n_sub, axis=-1, keepdims=True)
    n_sub[np.sum(n_sub * d0, axis=-1) > 0.0] *= -1.0
    d1 = _reflect(d0, n_sub)

    # ---- 主面：抛物面 r^2 = 4 F z ----
    def f_main(p):
        return p[:, 0] ** 2 + p[:, 1] ** 2 - 4.0 * geo.F * p[:, 2]

    t_main = _first_root(p_sub, d1, f_main,
                         np.full(n, 1e-9), np.full(n, t_hi))
    ok &= np.isfinite(t_main)
    p_main = p_sub + np.where(np.isfinite(t_main), t_main, 0.0)[:, None] * d1

    r_main = np.hypot(p_main[:, 0], p_main[:, 1])
    ok &= r_main <= geo.R * (1.0 + 1e-9)
    ok &= p_main[:, 2] >= -1e-9

    # ---- 主面法向与出射 ----
    n_main = np.stack([2.0 * p_main[:, 0], 2.0 * p_main[:, 1],
                       np.full(n, -4.0 * geo.F)], axis=-1)
    n_main /= np.linalg.norm(n_main, axis=-1, keepdims=True)
    n_main[np.sum(n_main * d1, axis=-1) > 0.0] *= -1.0
    d2 = _reflect(d1, n_main)

    r1 = np.where(ok, t_sub, np.nan)
    r2 = np.where(ok, t_main, np.nan)
    return p_sub, p_main, d2, r1, r2, ok


def feed_half_angle_for_edge(geo: Cassegrain, tol: float = 1e-10) -> float:
    """二分求「恰好打到主面边缘」的馈源出射角。"""
    def r_main_at(theta: float) -> float:
        th = np.array([theta])
        ph = np.array([0.0])
        p_sub, p_main, _, _, _, ok = _trace_one_direction(geo, th, ph)
        if not ok[0]:
            return np.inf
        return float(np.hypot(p_main[0, 0], p_main[0, 1]))

    lo, hi = 1e-6, np.pi / 2 - 1e-6
    if r_main_at(hi) < geo.R:
        return hi
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if r_main_at(mid) < geo.R:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def trace_rays(
    geo: Cassegrain,
    n_radial: int = 24,
    n_azimuth: int = 48,
    theta_max: float | None = None,
) -> RayBundle:
    """从馈源发出射线束，依次打到副面、主面。

    theta 采用中点采样（避开轴心奇异），phi 均匀分布。
    """
    geo.assert_consistency()
    if theta_max is None:
        theta_max = feed_half_angle_for_edge(geo)

    th_1d = (np.arange(n_radial) + 0.5) * (theta_max / n_radial)
    ph_1d = (np.arange(n_azimuth) + 0.5) * (2.0 * np.pi / n_azimuth)
    TH, PH = np.meshgrid(th_1d, ph_1d, indexing="ij")
    theta = TH.ravel()
    phi = PH.ravel()

    p_sub, p_main, d_out, r1, r2, ok = _trace_one_direction(geo, theta, phi)
    return RayBundle(theta=theta, phi=phi, p_sub=p_sub, p_main=p_main,
                     d_out=d_out, r1=r1, r2=r2, valid=ok)


def _probe() -> None:
    from common.cassegrain import default_20lambda

    print("=== 扫 L，看准直误差 / 遮挡比 / 馈源位置 ===")
    print(f"  {'L':>6} {'遮挡':>7} {'命中':>8} {'准直误差':>11} {'光程起伏':>11}")
    # L 太小会让副面过大、遮挡超限（几何自检会拦下），所以从 5.5 起
    for L in (5.5, 6.0, 6.4, 6.8, 7.2):
        geo = default_20lambda()
        geo = Cassegrain(lam=geo.lam, D=geo.D, F=geo.F, M=geo.M, L=L)
        b = trace_rays(geo, n_radial=16, n_azimuth=24)
        print(f"  {L:6.2f} {geo.blocking_ratio * 100:6.2f}%"
              f" {b.n_valid:4d}/{b.n_rays:<4d}"
              f" {b.collimation_error():11.2e} {b.path_length_ripple():11.2e}")


if __name__ == "__main__":
    _probe()
