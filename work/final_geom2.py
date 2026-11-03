import numpy as np
F = 8.0
def refl(d,n):
    v=d-2*np.dot(d,n)*n; return v/np.linalg.norm(v)

# 这次用「顶点在 z=L, 中心 zc=L+a, 近焦点 zc-c, 远焦点 zc+c」
def make(L, e):
    a = (L - F)/2.0          # 由 L = F + 2a
    if a <= 0: return None
    c = a*e
    zc = L + a
    b2 = c*c - a*a
    if b2 <= 0: return None
    return dict(L=L,a=a,e=e,c=c,zc=zc,b2=b2,near=zc-c,far=zc+c)

def trace(u, g):
    a,zc,b2 = g['a'],g['zc'],g['b2']
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
    return Q,d2,Q[1]-Q[0]/(d2[0]/d2[1])

print("副面顶点 z=L, 近焦点须在 z=F=8 上 (即 L = F + 2a)")
print("  L      e      a      近焦点    远焦点   副面半径 | 交点z (u=0.2/0.5/0.8)        离散")
for L in (10.0, 12.0, 14.0, 16.0, 20.0):
    for e in (1.5, 2.0, 3.0, 4.0, 6.0):
        g = make(L,e)
        if g is None: continue
        zs=[]
        for u in (0.2,0.5,0.8):
            o=trace(u,g); zs.append(o[2] if o else np.nan)
        zs=np.array(zs)
        if np.any(np.isnan(zs)):
            print("%5.1f %6.2f %7.3f %8.3f %8.3f  有射线无交点"%(L,e,g['a'],g['near'],g['far'])); continue
        print("%5.1f %6.2f %7.3f %8.3f %8.3f | %8.3f %8.3f %8.3f  %.3e"%(
            L,e,g['a'],g['near'],g['far'],zs[0],zs[1],zs[2],np.max(zs)-np.min(zs)))
    print()
