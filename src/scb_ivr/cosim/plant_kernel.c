/* One implicit step of the co-simulation plant (circuit.Sim.step: trapezoid or Euler, cached LU) with the
 * nonlinear-Coss chord iteration, in C, with the same floating-point operations as numpy/scipy on this machine:
 * - dense products through Accelerate's cblas_dgemv$NEWLAPACK$ILP64 with numpy's arguments
 *   (A @ x: RowMajor/NoTrans; r.T @ x on the C-ordered r: RowMajor/Trans);
 * - the linear solves through Accelerate's dgetrs$NEWLAPACK, as scipy's lu_solve (Fortran-ordered LU, 1-based ipiv);
 * - element-wise operations one at a time (compiled with -ffp-contract=off), except numpy's compiled interp, whose
 *   slope*(x - xp[j]) + fp[j] is an FMA in numpy's build and is written as fma() here.
 * Return 0: done (y1 written, *iters = chord iterations, 0 if linear); 1: a right-hand side is not finite (the
 * caller raises as lu_solve does); 2: the chord iteration did not converge in 8 (the caller redoes the step in
 * Python, which takes the full-Newton fallback).
 * From A95 (experiments/track_A_periodic_steady_state/A95_cosim_c_kernel), where its bit identity was gated.
 */
#include <math.h>
#include <stdint.h>
#include <string.h>

extern void cblas_dgemv_acc(int order, int trans, int64_t m, int64_t n, double alpha, const double *a, int64_t lda,
                            const double *x, int64_t incx, double beta, double *y, int64_t incy)
    __asm("_cblas_dgemv$NEWLAPACK$ILP64");
extern void dgetrs_acc(const char *trans, const int *n, const int *nrhs, const double *a, const int *lda,
                       const int *ipiv, double *b, const int *ldb, int *info, size_t len_trans)
    __asm("_dgetrs$NEWLAPACK");

enum { ROW = 101, NOTRANS = 111, TRANS = 112, NMAX = 32 };

typedef struct {          /* constant per plant */
    int n;                /* states (nodes + phase currents) */
    int m;                /* switches */
    int nonlinear;        /* A86 Coss(V) on */
    const double *r;      /* m x n switch incidence, C order */
    const double *vinf;   /* m: 1 for a switch whose drain is vin */
    const double *nper;   /* m: devices per switch */
    const double *clin;   /* m: linear capacitance already in M */
    const double *vt, *qt;/* Coss charge table (V, C) */
    int64_t nt;
    double v_max, q_end, c_end;
} ctx_t;

typedef struct {          /* per topology entry (A88 Sim.step's cache entry) */
    const double *rhs_m;  /* n x n, C order */
    const double *lhs;    /* n x n, C order */
    const double *lu;     /* n x n, Fortran order (scipy lu_factor) */
    const int *ipiv1;     /* n, 1-based */
    const double *fv, *fl;/* n: source vectors (vin, load) */
    const double *frev;   /* n or NULL: reverse-drop sources */
} ent_t;

static int all_finite(const double *b, int n) {
    for (int i = 0; i < n; i++) if (!isfinite(b[i])) return 0;
    return 1;
}

static int solve(const ent_t *e, int n, const double *b, double *x) {
    if (!all_finite(b, n)) return 1;
    memcpy(x, b, sizeof(double) * n);
    int nrhs = 1, info = 0;
    dgetrs_acc("N", &n, &nrhs, e->lu, &n, e->ipiv1, x, &n, &info, 1);
    return info == 0 ? 0 : 1;
}

static void gemv(const double *a, int m, int n, const double *x, double *y) {      /* y = A @ x, A m x n C order */
    cblas_dgemv_acc(ROW, NOTRANS, m, n, 1.0, a, n, x, 1, 0.0, y, 1);
}

static void gemv_t(const double *a, int m, int n, const double *x, double *y) {    /* y = A.T @ x */
    cblas_dgemv_acc(ROW, TRANS, m, n, 1.0, a, n, x, 1, 0.0, y, 1);
}

static long search(double x, const double *xp, int64_t n) {        /* largest j with xp[j] <= x */
    int64_t lo = 0, hi = n;
    while (lo < hi) { int64_t mid = lo + ((hi - lo) >> 1); if (x >= xp[mid]) lo = mid + 1; else hi = mid; }
    return (long)(lo - 1);
}

