"""Geometrically nonlinear free-warpage shape (Hyer-type Rayleigh-Ritz, von Karman strains).

Large thin panels do not stay as a spherical dome: membrane stretching makes the
doubly-curved shape expensive and the panel bifurcates toward a cylindrical shape.
Linear CLT therefore over-predicts the warpage of large panels. This module minimizes the
total potential energy over
    w = -(a x^2 + b y^2)/2
    u = c1 x + c2 x^3 + c3 x y^2
    v = d1 y + d2 y^3 + d3 x^2 y
using the laminate ABD matrices and equivalent thermal resultants N_T, M_T.
"""
import numpy as np
from scipy.optimize import minimize


def _gauss(n, L):
    x, w = np.polynomial.legendre.leggauss(n)
    return x * L / 2, w * L / 2


def free_shape(A, B, D, NT, MT, Lx, Ly, kappa_lin, n_gauss=12):
    xg, wx = _gauss(n_gauss, Lx)
    yg, wy = _gauss(n_gauss, Ly)
    X, Y = np.meshgrid(xg, yg, indexing="ij")
    W = np.outer(wx, wy)
    ABD = np.block([[A, B], [B, D]])
    F = np.concatenate([NT, MT])
    s = max(abs(kappa_lin[0]), abs(kappa_lin[1]), 1e-9)  # curvature scale

    def fields(p):
        a, b, c1, c2, c3, d1, d2, d3 = p
        a *= s; b *= s
        wx_ = -a * X; wy_ = -b * Y
        ex = c1 * 1e-4 + 3 * c2 * 1e-4 / Lx**2 * X**2 + c3 * 1e-4 / Lx**2 * Y**2 + 0.5 * wx_**2
        ey = d1 * 1e-4 + 3 * d2 * 1e-4 / Ly**2 * Y**2 + d3 * 1e-4 / Ly**2 * X**2 + 0.5 * wy_**2
        gxy = 2 * (c3 * 1e-4 / Lx**2 + d3 * 1e-4 / Ly**2) * X * Y + wx_ * wy_
        kx = np.full_like(X, a); ky = np.full_like(X, b); kxy = np.zeros_like(X)
        return np.stack([ex, ey, gxy, kx, ky, kxy])

    def energy(p):
        e = fields(p)
        dens = 0.5 * np.einsum("i...,ij,j...->...", e, ABD, e) - np.einsum("i...,i->...", e, F)
        return np.sum(dens * W)

    kl0, kl1 = kappa_lin[0] / s, kappa_lin[1] / s
    starts = [[kl0, kl1], [kl0 + kl1, 0.0], [0.0, kl0 + kl1], [kl0, -0.2 * kl1], [-0.2 * kl0, kl1]]
    best = None
    sols = []
    for a0, b0 in starts:
        p0 = np.array([a0, b0, 0, 0, 0, 0, 0, 0], float)
        r = minimize(energy, p0, method="BFGS", options={"gtol": 1e-12, "maxiter": 5000})
        sols.append(r)
        if best is None or r.fun < best.fun - 1e-12:
            best = r
    a, b = best.x[0] * s, best.x[1] * s
    # warpage of w = -(a x^2 + b y^2)/2 over the rectangle (peak-to-valley)
    corners = [-(a * (Lx/2)**2 + b * (Ly/2)**2) / 2, -(a * (Lx/2)**2) / 2, -(b * (Ly/2)**2) / 2, 0.0]
    warp = max(corners) - min(corners)
    ratio = min(abs(a), abs(b)) / max(abs(a), abs(b), 1e-30)
    shape = "dome/bowl (spherical)" if ratio > 0.8 else ("cylindrical" if ratio < 0.2 else "elliptic (transition)")
    if a * b < 0 and ratio > 0.2:
        shape = "saddle"
    return {"kx": a, "ky": b, "warpage": warp, "shape": shape, "energy": best.fun}


def linear_warpage(kappa, Lx, Ly):
    a, b = kappa[0], kappa[1]
    corners = [-(a * (Lx/2)**2 + b * (Ly/2)**2) / 2, -(a * (Lx/2)**2) / 2, -(b * (Ly/2)**2) / 2, 0.0]
    return max(corners) - min(corners)
