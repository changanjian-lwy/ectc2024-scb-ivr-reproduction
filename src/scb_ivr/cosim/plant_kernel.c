/* One implicit step of the co-simulation plant (circuit.Sim.step: trapezoid or Euler, cached LU) with the
 * nonlinear-Coss chord iteration, in C, with the same floating-point operations as numpy/scipy on this machine:
 * - dense products through Accelerate's cblas_dgemv$NEWLAPACK$ILP64 with numpy's arguments
 *   (A @ x: RowMajor/NoTrans; r.T @ x on the C-ordered r: RowMajor/Trans);
 * - the linear solves through Accelerate's dgetrs$NEWLAPACK, as scipy's lu_solve (Fortran-ordered LU, 1-based ipiv);
 * - element-wise operations one at a time (compiled with -ffp-contract=off), except numpy's compiled interp, whose
 *   slope*(x - xp[j]) + fp[j] is an FMA in numpy's build and is written as fma() here.
 * Return 0: done (y1 written, *iters = chord iterations, 8 + Newton iterations after a fallback, 0 if linear);
 * 1: a right-hand side of the chord is not finite (the caller raises ValueError, as lu_solve does);
 * 3: the full-Newton fallback did not converge in 30 (RuntimeError, as in Python); 4: its matrix is singular
 * (numpy.linalg.LinAlgError). The fallback reproduces numpy: w = n*c(v1) - clin, (r.T * w) @ r through
 * cblas_dgemm$NEWLAPACK$ILP64 (RowMajor, Trans on the F-ordered r.T*w, NoTrans on r), jac = lhs + that, and
 * np.linalg.solve through dgesv$NEWLAPACK$ILP64 on F-ordered copies (both checked bit for bit against numpy).
 * From A95 (experiments/track_A_periodic_steady_state/A95_cosim_c_kernel), where its bit identity was gated.
 */
#include <math.h>
#include <stdint.h>
#include <string.h>

extern void cblas_dgemv_acc(int order, int trans, int64_t m, int64_t n, double alpha, const double *a, int64_t lda,
                            const double *x, int64_t incx, double beta, double *y, int64_t incy)
    __asm("_cblas_dgemv$NEWLAPACK$ILP64");
extern void cblas_dgemm_acc(int order, int ta, int tb, int64_t m, int64_t n, int64_t k, double alpha, const double *a,
                            int64_t lda, const double *b, int64_t ldb, double beta, double *c, int64_t ldc)
    __asm("_cblas_dgemm$NEWLAPACK$ILP64");
extern void dgesv_acc(const int64_t *n, const int64_t *nrhs, double *a, const int64_t *lda, int64_t *ipiv, double *b,
                      const int64_t *ldb, int64_t *info)
    __asm("_dgesv$NEWLAPACK$ILP64");
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
    const double *ct;     /* Coss capacitance table (EPC2067Coss.ct), for the full-Newton fallback */
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
    /* full-Newton fallback (circuit.Sim._nonlinear's second loop) */
    double w[NMAX], A[NMAX * NMAX], G[NMAX * NMAX], jac[NMAX * NMAX];
    for (int it = 1; it <= 30; it++) {
        gemv(c->r, m, n, y1, v1);
        for (int i = 0; i < m; i++) { double a = c->vinf[i] * vin1; v1[i] = v1[i] + a; }
        qf(c, v1, qv);
        for (int i = 0; i < m; i++) {
            double a = c->nper[i] * qv[i]; a = a - q0[i];
            double d = v1[i] - v0[i]; d = c->clin[i] * d;
            corr[i] = a - d;
        }
        for (int i = 0; i < m; i++) {                         /* w = n * m.c(v1) - clin */
            double cv = interp1(fabs(v1[i]), c->vt, c->ct, c->nt);
            double a = c->nper[i] * cv; w[i] = a - c->clin[i];
        }
        for (int j = 0; j < m; j++)                           /* r.T * w, Fortran order (n x m) */
            for (int i = 0; i < n; i++) A[j * n + i] = c->r[j * n + i] * w[j];
        cblas_dgemm_acc(ROW, TRANS, NOTRANS, n, n, m, 1.0, A, n, c->r, n, 0.0, G, n);
        for (int i = 0; i < n * n; i++) jac[i] = e->lhs[i] + G[i];   /* C order */
        gemv(e->lhs, n, n, y1, t);
        for (int i = 0; i < n; i++) u[i] = t[i] - rhs[i];
        gemv_t(c->r, m, n, corr, s);
        for (int i = 0; i < n; i++) b[i] = u[i] + s[i];
        double af[NMAX * NMAX];                                /* np.linalg.solve: F-ordered copies, dgesv */
        for (int i = 0; i < n; i++) for (int k = 0; k < n; k++) af[k * n + i] = jac[i * n + k];
        memcpy(dz, b, sizeof(double) * n);
        int64_t nn = n, one = 1, info = 0, ipiv[NMAX];
        dgesv_acc(&nn, &one, af, &nn, ipiv, dz, &nn, &info);
        if (info > 0) return 4;
        int conv = 1;
        for (int i = 0; i < n; i++) { y1[i] = y1[i] - dz[i]; if (!(fabs(dz[i]) < 1e-7)) conv = 0; }
        if (conv) { *iters = 8 + it; return 0; }
    }
    return 3;
}

