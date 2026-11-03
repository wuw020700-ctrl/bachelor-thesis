"""配置文件读取与校验。"""

import pytest

from antennasim.config import CaseConfig, ConfigError, load_config


def test_load_case_file(cfg):
    assert cfg.name == "cassegrain_20lambda"
    assert cfg.geometry.diameter == pytest.approx(20.0)
    assert cfg.geometry.f_over_d == pytest.approx(0.4)
    assert cfg.geometry.magnification == pytest.approx(4.0)


def test_derived_quantities(cfg):
    # F = D * (F/D)
    assert cfg.focal_length == pytest.approx(8.0)
    # 未指定 sub_vertex 时取 M*F/(M+1) = 6.4
    assert cfg.sub_vertex == pytest.approx(4.0 * 8.0 / 5.0)


def test_missing_name_rejected(tmp_path):
    p = tmp_path / "bad.yaml"
    p.write_text("geometry:\n  diameter: 20\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="case.name"):
        load_config(p)


def test_illegal_values_rejected(tmp_path):
    p = tmp_path / "bad.yaml"
    p.write_text("case:\n  name: x\ngeometry:\n  magnification: 0.5\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="magnification"):
        load_config(p)


def test_sub_vertex_out_of_range_rejected(tmp_path):
    p = tmp_path / "bad.yaml"
    p.write_text(
        "case:\n  name: x\ngeometry:\n  diameter: 20\n  f_over_d: 0.4\n"
        "  magnification: 4\n  sub_vertex: 12.0\n",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="副面顶点"):
        load_config(p)


def test_missing_file_rejected(tmp_path):
    with pytest.raises(ConfigError, match="找不到"):
        load_config(tmp_path / "nope.yaml")


def test_defaults_fill_missing_sections(tmp_path):
    p = tmp_path / "minimal.yaml"
    p.write_text("case:\n  name: minimal\n", encoding="utf-8")
    cfg = load_config(p)
    assert isinstance(cfg, CaseConfig)
    assert cfg.geometry.diameter == pytest.approx(20.0)
    assert cfg.sampling.n_rho > 0


def test_unknown_key_rejected_as_config_error(tmp_path):
    """拼错一个键（feed: {qq: 8}）应当报配置错误，而不是抛 TypeError 堆栈。"""
    p = tmp_path / "typo.yaml"
    p.write_text("case:\n  name: t\nfeed:\n  qq: 8\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="无法识别的字段"):
        load_config(p)

