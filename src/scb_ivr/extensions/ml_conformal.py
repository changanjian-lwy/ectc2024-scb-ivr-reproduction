"""Conformal prediction in numpy (extension ml_design_assist): distribution-free intervals around a point model.

Split conformal (Vovk et al. 2005; Angelopoulos & Bates 2023): from n calibration scores s_i (how far past predictions
were off) and a miscoverage alpha, take q = the ceil((n + 1)(1 - alpha))-th smallest score (infinite when that rank
exceeds n). If a new score is exchangeable with the calibration scores, the interval built from q covers the outcome
with probability >= 1 - alpha (and < 1 - alpha + 1 / (n + 1) without ties). No model of the error is needed.

Scores, for a point prediction p and an outcome y (kind):
- "rel": r = y / p - 1 (p > 0), interval p (1 + r);
- "log": r = ln(y / p) (p, y > 0), interval p exp(r);
- "abs": r = y - p, interval p + r.
Symmetric: q from |r|, interval [p (-q), p (+q)]. Signed: two one-sided quantiles at alpha / 2 each, q_hi from r and
q_lo from -r, interval [p (-q_lo), p (+q_hi)]: narrower when the model is biased.
Mondrian: a separate calibration per group (e.g. rising line steps, D63's known weak domain), each with its own
guarantee.
Adaptive conformal inference (Gibbs & Candes 2021), for scores that drift: after each batch the level is moved,
alpha_t <- alpha_t + gamma sum_i (alpha - err_i), so the long-run miss rate tends to alpha whatever the drift.
"""
from __future__ import annotations

import math

import numpy as np

KINDS = ("rel", "log", "abs")


def quantile(scores, alpha):
    """The ceil((n + 1)(1 - alpha))-th smallest score; +inf if that rank exceeds n, -inf if it is below 1."""
    s = np.sort(np.asarray(scores, float))
    k = math.ceil((len(s) + 1) * (1 - alpha) - 1e-12)
    if k > len(s):
        return math.inf
    if k < 1:
        return -math.inf
    return float(s[k - 1])


def score(p, y, kind):
    p, y = np.asarray(p, float), np.asarray(y, float)
    if kind == "rel":
        return y / p - 1
    if kind == "log":
        return np.log(y / p)
    if kind == "abs":
        return y - p
    raise ValueError(kind)


def invert(p, r, kind):
    p = np.asarray(p, float)
    with np.errstate(over="ignore", invalid="ignore"):
        if kind == "rel":
            return p * (1 + r)
        if kind == "log":
            return p * np.exp(r)
        return p + r


def band(cal_p, cal_y, p, alpha, kind="rel", signed=False):
    """(lo, hi) for predictions p from calibration pairs (cal_p, cal_y)."""
    r = score(cal_p, cal_y, kind)
    if signed:
        q_hi, q_lo = quantile(r, alpha / 2), quantile(-r, alpha / 2)
    else:
        q_hi = q_lo = quantile(np.abs(r), alpha)
    return invert(p, -q_lo, kind), invert(p, q_hi, kind)


def mondrian_band(cal_p, cal_y, cal_g, p, g, alpha, kind="rel", signed=False):
    """band() calibrated within each prediction's group only."""
    cal_p, cal_y, cal_g = np.asarray(cal_p, float), np.asarray(cal_y, float), np.asarray(cal_g)
    p, g = np.atleast_1d(np.asarray(p, float)), np.atleast_1d(np.asarray(g))
    lo, hi = np.empty(len(p)), np.empty(len(p))
    for grp in set(g.tolist()):
        m, c = g == grp, cal_g == grp
        lo[m], hi[m] = band(cal_p[c], cal_y[c], p[m], alpha, kind, signed)
    return lo, hi


class ACI:
    """Adaptive conformal inference around band(): the working level alpha_t moves with the observed misses."""

    def __init__(self, alpha, gamma):
        self.alpha, self.gamma, self.a = alpha, gamma, alpha

    def band(self, cal_p, cal_y, p, kind="rel", signed=False):
        return band(cal_p, cal_y, p, self.a, kind, signed)

    def update(self, covered):
        """covered: one bool per prediction of the last batch."""
        self.a += self.gamma * float(np.sum(self.alpha - (1 - np.asarray(covered, float))))
        return self.a
