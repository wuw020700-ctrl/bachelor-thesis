"""几何光学射线追踪的两个物理不变量。

这是本项目最重要的两个判据：
  1. 准直误差 —— 出射方向应平行于视轴
  2. 等光程   —— r1 + r2 - z_main 应为常数
只要双曲面取支、焦点位置或法向有任何错误，这两项会立刻失效。
"""

import numpy as np


def test_all_rays_complete_the_chain(bundle):
    assert bundle.n_valid == bundle.n_rays, "存在未走完 馈源->副面->主面 的射线"


def test_collimation_error_is_at_machine_precision(bundle):
    err = bundle.collimation_error()
    assert err < 1e-12, f"准直误差过大: {err:.3e}"


def test_optical_path_is_constant(bundle):
    ripple = bundle.path_length_ripple()
    assert ripple < 1e-10, f"等光程起伏过大: {ripple:.3e}"


def test_outgoing_direction_is_along_axis(bundle):
    d = bundle.d_out[bundle.valid]
    assert np.allclose(d[:, 2], 1.0, atol=1e-12)


def test_rays_land_within_aperture(bundle, geo):
    r = bundle.aperture_radius[bundle.valid]
    assert r.min() > 0.0
    assert r.max() <= geo.R * (1 + 1e-9)


def test_ray_count_scales_with_sampling(geo):
    from go_po.rays import trace_rays

    b = trace_rays(geo, n_radial=6, n_azimuth=8)
    assert b.n_rays == 48
