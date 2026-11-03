import numpy as np, math

F = 8.0          # 主面焦距
R = 10.0         # 主面半径
lam = 1.0

def reflect(d, n):
    dn = float(np.dot(d, n))
    v = d - 2*dn*n
    return v/np.linalg.norm(v)

# 主面 r^2 = 4Fz, 焦点 (0,0,F)
def primary_hit(r):
    return np.array([r, 0.0, r*r/(4*F)])

def primary_normal(p):
    n = np.array([-p[0], -p[1], 2*F])
    return n/np.linalg.norm(n)

def trace(r, L, e, a=None):
    """给定主面半径 r、副面顶点轴向位置 L、离心率 e，返回出射方向。"""
    P = primary_hit(r)
    d_in = (P - np.array([0,0,F])); d_in /= np.linalg.norm(d_in)
    n1 = primary_normal(P)
    d1 = reflect(d_in, n1)

    # 双曲面：顶点 z=L，中心 z=L+a，实半轴 a，离心率 e，b^2=a^2(e^2-1)
    if a is None:
        a = L/(2*(e-1)) if e > 1 else np.nan
    b2 = a*a*(e*e-1)
    zc = L + a
    def fv(p):
        return (p[2]-zc)**2/a**2 - (p[0]**2+p[1]**2)/b2 - 1.0
    # 扫描找首个变号
    ts = np.linspace(1e-9, 4*(L+abs(a)+F), 20000)
    prev = fv(P)
    t_hit = None
    for t in ts:
        cur = fv(P + t*d1)
        if np.sign(cur) != np.sign(prev):
            t_hit = t; break
        prev = cur
    if t_hit is None: return None, None, None
    Q = P + t_hit*d1
    n2 = np.array([-2*Q[0]/b2, -2*Q[1]/b2, 2*(Q[2]-zc)/a**2])
    n2 /= np.linalg.norm(n2)
    if np.dot(n2, d1) > 0: n2 = -n2
    d2 = reflect(d1, n2)
    return Q, d2, a

print("F=%.1f, 数值扫描: 固定 L, 扫 e, 看准直误差 min|d2_xy|" % F)
for L in (2.0, 3.0, 4.0, 6.0):
    print("---- L = %.1f ----" % L)
    best = None
    for e in np.arange(1.05, 6.0, 0.05):
        a = L/(2*(e-1))
        errs = []
        for r in (2.0, 4.0, 6.0, 8.0, 10.0):
            Q, d2, _ = trace(r, L, e, a)
            if d2 is None: errs.append(np.nan); continue
            errs.append(abs(d2[0])/max(abs(d2[2]),1e-9))
        m = np.nanmax(errs)
        if best is None or m < best[1]:
            best = (e, m, a)
    print("   best e=%.3f  a=%.4f  最大斜率误差=%.4e" % best)
    e_best = best[0]
    for r in (2.0, 6.0, 10.0):
        Q, d2, a = trace(r, L, e_best, L/(2*(e_best-1)))
        if d2 is None: print("   r=%.1f -> 无交点" % r); continue
        print("   r=%5.1f  Q=(%.4f,%.4f,%.4f)  d2=(%.6f, %.6f, %.6f)" % (r, Q[0],Q[1],Q[2], d2[0],d2[1],d2[2]))
