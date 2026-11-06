"""3D panel-shape visualization: static PNG grid and a self-contained interactive HTML viewer."""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
import plotstyle  # noqa: F401

DIVERGING = LinearSegmentedColormap.from_list("warp", ["#2f5fa7", "#9db5d9", "#f2f1ee", "#e3a59b", "#b23a32"])


def png_grid(results, path, step_filter):
    """Rows = carriers, columns = steps flagged plot3d. Height = free (gravity-free) shape."""
    idx = [i for i, s in enumerate(results[0]["steps"]) if step_filter(s)]
    if not idx:
        return
    nr, nc = len(results), len(idx)
    fig = plt.figure(figsize=(3.4 * nc, 3.1 * nr + 0.8), dpi=150)
    for a, r in enumerate(results):
        for b, i in enumerate(idx):
            s = r["steps"][i]; f = s["field"]
            X, Y = np.meshgrid(np.array(f["x"]), np.array(f["y"]), indexing="ij")
            Z = np.array(f["z"]) / 1e3  # mm
            ax = fig.add_subplot(nr, nc, a * nc + b + 1, projection="3d")
            lim = max(abs(Z.min()), abs(Z.max()), 1e-3)
            ax.plot_surface(X, Y, Z, cmap=DIVERGING, norm=TwoSlopeNorm(0, -lim, lim), rstride=1, cstride=1,
                            linewidth=0, antialiased=True, shade=True)
            ax.set_box_aspect((X.max() - X.min(), Y.max() - Y.min(), 180))
            ax.set_zlim(-lim, lim)
            ax.view_init(elev=24, azim=-58)
            ax.set_xticks([]); ax.set_yticks([])
            ax.tick_params(axis="z", labelsize=6, pad=1)
            pv = Z.max() - Z.min()
            ax.set_title(f"{s['step']}. {s['name']}\nPV {pv:.2f} mm · corner−center {s['warp_corner_minus_center_um']/1e3:+.2f} mm",
                         fontsize=7.5, pad=0)
            if b == 0:
                ax.text2D(-0.08, 0.5, r["option"], transform=ax.transAxes, rotation=90, va="center", fontsize=11)
    fig.suptitle("Panel 3D shape (gravity-free, height vs. centre, mm; z exaggerated, viewed from top side of each step)",
                 x=0.01, ha="left", fontsize=10)
    fig.subplots_adjust(left=0.03, right=0.99, top=0.9, bottom=0.02, wspace=0.05, hspace=0.18)
    fig.savefig(path); plt.close(fig)


