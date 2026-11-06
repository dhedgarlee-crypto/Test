"""Compare organic / glass / ceramic cores: warpage, stiffness, vacuum-chuck feasibility.

Usage:  python3 run_compare.py [cases.json] [--quick]
Outputs: outputs/results.json, outputs/summary.md, outputs/fig*.png
"""
import json, sys, os, time
from multiprocessing import Pool
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import plotstyle  # noqa: F401  (Korean font)
from model import load_config, analyze

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "outputs")
CFG = next((a for a in sys.argv[1:] if a.endswith(".json")), os.path.join(HERE, "cases.json"))
QUICK = "--quick" in sys.argv

# Reference categorical palette, first three slots (validated all-pairs, light mode).
COLORS = {"Organic": "#2a78d6", "Glass": "#eb6834", "Glass-lowCTE": "#eb6834", "Ceramic": "#1baf7a"}
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"


def _job(args):
    core, t, size, mesh, fe = args
    cfg, mats = load_config(CFG)
    t0 = time.time()
    r = analyze(cfg, mats, core, t, size, mesh, run_fe=fe)
    r["runtime_s"] = round(time.time() - t0, 1)
    return r


def style(ax, title, xlabel, ylabel):
    ax.set_title(title, loc="left", fontsize=11, color=INK, pad=10)
    ax.set_xlabel(xlabel, color=INK2); ax.set_ylabel(ylabel, color=INK2)
    ax.grid(True, color=GRID, lw=0.8); ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color("#b9b8b2")
    ax.tick_params(colors=INK2)


