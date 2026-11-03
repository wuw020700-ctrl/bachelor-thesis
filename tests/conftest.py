"""pytest 公共配置：把 src 加入导入路径，并提供常用 fixture。"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from antennasim.config import load_config  # noqa: E402
from common.cassegrain import default_20lambda  # noqa: E402


@pytest.fixture(scope="session")
def root() -> Path:
    return ROOT


@pytest.fixture(scope="session")
def geo():
    return default_20lambda(M=4.0)


@pytest.fixture(scope="session")
def cfg():
    return load_config(ROOT / "cases" / "cassegrain_20lambda.yaml")


@pytest.fixture(scope="session")
def bundle(geo):
    from go_po.rays import trace_rays

    return trace_rays(geo, n_radial=12, n_azimuth=24)