VIEWER = r"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Panel Warpage 3D</title>
<script src="https://cdn.jsdelivr.net/npm/plotly.js-dist-min@2.35.2/plotly.min.js"></script>
<style>
:root{--bg:#fcfcfb;--panel:#ffffff;--ink:#0b0b0b;--ink2:#52514e;--line:#e4e3df;--accent:#2a78d6;--fail:#c0392b;--pass:#1b7f4c;}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#1a1a19;--panel:#222220;--ink:#f0efec;--ink2:#c3c2b7;--line:#3a3936;--accent:#3987e5;--fail:#e66767;--pass:#3fbf7f;}}
:root[data-theme="dark"]{--bg:#1a1a19;--panel:#222220;--ink:#f0efec;--ink2:#c3c2b7;--line:#3a3936;--accent:#3987e5;--fail:#e66767;--pass:#3fbf7f;}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 "Pretendard","Noto Sans KR","Malgun Gothic",system-ui,sans-serif}
header{padding:16px 16px 4px}h1{font-size:18px;margin:0 0 2px}header p{margin:0;color:var(--ink2);font-size:12.5px}
.controls{display:flex;flex-wrap:wrap;gap:10px 18px;align-items:center;padding:10px 16px;border-bottom:1px solid var(--line)}
.seg{display:inline-flex;border:1px solid var(--line);border-radius:8px;overflow:hidden}
.seg button{background:var(--panel);color:var(--ink);border:0;padding:6px 12px;cursor:pointer;font:inherit;font-size:13px}
.seg button[aria-pressed="true"]{background:var(--accent);color:#fff}
label{font-size:12.5px;color:var(--ink2);display:inline-flex;gap:6px;align-items:center}
input[type=range]{width:180px}
.stepbar{display:flex;gap:10px;align-items:center;padding:10px 16px;flex-wrap:wrap}
.stepbar input{flex:1;min-width:220px}
.stepname{font-weight:600;min-width:240px}
.grid{display:grid;grid-template-columns:repeat(var(--n),minmax(0,1fr));gap:12px;padding:0 16px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:8px 10px;min-width:0}
.card h2{font-size:14px;margin:2px 0 4px;display:flex;justify-content:space-between;gap:6px;flex-wrap:wrap}
.meta{font-size:12px;color:var(--ink2);display:grid;grid-template-columns:auto 1fr;gap:1px 10px}
.meta b{color:var(--ink);font-weight:600}
.badge{font-size:11.5px;padding:1px 8px;border-radius:10px;border:1px solid currentColor}
.pass{color:var(--pass)}.fail{color:var(--fail)}
.plot{height:420px}
#trend{height:260px;margin:12px 16px 24px;background:var(--panel);border:1px solid var(--line);border-radius:10px}
@media (max-width:900px){.grid{grid-template-columns:1fr}.plot{height:340px}}
</style></head><body>
<header><h1>Panel Warpage 3D 뷰어</h1>
<p>자중을 제외한 자유 형상의 중앙 기준 높이(µm)입니다. 각 공정 시점에 위를 향한 면에서 본 형상이고, 높이는 과장해서 표시합니다. 입력 파일: __SRC__</p></header>
<div class="controls">
  <span class="seg" id="mode"><button data-m="all" aria-pressed="true">3종 비교</button><button data-m="one">단일</button></span>
  <span class="seg" id="carriers"></span>
  <label>높이 과장 <input type="range" id="ex" min="0.05" max="1" step="0.05" value="0.35"></label>
  <label><input type="checkbox" id="samez"> 모든 Carrier 같은 높이 축</label>
  <label><input type="checkbox" id="placed"> 흡착 단계: 척 위 놓인 상태(자중) 표시</label>
</div>
<div class="stepbar"><button id="prev">◀</button><input type="range" id="step" min="0" value="0"><button id="next">▶</button><span class="stepname" id="stepname"></span></div>
<div class="grid" id="grid"></div>
<div id="trend"></div>
<script>
const D = __DATA__;
const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const COL = {"Organic":"#2a78d6","Glass":"#eb6834","Ceramic":"#1baf7a"};
const DIV = [[0,"#2f5fa7"],[0.25,"#9db5d9"],[0.5,"#f2f1ee"],[0.75,"#e3a59b"],[1,"#b23a32"]];
let mode="all", sel=D.results[0].option, step=0;
const stepEl=document.getElementById("step"); stepEl.max=D.results[0].steps.length-1;
const cbox=document.getElementById("carriers");
D.results.forEach(r=>{const b=document.createElement("button");b.textContent=r.option;b.dataset.c=r.option;
  b.setAttribute("aria-pressed", r.option===sel);cbox.appendChild(b);});
function shown(){return mode==="all"?D.results:D.results.filter(r=>r.option===sel);}
function zOf(s){const usePlaced=document.getElementById("placed").checked && s.placed; return usePlaced? s.placed : s.z;}
function fmt(v,d=0){return (v>0?"+":"")+v.toFixed(d);}
function render(){
  const rs=shown(), grid=document.getElementById("grid"); grid.style.setProperty("--n", rs.length);
  cbox.style.display = mode==="all"?"none":"inline-flex";
  const s0=D.results[0].steps[step]; document.getElementById("stepname").textContent=`${s0.step}. ${s0.name}  (${s0.T.toFixed(0)} °C)`;
  let gmax=0; if(document.getElementById("samez").checked){D.results.forEach(r=>{const z=zOf(r.steps[step]).flat();gmax=Math.max(gmax,...z.map(Math.abs));});}
  grid.innerHTML="";
  rs.forEach(r=>{
    const s=r.steps[step], z=zOf(s), flat=z.flat(), lim=gmax||Math.max(1,...flat.map(Math.abs));
    const card=document.createElement("div"); card.className="card";
    const ch=s.chuck? `<span class="badge ${s.chuck.pass?"pass":"fail"}">흡착 ${s.chuck.pass?"PASS":"FAIL"}</span>`:"";
    card.innerHTML=`<h2><span style="color:${COL[r.option]||css('--accent')}">● ${r.option}</span>${ch}</h2>
      <div class="meta"><span>PV</span><b>${(Math.max(...flat)-Math.min(...flat)).toFixed(0)} µm</b>
      <span>코너−중앙</span><b>${fmt(s.cmc)} µm (${s.cmc>0?"가장자리 up":"중앙 up"})</b>
      <span>비선형 PV / 형상</span><b>${s.nl.toFixed(0)} µm · ${s.shape}</b>
      <span>두께 / D*</span><b>${s.t.toFixed(0)} µm · ${s.D.toFixed(1)} N·m</b>
      ${s.chuck?`<span>흡착</span><b>놓인 gap ${s.chuck.placed_gap_um.toFixed(0)} µm → 진공 후 ${s.chuck.gap_um.toFixed(1)} µm, plenum ${s.chuck.plenum_kPa.toFixed(1)} kPa${s.chuck.p_req_kPa!=null?`, 필요 ${isFinite(s.chuck.p_req_kPa)?s.chuck.p_req_kPa.toFixed(0):">1024"} kPa`:""}</b>`:""}</div>
      <div class="plot"></div>`;
    grid.appendChild(card);
    const ex=+document.getElementById("ex").value;
    Plotly.react(card.querySelector(".plot"),[{type:"surface",x:D.x,y:D.y,z:z.map(row=>row), transpose:true,
      colorscale:DIV,cmin:-lim,cmax:lim,cmid:0,colorbar:{title:{text:"µm"},thickness:10,len:0.7},
      hovertemplate:"x %{x:.0f} mm<br>y %{y:.0f} mm<br>z %{z:.0f} µm<extra></extra>",
      contours:{z:{show:true,usecolormap:true,project:{z:false}}}}],
      {margin:{l:0,r:0,t:0,b:0},paper_bgcolor:"rgba(0,0,0,0)",font:{color:css('--ink2'),size:11},
       scene:{aspectmode:"manual",aspectratio:{x:1,y:D.ly/D.lx,z:ex},
         xaxis:{title:"x (mm)",gridcolor:css('--line')},yaxis:{title:"y (mm)",gridcolor:css('--line')},
         zaxis:{title:"z (µm)",range:[-lim*1.05,lim*1.05],gridcolor:css('--line')},
         camera:{eye:{x:-1.5,y:-1.6,z:1.0}}}},{displaylogo:false,responsive:true});
  });
  // trend chart
  const tr=D.results.map(r=>({x:r.steps.map((s,i)=>i),y:r.steps.map(s=>s.cmc/1000),name:r.option,mode:"lines",
     line:{color:COL[r.option],width:2},hovertemplate:"%{text}<br>%{y:.2f} mm<extra>"+r.option+"</extra>",text:r.steps.map(s=>s.step+". "+s.name)}));
  Plotly.react("trend",tr,{margin:{l:56,r:16,t:30,b:30},paper_bgcolor:"rgba(0,0,0,0)",plot_bgcolor:"rgba(0,0,0,0)",
    title:{text:"공정별 warpage (코너−중앙, mm) — 세로선: 현재 단계",x:0.01,font:{size:13,color:css('--ink')}},
    font:{color:css('--ink2'),size:11},xaxis:{gridcolor:css('--line'),zeroline:false,title:""},
    yaxis:{gridcolor:css('--line'),zerolinecolor:css('--ink2')},legend:{orientation:"h",y:1.12,x:1,xanchor:"right"},
    shapes:[{type:"line",x0:step,x1:step,yref:"paper",y0:0,y1:1,line:{color:css('--ink2'),dash:"dot",width:1}}]},
    {displaylogo:false,responsive:true});
}
document.getElementById("mode").onclick=e=>{if(!e.target.dataset.m)return;mode=e.target.dataset.m;
  [...e.currentTarget.children].forEach(b=>b.setAttribute("aria-pressed",b.dataset.m===mode));render();};
cbox.onclick=e=>{if(!e.target.dataset.c)return;sel=e.target.dataset.c;[...cbox.children].forEach(b=>b.setAttribute("aria-pressed",b.dataset.c===sel));render();};
stepEl.oninput=()=>{step=+stepEl.value;render();};
document.getElementById("prev").onclick=()=>{step=Math.max(0,step-1);stepEl.value=step;render();};
document.getElementById("next").onclick=()=>{step=Math.min(+stepEl.max,step+1);stepEl.value=step;render();};
["ex","samez","placed"].forEach(id=>document.getElementById(id).oninput=render);
render();
document.getElementById("trend").on("plotly_click",ev=>{step=ev.points[0].x;stepEl.value=step;render();});
</script></body></html>
"""


def viewer_html(results, path, src_name, stride=1):
    r0 = results[0]["steps"][0]["field"]
    x = np.array(r0["x"])[::stride]; y = np.array(r0["y"])[::stride]
    data = {"x": np.round(x, 1).tolist(), "y": np.round(y, 1).tolist(), "lx": float(x.max() - x.min()),
            "ly": float(y.max() - y.min()), "results": []}
    for r in results:
        steps = []
        for s in r["steps"]:
            z = np.array(s["field"]["z"])[::stride, ::stride]
            e = {"step": s["step"], "name": s["name"], "T": s["T"], "cmc": s["warp_corner_minus_center_um"],
                 "nl": s["warp_PV_nonlinear_unit_um"], "shape": s["shape"], "t": s["thickness_um"], "D": s["Dstar_unit"],
                 "z": np.round(z).astype(int).tolist(), "chuck": None, "placed": None}
            c = s.get("chuck")
            if c:
                e["chuck"] = {k: (None if (isinstance(v, float) and not np.isfinite(v)) and k != "p_req_kPa" else v)
                              for k, v in c.items() if k != "field"}
                if e["chuck"].get("p_req_kPa") == float("inf"):
                    e["chuck"]["p_req_kPa"] = 1e9
                pz = np.array(c["field"]["placed"])[::stride, ::stride] * 1e6
                e["placed"] = np.round(pz).astype(int).tolist()
            steps.append(e)
        data["results"].append({"option": r["option"], "steps": steps})
    html = VIEWER.replace("__DATA__", json.dumps(data, ensure_ascii=False, separators=(",", ":"))).replace("__SRC__", src_name)
    open(path, "w", encoding="utf-8").write(html)
