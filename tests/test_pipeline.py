"""端到端流水线：配置文件进，结果文件出。"""

import json

from antennasim.pipeline import run_pipeline


def test_pipeline_runs_and_reports_ok(cfg, tmp_path):
    result = run_pipeline(cfg, project_root=tmp_path, make_figure=False, verbose=False)
    assert result.ok, f"流水线未通过校验: {result.metrics}"
    assert result.seconds > 0


def test_pipeline_writes_outputs(cfg, tmp_path):
    result = run_pipeline(cfg, project_root=tmp_path, make_figure=False, verbose=False)
    npz_path = tmp_path / cfg.output.directory / f"{cfg.output.tag}.npz"
    json_path = tmp_path / cfg.output.directory / f"{cfg.output.tag}.json"
    assert npz_path.exists()
    assert json_path.exists()

    meta = json.loads(json_path.read_text(encoding="utf-8"))
    assert meta["case"] == cfg.name
    assert all(meta["checks"].values()), meta["checks"]


def test_pipeline_is_reproducible(cfg, tmp_path):
    """同一配置跑两次，指标必须一致。"""
    a = run_pipeline(cfg, project_root=tmp_path, make_figure=False, verbose=False)
    b = run_pipeline(cfg, project_root=tmp_path, make_figure=False, verbose=False)
    assert a.metrics == b.metrics


def test_pipeline_rejects_inconsistent_geometry(cfg, tmp_path):
    """把副面位置改到非法范围，应在建模阶段就报错。"""
    import dataclasses

    import pytest

    from antennasim.config import ConfigError

    bad_geom = dataclasses.replace(cfg.geometry, sub_vertex=20.0)
    bad_cfg = dataclasses.replace(cfg, geometry=bad_geom)
    with pytest.raises(ConfigError):
        bad_cfg.validate()
