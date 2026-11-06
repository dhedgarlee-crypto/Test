"""Run the I-Cube E-type process sequence for every carrier option in the Excel template.

Usage:  python3 run_process.py [templates/ICubeE_warpage_input.xlsx] [--quick] [--out DIR]
                               [--sweep LAYER=t1,t2,...]   (layer-thickness sweep in µm, e.g. COP_DIE=200,300,400,500)
Outputs (default outputs/process/): process_results.xlsx, summary.md, results.json,
fig_process_warpage.png, fig_chuck_gap_maps.png, fig_3d_shapes.png, warpage_3d_viewer.html,
and with --sweep: fig_sweep_<LAYER>.png, sweep_<LAYER>.md
"""
import os, sys, json, time
from multiprocessing import Pool
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import plotstyle  # noqa: F401  (Korean font)
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

from xlsx_io import read_template
from process import PanelState
from plate_fe import QuarterPlate
from materials import Material
import ritz
import viz3d

HERE = os.path.dirname(os.path.abspath(__file__))
ARGS = sys.argv[1:]
XLSX = next((a for a in ARGS if a.endswith(".xlsx")), os.path.join(HERE, "templates", "ICubeE_warpage_input.xlsx"))
OUT = ARGS[ARGS.index("--out") + 1] if "--out" in ARGS else os.path.join(HERE, "outputs", "process")
QUICK = "--quick" in ARGS
SWEEP = ARGS[ARGS.index("--sweep") + 1] if "--sweep" in ARGS else None
ZONES = ("unit", "edge")
COLORS = {"Organic": "#2a78d6", "Glass": "#eb6834", "Ceramic": "#1baf7a"}
FALLBACK = ["#2a78d6", "#eb6834", "#1baf7a"]


def zone_fn_factory(ux, uy):
    return lambda x, y: 0 if (abs(x) <= ux / 2 and abs(y) <= uy / 2) else 1


def make_plate(states, orient, Lx, Ly, zf, nx):
    props = []
    for z in ZONES:
        S = states[z]
        props.append((S.Dstar(), -orient * S.kappa, S.areal_mass()))
    return QuarterPlate(Lx, Ly, None, None, None, nx=nx, zone_fn=zf, zone_props=props)


def corner_minus_center(P, w):
    W = w.reshape(P.nx + 1, P.ny + 1)
    return W[-1, -1] - W[0, 0], W.max() - W.min()


