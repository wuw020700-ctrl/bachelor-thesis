import numpy as np
F = 8.0
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

for Z_REF in (20.0, 30.0, 50.0):
    C = F + Z_REF
    print("=========== Z_REF = %.1f  (C=%.1f) ===========" % (Z_REF, C))
    print("u      r_p      t        r_s      z_s")
    surf=[]
    for u in (0.0,0.01,0.02,0.04,0.06,0.08,0.10,0.14,0.18,0.22):
        P, L1, d1 = geom(u)
        def Phi(t): 
            Q = P + t*d1; return L1 + t + (Z_REF - Q[1]) - C
        lo, hi = 0.0, 500.0
        if Phi(lo)*Phi(hi) > 0:
            print("%.2f  无解  Phi(0)=%.5f Phi(500)=%.5f" % (u, Phi(lo), Phi(hi))); continue
        for _ in range(200):
            mid=0.5*(lo+hi)
            if Phi(lo)*Phi(mid) <= 0: hi=mid
            else: lo=mid
        t=0.5*(lo+hi); Q = P + t*d1
        surf.append((Q[0],Q[1]))
        print("%.2f  %7.3f  %8.4f  %7.4f  %7.4f" % (u, P[0], t, Q[0], Q[1]))
    surf=np.array(surf)
    r,z = surf[:,0], surf[:,1]
    M = np.column_stack([z*z, z, np.ones_like(z), -r*r]); b=np.ones_like(z)
    sol,*_ = np.linalg.lstsq(M,b,rcond=None)
    A,C1,C2,B = sol
    res = M@sol-b
    print("  fit: A=%.6f C1=%.4f C2=%.4f B=%.6f  maxres=%.2e" % (A,C1,C2,B,np.max(np.abs(res))))
    if A>1e-12:
        a=1/np.sqrt(A); zc=-C1/(2*A); e=np.sqrt(1+B/A)
        print("  => a=%.4f zc=%.4f e=%.4f 顶点z=%.4f 近焦点z=%.4f 远焦点z=%.4f" % (a,zc,e,zc-a,zc-a*e,zc+a*e))
    print()
