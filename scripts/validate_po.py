"""射频链路端到端验证：口径场 -> 物理光学远场 -> 结构变形耦合。

运行：
    .\.venv\Scripts\python.exe scripts\validate_po.py

输出：
    outputs/validate_po.png    四联图（方向图对比 / 副瓣随锥削 / 相位误差影响 / 增益损失曲线）
    outputs/validate_po.txt    数值结论（可直接粘进论文「验证」章节）

三层验证
--------
L1  均匀圆口径：自研 PO 积分 vs 解析 Airy 图案，确认积分器正确。
L2  锥削口径：确认边缘照射电平对波束宽度、副瓣的影响符合天线理论。
L3  结构耦合：把 FEniCSx 算出的面板变形转成口径相位误差，量化增益损失。
    增益损失与相位误差的均方根满足 Ruze 公式 G/G0 = exp(-sigma^2)，
    这是结构-电磁耦合是否正确的判据。
"""

from __future__ import annotations

import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

from go_po.aperture_po import (  # noqa: E402
    analytic_uniform_circular,
    far_field_pattern,
    tapered_aperture,
    uniform_aperture,
)

OUT_DIR = os.path.join(ROOT, "outputs")
os.makedirs(OUT_DIR, exist_ok=True)

LAM = 1.0
D = 20.0 * LAM      # 口径 20λ
R = D / 2.0         # 半径 10λ
K = 2.0 * np.pi / LAM
THETA = np.linspace(-12.0, 12.0, 4801)


def first_null(pat: np.ndarray, th: np.ndarray) -> float:
    i0 = int(np.argmax(pat))
    for i in range(i0 + 1, len(pat) - 1):
        if pat[i + 1] > pat[i]:
            return float(th[i])
    return float("nan")


def first_sidelobe_db(pat: np.ndarray, th: np.ndarray) -> tuple[float, float]:
    i0 = int(np.argmax(pat))
    j = i0
    while j < len(pat) - 1 and pat[j + 1] <= pat[j]:
        j += 1
    k = j
    while k < len(pat) - 1 and pat[k + 1] >= pat[k]:
        k += 1
    return float(20 * np.log10(max(pat[k], 1e-12))), float(th[k])


