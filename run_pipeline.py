#!/usr/bin/env python
"""一条命令跑完整个算例。

用法：
    python run_pipeline.py cases/cassegrain_20lambda.yaml

也可以换任何符合 schema 的配置文件。
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from antennasim.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
