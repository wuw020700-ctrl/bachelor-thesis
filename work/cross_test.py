import numpy as np
from scipy.optimize import brentq

F = 8.0

def refl(d,n):
    v = d - 2*np.dot(d,n)*n; return v/np.linalg.norm(v)

def ray_cross(u, L, e):
    """双曲面近焦点固定在 z=F（即 zc - c = F）。
       近主面叶顶点 z = zc - a = L  =>  a = L - F, c = a + F, e = c/a
       注意：这里 e 由 a 决定，所以我们改以 a 为未知量更直接。"""
    a = L - F
    if a <= 0: return None
    c = a + F
    nn = c/a                      # 实际离心率
    if nn <= 1: return None
    zc = L + a
    b2 = c*c - a*a
    # 主面点
    r = F*u; P = np.array([r, r*r/(4*F)])
    Fp = np.array([0.0, F]); d = P - Fp; d /= np.linalg.norm(d)
    n1 = np.array([-P[0], 2*F]); n1 /= np.linalg.norm(n1)
    d1 = refl(d, n1)
    def fv(Q): return (Q[1]-zc)**2/a**2 - Q[0]**2/b2 - 1.0
    ts = np.linspace(1e-9, 400.0, 80000); prev = fv(P); t = None
    for tt in ts:
        cur = fv(P + tt*d1)
        if np.sign(cur) != np.sign(prev): t = tt; break
        prev = cur
    if t is None: return None
    Q = P + t*d1
    if Q[1] < 0: return None
    n2 = np.array([-2*Q[0]/b2, 2*(Q[1]-zc)/a**2]); n2 /= np.linalg.norm(n2)
    if np.dot(n2, d1) > 0: n2 = -n2
    d2 = refl(d1, n2)
    if abs(d2[1]) < 1e-13: return None
    return Q, d2, Q[1] - Q[0]/(d2[0]/d2[1])

# 扫 a（等价扫 e），看不同 u 的交点 z 是否一致
print("a      e       顶点L    u=0.3交点    u=0.6交点    u=0.9交点    离散度")
for a in (0.2,0.4,0.6,0.8,1.0,1.5,2.0,3.0,4.0):
    L = F + a
    e = (a+F)/a
    zs=[]
    for u in (0.3,0.6,0.9):
        out = ray_cross(u, L, e)
        zs.append(out[2] if out else np.nan)
    zs=np.array(zs)
    if np.any(np.isnan(zs)):
        print("%.2f  %6.3f  %6.3f   有射线无交点" % (a,e,L)); continue
    print("%.2f  %6.3f  %6.3f   %9.4f   %9.4f   %9.4f   %.3e" % (
        a,e,L, zs[0],zs[1],zs[2], np.max(zs)-np.min(zs)))