static double interp1(double x, const double *xp, const double *fp, int64_t n) {     /* numpy's compiled interp */
    if (isnan(x)) return x;
    if (x > xp[n - 1]) return fp[n - 1];
    if (x < xp[0]) return fp[0];
    long j = search(x, xp, n);
    if (j == n - 1) return fp[j];
    if (xp[j] == x) return fp[j];
    double s = (fp[j + 1] - fp[j]) / (xp[j + 1] - xp[j]);
    double r = fma(s, x - xp[j], fp[j]);
    if (isnan(r)) {
        r = fma(s, x - xp[j + 1], fp[j + 1]);
        if (isnan(r) && fp[j] == fp[j + 1]) r = fp[j];
    }
    return r;
}

static double nsign(double v) { return v > 0 ? 1.0 : (v < 0 ? -1.0 : (v == 0 ? 0.0 : v)); }   /* np.sign */

static void qf(const ctx_t *c, const double *v, double *q) {        /* EPC2067Coss.q, element by element */
    double a[NMAX], out[NMAX];
    int any = 0;
    for (int i = 0; i < c->m; i++) { a[i] = fabs(v[i]); out[i] = interp1(a[i], c->vt, c->qt, c->nt); any |= a[i] > c->v_max; }
    if (any) {
        for (int i = 0; i < c->m; i++) {
            if (a[i] > c->v_max) { double t = a[i] - c->v_max; t = c->c_end * t; out[i] = c->q_end + t; }
        }
    }
    for (int i = 0; i < c->m; i++) q[i] = nsign(v[i]) * out[i];
}

int pk_step(const ctx_t *c, const ent_t *e, const double *y, double *y1, double h, int euler,
            double vin0, double vin1, double ld0, double ld1, int *iters) {
    const int n = c->n, m = c->m;
    double f0[NMAX], f1[NMAX], term[NMAX], rhs[NMAX], t[NMAX], u[NMAX];
    /* rhs = rhs_m @ y + term (+ h*frev), term = h*f1 or (0.5*h)*(f0 + f1), f = fv*vin + fl*ld */
    for (int i = 0; i < n; i++) { double a = e->fv[i] * vin1; double b = e->fl[i] * ld1; f1[i] = a + b; }
    if (euler) {
        for (int i = 0; i < n; i++) term[i] = h * f1[i];
    } else {
        for (int i = 0; i < n; i++) { double a = e->fv[i] * vin0; double b = e->fl[i] * ld0; f0[i] = a + b; }
        double hh = 0.5 * h;
        for (int i = 0; i < n; i++) { double s = f0[i] + f1[i]; term[i] = hh * s; }
    }
    gemv(e->rhs_m, n, n, y, t);
    for (int i = 0; i < n; i++) rhs[i] = t[i] + term[i];
    if (e->frev) for (int i = 0; i < n; i++) { double hf = h * e->frev[i]; rhs[i] = rhs[i] + hf; }
    if (solve(e, n, rhs, y1)) return 1;
    *iters = 0;
    if (!c->nonlinear) return 0;

    /* A86 chord iteration on the cached LU */
    double v0[NMAX], v1[NMAX], q0[NMAX], qv[NMAX], corr[NMAX], b[NMAX], dz[NMAX], s[NMAX];
    gemv(c->r, m, n, y, v0);
    for (int i = 0; i < m; i++) { double a = c->vinf[i] * vin0; v0[i] = v0[i] + a; }
    qf(c, v0, qv);
    for (int i = 0; i < m; i++) q0[i] = c->nper[i] * qv[i];
    for (int it = 1; it <= 8; it++) {
        gemv(c->r, m, n, y1, v1);
        for (int i = 0; i < m; i++) { double a = c->vinf[i] * vin1; v1[i] = v1[i] + a; }
        qf(c, v1, qv);
        for (int i = 0; i < m; i++) {
            double a = c->nper[i] * qv[i]; a = a - q0[i];
            double d = v1[i] - v0[i]; d = c->clin[i] * d;
            corr[i] = a - d;
        }
        gemv(e->lhs, n, n, y1, t);
        for (int i = 0; i < n; i++) u[i] = t[i] - rhs[i];
        gemv_t(c->r, m, n, corr, s);
        for (int i = 0; i < n; i++) b[i] = u[i] + s[i];
        if (solve(e, n, b, dz)) return 1;
        int conv = 1;
        for (int i = 0; i < n; i++) { y1[i] = y1[i] - dz[i]; if (!(fabs(dz[i]) < 1e-7)) conv = 0; }
        if (conv) { *iters = it; return 0; }
    }
    return 2;
}

int pk_abi(void) { return 1; }
