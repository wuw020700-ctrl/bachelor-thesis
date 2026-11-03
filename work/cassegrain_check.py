"""Scratch: verify the correct Cassegrain geometry from first principles.

Physical requirements a valid Cassegrain must satisfy:
  (R1) the hyperbola's NEAR focus coincides with the parabola focus, z = F
  (R2) the sub-reflector vertex sits at z = L with 0 < L < F
  (R3) a ray leaving the feed at the FAR focus, after reflecting off the sub
       and then the main reflector, leaves PARALLEL to the z axis

(R3) is the real test: if the geometry is right, the collimation error is ~0.
"""

import numpy as np

F = 8.0
D = 20.0
M = 4.0
R = D / 2


def build(L, F, M):
    """Hyperbola from vertex position L and magnification M."""
    # vertex at z_c + a = L, near focus at z_c + c = F
    c_minus_a = F - L
    c = (M + 1) * c_minus_a / 2
    a = (M - 1) * c_minus_a / 2
    z_c = L - a
    b2 = c * c - a * a
    z_far = z_c - c
    return dict(a=a, c=c, b2=b2, z_c=z_c, L=L, z_far=z_far,
                z_near=z_c + c, e=c / a)


def reflect(d, n):
    dn = np.sum(d * n, axis=-1, keepdims=True)
    out = d - 2.0 * dn * n
    return out / np.linalg.norm(out, axis=-1, keepdims=True)


def implicit_sub(p, g):
    r2 = p[..., 0] ** 2 + p[..., 1] ** 2
    return (p[..., 2] - g["z_c"]) ** 2 / g["a"] ** 2 - r2 / g["b2"] - 1.0


def implicit_main(p, F):
    r2 = p[..., 0] ** 2 + p[..., 1] ** 2
    return r2 - 4.0 * F * p[..., 2]


def first_root(o, d, f, t_max, n_scan=4000, n_bis=80, t_min=None):
    """First root of f along o + t d for t in [t_min, t_max] (per ray)."""
    n = o.shape[0]
    if t_min is None:
        t_min = np.full(n, 1e-9)
    vals = np.empty((n, n_scan))
    frac = np.linspace(0.0, 1.0, n_scan)
    ts = t_min[:, None] + frac[None, :] * (t_max - t_min)[:, None]
    for j in range(n_scan):
        vals[:, j] = f(o + ts[:, j][:, None] * d)
    sgn = np.sign(vals)
    sgn[sgn == 0] = 1.0
    change = sgn[:, 1:] != sgn[:, :-1]
    found = change.any(axis=1)
    idx = np.argmax(change, axis=1)
    lo = ts[np.arange(n), idx]
    hi = ts[np.arange(n), idx + 1]
    vlo = f(o + lo[:, None] * d)
    for _ in range(n_bis):
        mid = 0.5 * (lo + hi)
        vmid = f(o + mid[:, None] * d)
        same = np.sign(vmid) == np.sign(vlo)
        lo = np.where(same, mid, lo)
        hi = np.where(same, hi, mid)
    return np.where(found, 0.5 * (lo + hi), np.nan)


def trace(g, F, R, n_theta=200, theta_min=1e-4):
    """Feed -> sub -> main -> out, for a fan of rays in the x-z plane."""
    z_f = g["z_far"]
    feed = np.array([0.0, 0.0, z_f])
    # generous window: scan well past the main aperture, then filter by r <= R
    theta_max = np.arctan(2.5 * R / abs(F - z_f))
    th = np.linspace(theta_min, theta_max, n_theta)

    d0 = np.stack([np.sin(th), np.zeros_like(th), np.cos(th)], axis=-1)
    # sub surface (near branch, which faces the feed)
    # Only the RIGHT branch (z >= z_c) is the sub reflector; start the scan
    # where each ray reaches z = z_c so we never lock onto the left branch.
    t_zc = (g["z_c"] - z_f) / d0[:, 2]
    t_max_all = 6.0 * (abs(z_f) + F)
    t_sub = first_root(np.tile(feed, (n_theta, 1)), d0,
                       lambda p: implicit_sub(p, g), t_max_all,
                       t_min=t_zc)
    ok = np.isfinite(t_sub)
    p_sub = feed + np.where(ok, t_sub, 0.0)[:, None] * d0

    # sub normal: grad of (z-zc)^2/a^2 - r^2/b^2
    nrm = np.stack([-2 * p_sub[:, 0] / g["b2"],
                    -2 * p_sub[:, 1] / g["b2"],
                    2 * (p_sub[:, 2] - g["z_c"]) / g["a"] ** 2], axis=-1)
    nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
    flip = np.sum(nrm * d0, axis=-1) > 0
    nrm[flip] *= -1
    d1 = reflect(d0, nrm)

    # sub -> main
    t_main = first_root(p_sub, d1, lambda p: implicit_main(p, F),
                        t_max_all)
    ok &= np.isfinite(t_main)
    p_main = p_sub + np.where(np.isfinite(t_main), t_main, 0.0)[:, None] * d1

    # keep only rays that actually land on the main aperture
    r_main = np.hypot(p_main[:, 0], p_main[:, 1])
    ok &= r_main <= R * (1.0 + 1e-9)

    n_main = np.stack([2 * p_main[:, 0], 2 * p_main[:, 1],
                       np.full(n_theta, -4.0 * F)], axis=-1)
    n_main /= np.linalg.norm(n_main, axis=-1, keepdims=True)
    flip = np.sum(n_main * d1, axis=-1) > 0
    n_main[flip] *= -1
    d2 = reflect(d1, n_main)

    return dict(valid=ok, p_sub=p_sub, p_main=p_main, d_out=d2,
                collim=np.max(np.abs(d2[ok][:, :2])) if ok.any() else np.nan)