int pk_abi(void) { return 1; }

/* ---- The whole step loop (KernelPlant2): FastPlant._advance and the bridge's per-step monitors in C. ----------
 * State lives in Python-owned buffers. pk_run steps until t_target (A73's diode check, reverse-conduction energy,
 * peak V_DS / current, diode flags, Euler counter), updating the bridge's monitors after each step (zero-crossing
 * TDC, valley tracking), and stops early when Python has to act:
 *   RUN_DONE 0: t reached t_target;  RUN_LATCH 1: the armed phase-1 latch condition held after a step;
 *   RUN_NEED 2: no topology entry for need_key (Python builds it and calls again; nothing was changed);
 *   RUN_PY 3: this step is Python's (a partial step, h != p.h, or a chord that did not converge);
 *   RUN_ERR 4: a non-finite right-hand side; RUN_NOCONV 5 / RUN_SINGULAR 6: the full-Newton fallback failed
 *   (Python raises as before).  Every operation follows the Python code it replaces. */
enum { RUN_DONE = 0, RUN_LATCH = 1, RUN_NEED = 2, RUN_PY = 3, RUN_ERR = 4, RUN_NOCONV = 5, RUN_SINGULAR = 6 };

typedef struct {
    int n, m, N, nv;
    double *y, *t, *rev_e, *rev_t, *vmax, *ipk, *vd;
    int32_t *gh, *gl, *diode, *euler_left, *last_donly, *load_on;
    int64_t *steps;
    double p_h, v_on, rev_vf, rev_r, vin, t_ramp, i_load, t_load;
    int32_t rev_drop, load_cc;
    const double *nsw;
    const int32_t *dsel, *ssel;
    const ent_t **table;
    int32_t *hoff_set, *cross_set, *vprev_valid, *vmin_set;
    double *t_cross, *v_prev, *t_prev, *vmin, *t_vmin;
    int64_t need_key;
    int64_t chord_iters;
    double i_step, t_step;                            /* A100: load current step (0, inf without one) */
} run_t;

static double vin_at(const run_t *r, double t) {      /* CircuitParams.vin_at */
    if (r->t_ramp > 0) { double a = t / r->t_ramp; return r->vin * (a < 1.0 ? a : 1.0); }
    return r->vin;
}

static double load_at(const run_t *r, double t) {     /* CircuitParams.load_at */
    double a = (r->load_cc && t >= r->t_load) ? r->i_load : 0.0;
    double b = (t >= r->t_step) ? r->i_step : 0.0;
    return a + b;
}

static void vds_all(const run_t *r, const double *y, double vin, double *vd) {  /* FastSim.vds_all */
    double e[NMAX + 2];
    for (int i = 0; i < r->nv; i++) e[i] = y[i];
    e[r->nv] = vin; e[r->nv + 1] = 0.0;
    for (int j = 0; j < r->m; j++) vd[j] = e[r->dsel[j]] - e[r->ssel[j]];
}

