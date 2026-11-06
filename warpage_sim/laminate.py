"""Classical laminate theory with incremental (temperature-stepped) thermal loading.

Convention: z is measured upward from the laminate mid-thickness, strain = eps0 + z*kappa.
A free (unconstrained) laminate deforms as w = -(kx x^2 + ky y^2 + kxy x y)/2, so a
negative kappa means the edges move up (bowl / "smile" seen from the top layer).
"""
import numpy as np


def z_coords(layers):
    h = sum(L.thickness for L in layers)
    z = np.concatenate([[0.0], np.cumsum([L.thickness for L in layers])]) - h / 2
    return z


def abd(layers, T):
    z = z_coords(layers)
    A = np.zeros((3, 3)); B = np.zeros((3, 3)); D = np.zeros((3, 3))
    for k, L in enumerate(layers):
        Q = L.material.Q(T)
        z0, z1 = z[k], z[k + 1]
        A += Q * (z1 - z0)
        B += Q * (z1 ** 2 - z0 ** 2) / 2
        D += Q * (z1 ** 3 - z0 ** 3) / 3
    return A, B, D


def thermal_resultant_increment(layers, T, dT):
    z = z_coords(layers)
    N = np.zeros(3); M = np.zeros(3)
    for k, L in enumerate(layers):
        Qa = L.material.Q(T) @ L.material.alpha(T) * dT
        z0, z1 = z[k], z[k + 1]
        N += Qa * (z1 - z0)
        M += Qa * (z1 ** 2 - z0 ** 2) / 2
    return N, M


def cooldown(layers, T_stress_free, T_end, n_steps=300):
    """Incrementally integrate free thermal deformation from T_stress_free to T_end.

    Returns dict with temperature history of curvature, mid-plane strain, and layer stresses
    (at bottom/top surface of every layer) at T_end.
    """
    Ts = np.linspace(T_stress_free, T_end, n_steps + 1)
    z = z_coords(layers)
    eps0 = np.zeros(3); kap = np.zeros(3)
    sig = np.zeros((len(layers), 2, 3))  # layer, (bottom, top), (sx, sy, txy)
    hist_T, hist_k = [Ts[0]], [kap.copy()]
    for i in range(n_steps):
        T = 0.5 * (Ts[i] + Ts[i + 1]); dT = Ts[i + 1] - Ts[i]
        A, B, D = abd(layers, T)
        N, M = thermal_resultant_increment(layers, T, dT)
        ABD = np.block([[A, B], [B, D]])
        d = np.linalg.solve(ABD, np.concatenate([N, M]))
        de, dk = d[:3], d[3:]
        eps0 += de; kap += dk
        for k, L in enumerate(layers):
            Q = L.material.Q(T); a = L.material.alpha(T)
            for j, zz in enumerate((z[k], z[k + 1])):
                sig[k, j] += Q @ (de + zz * dk - a * dT)
        hist_T.append(Ts[i + 1]); hist_k.append(kap.copy())
    return {"T": np.array(hist_T), "kappa_hist": np.array(hist_k),
            "eps0": eps0, "kappa": kap, "stress": sig}


def flatten_stress(layers, T, kappa_free, stress_free):
    """Stresses after the chuck forces the laminate flat (kappa -> 0, in-plane free)."""
    A, B, D = abd(layers, T)
    dk = -kappa_free
    de = -np.linalg.solve(A, B @ dk)
    z = z_coords(layers)
    sig = stress_free.copy()
    for k, L in enumerate(layers):
        Q = L.material.Q(T)
        for j, zz in enumerate((z[k], z[k + 1])):
            sig[k, j] += Q @ (de + zz * dk)
    return sig


def reduced_bending_stiffness(layers, T):
    """D* = D - B A^-1 B : bending stiffness with free in-plane deformation."""
    A, B, D = abd(layers, T)
    return D - B @ np.linalg.solve(A, B)


def effective_thermal_resultants(layers, T, eps0, kappa):
    """Equivalent constant N_T, M_T at temperature T reproducing (eps0, kappa) linearly."""
    A, B, D = abd(layers, T)
    return A @ eps0 + B @ kappa, B @ eps0 + D @ kappa


def areal_mass(layers):
    return sum(L.material.rho * L.thickness for L in layers)