def simulate(arg):
    option, overrides, fast = arg if isinstance(arg, tuple) else (arg, {}, False)
    cfg = read_template(XLSX)
    for lid, t_um in overrides.items():
        cfg["layers"][lid]["t"] = t_um * 1e-6
    pn = cfg["panel"]
    Lx, Ly = pn["panel_x_mm"] * 1e-3, pn["panel_y_mm"] * 1e-3
    zf = zone_fn_factory(pn["unit_region_x_mm"] * 1e-3, pn["unit_region_y_mm"] * 1e-3)
    nx = 12 if QUICK else int(pn.get("mesh", 24))
    find_preq = str(pn.get("find_required_pressure", "YES")).upper().startswith("Y") and not QUICK and not fast
    c2 = pn.get("carrier2_option", "SAME")
    c2 = option if (c2 is None or str(c2).upper() == "SAME") else c2
    T0 = float(pn.get("T_start_C", 25))
    states = {z: PanelState(T0) for z in ZONES}
    orient = 1
    rec = []

    def all_(fn):
        for z in ZONES:
            fn(states[z], z)

    def add_layers(ids, T):
        all_(lambda S, z: S.temp_to(T))
        for lid in ids:
            L = cfg["layers"][lid]
            all_(lambda S, z: S.add(lid, L["group"], L["mat"][z], L["t"]))
        all_(lambda S, z: S.cure_shrink(set(ids)))

    t_start = time.time()
    for st in cfg["steps"]:
        typ = str(st["type"]).upper(); T = st.get("T_C"); tg = st["targets"]
        chuck = None
        if typ == "START":
            for lid, m, t in cfg["carriers"][option]:
                all_(lambda S, z: S.add(lid, "CARRIER1", m, t))
            if T is not None:
                all_(lambda S, z: S.temp_to(T))
            for lid in tg:
                L = cfg["layers"][lid]
                all_(lambda S, z: S.add(lid, L["group"], L["mat"][z], L["t"]))
        elif typ == "ADD":
            add_layers(tg, T)
        elif typ == "ADD_FILL":
            all_(lambda S, z: S.temp_to(T))
            for lid in tg:
                L = cfg["layers"][lid]
                if not L["host"]:
                    raise ValueError(f"ADD_FILL: layer {lid} has no host_layer")
                all_(lambda S, z: S.add_parallel(lid, L["group"], L["mat"][z], L["host"]))
            all_(lambda S, z: S.cure_shrink(set(tg)))
        elif typ == "ADD_CARRIER2":
            add_layers(tg, T)
            for lid, m, t in reversed(cfg["carriers"][c2]):
                all_(lambda S, z: S.add(lid + "_2", "CARRIER2", m, t))
        elif typ == "TEMP":
            all_(lambda S, z: S.temp_to(T))
        elif typ == "GRIND":
            if T is not None:
                all_(lambda S, z: S.temp_to(T))
            all_(lambda S, z: S.grind(tg[0], float(st["value"]) * 1e-6))
        elif typ == "REMOVE":
            if T is not None:
                all_(lambda S, z: S.temp_to(T))
            all_(lambda S, z: S.remove(tg))
        elif typ == "FLIP":
            orient = -orient
        elif typ == "CHUCK":
            all_(lambda S, z: S.temp_to(T))
            eq = cfg["equipment"][st["equipment"]]
            P = make_plate(states, orient, Lx, Ly, zf, nx)
            pv, gc, beta, tol = (float(eq["vacuum_kPa"]) * 1e3, float(eq["capture_gap_um"]) * 1e-6,
                                 float(eq["leak_beta"]), float(eq["seal_tol_um"]) * 1e-6)
            r = P.chuck(pv, gc, leak_beta=beta)
            pr = P.required_pressure(gc, tol, p_max=1.024e6, leak_beta=beta) if find_preq else None
            # flattening stresses vs allowables (single-material layers only)
            worst = []
            for z in ZONES:
                for L, sb, stt in states[z].flatten_stresses():
                    smax = float(max(sb[:2].max(), stt[:2].max()))
                    allow = getattr(L.mat, "allowable_stress", None) if isinstance(L.mat, Material) else None
                    worst.append((L.id, z, smax, None if allow is None else allow / 1e6))
            viol = [w for w in worst if w[3] is not None and w[2] > w[3]]
            chk = sorted([w for w in worst if w[3] is not None], key=lambda w: w[2] / w[3], reverse=True)
            chuck = {"equipment": st["equipment"], "placed_gap_um": float(r["w_placed"].max() * 1e6),
                     "gap_um": float(r["max_gap"] * 1e6), "plenum_kPa": float(r["p_plenum"] / 1e3),
                     "captured": float((P.area_e * r["captured"]).sum() / P.area_e.sum()),
                     "p_req_kPa": None if pr is None else (float(pr / 1e3) if np.isfinite(pr) else float("inf")),
                     "pass": bool(r["max_gap"] <= tol), "stress_pass": not viol,
                     "stress_ratio_max": None if not chk else f"{chk[0][0]}({chk[0][1]}) {chk[0][2]:.0f}/{chk[0][3]:.0f} MPa",
                     "field": {"x": None}}
            x, y, Wp = P.full_field(r["w_placed"]); _, _, Wv = P.full_field(r["w"])
            chuck["field"] = {"x": x.tolist(), "y": y.tolist(), "placed": Wp.tolist(), "vacuum": Wv.tolist()}
        else:
            raise ValueError(f"unknown step type {typ}")

        # ---- record state ----
        Su = states["unit"]
        P = make_plate(states, orient, Lx, Ly, zf, nx)
        wfree = P.free_shape()
        cmc, pvv = corner_minus_center(P, wfree)
        fx, fy, fz = P.full_field(wfree)
        A, B, D = Su.abd(Su.T)
        NT = A @ Su.eps0 + B @ Su.kappa; MT = B @ Su.eps0 + D @ Su.kappa
        nl = ritz.free_shape(A, B, D, NT, MT, Lx, Ly, Su.kappa) if np.abs(Su.kappa).max() > 1e-6 else {"warpage": 0.0, "shape": "flat"}
        res = max(np.abs(Su.residual()[0]).max(), np.abs(states["edge"].residual()[0]).max())
        rec.append({"step": st["step"], "name": st["name"], "type": typ, "T": states["unit"].T, "orient": orient,
                    "thickness_um": Su.thickness() * 1e6,
                    "kappa_unit": float(-orient * Su.kappa[0]), "kappa_edge": float(-orient * states["edge"].kappa[0]),
                    "warp_corner_minus_center_um": float(cmc * 1e6), "warp_PV_linear_um": float(pvv * 1e6),
                    "warp_PV_nonlinear_unit_um": float(nl["warpage"] * 1e6), "shape": nl["shape"],
                    "Dstar_unit": float(Su.Dstar()[0, 0]), "Dstar_edge": float(states["edge"].Dstar()[0, 0]),
                    "mass_kg_m2": Su.areal_mass(), "equilibrium_residual_N_m": float(res),
                    "layers": [L.id for L in Su.layers], "chuck": chuck, "plot3d": bool(st.get("plot3d")),
                    "field": {"x": (fx * 1e3).tolist(), "y": (fy * 1e3).tolist(), "z": (fz * 1e6).round(1).tolist()}})
    return {"option": option, "carrier2": c2, "steps": rec, "runtime_s": round(time.time() - t_start, 1)}


