"""Chuck feasibility from a MEASURED warpage (bypasses material/process uncertainty).

Give the panel's effective bending stiffness (single equivalent layer E, nu, t — or D directly)
and the measured peak-to-valley warpage + shape; get the vacuum-chuck verdict.

Example:
  python3 assess_measured.py --size 300 300 --E 340 --nu 0.22 --t 1.0 --rho 3750 \
      --pv 300 --shape saddle --vacuum 80 --gcap 10 --beta 30 --tol 20
"""
import argparse
import numpy as np
from plate_fe import QuarterPlate


def natural_curvature(shape, pv, Lx, Ly):
    """FE convention k = (w_xx, w_yy, 2w_xy); positive = edges up."""
    a, b = Lx / 2, Ly / 2
    if shape in ("bowl", "dome"):
        k = 2 * pv / (a * a + b * b)
        k = k if shape == "bowl" else -k
        return np.array([k, k, 0.0])
    if shape == "saddle":
        k = 2 * pv / (a * a + b * b)
        return np.array([k, -k, 0.0])
    if shape in ("cylinder", "cylinder-down"):
        k = 2 * pv / (a * a)
        return np.array([k if shape == "cylinder" else -k, 0.0, 0.0])
    raise ValueError(shape)


def assess(size_mm, D, areal_mass, pv_um, shape, vacuum_kPa=80, gcap_um=10, tol_um=20, mesh=24, find_preq=True,
           leak_beta=30.0):
    Lx, Ly = size_mm[0] * 1e-3, size_mm[1] * 1e-3
    k = natural_curvature(shape, pv_um * 1e-6, Lx, Ly)
    P = QuarterPlate(Lx, Ly, D, k, areal_mass, nx=mesh)
    r = P.chuck(vacuum_kPa * 1e3, gcap_um * 1e-6, leak_beta=leak_beta)
    out = {"kappa_1_per_m": float(abs(k[0])), "placed_gap_um": float(r["w_placed"].max() * 1e6),
           "gap_at_vacuum_um": float(r["max_gap"] * 1e6),
           "captured_fraction": float((P.area_e * r["captured"]).sum() / P.area_e.sum()),
           "plenum_vacuum_kPa": float(r["p_plenum"] / 1e3),
           "pass": bool(r["max_gap"] <= tol_um * 1e-6)}
    if find_preq:
        pr = P.required_pressure(gcap_um * 1e-6, tol_um * 1e-6, leak_beta=leak_beta)
        out["p_req_kPa"] = float(pr / 1e3) if np.isfinite(pr) else None
    return out, P, r


def plate_D(E_GPa, nu, t_mm):
    E, t = E_GPa * 1e9, t_mm * 1e-3
    c = E * t ** 3 / (12 * (1 - nu ** 2))
    return np.array([[c, nu * c, 0], [nu * c, c, 0], [0, 0, c * (1 - nu) / 2]])


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--size", nargs=2, type=float, required=True, help="panel size mm")
    ap.add_argument("--E", type=float, required=True, help="equivalent modulus GPa")
    ap.add_argument("--nu", type=float, default=0.25)
    ap.add_argument("--t", type=float, required=True, help="total thickness mm")
    ap.add_argument("--rho", type=float, default=2500, help="density kg/m^3")
    ap.add_argument("--pv", type=float, required=True, help="measured warpage peak-to-valley um")
    ap.add_argument("--shape", default="bowl", choices=["bowl", "dome", "saddle", "cylinder", "cylinder-down"])
    ap.add_argument("--vacuum", type=float, default=80, help="available vacuum kPa")
    ap.add_argument("--gcap", type=float, default=10, help="capture gap um (equipment constant)")
    ap.add_argument("--beta", type=float, default=30, help="leak coefficient (equipment constant, 0 = no leak)")
    ap.add_argument("--tol", type=float, default=20, help="seal tolerance um")
    ap.add_argument("--mesh", type=int, default=24)
    a = ap.parse_args()
    out, _, _ = assess(a.size, plate_D(a.E, a.nu, a.t), a.rho * a.t * 1e-3, a.pv, a.shape, a.vacuum, a.gcap, a.tol, a.mesh,
                       leak_beta=a.beta)
    for k, v in out.items():
        print(f"{k:20s} {v}")
