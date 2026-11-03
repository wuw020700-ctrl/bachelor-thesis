"""命令行入口。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from antennasim.config import ConfigError, load_config
from antennasim.pipeline import run_pipeline


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="antennasim",
        description="天线仿真开源软件集成平台：跑一个算例配置文件，输出结果与校验指标。",
    )
    parser.add_argument("config", help="算例配置文件（YAML）")
    parser.add_argument("--project-root", default=None,
                        help="项目根目录，输出目录相对它解析（默认当前目录）")
    parser.add_argument("--no-figure", action="store_true", help="跳过出图")
    parser.add_argument("--quiet", action="store_true", help="只输出最终汇总")
    args = parser.parse_args(argv)

    try:
        cfg = load_config(args.config)
    except ConfigError as exc:
        print(f"配置错误：{exc}", file=sys.stderr)
        return 2

    # 优先级：命令行显式指定 > 配置文件
    # 没给 --no-figure 时传 None，让配置文件里的 output.figure 决定；
    # 早先直接传 not args.no_figure，等于永远传 True，把配置覆盖掉了。
    make_figure = False if args.no_figure else None

    result = run_pipeline(
        cfg,
        project_root=args.project_root,
        make_figure=make_figure,
        verbose=not args.quiet,
    )
    print()
    print(result.summary())
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
