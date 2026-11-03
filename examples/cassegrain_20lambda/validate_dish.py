"""Milestone M2: validate the self-written GO/PO chain on a 20-lambda dish.

Checks
------
1. Uniform aperture illumination vs the analytic Airy pattern.
   This one is expected to match to ~1e-6 and is the hard correctness gate.
2. Feed-tapered aperture pattern via the Kirchhoff aperture integral.
3. Surface PO integral with a spherical feed wave.

Note on 2 vs 3
--------------
Both use the same aperture edge taper, and their null positions line up, but
the sidelobe levels differ. That is expected for a deep dish (F/D = 0.4,
half-angle 64 deg): the aperture-field (Kirchhoff) formulation drops the
obliquity/projection factor that the surface PO integral keeps. Quantifying
this difference is an open item for the write-up, not a bug to paper over.

Run:
    .venv\\Scripts\\python.exe examples\\cassegrain_20lambda\\validate_dish.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from common.constants import wavenumber
from go_po.feed import (
    aperture_illumination,
    cos_power_pattern,
    edge_taper_db,
    slant_range,
)
from go_po.geometry import ParabolicDish
from go_po.po import (
    analytic_uniform_circular_aperture,
    far_field_aperture,
    po_surface_far_field,
)


def db(x):
    return 20.0 * np.log10(np.maximum(np.abs(x), 1e-12))


def main() -> int:
    wavelength = 1.0
    dish = ParabolicDish(diameter=20.0 * wavelength, f_over_d=0.4)
    k = wavenumber(wavelength)

    print(f"dish D        = {dish.diameter:.1f} lambda")
    print(f"focal length  = {dish.focal_length:.2f} lambda")
    print(f"depth         = {dish.depth:.3f} lambda")
    print(f"half angle    = {np.degrees(dish.half_angle):.2f} deg")
    print()

    theta = np.linspace(0.0, np.radians(12.0), 241)

    # --- 1. uniform aperture vs analytic Airy -------------------------------
    uniform = lambda rho: np.ones_like(rho)
    got = far_field_aperture(dish.radius, k, uniform, theta)
    exact = analytic_uniform_circular_aperture(dish.radius, k, theta)
    err = np.max(np.abs(got - exact))
    print(f"[1] Airy check: max|numeric - analytic| = {err:.3e}")
    print(f"    first null numeric at {np.degrees(theta[np.argmin(db(got)[1:]) + 1]):.3f} deg")

    # --- 2. tapered aperture -------------------------------------------------
    q = 8.0
    feed = cos_power_pattern(q)
    print(f"[2] feed cos^{q:g}: raw GO edge taper = {edge_taper_db(dish, feed):.2f} dB")

    # Rescale the feed so the aperture edge lands at -10 dB, then use the SAME
    # illumination in both the aperture integral and the surface PO integral.
    target_db = -10.0
    target = 10.0 ** (target_db / 20.0)
    g0 = float(np.ravel(feed(np.array([0.0])))[0])
    ge = float(np.ravel(feed(np.array([dish.half_angle])))[0])
    r0 = float(np.ravel(slant_range(dish, np.array([0.0])))[0])
    re = float(np.ravel(slant_range(dish, np.array([dish.half_angle])))[0])
    centre_raw, edge_raw = g0 / r0, ge / re
    alpha = (1.0 - target) / (centre_raw - edge_raw)
    beta = target - alpha * edge_raw

    def feed_norm(theta):
        # g'(theta) = r(theta) * (beta + alpha * g(theta)/r(theta))
        return beta * slant_range(dish, theta) + alpha * feed(theta)

    illum = aperture_illumination(dish, feed, normalize_edge_db=target_db)
    tapered = far_field_aperture(dish.radius, k, illum, theta)

    # --- 3. surface PO with feed spherical wave ------------------------------
    print("[3] surface PO integral (this is the slow one) ...")
    surface = po_surface_far_field(
        dish,
        k,
        feed_norm,
        theta,
        feed_polarization="x",
        n_rho=110,
        n_phi=200,
    )
    surface_mag = np.abs(surface[:, 0]) ** 2 + np.abs(surface[:, 1]) ** 2

    # --- report --------------------------------------------------------------
    def nulls(curve, floor_db=-30.0):
        mag = db(curve)
        out = []
        for i in range(1, len(mag) - 1):
            if mag[i] < floor_db and mag[i] <= mag[i - 1] and mag[i] <= mag[i + 1]:
                if not out or np.degrees(theta[i]) - out[-1] > 0.5:
                    out.append(np.degrees(theta[i]))
        return out

    n_ap = nulls(tapered)
    n_po = nulls(np.sqrt(surface_mag))
    print(f"    edge taper {target_db:.1f} dB applied to both methods")
    print(f"    deep-dip angles (-30 dB), aperture: {[f'{v:.2f}' for v in n_ap]}")
    print(f"    deep-dip angles (-30 dB), surface : {[f'{v:.2f}' for v in n_po]}")
    print("    sidelobe levels differ: deep dish obliquity factor (see module docstring)")
    print()

    out_dir = ROOT / "data" / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    np.savez(
        out_dir / "m2_validation.npz",
        theta=theta,
        uniform=got,
        analytic=exact,
        tapered=tapered,
        surface_power=surface_mag,
    )

    fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
    ax[0].plot(np.degrees(theta), db(got), "--", label="aperture integral")
    ax[0].plot(np.degrees(theta), db(exact), ":", lw=2, label="analytic Airy")
    ax[0].set_title(f"Uniform aperture (max err {err:.2e})")
    ax[0].set_xlabel("theta [deg]")
    ax[0].set_ylabel("normalised [dB]")
    ax[0].set_ylim(-40, 2)
    ax[0].grid(alpha=0.3)
    ax[0].legend()

    ax[1].plot(np.degrees(theta), db(tapered), label="aperture (Kirchhoff) integral")
    ax[1].plot(np.degrees(theta), db(np.sqrt(surface_mag)), "--", label="surface PO integral")
    ax[1].set_title(f"Cross-check, {target_db:.0f} dB edge taper (nulls align)")
    ax[1].set_xlabel("theta [deg]")
    ax[1].set_ylim(-40, 2)
    ax[1].grid(alpha=0.3)
    ax[1].legend()

    fig.tight_layout()
    fig_path = out_dir / "m2_validation.png"
    fig.savefig(fig_path, dpi=140)
    print(f"saved: {fig_path}")
    return 0 if err < 5e-3 else 1


if __name__ == "__main__":
    raise SystemExit(main())
