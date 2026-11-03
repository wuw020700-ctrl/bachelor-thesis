import numpy as np
F = 8.0
def refl(d,n):
    v=d-2*np.dot(d,n)*n; return v/np.linalg.norm(v)

def design(M, F=8.0):
    """封闭解: 近焦点 z=0, 远焦点 z=MF（在 +z 远场侧作参考）"""
    L = F*(M-1)/(M+1)
    a = F*(M-1)/(M+1)          # = L
    # a(e-1) = L - F  ->  但上面两式需重新推；这里直接解方程组
    return L, a

def build(M, F=8.0):
    L = F*(M-1)/(M+1)
    # 未知 a, e:  (1) zc - a = L ; (2) zc - ae = 0 ; (3) zc + ae = MF
    # 由(2)(3): zc = MF/2, ae = MF/2 ; 由(1): a = zc - L = MF/2 - L
    zc = M*F/2.0
    ae = M*F/2.0
    a = zc - L
    if a <= 0: return None
    e = ae/a
    if e <= 1: return None
    return dict(L=L, zc=zc, a=a, e=e, b2=ae*ae - a*a, near=zc-ae, far=zc+ae)

def trace(u, g):
    a,e,zc,b2 = g['a'],g['e'],g['zc'],g['b2']
    r=F*u; P=np.array([r, r*r/(4*F)])
    Fp=np.array([0.0,F]); d=P-Fp; d/=np.linalg.norm(d)
    n1=np.array([-P[0],2*F]); n1/=np.linalg.norm(n1)
    d1=refl(d,n1)
    def fv(Q): return (Q[1]-zc)**2/a**2 - Q[0]**2/b2 - 1.0
    ts=np.linspace(1e-9,600.0,150000); prev=fv(P); t=None
    for tt in ts:
        cur=fv(P+tt*d1)
        if np.sign(cur)!=np.sign(prev): t=tt; break
        prev=cur
    if t is None: return None
    Q=P+t*d1
    n2=np.array([-2*Q[0]/b2, 2*(Q[1]-zc)/a**2]); n2/=np.linalg.norm(n2)
    if np.dot(n2,d1)>0: n2=-n2
    d2=refl(d1,n2)
    if abs(d2[1])<1e-14: return None
    return Q,d2, Q[1]-Q[0]/(d2[0]/d2[1])

print("封闭解验证: 副面 = 双曲面, 近焦点 z=0, 远焦点 z=MF")
print(" M      L        z_c       a        e       近焦点   远焦点   |  射线交点z (u=0.3/0.6/0.9)   离散")
for M in (1.5,2.0,3.0,4.0,6.0,10.0):
    g=build(M)
    if g is None: print("%4.1f  -> 无有效解"%M); continue
    zs=[]
    for u in (0.3,0.6,0.9):
        o=trace(u,g); zs.append(o[2] if o else np.nan)
    zs=np.array(zs)
    if np.any(np.isnan(zs)):
        print("%4.1f  %7.3f  %7.3f  %7.3f  %7.3f  %7.3f  %7.3f  |  有射线无交点"%(M,g['L'],g['zc'],g['a'],g['e'],g['near'],g['far']))
        continue
    print("%4.1f  %7.3f  %7.3f  %7.3f  %7.3f  %7.3f  %7.3f  |  %8.4f %8.4f %8.4f   %.3e"%(
        M,g['L'],g['zc'],g['a'],g['e'],g['near'],g['far'],zs[0],zs[1],zs[2],np.max(zs)-np.min(zs)))
