"""Physical optics (PO) far-field integrals.

Two variants are provided:

1. ``far_field_aperture`` - Kirchhoff/PO integration over the projected
   aperture. This is the workhorse for reflector pattern cuts and is what the
   validation example checks against the analytic Airy pattern.

2. ``po_surface_far_field`` - the explicit surface integral
   ``E ~ (I - r r^T) . integral (n x H) exp(j k r . r') dS``
   evaluated directly on the reflector surface with a spherical-wave
   incidence from the feed. This is the "self-written GO/PO" piece the
   project brief asks for.
"""

from __future__ import annotations

import numpy as np

from common.constants import ETA0
from go_po.feed import slant_range, theta_of_rho
from go_po.geometry import ParabolicDish, build_polar_grid


def analytic_uniform_circular_aperture(radius: float, k: float, theta):
    """Airy pattern of a uniformly illuminated circular aperture.

    Returns the normalised voltage pattern ``2 J1(u)/u`` with ``u = k a sin``.
    """
    from scipy.special import j1

    theta = np.asarray(theta, dtype=float)
    u = k * radius * np.sin(theta)
    out = np.ones_like(u)
    nz = u != 0
    out[nz] = 2.0 * j1(u[nz]) / u[nz]
    return out


def _direction(theta, phi):
    theta = np.atleast_1d(np.asarray(theta, dtype=float))
    phi = np.asarray(phi, dtype=float)
    return np.stack(
        [
            np.sin(theta) * np.cos(phi),
            np.sin(theta) * np.sin(phi),
            np.cos(theta),
        ],
        axis=-1,
    )


def far_field_aperture(
    radius: float,
    k: float,
    illumination,
    theta,
    phi: float = 0.0,
    *,
    n_rho: int = 220,
    n_phi: int = 360,
    normalize: float | None = None,
):
    """Kirchhoff far field of a circular aperture.

    ``illumination(rho)`` gives the aperture voltage distribution.

    ``normalize``
        Fixed normalisation constant. Leave as None to normalise by the
        boresight sum of the supplied illumination. Pass an explicit value
        when comparing two illuminations (e.g. with and without a central
        blockage) - otherwise the blockage is normalised away and the gain
        loss comes out as 0 dB.

    **复口径场**（2026-11-03 修）：
        ``illumination`` 可以返回复数，用来带口径相位扰动（变形->相位）。
        旧版这里写的是 ``dtype=float``，numpy 只发一条 ComplexWarning 就取实部，
        相位整段丢掉、静默算错。

        注意：带相位扰动时**必须**自己传 ``normalize``（用未扰动口径的视轴和），
        否则会按扰动后的视轴和归一化，增益损失又变成 0 dB。
    """
    rho, phi_a, dA = build_polar_grid(radius, n_rho, n_phi)
    amp = np.asarray(illumination(rho), dtype=complex) * np.ones_like(rho, dtype=complex)

    theta = np.atleast_1d(np.asarray(theta, dtype=float))
    u = np.sin(theta) * np.cos(phi)
    v = np.sin(theta) * np.sin(phi)

    # phase[k, i, j] = k * rho_ij * (u_k cos(phi_a) + v_k sin(phi_a))
    phase = k * rho[None, :, :] * (
        u[:, None, None] * np.cos(phi_a)[None, :, :]
        + v[:, None, None] * np.sin(phi_a)[None, :, :]
    )
    field = np.sum(amp[None, :, :] * np.exp(1j * phase) * dA[None, :, :], axis=(1, 2))

    if normalize is None:
        ref = np.sum(amp * dA)
        normalize = ref if abs(ref) > 0.0 else 1.0
    return field / normalize


def po_surface_far_field(
    dish: ParabolicDish,
    k: float,
    feed_pattern,
    theta,
    phi: float = 0.0,
    *,
    feed_polarization: str = "x",
    n_rho: int = 140,
    n_phi: int = 240,
    block_radius: float | None = None,
):
    """Explicit PO surface integral on the parabolic reflector.

    Parameters
    ----------
    feed_pattern:
        Voltage pattern ``g(theta)`` of the feed located at the focus.
    block_radius:
        Optional radius of a central blockage (e.g. the sub reflector shadow),
        as seen on the aperture.
    """
    rho_max = dish.radius
    rho, phi_a, dA = build_polar_grid(rho_max, n_rho, n_phi)
    keep = np.ones_like(rho, dtype=bool)
    if block_radius is not None:
        keep &= rho >= block_radius

    rho = rho[keep]
    phi_a = phi_a[keep]
    dA = dA[keep]

    theta_f = theta_of_rho(dish, rho)
    r_f = slant_range(dish, theta_f)

    # incident direction (from focus toward the surface)
    r_hat = dish.feed_direction_from_focus(rho, phi_a)
    n_hat = dish.surface_normal(rho, phi_a)

    if feed_polarization == "x":
        e_co = np.array([1.0, 0.0, 0.0])
    elif feed_polarization == "y":
        e_co = np.array([0.0, 1.0, 0.0])
    else:
        raise ValueError("feed_polarization must be 'x' or 'y'")

    # transverse (to r_hat) polarization of the spherical feed wave
    proj = np.sum(r_hat * e_co, axis=-1, keepdims=True)
    e_inc = e_co - r_hat * proj
    e_inc /= np.linalg.norm(e_inc, axis=-1, keepdims=True)

    amp = feed_pattern(theta_f) * np.exp(-1j * k * r_f) / r_f
    e_inc = amp[:, None] * e_inc
    h_inc = np.cross(r_hat, e_inc) / ETA0
    j_s = 2.0 * np.cross(n_hat, h_inc)

    # surface area element: dS = dA * sqrt(1 + (dz/drho)^2)
    dz_drho = rho / (2.0 * dish.focal_length)
    dS = dA * np.sqrt(1.0 + dz_drho**2)

    surface = dish.surface_point(rho, phi_a)

    out = []
    for t in np.atleast_1d(theta):
        r_dir = _direction(t, phi)[0]
        phase = np.exp(1j * k * (surface @ r_dir))
        integral = np.sum(j_s * (phase * dS)[:, None], axis=0)
        e_far = integral - r_dir * (r_dir @ integral)
        out.append(e_far)

    e_far = np.array(out)
    ref = np.abs(e_far[0]).max()
    return e_far / ref
