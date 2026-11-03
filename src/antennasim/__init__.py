"""antennasim —— 天线仿真开源软件集成平台。

把三个异构的开源工具串成一条可复现的链路：

    馈源全波仿真 (openEMS)
        -> 高频近似 (自研 GO/PO)
        -> 结构变形 (FEniCSx)
        -> 双域耦合

本包负责几何建模、射线追踪、远场计算与结果输出的编排。
底层数值代码位于 ``common`` 与 ``go_po`` 包。
"""

__version__ = "0.1.0"

from antennasim.config import CaseConfig, load_config
from antennasim.pipeline import PipelineResult, run_pipeline

__all__ = ["CaseConfig", "load_config", "PipelineResult", "run_pipeline", "__version__"]