def write_outputs(results, cfg):
    os.makedirs(OUT, exist_ok=True)
    slim = [{**r, "steps": [{**{k: v for k, v in s.items() if k != "field"},
                             "chuck": None if s["chuck"] is None else {k: v for k, v in s["chuck"].items() if k != "field"}}
                            for s in r["steps"]]} for r in results]
    json.dump(slim, open(os.path.join(OUT, "results.json"), "w"), indent=1, ensure_ascii=False)
    col = {r["option"]: COLORS.get(r["option"], FALLBACK[i % 3]) for i, r in enumerate(results)}

    # ---------------- Fig A: warpage & stiffness through the process (two charts) ----------------
    steps = results[0]["steps"]
    xs = np.arange(len(steps))
    labels = [f"{s['step']}. {s['name']}" for s in steps]
    fig, axs = plt.subplots(2, 1, figsize=(13, 8.6), dpi=150, sharex=True, gridspec_kw={"height_ratios": [3, 2]})
    for r in results:
        w = [s["warp_corner_minus_center_um"] / 1e3 for s in r["steps"]]
        axs[0].plot(xs, w, "-", color=col[r["option"]], lw=2, label=r["option"])
        for i, s in enumerate(r["steps"]):
            if s["chuck"]:
                ok = s["chuck"]["pass"]
                axs[0].scatter(i, w[i], s=70, zorder=4, color=col[r["option"]] if ok else "white",
                               edgecolor=col[r["option"]], lw=2)
        axs[0].annotate(f"{w[-1]:+.2f} mm", (xs[-1], w[-1]), xytext=(6, 0), textcoords="offset points",
                        va="center", fontsize=9, color="#0b0b0b")
        axs[1].plot(xs, [s["Dstar_unit"] for s in r["steps"]], "-", color=col[r["option"]], lw=2, label=r["option"])
    axs[0].axhline(0, color="#8a8984", lw=1)
    axs[0].scatter([], [], s=60, color="#52514e", label="흡착 PASS (filled)")
    axs[0].scatter([], [], s=60, color="white", edgecolor="#52514e", lw=2, label="흡착 FAIL (hollow)")
    axs[0].set_ylabel("Warpage: corner − center (mm)\n+ edges up, viewed from top", color="#52514e")
    axs[0].set_title("Warpage through the process (linear plate FE, unit + edge zones)", loc="left", fontsize=11)
    axs[1].set_yscale("log"); axs[1].set_ylabel("Bending stiffness D* unit zone (N·m)", color="#52514e")
    axs[1].set_title("Panel bending stiffness through the process", loc="left", fontsize=11)
    for ax in axs:
        ax.grid(True, color="#e4e3df"); ax.set_axisbelow(True)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
    axs[0].legend(frameon=False, fontsize=9, ncol=5, loc="upper left")
    axs[1].set_xticks(xs); axs[1].set_xticklabels(labels, rotation=60, ha="right", fontsize=8)
    for ax in axs:
        for i, s in enumerate(steps):
            if s["type"] == "FLIP":
                ax.axvline(i, color="#b9b8b2", lw=1, ls=":")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig_process_warpage.png")); plt.close(fig)

    # ---------------- Fig B: gap maps at each chuck step ----------------
    ch = [i for i, s in enumerate(steps) if s["chuck"]]
    fig, axs = plt.subplots(len(results), len(ch), figsize=(2.6 * len(ch), 2.6 * len(results) + 0.6), dpi=150, squeeze=False)
    for a, r in enumerate(results):
        for b, i in enumerate(ch):
            c = r["steps"][i]["chuck"]; f = c["field"]; ax = axs[a, b]
            im = ax.pcolormesh(np.array(f["x"]) * 1e3, np.array(f["y"]) * 1e3, np.array(f["placed"]).T * 1e3,
                               cmap="Blues", shading="gouraud", vmin=0)
            ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
            verdict = "PASS" if c["pass"] else "FAIL"
            ax.set_title(f"{r['steps'][i]['step']}. {c['equipment']}\n{verdict}  gap {c['gap_um']:.0f} µm", fontsize=7.5)
            cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.02); cb.ax.tick_params(labelsize=6)
            if b == 0:
                ax.set_ylabel(r["option"], fontsize=10, color=col[r["option"]])
    fig.suptitle("As-placed gap to chuck before vacuum (mm) — title: verdict and residual gap after vacuum", x=0.01, ha="left", fontsize=10)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig_chuck_gap_maps.png")); plt.close(fig)

    # ---------------- 3D shapes ----------------
    viz3d.png_grid(results, os.path.join(OUT, "fig_3d_shapes.png"), lambda s: s["plot3d"])
    viz3d.viewer_html(results, os.path.join(OUT, "warpage_3d_viewer.html"), os.path.basename(XLSX))

    # ---------------- Excel results ----------------
    wb = Workbook(); ws = wb.active; ws.title = "Chuck_Summary"
    hdr = ["Carrier", "Step", "공정", "설비", "온도[°C]", "Warpage corner−center [µm]", "Warpage PV 비선형(unit) [µm]", "형상",
           "놓인 상태 최대 gap [µm]", "진공 후 최대 gap [µm]", "Plenum 진공 [kPa]", "포착 면적", "필요 진공 [kPa]", "흡착", "평탄화 응력", "최대 응력/허용"]
    ws.append(hdr)
    for r in results:
        for s in r["steps"]:
            c = s["chuck"]
            if not c:
                continue
            pr = c["p_req_kPa"]
            ws.append([r["option"], s["step"], s["name"], c["equipment"], s["T"], round(s["warp_corner_minus_center_um"]),
                       round(s["warp_PV_nonlinear_unit_um"]), s["shape"], round(c["placed_gap_um"]), round(c["gap_um"], 1),
                       round(c["plenum_kPa"], 1), round(c["captured"], 3),
                       None if pr is None else (">1024" if not np.isfinite(pr) else round(pr, 1)),
                       "PASS" if c["pass"] else "FAIL", "PASS" if c["stress_pass"] else "FAIL", c["stress_ratio_max"]])
    for r in results:
        w2 = wb.create_sheet(f"Steps_{r['option']}"[:31])
        w2.append(["Step", "공정", "유형", "T[°C]", "방향(+1 원래/-1 반전)", "두께[µm]", "κ unit[1/m]", "κ edge[1/m]",
                   "Warpage corner−center [µm]", "Warpage PV 선형 [µm]", "Warpage PV 비선형 unit [µm]", "형상",
                   "D* unit [N·m]", "D* edge [N·m]", "면밀도[kg/m²]", "평형 잔차[N/m]", "적층(아래→위)"])
        for s in r["steps"]:
            w2.append([s["step"], s["name"], s["type"], round(s["T"], 1), s["orient"], round(s["thickness_um"], 1),
                       round(s["kappa_unit"], 4), round(s["kappa_edge"], 4), round(s["warp_corner_minus_center_um"]),
                       round(s["warp_PV_linear_um"]), round(s["warp_PV_nonlinear_unit_um"]), s["shape"],
                       round(s["Dstar_unit"], 3), round(s["Dstar_edge"], 3), round(s["mass_kg_m2"], 3),
                       f"{s['equilibrium_residual_N_m']:.1e}", " / ".join(s["layers"])])
    meas = cfg["measured"]
    if meas:
        w3 = wb.create_sheet("Model_vs_Measured")
        w3.append(["Step", "Carrier", "Panel", "실측 warpage [µm]", "모델 warpage [µm]", "차이 [µm]", "실측 흡착", "모델 흡착"])
        for m in meas:
            r = next((x for x in results if x["option"] == m["carrier_option"]), None)
            s = None if r is None else next((x for x in r["steps"] if x["step"] == m["step"]), None)
            if s is None:
                continue
            mod = s["warp_corner_minus_center_um"]
            w3.append([m["step"], m["carrier_option"], m.get("panel_id"), m.get("warpage_um"), round(mod),
                       None if m.get("warpage_um") is None else round(mod - float(m["warpage_um"])), m.get("chuck_result"),
                       None if not s["chuck"] else ("PASS" if s["chuck"]["pass"] else "FAIL")])
    for w in wb.worksheets:
        for c in w[1]:
            c.font = Font(name="Arial", bold=True, color="FFFFFF", size=10); c.fill = PatternFill("solid", fgColor="1F3864")
            c.alignment = Alignment(wrap_text=True, vertical="center")
        for row in w.iter_rows(min_row=2):
            for c in row:
                c.font = Font(name="Arial", size=10, color="C00000" if c.value == "FAIL" else "000000", bold=c.value == "FAIL")
        w.row_dimensions[1].height = 45; w.freeze_panes = "C2"
        for j in range(1, w.max_column + 1):
            w.column_dimensions[get_column_letter(j)].width = 14
        w.column_dimensions["C"].width = 26
    wb.save(os.path.join(OUT, "process_results.xlsx"))

    # ---------------- markdown summary ----------------
    L = [f"# Process warpage & chuck summary\n", f"Input: `{os.path.relpath(XLSX, HERE)}`\n",
         "| Carrier | Step | 공정 | Warpage corner−center (µm) | Placed gap (µm) | Gap after vacuum (µm) | Plenum (kPa) | p_req (kPa) | 흡착 | 응력 |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for r in results:
        for s in r["steps"]:
            c = s["chuck"]
            if c:
                pr = c["p_req_kPa"]; prs = "-" if pr is None else (">1024" if not np.isfinite(pr) else f"{pr:.1f}")
                L.append(f"| {r['option']} | {s['step']} | {s['name']} | {s['warp_corner_minus_center_um']:+.0f} | {c['placed_gap_um']:.0f} | "
                         f"{c['gap_um']:.1f} | {c['plenum_kPa']:.1f} | {prs} | {'PASS' if c['pass'] else '**FAIL**'} | {'PASS' if c['stress_pass'] else '**FAIL** ' + str(c['stress_ratio_max'])} |")
    L.append("\n## Final state\n")
    for r in results:
        s = r["steps"][-1]
        L.append(f"- **{r['option']}** (2nd carrier: {r['carrier2']}): warpage corner−center {s['warp_corner_minus_center_um']:+.0f} µm, "
                 f"PV nonlinear {s['warp_PV_nonlinear_unit_um']:.0f} µm ({s['shape']}), thickness {s['thickness_um']:.0f} µm, runtime {r['runtime_s']} s")
    open(os.path.join(OUT, "summary.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


def run_sweep(cfg, opts):
    lid, vals = SWEEP.split("=")
    vals = [float(v) for v in vals.split(",")]
    jobs = [(o, {lid: v}, True) for o in opts for v in vals]
    with Pool(min(len(jobs), os.cpu_count() or 1)) as p:
        res = p.map(simulate, jobs)
    os.makedirs(OUT, exist_ok=True)
    steps = res[0]["steps"]; xs = np.arange(len(steps))
    fig, axs = plt.subplots(1, len(opts), figsize=(5.2 * len(opts), 4.6), dpi=150, sharey=True, squeeze=False)
    L = [f"# Sweep: {lid} thickness\n", "| Carrier | " + lid + " (µm) | " +
         " | ".join(f"{s['step']}. {s['name']}" for s in steps if s["plot3d"]) + " |",
         "|---|---|" + "---|" * sum(1 for s in steps if s["plot3d"])]
    for a, o in enumerate(opts):
        ax = axs[0, a]; base = COLORS.get(o, FALLBACK[a % 3])
        rs = [r for (j, r) in zip(jobs, res) if j[0] == o]
        for k, (v, r) in enumerate(zip(vals, rs)):
            light = 0.75 * (1 - (k + 1) / len(vals))  # sequential: light -> dark = thin -> thick
            c = matplotlib.colors.to_rgb(base); c = tuple(ci + (1 - ci) * light for ci in c)
            w = [s["warp_corner_minus_center_um"] / 1e3 for s in r["steps"]]
            ax.plot(xs, w, color=c, lw=2, label=f"{v:g} µm")
            L.append(f"| {o} | {v:g} | " + " | ".join(f"{s['warp_corner_minus_center_um']:+.0f}" for s in r["steps"] if s["plot3d"]) + " |")
        ax.axhline(0, color="#8a8984", lw=1)
        for i, s in enumerate(steps):
            if s["plot3d"]:
                ax.axvline(i, color="#d6d5d0", lw=1, ls=":")
        ax.set_title(f"{o}", loc="left", fontsize=11, color=base)
        ax.set_xticks([i for i, s in enumerate(steps) if s["plot3d"]])
        ax.set_xticklabels([f"{s['step']}. {s['name']}" for s in steps if s["plot3d"]], rotation=50, ha="right", fontsize=8)
        ax.grid(True, axis="y", color="#e4e3df"); ax.set_axisbelow(True)
        for sp in ("top", "right"):
            ax.spines[sp].set_visible(False)
        ax.legend(title=f"{lid} 두께", frameon=False, fontsize=8, title_fontsize=8)
    axs[0, 0].set_ylabel("Warpage corner − center (mm)\n+ edges up", color="#52514e")
    fig.suptitle(f"{lid} 두께에 따른 공정별 warpage (점선 = 3D 출력 단계)", x=0.01, ha="left", fontsize=12)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, f"fig_sweep_{lid}.png")); plt.close(fig)
    open(os.path.join(OUT, f"sweep_{lid}.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    cfg = read_template(XLSX)
    opts = [o.strip() for o in str(cfg["panel"]["carrier_options"]).split(",")]
    if SWEEP:
        run_sweep(cfg, opts)
        sys.exit(0)
    with Pool(min(len(opts), os.cpu_count() or 1)) as p:
        results = p.map(simulate, opts)
    write_outputs(results, cfg)
