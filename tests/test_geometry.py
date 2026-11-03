"""卡塞格伦几何的物理自检。"""

import pytest

from common.cassegrain import Cassegrain, default_20lambda


def test_near_focus_coincides_with_parabola_focus(geo):
    """双曲面近焦点必须精确落在抛物面焦点 z = F。"""
    assert abs(geo.z_focus_near - geo.F) < 1e-12


def test_magnification_identity(geo):
    """M 必须等于 (c+a)/(c-a)。"""
    assert (geo.c + geo.a) / (geo.c - geo.a) == pytest.approx(geo.M, rel=1e-12)


def test_eccentricity(geo):
    assert geo.e == pytest.approx((geo.M + 1) / (geo.M - 1), rel=1e-12)


def test_consistency_report_all_pass(geo):
    report = geo.consistency_report()
    assert report, "自检报告不应为空"
    failed = [name for name, _, ok in report if not ok]
    assert not failed, f"以下自检项未通过: {failed}"


def test_blockage_is_reasonable(geo):
    """副面遮挡比必须为正且小于 15%（工程上可接受的上限）。"""
    assert 0.0 < geo.blocking_ratio < 0.15


def test_sub_rim_is_computed_not_zero(geo):
    """副面边缘不能退化为 0——早期版本曾在顶点处求半径，结果恒为 0。"""
    rim = geo.sub_rim()
    assert rim is not None
    r, z = rim
    assert r > 0.5
    assert z > geo.L


def test_invalid_L_rejected():
    with pytest.raises(ValueError):
        Cassegrain(D=20.0, F=8.0, M=4.0, L=9.0)   # L 必须 < F


def test_invalid_M_rejected():
    with pytest.raises(ValueError):
        Cassegrain(D=20.0, F=8.0, M=0.8)
