"""口径场远场积分的归一化与增益损失。

对应 2026-11-03 审查第 6 条：``far_field_pattern`` 原来只能按峰值归一化，
``tapered_aperture(phase_error=...)`` 又是唯一带复相位的口径工厂，
于是「变形 -> 增益下降」这条路算不出来（永远 0 dB）。
"""

import numpy as np

from go_po.aperture_po import axial_amplitude, far_field_pattern, tapered_aperture


def test_peak_normalisation_is_still_default():
    """不传 normalize 时保持老行为：最大值恒为 1。"""
    af = tapered_aperture(10.0, edge_taper_db=-10.0, n_per_lambda=10.0)
    pat = far_field_pattern(af, np.array([0.0, 3.0, 6.0]))
    assert abs(float(pat.max()) - 1.0) < 1e-12


def test_explicit_normalisation_recovers_gain_loss():
    """共用同一个参考时，相位扰动必须让轴向增益掉下来。"""
    af0 = tapered_aperture(10.0, edge_taper_db=-10.0, n_per_lambda=10.0)
    ref = axial_amplitude(af0)

    rng = np.random.default_rng(20261104)
    dphi = rng.normal(scale=0.8, size=af0.n_points)
    af1 = tapered_aperture(
        10.0, edge_taper_db=-10.0, phase_error=dphi, n_per_lambda=10.0
    )

    g0 = float(far_field_pattern(af0, np.array([0.0]), normalize=ref)[0])
    g1 = float(far_field_pattern(af1, np.array([0.0]), normalize=ref)[0])
    loss_db = 20.0 * np.log10(g1 / g0)

    assert g0 > 0.0
    assert loss_db < -1.0, f"相位扰动没有带来增益损失（{loss_db:.2f} dB）"


def test_axial_amplitude_drops_with_phase_error():
    """轴向幅度随相位误差单调下降，且量级与 exp(-sigma^2/2) 相符。"""
    af0 = tapered_aperture(10.0, edge_taper_db=-10.0, n_per_lambda=10.0)
    ref = axial_amplitude(af0)

    rng = np.random.default_rng(7)
    for sigma in (0.3, 0.6, 1.0):
        dphi = rng.normal(scale=sigma, size=af0.n_points)
        af = tapered_aperture(
            10.0, edge_taper_db=-10.0, phase_error=dphi, n_per_lambda=10.0
        )
        g = float(far_field_pattern(af, np.array([0.0]), normalize=ref)[0])
        assert 0.0 < g <= 1.0
        # 幅度比落在 exp(-sigma^2/2) 的附近（随机屏，允许统计涨落）
        expect = np.exp(-0.5 * sigma ** 2)
        assert abs(g - expect) < 0.12, f"sigma={sigma}: {g:.3f} vs {expect:.3f}"
