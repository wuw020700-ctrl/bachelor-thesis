import numpy as np
from scipy.optimize import minimize_scalar

F = 8.0
def refl(d,n):
    v=d-2*np.dot(d,n)*n; return v/np.linalg.norm(v)

def cross(u, a):
    c = a + F; e = c/a
    if a<=0 or e<=1: return None
    L = c - a + F          # 顶点 z = zc - a, zc = c + F  => 顶点 = c + F - a = F + F = 2F? 重新定义见下
    zc = F + c             # 近焦点 = zc - c = F  ✓
    b2 = c*c - a*a
    r = F*u; P = np.array([r, r*r/(4*F)])
    Fp = np.array([0.0,F]); d = P-Fp; d/=np.linalg.norm(d)
    n1 = np.array([-P[0], 2*F]); n1/=np.linalg.norm(n1)
    d1 = refl(d,n1)
    def fv(Q): return (Q[1]-zc)**2/a**2 - Q[0]**2/b2 - 1.0
    ts=np.linspace(1e-9,600.0,120000); prev=fv(P); t=None
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
    return Q, d2, Q[1]-Q[0]/(d2[0]/d2[1])

print("近焦点固定在 z=F。以实半轴 a 为自由参数，求交点一致性。")
print("a       e       顶点z    交点z(u=0.3)   (u=0.6)     (u=0.9)     离散")
best=(None,1e9)
for a in (0.05,0.1,0.2,0.3,0.5,0.8,1.2,2.0,3.0,5.0,8.0,12.0,20.0):
    zc=F+a+F; L=zc-a
    zs=[]
    for u in (0.3,0.6,0.9):
        o=cross(u,a); zs.append(o[2] if o else np.nan)
    zs=np.array(zs)
    if np.any(np.isnan(zs)):
        print("%6.2f  %7.3f  %7.3f   有射线无交点"%(a,(a+F)/a,L)); continue
    sp=np.max(zs)-np.min(zs)
    if sp<best[1]: best=(a,sp)
    print("%6.2f  %7.3f  %7.3f  %11.4f  %10.4f  %10.4f  %.3e"%(a,(a+F)/a,L,zs[0],zs[1],zs[2],sp))
print()
print("最优 a=%.4f  离散=%.3e" % best)
