"""单反射面几何与极坐标采样。

坐标约定
--------
    z  : 视轴（boresight），反射面开口朝 +z
    x,y: 口径平面
    rho: 口径平面内的半径

所有长度用同一单位（米，或在归一化研究里用波长 λ）。

注意：双反射面的卡塞格伦几何在 ``common.cassegrain``，不要在这里重复定义。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ParabolicDish:
    """抛物面主反射面，z = rho^2 / (4F)。

    Parameters
    ----------
    diameter:
        口径直径 D。
    f_over_d:
        焦径比 F/D。
    """

    diameter: float
    f_over_d: float = 0.4

    @property
    def radius(self) -> float:
        return 0.5 * self.diameter

    @property
    def focal_length(self) -> float:
        return self.f_over_d * self.diameter

    @property
    def half_angle(self) -> float:
        """馈源半张角 theta_0（弧度）。"""
        return 2.0 * np.arctan(1.0 / (4.0 * self.f_over_d))

    @property
    def depth(self) -> float:
        """矢高（抛物面深度）。"""
        return self.radius**2 / (4.0 * self.focal_length)

    def z_of_rho(self, rho):
        rho = np.asarray(rho, dtype=float)
        return rho**2 / (4.0 * self.focal_length)

    def surface_normal(self, rho, phi):
        """反射面单位法向（指向 +z / 馈源一侧）。

        对 z = rho^2/(4F)，法向为 (-rho cos phi, -rho sin phi, 2F) 归一化。
        """
        rho = np.asarray(rho, dtype=float)
        phi = np.asarray(phi, dtype=float)
        F = self.focal_length
        n = np.stack(
            [-rho * np.cos(phi), -rho * np.sin(phi), np.full_like(rho, 2.0 * F)],
            axis=-1,
        )
        return n / np.linalg.norm(n, axis=-1, keepdims=True)

    def surface_point(self, rho, phi):
        rho = np.asarray(rho, dtype=float)
        phi = np.asarray(phi, dtype=float)
        return np.stack(
            [rho * np.cos(phi), rho * np.sin(phi), self.z_of_rho(rho)],
            axis=-1,
        )

    def feed_direction_from_focus(self, rho, phi):
        """从焦点 (0,0,F) 指向反射面某点的单位矢量。"""
        p = self.surface_point(rho, phi)
        focus = np.array([0.0, 0.0, self.focal_length])
        d = p - focus
        return d / np.linalg.norm(d, axis=-1, keepdims=True)


def build_polar_grid(radius: float, n_rho: int, n_phi: int):
    """圆形口径的极坐标采样（rho 方向取中点，避免 rho = 0 采样点）。

    Returns
    -------
    rho, phi : shape (n_rho, n_phi)
    dA       : 面元 rho * drho * dphi
    """
    drho = radius / n_rho
    dphi = 2.0 * np.pi / n_phi
    rho_1d = (np.arange(n_rho) + 0.5) * drho
    phi_1d = (np.arange(n_phi) + 0.5) * dphi
    rho, phi = np.meshgrid(rho_1d, phi_1d, indexing="ij")
    dA = rho * drho * dphi
    return rho, phi, dA
