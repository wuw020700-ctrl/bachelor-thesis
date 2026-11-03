"""命令行入口的行为，特别是「命令行 > 配置文件」的优先级。"""

import dataclasses
from pathlib import Path

from antennasim.cli import main
from antennasim.config import load_config

ROOT = Path(__file__).resolve().parents[1]


def _make_case(tmp_path, *, figure: bool):
    """基于标准算例派生一个配置，写回文件，返回 (路径, 配置)。"""
    src = load_config(ROOT / "cases" / "cassegrain_20lambda.yaml")
    cfg = dataclasses.replace(
        src,
        output=dataclasses.replace(src.output, figure=figure, tag=f"t{int(figure)}"),
    )
    p = tmp_path / "case.yaml"
    cfg.dump(p)                       # 用正规的导出方法，schema 不会错
    return p, cfg


def test_config_figure_false_is_respected(tmp_path):
    """配置文件写 figure: false 时，不应生成图。"""
    p, cfg = _make_case(tmp_path, figure=False)
    rc = main([str(p), "--project-root", str(tmp_path), "--quiet"])
    assert rc == 0
    assert not (tmp_path / cfg.output.directory / f"{cfg.output.tag}.png").exists()


def test_no_figure_flag_overrides_config(tmp_path):
    """配置文件写 figure: true，命令行给 --no-figure 时也不出图。"""
    p, cfg = _make_case(tmp_path, figure=True)
    rc = main([str(p), "--project-root", str(tmp_path), "--quiet", "--no-figure"])
    assert rc == 0
    assert not (tmp_path / cfg.output.directory / f"{cfg.output.tag}.png").exists()


def test_config_roundtrip(tmp_path):
    """配置导出后重新读入，内容必须一致。"""
    p, cfg = _make_case(tmp_path, figure=False)
    again = load_config(p)
    assert again == cfg


def test_config_error_returns_code_two(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("case:\n  name: \n", encoding="utf-8")
    assert main([str(bad)]) == 2
