import numpy as np
F = 8.0; Z_REF = 12.0

def P_of(u):
    r = F*u; return np.array([r, r*r/(4*F)])
def n1_of(P):
    n = np.array([-P[0], 2*F]); return n/np.linalg.norm(n)
def refl(d,n): return d - 2*np.dot(d,n)*n

def geom(u):
    Fp = np.array([0.0,F]); P = P_of(u)
    d = P-Fp; L1 = np.linalg.norm(d); d /= L1
    d1 = refl(d, n1_of(P)); d1 /= np.linalg.norm(d1)
    return P, L1, d1

def Phi(u, t):
    P, L1, d1 = geom(u)
    Q = P + t*d1
    return L1 + t + (Z_REF - Q[1])

# 常数取轴上光线: u=0, P=(0,0), d1 应为 -z 方向
P0, L10, d10 = geom(0.0)
print("轴上: P0=%s  L1=%.6f  d1=(%.6e, %.6f)" % (P0, L10, d10[0], d10[1]))
C = Phi(0.0, 0.0)
print("C = %.6f" % C)
print()
print("u      r_p      t        r_s      z_s")
surf = []
for u in (0.0,0.02,0.05,0.1,0.15,0.2,0.25,0.3):
    lo, hi = 0.0, 200.0
    flo = Phi(u,lo)-C; fhi = Phi(u,hi)-C
    if flo*fhi > 0:
        print("%.2f  无解 flo=%.4f fhi=%.4f" % (u, flo, fhi)); continue
    for _ in range(200):
        mid = 0.5*(lo+hi)
        if (Phi(u,lo)-C)*(Phi(u,mid)-C) <= 0: hi = mid
        else: lo = mid
    t = 0.5*(lo+hi)
    P, L1, d1 = geom(u); Q = P + t*d1
    surf.append((Q[0], Q[1], u))
    print("%.2f  %7.3f  %8.4f  %7.4f  %7.4f" % (u, P[0], t, Q[0], Q[1]))

surf = np.array(surf)
print()
print("曲面点 (r_s, z_s)，检验是否为双曲面:")
r, z = surf[:,0], surf[:,1]
# 尝试拟合近主面叶双曲面 (z-zc)^2/a^2 - r^2/b^2 = 1
# 线性化: z^2 - 2 zc z + zc^2 - a^2 = (a^2/b^2) r^2
# 令 A = 1/a^2, B = a^2/b^2 => A z^2 - 2 A zc z + (A zc^2 - 1) = B r^2
# 即 A z^2 + C1 z + C2 = B r^2,  未知 A, C1, C2, B
M = np.column_stack([z*z, z, np.ones_like(z), -r*r])
b = np.ones_like(z)
sol, *_ = np.linalg.lstsq(M, b, rcond=None)
A, C1, C2, B = sol
res = M@sol - b
print("  A=%.6f  C1=%.6f  C2=%.6f  B=%.6f" % (A,C1,C2,B))
print("  拟合残差 max=%.3e  (相对 1 的偏差)" % np.max(np.abs(res)))
if A > 0:
    a = 1/np.sqrt(A); zc = -C1/(2*A); e = np.sqrt(1 + B/A)
    print("  => a=%.4f  zc=%.4f  e=%.4f  (顶点 z=zc-a=%.4f)" % (a, zc, e, zc-a))
    print("  => 近焦点 z = zc - a*e = %.4f" % (zc - a*e))
    print("  => 远焦点 z = zc + a*e = %.4f" % (zc + a*e))
    print("  => 主面焦距 F = %.4f" % F)