def main():
    os.makedirs(OUT, exist_ok=True)
    cfg, mats = load_config(CFG)
    cores, extra = cfg["cores"], cfg.get("extra_cores", [])
    t0 = cfg["core_thickness_mm"]
    mesh_main, mesh_sweep = (16, 14) if QUICK else (cfg["mesh"]["main"], cfg["mesh"]["sweep"])
    sizes = [tuple(s) for s in cfg["panel_sizes_mm"]]
    main_size = tuple(cfg["main_panel_mm"])
    sweep_t = cfg["thickness_sweep_mm"][::2] if QUICK else cfg["thickness_sweep_mm"]

    jobs = [(c, t0, s, mesh_main, True) for c in cores + extra for s in sizes]
    jobs += [(c, t, main_size, mesh_sweep, True) for c in cores for t in sweep_t if t != t0]
    with Pool(min(4, os.cpu_count() or 1)) as pool:
        res = pool.map(_job, jobs)
    main_res = res[:len(cores + extra) * len(sizes)]
    sweep = [r for r in res if tuple(r["size_mm"]) == main_size and r["core"] in cores]

    with open(os.path.join(OUT, "results.json"), "w") as f:
        json.dump({"config": cfg, "main": main_res, "sweep": sweep}, f, indent=1, ensure_ascii=False)

    eq = cfg["equipment"]; p_av = eq["vacuum_available_kPa"]
    short = lambda r: r["layer_names"][0]

    # ---------- Fig 1: curvature build-up during cool-down -> warpage at main size ----------
    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=150)
    for c in cores + extra:
        r = next(x for x in main_res if x["core"] == c and tuple(x["size_mm"]) == main_size)
        T = np.array(r["kappa_vs_T"]["T"]); kx = np.array(r["kappa_vs_T"]["kx"])
        Lx, Ly = main_size[0] * 1e-3, main_size[1] * 1e-3
        w = -kx * ((Lx / 2) ** 2 + (Ly / 2) ** 2) / 2 * 1e3  # corner height vs center (linear), mm
        ax.plot(T, w, lw=2, color=COLORS[short(r)], ls="--" if c in extra else "-")
        ax.annotate(f"{short(r)}  {w[-1]:+.1f} mm", (T[-1], w[-1]), xytext=(6, 0), textcoords="offset points",
                    va="center", fontsize=9, color=INK)
    ax.axhline(0, color="#8a8984", lw=1)
    ax.invert_xaxis(); ax.set_xlim(cfg["T_stress_free_C"], cfg["T_chuck_C"] - 35)
    style(ax, f"Warpage build-up during cool-down ({main_size[0]}x{main_size[1]} mm, linear CLT)",
          "Temperature (°C)  — cooling →", "Corner height vs. center (mm)\n+ edges up / − center up")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig1_warpage_vs_temperature.png")); plt.close(fig)

    # ---------- Fig 2: thickness trade-off: warpage and required pressure (two charts, one axis each) ----------
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.2), dpi=150)
    for c in cores:
        rs = sorted([r for r in sweep if r["core"] == c], key=lambda r: r["core_t_mm"])
        t = [r["core_t_mm"] for r in rs]; col = COLORS[short(rs[0])]
        axs[0].plot(t, [r["warpage_nonlinear_um"] / 1e3 for r in rs], "-o", color=col, lw=2, ms=5, label=short(rs[0]))
        pr = [r["p_req_FE_kPa"] if r["p_req_FE_kPa"] is not None else np.nan for r in rs]
        axs[1].plot(t, pr, "-o", color=col, lw=2, ms=5, label=short(rs[0]))
        fail = [ti for ti, r in zip(t, rs) if r["p_req_FE_kPa"] is None]
        if fail:
            axs[1].plot(fail, [1000] * len(fail), "x", color=col, ms=8, mew=2)
    axs[0].set_yscale("log"); axs[1].set_yscale("log")
    axs[1].axhline(p_av, color=INK, lw=1.2, ls="--")
    axs[1].annotate(f"available vacuum {p_av} kPa", (axs[1].get_xlim()[0], p_av), xytext=(4, 4),
                    textcoords="offset points", fontsize=8.5, color=INK)
    style(axs[0], "Free warpage (nonlinear, peak-to-valley)", "Core thickness (mm)", "Warpage (mm)")
    style(axs[1], "Vacuum needed for full contact (FE)", "Core thickness (mm)", "Required pressure (kPa)")
    for ax in axs:
        ax.legend(frameon=False, fontsize=9)
    axs[1].text(0.99, 0.02, "× = not achievable ≤ 1 MPa", transform=axs[1].transAxes, ha="right", fontsize=8, color=INK2)
    fig.suptitle(f"{main_size[0]}x{main_size[1]} mm panel — core thickness trade-off", x=0.01, ha="left", fontsize=12, color=INK)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig2_thickness_tradeoff.png")); plt.close(fig)

    # ---------- Fig 3: stiffness vs curvature map (what really decides chucking) ----------
    fig, ax = plt.subplots(figsize=(7, 4.6), dpi=150)
    for r in sweep + [x for x in main_res if tuple(x["size_mm"]) == main_size]:
        col = COLORS[short(r)]
        ok = r.get("chuck_pass")
        ax.scatter(r["Dstar11_Nm"], abs(r["kappa_x_per_m"]), s=40, color=col if ok else "white",
                   edgecolor=col, lw=1.6, zorder=3)
    D = np.logspace(-2, 3, 50)
    tol = eq["seal_tolerance_um"] * 1e-6
    ax.plot(D, np.sqrt(2 * tol * p_av * 1e3 / D), color=INK, lw=1.2, ls="--")
    ax.annotate("edge-lift limit  D·κ² = 2·p·δ", (D[8], np.sqrt(2 * tol * p_av * 1e3 / D[8])), xytext=(6, 2),
                textcoords="offset points", fontsize=8.5, color=INK)
    ax.set_xscale("log"); ax.set_yscale("log")
    for name, col in [("Organic", COLORS["Organic"]), ("Glass", COLORS["Glass"]), ("Ceramic", COLORS["Ceramic"])]:
        ax.scatter([], [], color=col, s=40, label=name)
    ax.scatter([], [], color="white", edgecolor=INK2, s=40, label="hollow = chuck fails")
    ax.legend(frameon=False, fontsize=9, loc="lower left")
    style(ax, "Bending stiffness vs. warpage curvature (FE verdict per point)", "Bending stiffness D* (N·m)",
          "|Curvature| κ (1/m)")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig3_stiffness_vs_curvature.png")); plt.close(fig)

    # ---------- summary.md ----------
    L = []
    L.append(f"# Warpage & vacuum-chuck comparison\n")
    L.append(f"Stack (bottom→top): core {t0} mm + " + " + ".join(f"{m} {t} mm" for m, t in cfg["top_stack_bottom_to_top"]))
    L.append(f"\nCool-down {cfg['T_stress_free_C']} → {cfg['T_chuck_C']} °C. Vacuum {p_av} kPa, capture gap "
             f"{eq['capture_gap_um']} µm, seal tolerance {eq['seal_tolerance_um']} µm, leak β {eq.get('leak_beta', 0)}.\n")
    L.append("| Core | Panel (mm) | κ (1/m) | Shape | Warpage lin / nonlin (µm) | D* (N·m) | As-placed gap (µm) | p_req FE (kPa) | p_req analytic (kPa) | Gap @ avail. (µm) | Plenum @ avail. (kPa) | Chuck | Flattened stress max core / EMC (MPa) | Stress |")
    L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in main_res:
        pr = "> 1000" if r["p_req_FE_kPa"] is None else f"{r['p_req_FE_kPa']:.1f}"
        sm = r["flat_stress_max_MPa"]
        L.append(f"| {r['core']} | {r['size_mm'][0]}×{r['size_mm'][1]} | {r['kappa_x_per_m']:+.3f} | {r['edge_direction']}, {r['nonlinear_shape']} | "
                 f"{r['warpage_linear_um']:.0f} / {r['warpage_nonlinear_um']:.0f} | {r['Dstar11_Nm']:.2f} | {r['placed_gap_um']:.0f} | {pr} | "
                 f"{r['p_req_analytic_kPa']:.1f} | {r['gap_at_available_um']:.1f} | {r['plenum_at_available_kPa']:.1f} | {'PASS' if r['chuck_pass'] else 'FAIL'} | "
                 f"{sm[0]:.0f} / {sm[-1]:.0f} (allow {r['allowable_MPa'][0]:.0f} / {r['allowable_MPa'][-1]:.0f}) | {'PASS' if r['stress_pass'] else 'FAIL'} |")
    L.append("\n## Thickness sweep (" + f"{main_size[0]}×{main_size[1]} mm)\n")
    L.append("| Core | t (mm) | κ (1/m) | Warpage nonlin (µm) | D* (N·m) | p_req FE (kPa) | Chuck |")
    L.append("|---|---|---|---|---|---|---|")
    for r in sorted(sweep, key=lambda r: (r["core"], r["core_t_mm"])):
        pr = "> 1000" if r["p_req_FE_kPa"] is None else f"{r['p_req_FE_kPa']:.1f}"
        L.append(f"| {r['core']} | {r['core_t_mm']} | {r['kappa_x_per_m']:+.3f} | {r['warpage_nonlinear_um']:.0f} | {r['Dstar11_Nm']:.2f} | {pr} | {'PASS' if r['chuck_pass'] else 'FAIL'} |")
    open(os.path.join(OUT, "summary.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
