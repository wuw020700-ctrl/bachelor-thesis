"""20λ 卡塞格伦天线：几何定义与共焦设计方程。

坐标约定（全局统一，务必遵守）
------------------------------
* z 轴为视轴，主反射面开口朝 +z。
* 主反射面顶点在 z = 0，抛物面 r^2 = 4Fz，主面半径 R = D/2。
* 主面焦点在 z = F —— 它同时是双曲面的**近焦点**。
* 馈源放在双曲面的**远焦点** z = z_focus_far 上。
* 所有长度以波长 λ 归一化。

射线路径
--------
    馈源(z_focus_far) --副面--> --主面--> 平行于 z 轴射出

设计方程（已用射线追踪数值校验，见 work/cassegrain_check.py）
--------------------------------------------------------------------
两个自由设计参数：

    M : 放大率 (> 1)
    L : 副面顶点轴向位置（主面顶点起算），0 < L < F

由「副面顶点在 z = L」和「近焦点在 z = F」定出双曲面：

    c - a = F - L                   顶点到近焦点的距离
    c + a = M * (F - L)             顶点到远焦点的距离  =>  M = (c+a)/(c-a)
    a     = (M - 1) * (F - L) / 2
    c     = (M + 1) * (F - L) / 2
    e     = c / a = (M + 1) / (M - 1)
    b^2   = c^2 - a^2
    z_center = L - a                副面取双曲面右支 z >= z_center

焦点：

    z_focus_near = z_center + c = L + (c - a) = L + (F - L) = F   <- 恒等于 F
    z_focus_far  = z_center - c                                    <- 馈源位置

关于 L 取值（重要，别踩坑）
---------------------------
L 不是 F/M。用 L = F/M 会得到 16.4λ 的副面、**67% 遮挡**，物理上不能用。
L 越小副面越大、遮挡越重；L 越靠近 F 副面越小。默认取

    L = M * F / (M + 1)     =>   z_focus_far = 0

即把馈源放在主面顶点处，这是工程上常见的紧凑布置，遮挡约 4~5%。
要别的遮挡比请用 ``with_blockage()``。

系统等效焦距 f_sys = M * F（设计值）。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

__all__ = ["Cassegrain", "default_20lambda"]


@dataclass(frozen=True)
class Cassegrain:
    """卡塞格伦天线几何参数（长度单位 = 波长）。"""

    lam: float = 1.0
    """波长。"""

    D: float = 20.0
    """主面口径直径（题目锁定 20λ）。"""

    F: float = 8.0
    """主面焦距；F/D = 0.4。"""

    M: float = 4.0
    """放大率（> 1）。"""

    L: float | None = None
    """副面顶点轴向位置。None 时取 M*F/(M+1)，使馈源落在主面顶点。"""

    def __post_init__(self) -> None:
        if self.M <= 1.0:
            raise ValueError(f"放大率必须 > 1，当前 M={self.M}")
        if self.L is None:
            object.__setattr__(self, "L", self.M * self.F / (self.M + 1.0))
        if not 0.0 < self.L < self.F:
            raise ValueError(f"副面顶点须满足 0 < L < F({self.F})，当前 L={self.L}")

    # ------------------------------------------------------------------
    # 主面
    # ------------------------------------------------------------------
    @property
    def R(self) -> float:
        """主面口径半径。"""
        return 0.5 * self.D

    @property
    def z_rim_primary(self) -> float:
        """主面边缘 z 坐标。"""
        return self.R * self.R / (4.0 * self.F)

    @property
    def half_angle_feed(self) -> float:
        """馈源到**主面边缘**的直线张角（弧度）。

        ⚠️ 这不是馈源的照射半张角。卡塞格伦的边缘射线要先打到副面，
        真正的馈源出射半张角要比这个小得多（20λ 算例：这里 72.65°，
        实际 17.76°）。需要照射角请用 ``go_po.rays.feed_half_angle_for_edge``。
        """
        dz = self.z_rim_primary - self.z_focus_far
        return float(np.arctan(self.R / dz))

    # ------------------------------------------------------------------
    # 双曲面（副面）
    # ------------------------------------------------------------------
    @property
    def a(self) -> float:
        """双曲面实半轴。"""
        return (self.M - 1.0) * (self.F - self.L) / 2.0

    @property
    def c(self) -> float:
        """双曲面半焦距。"""
        return (self.M + 1.0) * (self.F - self.L) / 2.0

    @property
    def e(self) -> float:
        """双曲面离心率。"""
        return self.c / self.a

    @property
    def b2(self) -> float:
        return max(self.c * self.c - self.a * self.a, 0.0)

    @property
    def b(self) -> float:
        return float(np.sqrt(self.b2))

    @property
    def z_center(self) -> float:
        """双曲面几何中心 z 坐标。"""
        return self.L - self.a

    @property
    def z_focus_near(self) -> float:
        """近焦点 z —— 必须等于 F，否则副面无法与主面共焦。"""
        return self.z_center + self.c

    @property
    def z_focus_far(self) -> float:
        """远焦点 z —— 馈源相位中心放这里。"""
        return self.z_center - self.c

    @property
    def system_focal_length(self) -> float:
        """系统等效焦距（设计值）= M * F。"""
        return self.M * self.F

    def rim_radius_at(self, z: float) -> float:
        """右支双曲面在给定 z 处的半径；|z - z_center| < a 时返回 0。"""
        t = (z - self.z_center) ** 2 / self.a**2 - 1.0
        return float(np.sqrt(max(t, 0.0)) * self.b)

    def hyperbola_value(self, points: np.ndarray) -> np.ndarray:
        """双曲面隐式方程值 F(p) = (z-z_c)^2/a^2 - r^2/b^2 - 1。"""
        r2 = points[:, 0] ** 2 + points[:, 1] ** 2
        return (points[:, 2] - self.z_center) ** 2 / self.a**2 - r2 / self.b2 - 1.0

    # ------------------------------------------------------------------
    # 副面边缘：由「焦点 -> 主面边缘」直线与副面右支的交点定出
    # ------------------------------------------------------------------
    def sub_rim(self):
        """返回副面边缘点 (r, z)；无交点返回 None。

        副面反射后，出射线的反向延长线过近焦点 F，因此
        F、副面边缘点、主面边缘点 三点共线。沿该直线求双曲面零点即可。
        """
        F_pt = np.array([0.0, 0.0, self.F])
        P_m = np.array([self.R, 0.0, self.z_rim_primary])
        d = P_m - F_pt

        def resid(t: float) -> float:
            p = F_pt + t * d
            return (p[2] - self.z_center) ** 2 / self.a**2 - p[0] ** 2 / self.b2 - 1.0

        ts = np.linspace(1e-9, 1.0 - 1e-9, 4000)
        vals = np.array([resid(t) for t in ts])
        sgn = np.sign(vals)
        sgn[sgn == 0.0] = 1.0
        idx = np.where(sgn[1:] != sgn[:-1])[0]
        if idx.size == 0:
            return None

        lo, hi = ts[idx[0]], ts[idx[0] + 1]
        vlo = resid(lo)
        for _ in range(80):
            mid = 0.5 * (lo + hi)
            if np.sign(resid(mid)) == np.sign(vlo):
                lo = mid
            else:
                hi = mid
        t = 0.5 * (lo + hi)
        p = F_pt + t * d
        return float(np.hypot(p[0], p[1])), float(p[2])

    @property
    def d_rim(self) -> float:
        """副面口径直径。"""
        hit = self.sub_rim()
        return 0.0 if hit is None else 2.0 * hit[0]

    @property
    def blocking_ratio(self) -> float:
        """副面遮挡面积比（相对主面口径）。"""
        return (self.d_rim / self.D) ** 2

    # ------------------------------------------------------------------
    # 设计辅助
    # ------------------------------------------------------------------
    @classmethod
    def with_blockage(cls, target_blockage: float, **kwargs) -> "Cassegrain":
        """按目标遮挡比反解 L（二分）。"""
        lo, hi = 1e-3, kwargs.get("F", 8.0) - 1e-3
        for _ in range(200):
            mid = 0.5 * (lo + hi)
            geo = cls(L=mid, **kwargs)
            hit = geo.sub_rim()
            b = 0.0 if hit is None else (2.0 * hit[0] / geo.D) ** 2
            if b > target_blockage:
                lo = mid
            else:
                hi = mid
        return cls(L=0.5 * (lo + hi), **kwargs)

    # ------------------------------------------------------------------
    # 校验
    # ------------------------------------------------------------------
    def consistency_report(self, tol: float = 1e-9) -> list[tuple[str, float, bool]]:
        checks: list[tuple[str, float, bool]] = []

        err = abs(self.z_focus_near - self.F)
        checks.append((f"近焦点 z = F ({self.F:g})", err, err <= tol * max(1.0, self.F)))
        checks.append((f"M = (c+a)/(c-a) = {self.M:g}", (self.c + self.a) / (self.c - self.a) - self.M,
                       abs((self.c + self.a) / (self.c - self.a) - self.M) <= 1e-9 * self.M))
        checks.append(("b^2 > 0", -self.b2, self.b2 > 0.0))
        # 注意：副面本来就在主面前方（z 大于主面边缘），这不是错误，
        # 所以不要检查 L < z_rim_primary。
        checks.append((f"副面顶点 z={self.L:.4f} 在主面焦点 z={self.F:.4f} 之前",
                       self.L - self.F, self.L < self.F))
        checks.append((f"副面口径 d={self.d_rim:.4f} > 0", self.d_rim, self.d_rim > 0.0))
        checks.append((f"副面口径 d={self.d_rim:.4f} < D={self.D:g}", self.d_rim - self.D, self.d_rim < self.D))
        checks.append((f"遮挡面积比 {self.blocking_ratio * 100:.2f}% < 15%",
                       self.blocking_ratio - 0.15, self.blocking_ratio < 0.15))
        return checks

    def assert_consistency(self, tol: float = 1e-9) -> None:
        for name, err, ok in self.consistency_report(tol):
            if not ok:
                raise AssertionError(f"几何自检失败: {name} (余量 {err:.6e})")

    def summary(self) -> str:
        self.assert_consistency()
        rim = self.sub_rim()
        rim_txt = "n/a" if rim is None else f"r={rim[0]:.4f} λ @ z={rim[1]:.4f} λ"
        return "\n".join(
            [
                "20λ 卡塞格伦天线几何参数",
                f"  波长 λ                = {self.lam:g}",
                f"  主面口径 D            = {self.D:g} λ  (半径 {self.R:g} λ)",
                f"  主面焦距 F            = {self.F:g} λ  (F/D = {self.F / self.D:.3f})",
                f"  放大率 M              = {self.M:g}",
                f"  副面顶点轴向位置 L    = {self.L:.6f} λ",
                f"  双曲面实半轴 a        = {self.a:.6f} λ",
                f"  双曲面半焦距 c        = {self.c:.6f} λ",
                f"  双曲面离心率 e        = {self.e:.6f}",
                f"  双曲面虚半轴 b        = {self.b:.6f} λ",
                f"  双曲面中心 z          = {self.z_center:.6f} λ",
                f"  近焦点 z              = {self.z_focus_near:.6f} λ  (应 = F)",
                f"  馈源/远焦点 z         = {self.z_focus_far:.6f} λ",
                f"  副面口径 d_rim        = {self.d_rim:.6f} λ",
                f"  副面边缘              = {rim_txt}",
                f"  主面边缘 z            = {self.z_rim_primary:.6f} λ",
                f"  系统等效焦距          = {self.system_focal_length:.6f} λ  (f/D = {self.system_focal_length / self.D:.3f})",
                f"  遮挡面积比            = {self.blocking_ratio * 100:.3f} %",
                f"  馈源到主面边缘张角    = {np.degrees(self.half_angle_feed):.3f} °  （不是照射半张角）",
            ]
        )


def default_20lambda(M: float = 4.0, F: float = 8.0, D: float = 20.0) -> Cassegrain:
    """题目统一算例：20λ 卡塞格伦天线（D = 20λ, F/D = 0.4）。"""
    return Cassegrain(lam=1.0, D=D, F=F, M=M, L=M * F / (M + 1.0))


if __name__ == "__main__":
    geo = default_20lambda()
    print(geo.summary())
    print()
    for name, margin, ok in geo.consistency_report():
        print(f"  [{'OK  ' if ok else 'FAIL'}] {name}  (margin={margin:.3e})")
