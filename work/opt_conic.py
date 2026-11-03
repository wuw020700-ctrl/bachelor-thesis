import numpy as np
from scipy.optimize import minimize

F = 8.0; R = 10.0   # 主面焦距、半径

def primary(u):
    r = F*u
    return np.array([r, r*r/(4*F)])

def pnormal(P):
    n = np.array([-P[0], 2*F]); return n/np.linalg.norm(n)

def refl(d, n):
    v = d - 2*np.dot(d,n)*n; return v/np.linalg.norm(v)

def trace_out_slope(u, zc, a, e):
    """给定双曲面 (中心 zc, 实半轴 a, 离心率 e)，返回出射光线的斜率 dr/dz 与交点。"""
    b2 = a*a*(e*e-1)
    if b2 <= 0: return None
    Fp = np.array([0.0, F]); P = primary(u)
    d = P - Fp; d /= np.linalg.norm(d)
    d1 = refl(d, pnormal(P))
    def fv(Q): return (Q[1]-zc)**2/a**2 - Q[0]**2/b2 - 1.0
    ts = np.linspace(1e-9, 200.0, 40000)
    prev = fv(P); t_hit=None
    for t in ts:
        cur = fv(P + t*d1)
        if np.sign(cur) != np.sign(prev): t_hit=t; break
        prev=cur
    if t_hit is None: return None
    Q = P + t_hit*d1
    n2 = np.array([-2*Q[0]/b2, 2*(Q[1]-zc)/a**2]); n2/=np.linalg.norm(n2)
    if np.dot(n2,d1)>0: n2=-n2
    d2 = refl(d1,n2)
    if abs(d2[1]) < 1e-12: return None
    return Q, d2, d2[0]/d2[1]

def spread(params):
    zc, a, e = params
    if a <= 0 or e <= 1.0: return 1e3
    vals=[]
    for u in (0.15,0.3,0.45,0.6,0.75,0.9,1.0):
        out = trace_out_slope(u, zc, a, e)
        if out is None: return 1e3
        vals.append(out[2])
    vals=np.array(vals)
    return float(np.max(vals)-np.min(vals))

P0 = np.array([3.0, 1.0, 2.5])
print("初始 spread = %.6f" % spread(P0))
res = minimize(spread, P0, method='Nelder-Mead',
               options=dict(maxiter=4000, xatol=1e-10, fatol=1e-12))
zc,a,e = res.x
print("最优: zc=%.6f a=%.6f e=%.6f   spread=%.3e" % (zc,a,e,res.fun))
print("  顶点 z = zc - a = %.6f" % (zc-a))
print("  近焦点 z = zc - a*e = %.6f" % (zc-a*e))
print("  远焦点 z = zc + a*e = %.6f" % (zc+a*e))
print("  b^2 = %.6f" % (a*a*(e*e-1)))
print()
for u in (0.15,0.3,0.5,0.7,0.9,1.0,1.2):
    out = trace_out_slope(u, zc,a,e)
    if out is None: print("u=%.2f 无交点"%u); continue
    Q,d2,sl = out
    print("u=%4.2f  r_p=%6.3f  副面点=(%.4f,%.4f)  出射 d2=(%.6f,%.6f)  斜率=%.6f" % (u, F*u, Q[0],Q[1],d2[0],d2[1],sl))
