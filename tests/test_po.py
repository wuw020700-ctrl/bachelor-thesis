"""物理光学积分器的解析校核。

均匀照射的圆口径有解析解（艾里图案 2J1(u)/u）。
数值积分必须与它吻合，否则方向图的副瓣不可信。
"""

import numpy as np
import pytest

from go_po.po import analytic_uniform_circular_aperture, far_field_aperture


def _uniform(r):
    return np.ones_like(r)


def test_uniform_aperture_matches_airy(geo):
    k = 2.0 * np.pi
    theta = np.linspace(0.0, np.radians(12.0), 201)

    numeric = far_field_aperture(geo.R, k, _uniform, theta, n_rho=160, n_phi=288)
    exact = analytic_uniform_circular_aperture(geo.R, k, theta)

    assert np.max(np.abs(numeric - exact)) < 5e-3


def test_first_null_position(geo):
    """第一零点应出现在 k*a*sin(theta) = 3.8317。"""
    k = 2.0 * np.pi
    theta = np.linspace(0.0, np.radians(12.0), 1601)
    numeric = np.abs(far_field_aperture(geo.R, k, _uniform, theta, n_rho=200, n_phi=320))

    # 注意：不能用 argmin 找全局最小——艾里图案的零点越往后越深，
    # 全局最小落在 9.3° 附近。第一零点要取「第一个局部极小」。
    first = next(
        i for i in range(1, len(numeric) - 1)
        if numeric[i] < numeric[i - 1] and numeric[i] < numeric[i + 1]
    )
    expected = np.arcsin(3.8317 / (k * geo.R))
    assert theta[first] == pytest.approx(expected, abs=2e-3)


def test_boresight_is_normalised(geo):
    k = 2.0 * np.pi
    theta = np.array([0.0])
    val = far_field_aperture(geo.R, k, _uniform, theta)
    assert abs(abs(val[0]) - 1.0) < 1e-9


def test_explicit_normalisation_scales_result(geo):
    """normalize 是绝对除数，默认值是口径面元之和；
    显式传 2 倍参考时，结果应恰好减半。"""
    from go_po.geometry import build_polar_grid

    k = 2.0 * np.pi
    theta = np.array([0.0])

    # 与 far_field_aperture 的默认采样保持一致，才能复现它的内部参考值
    _, _, dA = build_polar_grid(geo.R, 220, 360)
    ref = float(dA.sum())

    a = far_field_aperture(geo.R, k, _uniform, theta, normalize=ref)
    b = far_field_aperture(geo.R, k, _uniform, theta, normalize=2.0 * ref)
    assert abs(b[0] - a[0] / 2.0) < 1e-9


def test_complex_illumination_preserves_power(geo):
    """纯相位照明不改变总辐射功率（帕塞瓦尔定理）。

    2026-11-03 审查第 2 条：旧版把 illumination 的返回值截成实部，
    ``cos(phi)`` 相当于给口径加了幅度权重，总辐射功率会掉一大截。
    这条判据比"峰值是否离开视轴"有力：取实部之后波束照样会偏，
    但口径功率不可能守恒。
    """
    k = 2.0 * np.pi
    A = 5.0
    theta = np.radians(np.linspace(0.0, 80.0, 801))
    weight = np.sin(theta)

    def flat(r):
        return np.ones_like(r, dtype=complex)

    def phase_only(r):
        return np.exp(1j * A * (r / geo.R) ** 2)

    norm0 = far_field_aperture(geo.R, k, flat, np.array([0.0]), normalize=1.0)[0]
    u = np.abs(
        far_field_aperture(geo.R, k, flat, theta, normalize=norm0, n_rho=120, n_phi=240)
    )
    p = np.abs(
        far_field_aperture(geo.R, k, phase_only, theta, normalize=norm0, n_rho=120, n_phi=240)
    )

    ratio = float(np.sum(p ** 2 * weight) / np.sum(u ** 2 * weight))
    assert 0.9 < ratio < 1.1, f"纯相位照明改变了总功率（比值 {ratio:.3f}），说明复场被截成了实部"


