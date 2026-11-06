"""Reproduce the 300x300 ceramic-carrier chucking history: small warpage, high stiffness.

Sweeps measured warpage (PV), shape and thickness for 96% alumina and compares with
organic/glass panels of the same warpage. Outputs outputs/fig4_measured_map.png + table.
"""
import os, json
from multiprocessing import Pool
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import plotstyle  # noqa: F401  (Korean font)
from assess_measured import assess, plate_D

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")
MATS = {"Organic": (26, 0.18, 1950), "Glass": (74, 0.22, 2380), "Ceramic": (340, 0.22, 3750)}
COLORS = {"Organic": "#2a78d6", "Glass": "#eb6834", "Ceramic": "#1baf7a"}
PVS = [100, 200, 400, 700, 1000, 1500, 2200, 3200]
SHAPES = ["bowl", "saddle"]
T_MM = 1.0


def job(a):
    mat, shape, pv = a
    E, nu, rho = MATS[mat]
    out, _, _ = assess((300, 300), plate_D(E, nu, T_MM), rho * T_MM * 1e-3, pv, shape,
                       vacuum_kPa=80, gcap_um=10, tol_um=20, mesh=20, find_preq=False, leak_beta=30)
    return dict(mat=mat, shape=shape, pv=pv, **out)


if __name__ == "__main__":
    jobs = [(m, s, pv) for m in MATS for s in SHAPES for pv in PVS]
    with Pool(4) as p:
        res = p.map(job, jobs)
    json.dump(res, open(os.path.join(OUT, "ceramic_case.json"), "w"), indent=1)
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.2), dpi=150, sharey=True)
    for ax, shape in zip(axs, SHAPES):
        for m in MATS:
            rs = [r for r in res if r["mat"] == m and r["shape"] == shape]
            ax.plot([r["pv"] for r in rs], [max(r["gap_at_vacuum_um"], 0.1) for r in rs], "-o", lw=2, ms=5,
                    color=COLORS[m], label=f"{m} (E={MATS[m][0]} GPa)")
        ax.axhline(20, color="#0b0b0b", lw=1.2, ls="--")
        ax.annotate("seal tolerance 20 µm", (100, 20), xytext=(2, 4), textcoords="offset points", fontsize=8.5)
        ax.set_xscale("log"); ax.set_yscale("log")
        ax.set_title(f"300×300 mm, t = {T_MM} mm, {shape} shape", loc="left", fontsize=10.5)
        ax.set_xlabel("Measured warpage PV (µm)", color="#52514e")
        ax.grid(True, color="#e4e3df"); ax.set_axisbelow(True)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    axs[0].set_ylabel("Max residual gap after vacuum on (µm)", color="#52514e")
    axs[0].legend(frameon=False, fontsize=9)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig4_same_warpage_by_stiffness.png")); plt.close(fig)
    for r in res:
        print(f"{r['mat']:8s} {r['shape']:7s} PV={r['pv']:5d}  placed={r['placed_gap_um']:7.0f}  gap@80={r['gap_at_vacuum_um']:9.1f}  cap={r['captured_fraction']:.2f}  {'PASS' if r['pass'] else 'FAIL'}")
