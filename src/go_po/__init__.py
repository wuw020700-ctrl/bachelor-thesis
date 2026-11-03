"""几何光学 (GO) 与物理光学 (PO) 模块。

* ``aperture_po``  —— 口径场法 PO 积分 + 解析 Airy 校核
* ``rays``         —— 卡塞格伦双反射面射线追踪（馈源 -> 副面 -> 主面）
* ``feed``         —— 馈源方向图与 GO 口径照射
* ``geometry``     —— 单抛物面几何与极坐标采样
* ``po``           —— 另一套 PO：口径积分 + 面元积分

注意：卡塞格伦几何在 ``common.cassegrain``，本包不重复定义。
"""

from go_po.feed import aperture_illumination, cos_power_pattern, edge_taper_db
from go_po.geometry import ParabolicDish, build_polar_grid
from go_po.po import (
    analytic_uniform_circular_aperture,
    far_field_aperture,
    po_surface_far_field,
)
from go_po.rays import RayBundle, feed_half_angle_for_edge, trace_rays

__all__ = [
    "ParabolicDish",
    "build_polar_grid",
    "cos_power_pattern",
    "aperture_illumination",
    "edge_taper_db",
    "analytic_uniform_circular_aperture",
    "far_field_aperture",
    "po_surface_far_field",
    "RayBundle",
    "trace_rays",
    "feed_half_angle_for_edge",
]
