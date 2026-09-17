"""Dimensionless algebra checks, not a device simulation or fitted model."""
from fractions import Fraction as F

def solve(a, b):
    m = [[F(x) for x in row] + [F(rhs)] for row, rhs in zip(a, b)]
    n = len(b)
    for k in range(n):
        pivot = next(j for j in range(k, n) if m[j][k])
        m[k], m[pivot] = m[pivot], m[k]
        scale = m[k][k]
        m[k] = [x / scale for x in m[k]]
        for j in range(n):
            if j != k:
                scale = m[j][k]
                m[j] = [x-scale*y for x, y in zip(m[j], m[k])]
    return [row[-1] for row in m]

def check(ch, cl, fly):
    # Node order a1,a2,a3,x1,x2,x3,x4; None is a rigid boundary.
    edges = [(None,0,ch[0]),(0,1,ch[1]),(1,2,ch[2]),(2,6,ch[3])]
    edges += [(j,j+3,fly[j]) for j in range(3)]
    edges += [(None,k+3,cl[k]) for k in range(4)]
    c = [[F(0) for _ in range(7)] for _ in range(7)]
    for u,v,w in edges:
        for node in (u,v):
            if node is not None:
                c[node][node] += w
        if u is not None and v is not None:
            c[u][v] -= w
            c[v][u] -= w
    a = [[ch[0]+ch[1]+fly[0],-ch[1],0],
         [-ch[1],ch[1]+ch[2]+fly[1],-ch[2]],
         [0,-ch[2],ch[2]+ch[3]+fly[2]]]
    bf = [[fly[0],0,0,0],[0,fly[1],0,0],[0,0,fly[2],ch[3]]]
    d = [fly[0]+cl[0],fly[1]+cl[1],fly[2]+cl[2],ch[3]+cl[3]]
    expected = [[F(0) for _ in range(7)] for _ in range(7)]
    for j in range(3):
        for k in range(3):
            expected[j][k] = a[j][k]
        for k in range(4):
            expected[j][k+3] = expected[k+3][j] = -bf[j][k]
    for k in range(4):
        expected[k+3][k+3] = d[k]
    assert c == expected, 'Matrix does not match capacitor incidence'
    for s in range(4):
        b = [row[s] for row in bf]
        p = solve(a,b)
        ceq = d[s]-sum(x*y for x,y in zip(b,p))
        assert ceq > 0
        velocity = p+[F(int(k==s)) for k in range(4)]
        residual = [sum(x*y for x,y in zip(row,velocity)) for row in c]
        assert all(x == 0 for x in residual[:3]), 'Internal KCL fails'
        assert residual[s+3] == ceq, 'Schur back-substitution fails'
        gamma = [p[0],p[1]-p[0],p[2]-p[1],1-p[2]][s]
        assert gamma > 0, 'Selected high-side voltage direction fails'

if __name__ == '__main__':
    check([F(1)]*4,[F(1)]*4,[F(1)]*3)
    check(list(map(F,[2,3,5,7])),list(map(F,[11,13,17,19])),list(map(F,[23,29,31])))
    print('PASS: incidence matrix and all four Schur reductions, two dimensionless fixtures.')
    print('Not a symbolic positivity proof, paper-topology validation or ZVS simulation.')