static int advance(const ctx_t *c, run_t *r, double h) {      /* FastPlant._advance for a full step */
    const int m = r->m, N = r->N, n = r->n;
    int32_t g[NMAX], d[NMAX], donly[NMAX];
    for (int k = 0; k < N; k++) { g[k] = r->gh[k] != 0; g[N + k] = r->gl[k] != 0; }
    for (int j = 0; j < m; j++) d[j] = r->diode[j] != 0;
    int euler = *r->euler_left > 0;
    double t0 = *r->t, t1 = t0 + h;
    double vin0 = vin_at(r, t0), vin1 = vin_at(r, t1);
    double y1[NMAX], vd1[NMAX];
    int it = 0;
    for (int pass = 0; pass < m + 1; pass++) {
        int64_t key = 0;
        for (int j = 0; j < m; j++) {
            int cond = g[j] || d[j];
            donly[j] = r->rev_drop ? (d[j] && !g[j]) : 0;
            key |= (int64_t)cond << j;
            key |= (int64_t)donly[j] << (m + j);
        }
        key |= (int64_t)euler << (2 * m);
        key |= (int64_t)(*r->load_on != 0) << (2 * m + 1);
        const ent_t *e = r->table[key];
        if (!e) { r->need_key = key; return RUN_NEED; }
        double ld1 = load_at(r, t1), ld0 = euler ? 0.0 : load_at(r, t0);
        int rc = pk_step(c, e, r->y, y1, h, euler, vin0, vin1, ld0, ld1, &it);
        if (rc == 1) return RUN_ERR;
        if (rc == 3) return RUN_NOCONV;
        if (rc == 4) return RUN_SINGULAR;
        if (rc == 2) return RUN_PY;
        int any = 0;
        for (int j = 0; j < m; j++) if (d[j] && !g[j]) any = 1;
        if (!any) break;
        vds_all(r, y1, vin1, vd1);
        int bad = 0;
        for (int j = 0; j < m; j++) if (d[j] && !g[j] && vd1[j] > r->v_on) bad = 1;
        if (!bad) break;
        for (int j = 0; j < m; j++) if (d[j] && !g[j] && vd1[j] > r->v_on) d[j] = 0;
    }
    /* commit, in FastPlant._advance's order */
    int changed = 0;
    for (int j = 0; j < m; j++) if (d[j] != (r->diode[j] != 0)) changed = 1;
    if (changed) { for (int j = 0; j < m; j++) r->diode[j] = d[j]; *r->euler_left = 2; }
    for (int j = 0; j < m; j++) r->last_donly[j] = donly[j];
    for (int i = 0; i < n; i++) r->y[i] = y1[i];
    *r->t = t1;
    *r->euler_left = *r->euler_left - 1 > 0 ? *r->euler_left - 1 : 0;
    vds_all(r, r->y, vin1, r->vd);
    if (r->rev_drop) {
        for (int j = 0; j < m; j++) {
            if (r->last_donly[j]) {
                double vj = r->vd[j];
                double a = -vj - r->rev_vf; a = r->nsw[j] * a; double isd = a / r->rev_r;
                if (isd > 0) { double q = -vj * isd; q = q * h; r->rev_e[j] = r->rev_e[j] + q; r->rev_t[j] = r->rev_t[j] + h; }
            }
        }
    }
    for (int j = 0; j < m; j++) { double a = r->vmax[j], b = r->vd[j]; r->vmax[j] = (a >= b || isnan(a)) ? a : b; }
    double mx = 0.0; int first = 1, nan = 0;
    for (int i = r->nv; i < n; i++) { double a = fabs(r->y[i]); if (isnan(a)) nan = 1; if (first || a > mx) mx = a; first = 0; }
    if (nan) mx = NAN;
    if (mx > *r->ipk) *r->ipk = mx;
    int nd[NMAX], ch2 = 0;
    for (int j = 0; j < m; j++) { nd[j] = (!g[j]) && (r->vd[j] < r->v_on); if (nd[j] != (r->diode[j] != 0)) ch2 = 1; }
    if (ch2) { for (int j = 0; j < m; j++) r->diode[j] = nd[j]; *r->euler_left = 2; }
    *r->steps += 1;
    r->chord_iters += it;
    return RUN_DONE;
}

static void monitors(run_t *r) {                       /* the bridge's on_step, zero-crossing TDC and valley */
    const int N = r->N;
    double t = *r->t;
    for (int k = 0; k < N; k++) {
        if (r->hoff_set[k] && !r->cross_set[k] && !r->gh[k] && !r->gl[k]) {
            double v = r->vd[N + k];
            if (v <= 0.0) {
                if (r->vprev_valid[k] && r->v_prev[k] > 0.0) {
                    double vp = r->v_prev[k], tp = r->t_prev[k];
                    double a = t - tp; a = a * vp; double b = vp - v; a = a / b; r->t_cross[k] = tp + a;
                } else {
                    r->t_cross[k] = t;
                }
                r->cross_set[k] = 1;
            }
            r->v_prev[k] = v; r->t_prev[k] = t; r->vprev_valid[k] = 1;
        }
    }
    for (int k = 0; k < N; k++) {
        if (r->vmin_set[k] && !r->gh[k] && !r->gl[k]) {
            double v = r->vd[k];
            if (v < r->vmin[k]) { r->vmin[k] = v; r->t_vmin[k] = t; }
        }
    }
}

int pk_run(const ctx_t *c, run_t *r, double t_target, int latch_armed, double latch_thr) {
    while (*r->t < t_target - 1e-18) {
        double rem = t_target - *r->t;
        double h = rem < r->p_h ? rem : r->p_h;            /* min(p.h, t_target - t) */
        if (h != r->p_h) return RUN_PY;
        int rc = advance(c, r, h);
        if (rc != RUN_DONE) return rc;
        monitors(r);
        if (latch_armed && r->y[r->nv] <= latch_thr) return RUN_LATCH;
    }
    return RUN_DONE;
}

int pk_abi2(void) { return 2; }