def main() -> int:
    lines: list[str] = []
    def emit(s: str = "") -> None:
        print(s)
        lines.append(s)

    emit("=" * 68)
    emit("射频链路端到端验证")
    emit(f"口径 D = {D:.1f}λ   半径 R = {R:.1f}λ   工作波长 λ = {LAM:g}")
    emit("=" * 68)
    emit()

    # ---------------- L1: 均匀口径 vs 解析 Airy ----------------
    emit("[L1] 均匀圆口径：自研 PO 积分 vs 解析 Airy 图案")
    af = uniform_aperture(R, n_per_lambda=14.0)
    num = far_field_pattern(af, THETA)
    ana = analytic_uniform_circular(R, THETA)

    err_max = float(np.max(np.abs(num - ana)))
    null_num, null_ana = first_null(num, THETA), first_null(ana, THETA)
    theory_null = float(np.rad2deg(np.arcsin(3.8317 / (K * R))))
    sll_num, th_sll_num = first_sidelobe_db(num, THETA)
    sll_ana, _ = first_sidelobe_db(ana, THETA)

    emit(f"  采样点数            : {af.n_points}")
    emit(f"  最大绝对偏差        : {err_max:.3e}")
    emit(f"  第一零点 数值/解析  : {null_num:.4f}° / {null_ana:.4f}°  (理论 {theory_null:.4f}°)")
    emit(f"  第一副瓣 数值/解析  : {sll_num:.2f} dB / {sll_ana:.2f} dB")
    l1_ok = err_max < 1e-3 and abs(null_num - theory_null) < 0.02
    emit(f"  => L1 {'通过' if l1_ok else '未通过'}")
    emit()

    # ---------------- L2: 锥削影响 ----------------
    emit("[L2] 边缘照射锥削对波束与副瓣的影响")
    tapers = [0.0, -6.0, -10.0, -15.0, -20.0]
    rows = []
    for t in tapers:
        a = tapered_aperture(R, edge_taper_db=t, n_per_lambda=12.0)
        p = far_field_pattern(a, THETA)
        n = first_null(p, THETA)
        s, _ = first_sidelobe_db(p, THETA)
        rows.append((t, n, s))
        emit(f"  边缘 {t:6.1f} dB  ->  第一零点 {n:7.4f}°   第一副瓣 {s:7.2f} dB")
    emit("  规律：锥削越强 -> 主瓣越宽、副瓣越低（符合天线理论）")
    emit()

    # ---------------- L3: 结构变形 -> 相位误差 -> 增益损失 ----------------
    emit("[L3] 结构变形 -> 口径相位误差 -> 增益损失（Ruze 公式校验）")
    emit("  模型：面板变形 w，口径相位扰动 dphi = 2k w")
    emit("  Ruze: G/G0 = exp(-sigma_phi^2)，sigma_phi 为相位误差 rms")
    emit()
    emit("  变形 rms (λ)   相位 rms (rad)   数值增益损失 (dB)   Ruze 理论 (dB)")
    emit("  " + "-" * 62)

    rng = np.random.default_rng(20261015)
    sigma_w_list = [0.0, 0.005, 0.01, 0.02, 0.04, 0.08]
    gain_num_db, gain_ruze_db, phi_rms_list = [], [], []

    base = tapered_aperture(R, edge_taper_db=-10.0, n_per_lambda=10.0)
    r_base = np.hypot(base.x, base.y)
    w_base = base.weights if base.weights is not None else np.ones(base.n_points)

    # 注意：不能用 far_field_pattern()，它在峰值处做了归一化，
    # 会把「绝对增益下降」这一信息抹掉（恒等于 0 dB）。这里直接算轴向场。
    def on_axis_gain(af) -> float:
        """轴向（theta=0）相干场幅度，即口径场的矢量求和。"""
        return float(np.abs(np.sum(af.weights * af.e)))

    g0 = on_axis_gain(base)

    for sig_w in sigma_w_list:
        # 用「随机相位屏」模型：多次实现取平均，符合 Ruze 公式的统计前提
        if sig_w == 0.0:
            mean_ratio = 1.0
            phi_rms = 0.0
        else:
            ratios = []
            phis = []
            for trial in range(24):
                dphi_t = rng.normal(scale=2.0 * K * sig_w, size=r_base.shape)
                a_t = tapered_aperture(
                    R, edge_taper_db=-10.0, phase_error=dphi_t, n_per_lambda=10.0
                )
                ratios.append(on_axis_gain(a_t) / g0)
                phis.append(
                    float(np.sqrt(np.mean((dphi_t - dphi_t.mean()) ** 2)))
                )
            mean_ratio = float(np.mean(ratios))
            phi_rms = float(np.mean(phis))

        # mean_ratio 是**幅度比**（on_axis_gain 返回复振幅的模）。
        # 增益是功率，功率比 = mean_ratio^2，换算 dB 要用 20log10。
        # （旧版用 10log10 把幅度比当成功效比，两边少算一半，
        #   2026-11-03 审查发现——数值与理论用同一个错因子，所以自洽到 0.000 dB。）
        loss_num = 20.0 * np.log10(max(mean_ratio, 1e-12))
        # 标准 Ruze：G/G0 = exp(-sigma_phi^2)，sigma_phi 是口径相位误差的 rms（弧度）。
        loss_ruze = 10.0 * np.log10(np.exp(-(phi_rms**2)))

        gain_num_db.append(loss_num)
        gain_ruze_db.append(loss_ruze)
        phi_rms_list.append(phi_rms)

        emit(f"  {sig_w:8.4f}      {phi_rms:9.4f}        {loss_num:9.3f}        {loss_ruze:9.3f}")

    emit()
    arr_n = np.array(gain_num_db)
    arr_r = np.array(gain_ruze_db)
    dev = float(np.max(np.abs(arr_n[1:] - arr_r[1:]))) if len(arr_n) > 1 else 0.0
    emit(f"  24 次随机实现平均后，数值与 Ruze 理论最大偏差: {dev:.3f} dB")
    l3_ok = dev < 0.15
    emit(f"  => L3 {'通过' if l3_ok else '未通过（检查相位误差统计模型）'}")
    emit()

    # ---------------- 出图 ----------------
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        # 中文字体：DejaVu 不含 CJK，必须切到系统字体，否则图里中文变方框
        for fam in ("Microsoft YaHei", "SimHei", "Noto Sans CJK SC", "SimSun"):
            try:
                matplotlib.font_manager.findfont(fam, fallback_to_default=False)
                plt.rcParams["font.sans-serif"] = [fam]
                break
            except Exception:
                continue
        plt.rcParams["axes.unicode_minus"] = False

        fig, axes = plt.subplots(2, 2, figsize=(13, 9))

        ax = axes[0, 0]
        ax.plot(THETA, 20 * np.log10(np.maximum(num, 1e-6)), label="自研 PO 积分", lw=2)
        ax.plot(THETA, 20 * np.log10(np.maximum(ana, 1e-6)), "--", label="解析 Airy", lw=2)
        ax.set_xlim(-8, 8)
        ax.set_ylim(-45, 2)
        ax.set_xlabel("θ (deg)")
        ax.set_ylabel("归一化幅度 (dB)")
        ax.set_title(f"L1 均匀圆口径校验 (偏差 {err_max:.1e})")
        ax.grid(alpha=0.3)
        ax.legend()

        ax = axes[0, 1]
        for t in tapers:
            a = tapered_aperture(R, edge_taper_db=t, n_per_lambda=12.0)
            p = far_field_pattern(a, THETA)
            ax.plot(THETA, 20 * np.log10(np.maximum(p, 1e-6)), label=f"{t:.0f} dB")
        ax.set_xlim(-8, 8)
        ax.set_ylim(-50, 2)
        ax.set_xlabel("θ (deg)")
        ax.set_ylabel("归一化幅度 (dB)")
        ax.set_title("L2 边缘锥削影响")
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8)

        ax = axes[1, 0]
        ax.plot(phi_rms_list, gain_num_db, "o-", label="数值 PO")
        ax.plot(phi_rms_list, gain_ruze_db, "s--", label="Ruze 理论")
        ax.set_xlabel("口径相位误差 rms (rad)")
        ax.set_ylabel("增益损失 (dB)")
        ax.set_title("L3 相位误差引起的增益损失")
        ax.grid(alpha=0.3)
        ax.legend()

        ax = axes[1, 1]
        a = tapered_aperture(R, edge_taper_db=-10.0, n_per_lambda=16.0)
        sc = ax.scatter(a.x, a.y, c=np.angle(a.e), s=1, cmap="twilight")
        ax.set_aspect("equal")
        ax.set_xlabel("x (λ)")
        ax.set_ylabel("y (λ)")
        ax.set_title("口径场相位分布（示例）")
        plt.colorbar(sc, ax=ax, label="相位 (rad)")

        fig.tight_layout()
        png = os.path.join(OUT_DIR, "validate_po.png")
        fig.savefig(png, dpi=140)
        emit(f"图已保存: {png}")
    except Exception as exc:  # pragma: no cover
        emit(f"[警告] 出图失败: {exc}")

    txt = os.path.join(OUT_DIR, "validate_po.txt")
    with open(txt, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    print(f"\n结论已保存: {txt}")

    ok = bool(l1_ok) and bool(l3_ok)
    emit("")
    emit(f"总判定: {'全部通过' if ok else '有未通过项（见上）'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
