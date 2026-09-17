"""Structural algebra checks, not integration error bounds or GaN validation."""
import numpy as np
from finite_resistance_interval import C,B,L,VO,RIND,G,offset,branch,rhs,jac
from check_newton_retained_candidate import Z

def main():
    assert np.allclose(C,C.T,rtol=0,atol=1e-20)
    eig=np.linalg.eigvalsh(C)
    assert eig.min()>0,'non-positive capacitor energy matrix'
    rng=np.random.default_rng(20260916)
    errors=[];derivatives=[];source_traps=[]
    for k in range(40):
        z=Z+rng.normal(size=11)*np.r_[np.full(7,.05),np.ones(4)]
        active=rng.random(8)>.5
        dz=rhs(0,z,True,active)/1e-9
        h,_=branch(z,True,active)
        kcl=C@dz[:7]+B@z[7:]+G.T@h
        assert np.max(abs(kcl))<1e-6
        lhs=z[:7]@C@dz[:7]+L*(z[7:]@dz[7:])
        v=G@z[:7]+offset
        diss=v@h+RIND*(z[7:]@z[7:])
        assert diss>=0,'passive branch energy sign failure'
        expected=offset@h-VO*np.sum(z[7:])-diss
        # Normalize by gross terms, not their nearly cancelling net power.
        gross=max(1.,abs(offset@h)+abs(VO*np.sum(z[7:]))+abs(diss))
        errors.append(abs(lhs-expected)/gross)
        assert errors[-1]<1e-9,'energy identity failed'
        wrong=-offset@h-VO*np.sum(z[7:])-diss
        source_traps.append(abs(lhs-wrong)/gross)
        d=rng.normal(size=11);eps=1e-6
        vp=G@(z[:7]+eps*d[:7])+offset
        vm=G@(z[:7]-eps*d[:7])+offset
        if np.any(np.sign(vp)!=np.sign(vm)):continue
        fd=(rhs(0,z+eps*d,True,active)-rhs(0,z-eps*d,True,active))/(2*eps)
        exact=jac(0,z,True,active)@d
        err=np.linalg.norm(fd-exact)/max(1.,np.linalg.norm(exact))
        derivatives.append(err)
        assert err<1e-6,'piecewise Jacobian mismatch'
    # Deliberate source-sign trap: a wrongly signed source term must fail.
    assert max(source_traps)>1e-3,'source-sign trap was not detected'
    print('PASS 40 sampled KCL and passive energy identities; source-sign trap detected')
    print('C eigenvalue range F',eig.min(),eig.max())
    print('max relative energy roundoff',max(errors))
    print('Quadratic reduced-coordinate identity; capacitor source-offset energy terms are not included.')
    print('piecewise Jacobian checks',len(derivatives),'max relative difference',max(derivatives))
    print('Does not certify event-time error, global convergence, real device physics, or paper reproduction.')

if __name__=='__main__':main()
