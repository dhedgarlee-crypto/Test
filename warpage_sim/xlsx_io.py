"""Read the Excel input template into simulation objects."""
from openpyxl import load_workbook
from materials import Material, TabulatedMaterial, CompositeMaterial


def _rows(ws):
    keys = [c.value for c in ws[2]]
    out = []
    for r in ws.iter_rows(min_row=3, values_only=True):
        if r[0] is None or str(r[0]).strip() == "":
            break
        out.append({k: (v.strip() if isinstance(v, str) else v) for k, v in zip(keys, r) if k})
    return out


def _num(v, default=None):
    return default if v is None or v == "" else float(v)


def read_template(path):
    wb = load_workbook(path, data_only=True)
    panel = {r["key"]: r["value"] for r in _rows(wb["Panel"])}

    mats = {}
    for r in _rows(wb["Materials"]):
        E_r = _num(r.get("E_rubbery_GPa"))
        mats[r["id"]] = Material(
            name=r["id"], E_glassy=_num(r["E_glassy_GPa"]) * 1e9, nu=_num(r["nu"]),
            alpha_x_glassy=_num(r["cte1_x_ppm"]) * 1e-6, rho=_num(r["density_kg_m3"]),
            alpha_y_glassy=None if r.get("cte1_y_ppm") is None else _num(r["cte1_y_ppm"]) * 1e-6,
            E_rubbery=None if E_r is None else E_r * 1e9,
            alpha_x_rubbery=None if r.get("cte2_x_ppm") is None else _num(r["cte2_x_ppm"]) * 1e-6,
            alpha_y_rubbery=None if r.get("cte2_y_ppm") is None else _num(r["cte2_y_ppm"]) * 1e-6,
            Tg=_num(r.get("Tg_C"), 1e9), Tg_width=_num(r.get("Tg_width_C"), 8.0),
            allowable_stress=None if r.get("allowable_MPa") is None else _num(r["allowable_MPa"]) * 1e6,
            cure_shrinkage=_num(r.get("cure_shrinkage_pct"), 0.0) * 1e-2)
    tab = {}
    for r in _rows(wb["Mat_T_Table"]):
        tab.setdefault(r["material_id"], []).append(r)
    for mid, rs in tab.items():
        if mid in mats:
            mats[mid] = TabulatedMaterial(
                mats[mid], [_num(x["T_C"]) for x in rs], [_num(x["E_GPa"]) * 1e9 for x in rs],
                [_num(x["cte_x_ppm"]) * 1e-6 for x in rs],
                [(_num(x["cte_y_ppm"]) if x.get("cte_y_ppm") is not None else _num(x["cte_x_ppm"])) * 1e-6 for x in rs])

    def mat(mid, where):
        if mid not in mats:
            raise KeyError(f"{where}: material '{mid}' not found in Materials sheet")
        return mats[mid]

    def build(lid, matrix, incls, rule):
        incls = [(mat(m, lid), f / 100.0) for m, f in incls if m and f]
        if not incls:
            return mat(matrix, lid)
        return CompositeMaterial(lid, mat(matrix, lid), incls, rule or "voigt")

    carriers = {}
    for r in sorted(_rows(wb["Carrier_Stack"]), key=lambda r: (r["carrier_option"], r["order"])):
        m = build(r["layer_id"], r["matrix"], [(r.get("incl1"), _num(r.get("incl1_pct"), 0))], r.get("rule"))
        carriers.setdefault(r["carrier_option"], []).append((r["layer_id"], m, _num(r["thickness_um"]) * 1e-6))

    layers = {}
    for r in _rows(wb["Layers"]):
        zones = {}
        for z in ("unit", "edge"):
            mx = r.get(f"matrix_{z}") or r["matrix_unit"]
            inc = [(r.get("incl1"), _num(r.get(f"incl1_{z}_pct"), 0)), (r.get("incl2"), _num(r.get(f"incl2_{z}_pct"), 0))]
            zones[z] = build(r["layer_id"], mx, inc, r.get("rule"))
        layers[r["layer_id"]] = {"group": r.get("group") or r["layer_id"], "t": _num(r["thickness_um"]) * 1e-6,
                                 "mat": zones, "desc": r.get("description", "")}

    steps = _rows(wb["Process"])
    for s in steps:
        s["targets"] = [t.strip() for t in str(s.get("targets") or "").split(",") if t.strip()]
    equipment = {r["equipment"]: r for r in _rows(wb["Equipment"])}
    measured = _rows(wb["Measured"])
    return {"panel": panel, "materials": mats, "carriers": carriers, "layers": layers,
            "steps": steps, "equipment": equipment, "measured": measured}