print("=" * 72)
print("候选 A: L = F/M   (dsh 用了 L=F/M，但 z_c 和 a 取错)")
g = build(L=F / M, F=F, M=M)
print(f"  L={g['L']:.4f}  a={g['a']:.4f}  c={g['c']:.4f}  e={g['e']:.4f}")
print(f"  z_c={g['z_c']:.4f}  近焦点 z={g['z_near']:.6f} (应={F})   远焦点 z={g['z_far']:.4f}")
r = trace(g, F, R)
rf = np.hypot(r["p_main"][:, 0], r["p_main"][:, 1])
print(f"  命中 {int(r['valid'].sum())}/{len(r['valid'])}  准直误差={r['collim']:.3e}")
if r["valid"].any():
    rs = np.hypot(r["p_sub"][:, 0], r["p_sub"][:, 1])
    print(f"  主面落点半径: {rf[r['valid']].min():.3f} .. {rf[r['valid']].max():.3f} λ (口径半径 {R})")
    print(f"  副面落点半径: {rs[r['valid']].min():.3f} .. {rs[r['valid']].max():.3f} λ")
    print(f"  副面落点 z  : {r['p_sub'][r['valid'], 2].min():.3f} .. {r['p_sub'][r['valid'], 2].max():.3f} λ")
    k = np.argmax(rs)
    print(f"  最外那条: 副面 r={rs[k]:.3f} z={r['p_sub'][k,2]:.3f}"
          f"  -> 主面 r={rf[k]:.3f} z={r['p_main'][k,2]:.3f}")

print()
print("=" * 72)
print("对照: dsh 的公式 (a=F(M-1)/2, z_c=L+a)")
a_d, L_d = F * (M - 1) / 2, F / M
print(f"  a={a_d:.4f}  c=a+F={a_d + F:.4f}  z_c=L+a={L_d + a_d:.4f}")
print(f"  近焦点 z = z_c - c = {L_d + a_d - (a_d + F):.4f}  (应={F})  -> 差 {abs(L_d + a_d - (a_d + F) - F):.4f}")

print()
print("=" * 72)
print("扫描 L：准直误差 / 副面最大半径 / 遮挡比 / 馈源位置")
print(f"  {'L':>6} {'a':>7} {'c':>7} {'z_c':>8} {'z_feed':>8} {'副面r_max':>9} {'遮挡':>7} {'准直':>10}")
for L in (0.5, 2.0, 4.0, 5.5, 6.0, 6.5, 7.0, 7.5):
    g = build(L=L, F=F, M=M)
    r = trace(g, F, R)
    rs = np.hypot(r["p_sub"][:, 0], r["p_sub"][:, 1])
    ok = r["valid"]
    rsub_max = rs[ok].max() if ok.any() else np.nan
    block = (2 * rsub_max / D) ** 2 if ok.any() else np.nan
    print(f"  {L:6.2f} {g['a']:7.3f} {g['c']:7.3f} {g['z_c']:8.3f} {g['z_far']:8.3f}"
          f" {rsub_max:9.3f} {block * 100:6.2f}% {r['collim']:10.2e}")
