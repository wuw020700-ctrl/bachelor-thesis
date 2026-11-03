import numpy as np
F = 8.0

def refl(d,n):
    v = d - 2*np.dot(d,n)*n; return v/np.linalg.norm(v)

def build(formula, M):
    """返回 (zc, a, e)。formula='A' 用 L=F(M-1)/(M+1)；'B' 用 L=F(M+1)/(M-1)。"""
    if formula == 'A':
        L = F*(M-1)/(M+1)
    else:
        L = F*(M+1)/(M-1)
    # 约束：远焦点 z = L + 2c = -B_sys（系统焦点在负 z），且近焦点 z = L - 2a = 0
    # 由近焦点定 a = L/2；c = a*e; 远焦点 = L+2c
    a = L/2.0
    c = a + F              # 近焦点 = zc - c = 0 -> zc = c；用 zc = L + a 的另一种摆放
    zc = L + a
    e = (zc + c - zc)/a    # 占位
    e = c/a
    return zc, a, e

def trace(u, zc, a, e):
    b2 = a*a*(e*e-1)
    if b2 <= 0: return None
    r = F*u; P = np.array([r, r*r/(4*F)])
    Fp = np.array([0.0, F]); d = P-Fp; d/=np.linalg.norm(d)
    n1 = np.array([-P[0], 2*F]); n1/=np.linalg.norm(n1)
    d1 = refl(d,n1)
    def fv(Q): return (Q[1]-zc)**2/a**2 - Q[0]**2/b2 - 1.0
    ts = np.linspace(1e-9, 300.0, 60000); prev=fv(P); t=None
    for tt in ts:
        cur=fv(P+tt*d1)
        if np.sign(cur)!=np.sign(prev): t=tt; break
        prev=cur
    if t is None: return None
    Q = P+t*d1
    n2 = np.array([-2*Q[0]/b2, 2*(Q[1]-zc)/a**2]); n2/=np.linalg.norm(n2)
    if np.dot(n2,d1)>0: n2=-n2
    d2 = refl(d1,n2)
    return Q, d2

print("判别：出射光线反向外推与轴的交点 z 应为系统焦点 -B_sys")
print("M    公式   L       副面顶点  出射斜率(多个u)                外推交点z")
for M in (2.0, 3.0, 4.0):
    for formula in ('A','B'):
        zc,a,e = build(formula, M)
        if a<=0 or e<=1: 
            print("%.1f  %s     无效 a=%.3f e=%.3f" % (M,formula,a,e)); continue
        vlist=[]; zcross=[]
        for u in (0.2,0.4,0.6,0.8,1.0):
            out = trace(u, zc,a,e)
            if out is None: continue
            Q,d2 = out
            if abs(d2[1])>1e-12:
                sl = d2[0]/d2[1]
                vlist.append(sl)
                zcross.append(Q[1] - Q[0]/sl)
        if not vlist:
            print("%.1f  %s     L=%.3f  无有效交点" % (M,formula,zc-a)); continue
        spread = max(vlist)-min(vlist)
        print("%.1f  %s     %7.3f  顶点=%7.3f  斜率=[%.4f..%.4f] 离散=%.4f  交点z=[%.2f..%.2f]" % (
            M, formula, zc-a, zc-a, min(vlist), max(vlist), spread, min(zcross), max(zcross)))
