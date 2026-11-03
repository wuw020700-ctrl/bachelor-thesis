import numpy as np
F = 8.0
def refl(d,n):
    v=d-2*np.dot(d,n)*n; return v/np.linalg.norm(v)

class Cass:
    """副面: 顶点在 z=L, 近焦点在 z=F(与主面焦点重合), 离心率 e。
       由 L = F - a(e+1) 与离心率定义得 a = (F-L)(2e-1)/(e^2-1)."""
    def __init__(self, L, e, F=8.0):
        self.L, self.e, self.F = L, e, F
        self.a = (F-L)*(2*e-1)/(e*e-1)
        self.c = self.a*self.e
        self.zc = L + self.a              # 中心
        self.b2 = self.c**2 - self.a**2
        assert self.a > 0 and self.b2 > 0
    @property
    def near(self): return self.zc - self.c
    @property
    def far(self):  return self.zc + self.c
    def rim_r(self):
        t = (self.L - self.zc)**2/self.a**2 - 1.0
        return np.sqrt(max(t,0.0))*np.sqrt(self.b2)

def trace(u, g):
    a,e,zc,b2,F = g.a,g.e,g.zc,g.b2,g.F
    r = F*u; P = np.array([r, r*r/(4*F)])
    Fp = np.array([0.0,F]); d = P-Fp; d/=np.linalg.norm(d)
    n1 = np.array([-P[0],2*F]); n1/=np.linalg.norm(n1)
    d1 = refl(d,n1)
    def fv(Q): return (Q[1]-zc)**2/a**2 - Q[0]**2/b2 - 1.0
    ts=np.linspace(1e-9,400.0,120000); prev=fv(P); t=None
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

print("固定 L，扫 e：看不同射线是否交轴于同一点")
print("  L     e       a       近焦点   远焦点   副面半径 | 交点z(u=0.2/0.5/0.8)          离散")
for L in (2.0, 3.0):
    for e in (1.2,1.4,1.6,1.8,2.0,2.5,3.0):
        try: g = Cass(L,e)
        except AssertionError: continue
        if g.near < -1e-9: continue
        zs=[]
        for u in (0.2,0.5,0.8):
            o=trace(u,g); zs.append(o[2] if o else np.nan)
        zs=np.array(zs)
        if np.any(np.isnan(zs)):
            print("%5.1f %6.2f  %7.4f  %7.4f %7.4f %7.4f | 有射线无交点"%(L,e,g.a,g.near,g.far,g.rim_r()))
            continue
        print("%5.1f %6.2f  %7.4f  %7.4f %7.4f %7.4f | %8.4f %8.4f %8.4f  %.3e"%(
            L,e,g.a,g.near,g.far,g.rim_r(),zs[0],zs[1],zs[2],np.max(zs)-np.min(zs)))
    print()
