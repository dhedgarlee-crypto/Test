"""Glue: build a panel from config, run CLT + nonlinear free shape + chuck FE."""
import json
import numpy as np
from materials import Material, Layer
import laminate as lam
import ritz
from plate_fe import QuarterPlate


def load_config(path):
    with open(path) as f:
        cfg = json.load(f)
    mats = {k: Material.from_dict(v) for k, v in cfg["materials"].items()}
    return cfg, mats


def build_stack(cfg, mats, core, core_t_mm):
    layers = [Layer(mats[core], core_t_mm * 1e-3)]
    layers += [Layer(mats[m], t * 1e-3) for m, t in cfg["top_stack_bottom_to_top"]]
    return layers


def analyze(cfg, mats, core, core_t_mm, size_mm, nmesh, run_fe=True, keep_fields=False):
    eq = cfg["equipment"]
    p_av = eq["vacuum_available_kPa"] * 1e3
    g_cap = eq["capture_gap_um"] * 1e-6
    tol = eq["seal_tolerance_um"] * 1e-6
    beta = eq.get("leak_beta", 0.0)
    Lx, Ly = size_mm[0] * 1e-3, size_mm[1] * 1e-3
    layers = build_stack(cfg, mats, core, core_t_mm)
    T0, T1 = cfg["T_stress_free_C"], cfg["T_chuck_C"]
    cd = lam.cooldown(layers, T0, T1)
    kap = cd["kappa"]
    A, B, D = lam.abd(layers, T1)
    Dst = lam.reduced_bending_stiffness(layers, T1)
    NT, MT = lam.effective_thermal_resultants(layers, T1, cd["eps0"], kap)
    nl = ritz.free_shape(A, B, D, NT, MT, Lx, Ly, kap)
    w_lin = ritz.linear_warpage(kap, Lx, Ly)
    sig_flat = lam.flatten_stress(layers, T1, kap, cd["stress"])
    m = lam.areal_mass(layers)

    def layer_max(sig):
        return [float(np.max(sig[k, :, :2])) / 1e6 for k in range(len(layers))]

    out = {
        "core": core, "core_t_mm": core_t_mm, "size_mm": list(size_mm),
        "total_t_mm": sum(L.thickness for L in layers) * 1e3,
        "kappa_x_per_m": float(kap[0]), "kappa_y_per_m": float(kap[1]),
        "radius_m": float(1 / max(abs(kap[0]), 1e-12)),
        "Dstar11_Nm": float(Dst[0, 0]),
        "warpage_linear_um": float(w_lin * 1e6),
        "warpage_nonlinear_um": float(nl["warpage"] * 1e6),
        "nonlinear_shape": nl["shape"],
        "edge_direction": "edges up (bowl)" if kap[0] < 0 else "center up (dome)",
        # closed-form edge-lift estimate: delta = D k^2 / (2 p)  ->  p = D k^2 / (2 delta)
        "p_req_analytic_kPa": float(Dst[0, 0] * kap[0] ** 2 / (2 * tol) / 1e3),
        "free_stress_max_MPa": layer_max(cd["stress"]),
        "flat_stress_max_MPa": layer_max(sig_flat),
        "layer_names": [L.material.name for L in layers],
        "allowable_MPa": [None if L.material.allowable_stress is None else L.material.allowable_stress / 1e6 for L in layers],
        "areal_mass_kg_m2": m,
        "kappa_vs_T": {"T": cd["T"].tolist(), "kx": cd["kappa_hist"][:, 0].tolist()},
    }
    if run_fe:
        P = QuarterPlate(Lx, Ly, Dst, -kap, m, nx=nmesh)
        pr = P.required_pressure(g_cap, tol, p_max=1.024e6, leak_beta=beta)
        res = P.chuck(p_av, g_cap, leak_beta=beta)
        out.update({
            "p_req_FE_kPa": float(pr / 1e3) if np.isfinite(pr) else None,
            "gap_at_available_um": float(res["max_gap"] * 1e6),
            "placed_gap_um": float(res["w_placed"].max() * 1e6),
            "captured_fraction": float((P.area_e * res["captured"]).sum() / P.area_e.sum()),
            "plenum_at_available_kPa": float(res["p_plenum"] / 1e3),
        })
        ok_stress = all(a is None or s <= a for s, a in zip(out["flat_stress_max_MPa"], out["allowable_MPa"]))
        out["chuck_pass"] = bool(np.isfinite(pr) and pr <= p_av)
        out["stress_pass"] = bool(ok_stress)
        if keep_fields:
            out["_fields"] = {"P": P, "res": res}
    return out
