"""Generate the Excel input template (templates/ICubeE_warpage_input.xlsx).

Row 1 of every table sheet = Korean label + unit, row 2 = machine key read by the tool,
data from row 3. Blue text = input cells. Default values are representative literature
values (placeholders) unless marked otherwise in the 'data_status' column.
"""
import os
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.comments import Comment
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.utils import get_column_letter

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "ICubeE_warpage_input.xlsx")
F = "Arial"
HDR_FILL = PatternFill("solid", fgColor="1F3864")
KEY_FILL = PatternFill("solid", fgColor="D9E1F2")
P_FILL = {"★★★": PatternFill("solid", fgColor="FCE4D6"), "★★": PatternFill("solid", fgColor="FFF2CC"),
          "★": PatternFill("solid", fgColor="E2EFDA")}
INPUT = Font(name=F, size=10, color="0000FF")
TEXT = Font(name=F, size=10, color="000000")
THIN = Border(*(Side(style="thin", color="BFBFBF"),) * 4)
PH = "대표값(교체 필요)"


def table(ws, cols, rows, widths=None, prio_col=None):
    """cols: list of (key, korean_label, comment)"""
    for j, (key, label, cm) in enumerate(cols, 1):
        c = ws.cell(1, j, label); c.font = Font(name=F, bold=True, color="FFFFFF", size=10)
        c.fill = HDR_FILL; c.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center"); c.border = THIN
        if cm:
            c.comment = Comment(cm, "warpage_sim")
        k = ws.cell(2, j, key); k.font = Font(name=F, size=8, color="595959", italic=True); k.fill = KEY_FILL; k.border = THIN
    for i, r in enumerate(rows, 3):
        for j, v in enumerate(r, 1):
            c = ws.cell(i, j, v); c.font = INPUT; c.border = THIN
            c.alignment = Alignment(vertical="center", wrap_text=isinstance(v, str) and len(v) > 18)
        if prio_col is not None:
            p = r[prio_col]
            if p in P_FILL:
                ws.cell(i, prio_col + 1).fill = P_FILL[p]
    ws.row_dimensions[1].height = 42
    ws.freeze_panes = "B3"
    for j, w in enumerate(widths or [], 1):
        ws.column_dimensions[get_column_letter(j)].width = w


def main():
    wb = Workbook()

    # ------------------------------------------------------------------ 안내
    ws = wb.active; ws.title = "안내"
    lines = [
        ("I-Cube E 구조 대면적 Panel Warpage · 진공 흡착 시뮬레이션 입력 템플릿", True),
        ("", False),
        ("사용 방법", True),
        ("1. 각 시트의 파란 글씨 셀을 실제 값으로 바꿉니다. 1행 = 항목/단위, 2행(회색) = 툴이 읽는 키 → 2행은 수정하지 마세요.", False),
        ("2. 'data_status' 열: 기본값은 '대표값(교체 필요)' 입니다. 실측값을 넣으면 '실측' 또는 '업체 Datasheet'로 바꿔 주세요.", False),
        ("3. 우선순위: ★★★ 필수 / ★★ 중요 / ★ 정밀도 향상 (셀 색상 동일)", False),
        ("4. 행 추가/삭제 가능 (빈 행에서 읽기 종료). 재료 이름(id)은 시트 간에 정확히 일치해야 합니다.", False),
        ("5. 실행:  python3 run_process.py templates/ICubeE_warpage_input.xlsx", False),
        ("", False),
        ("시트 구성", True),
        ("Panel        : 패널 크기, Unit 영역, 비교할 Carrier 옵션, 해석 설정", False),
        ("Materials    : 재료 물성 (E, ν, CTE α1/α2, Tg, 밀도, 경화수축, 허용응력)", False),
        ("Mat_T_Table  : (선택) DMA/TMA 온도별 곡선. 값이 있는 재료는 Materials의 Tg 모델 대신 이 표를 보간 사용", False),
        ("Carrier_Stack: Carrier 옵션별 적층 (유기 = PPG/Cu 적층, Glass, Ceramic)", False),
        ("Layers       : Carrier 위 적층층 정의 (두께, 기지재, 포함재와 면적비율 - Unit 영역/Edge 영역)", False),
        ("Process      : 공정 순서 (층 생성 온도, 온도 이력, Grinding, Carrier 분리, 반전, 흡착 판정)", False),
        ("Equipment    : 흡착 설비별 진공 조건과 설비 상수 (포착 gap, 누설계수 β) ", False),
        ("Measured     : (선택) 실측 warpage와 흡착 결과 → 모델 보정/검증용", False),
        ("", False),
        ("모델링 가정", True),
        ("• 각 층은 생성 온도(경화/몰드 온도)에서 무응력으로 패널 형상에 붙고, 이후 온도이력을 따라갑니다 (온도의존 탄성, 점탄성 완화는 미반영).", False),
        ("• Die/Cu post/Via/Cu 배선이 섞인 층은 면적비율로 균질화합니다: voigt = 연속 배선/평면, halpin = 기둥/블록(via, post, die).", False),
        ("• Unit 영역(die 배열)과 Edge 영역(패널 외곽 frame)을 별도 적층으로 계산 후 판 FE에서 결합합니다 (1/4 대칭).", False),
        ("• 흡착: 자중 → 진공 램프 → 포착 gap 이하 영역에 흡착력 → 밀폐 영역 배기 → 덮이지 않은 척 면 누설로 진공 저하.", False),
        ("• Equipment의 포착 gap/β는 설비 고유 상수 → 흡착 성공/실패 이력(Measured)으로 보정해야 판정 신뢰도가 확보됩니다.", False),
    ]
    for i, (t, b) in enumerate(lines, 1):
        c = ws.cell(i, 1, t); c.font = Font(name=F, size=12 if i == 1 else 10, bold=b)
    ws.column_dimensions["A"].width = 130
    r = len(lines) + 2
    ws.cell(r, 1, "범례").font = Font(name=F, bold=True, size=10)
    ws.cell(r + 1, 1, "파란 글씨 = 입력값 (수정 대상)").font = INPUT
    for k, (p, fill) in enumerate(P_FILL.items()):
        c = ws.cell(r + 2 + k, 1, f"{p}  우선순위 셀 색상"); c.fill = fill; c.font = TEXT

    # ------------------------------------------------------------------ Panel
    ws = wb.create_sheet("Panel")
    table(ws, [("key", "항목 키", None), ("value", "값", None), ("unit", "단위", None), ("note", "설명", None)], [
        ("panel_x_mm", 415, "mm", "패널 크기 X (사용자 제공)"),
        ("panel_y_mm", 512, "mm", "패널 크기 Y (사용자 제공)"),
        ("unit_region_x_mm", 395, "mm", "Unit(die) 배열 영역 X — 외곽 edge frame 제외 영역. 대표값(교체 필요)"),
        ("unit_region_y_mm", 492, "mm", "Unit(die) 배열 영역 Y. 대표값(교체 필요)"),
        ("T_start_C", 25, "°C", "1st Carrier 무응력 기준 온도"),
        ("carrier_options", "Organic,Glass,Ceramic", "-", "비교할 1st Carrier 옵션 (Carrier_Stack의 carrier_option 이름, 쉼표 구분)"),
        ("carrier2_option", "SAME", "-", "2nd Carrier: SAME = 1st와 동일, 또는 Carrier_Stack 옵션 이름 (확인 필요)"),
        ("mesh", 24, "-", "판 FE 1/4 격자 분할 수 (클수록 정밀/느림)"),
        ("find_required_pressure", "YES", "YES/NO", "흡착 단계마다 필요 진공압 탐색 (시간 증가)"),
    ], widths=[26, 24, 9, 90])

    # ------------------------------------------------------------------ Materials
    ws = wb.create_sheet("Materials")
    mcols = [
        ("id", "재료 ID", "시트 간 참조 이름"), ("category", "분류", None),
        ("E_glassy_GPa", "E (Tg 이하)\n[GPa]", "DMA storage modulus, 상온 부근"),
        ("E_rubbery_GPa", "E (Tg 이상)\n[GPa]", "Tg 전이가 없으면 비움"),
        ("Tg_C", "Tg\n[°C]", "DMA tanδ peak 또는 TMA 변곡점"), ("Tg_width_C", "Tg 전이폭\n[°C]", "기본 8"),
        ("nu", "ν\n[-]", None),
        ("cte1_x_ppm", "CTE α1 X\n[ppm/K]", "Tg 이하, TMA. 순간(tangent) CTE"), ("cte1_y_ppm", "CTE α1 Y\n[ppm/K]", "비우면 X와 동일"),
        ("cte2_x_ppm", "CTE α2 X\n[ppm/K]", "Tg 이상"), ("cte2_y_ppm", "CTE α2 Y\n[ppm/K]", None),
        ("density_kg_m3", "밀도\n[kg/m³]", "자중 계산용"),
        ("cure_shrinkage_pct", "경화수축 (선형, 겔화 이후)\n[%]", "층 생성 직후 적용되는 면내 선형 수축률. 체적수축의 약 1/3, 겔화 이후 분만"),
        ("allowable_MPa", "허용응력\n[MPa]", "흡착 평탄화 시 응력 판정 (취성재: Weibull 하위값)"),
        ("priority", "우선순위", None), ("data_status", "데이터 상태", None), ("source", "출처/측정법", None), ("note", "비고", None)]
    mats = [
        ("PPG", "Carrier(유기)", 24, 12, 230, 8, 0.15, 12, 13, 30, 32, 1900, 0, 300, "★★★", PH, "DMA 3점굽힘, TMA", "Prepreg 경사/위사 방향 CTE 구분 입력"),
        ("Cu_foil", "Carrier(유기)", 120, None, None, None, 0.34, 17, None, None, None, 8900, 0, None, "★★", PH, "문헌", "Carrier 내 Cu 평면층"),
        ("Glass_carrier", "Carrier", 74, None, None, None, 0.22, 8.0, None, None, None, 2380, 0, 50, "★★★", PH, "업체 Datasheet", "Glass 등급별 CTE 3~10 ppm. 허용응력 = 엣지 상태 반영 설계값"),
        ("Ceramic_carrier", "Carrier", 340, None, None, None, 0.22, 7.0, None, None, None, 3750, 0, 150, "★★★", PH, "업체 Datasheet", "96% Al2O3 가정"),
        ("Release1", "접착/Release", 2.5, 0.05, 180, 10, 0.35, 60, None, 200, None, 1200, 0, None, "★★★", PH, "DMA, TMA", "1st Carrier release/temporary bonding층. 고온 연화 여부가 결과를 좌우"),
        ("Adhesive2", "접착/Release", 2.0, 0.02, 150, 10, 0.35, 70, None, 220, None, 1200, 0, None, "★★★", PH, "DMA, TMA", "2nd Carrier 접합 접착제"),
        ("LPR", "유전체", 3.5, 1.0, 230, 10, 0.34, 45, None, 120, None, 1400, 0.05, None, "★★★", PH, "DMA, TMA, 경화수축", "LRDL/URDL 감광성 유전체"),
        ("Cu_plated", "금속", 110, None, None, None, 0.34, 17, None, None, None, 8900, 0, None, "★★", PH, "문헌/나노인덴테이션", "RDL 배선, Via, Cu Post"),
        ("Si", "Die", 130, None, None, None, 0.28, 2.6, None, None, None, 2330, 0, None, "★", PH, "문헌", "Bridge Die, IOD/CCD"),
        ("EMC1", "EMC", 24, 0.8, 155, 8, 0.30, 8, None, 30, None, 2000, 0.05, 80, "★★★", PH, "DMA, TMA, 경화수축(PVT)", "1st Mold"),
        ("EMC2", "EMC", 22, 0.7, 150, 8, 0.30, 9, None, 33, None, 1950, 0.05, 80, "★★★", PH, "DMA, TMA, 경화수축(PVT)", "2nd Mold (MUF이면 die 사이도 충진)"),
        ("Underfill", "Underfill", 9, 0.3, 120, 8, 0.33, 25, None, 90, None, 1700, 0.1, None, "★★", PH, "DMA, TMA", "CoP Underfill (CUF인 경우)"),
    ]
    table(ws, mcols, mats, widths=[16, 13, 10, 10, 8, 9, 6, 9, 9, 9, 9, 9, 13, 10, 9, 16, 20, 46], prio_col=14)
    dv = DataValidation(type="list", formula1='"★★★,★★,★"', allow_blank=True); ws.add_data_validation(dv); dv.add("O3:O200")
    dv2 = DataValidation(type="list", formula1=f'"{PH},실측,업체 Datasheet,문헌"', allow_blank=True); ws.add_data_validation(dv2); dv2.add("P3:P200")

    # ------------------------------------------------------------------ Mat_T_Table
    ws = wb.create_sheet("Mat_T_Table")
    rows = [("EXAMPLE_EMC", T, E, a, None, "예시 형식 (참조되지 않는 ID). 실제 재료 ID로 입력하면 Materials 값을 대체")
            for T, E, a in [(-50, 26, 7.5), (25, 24, 8), (100, 21, 9), (140, 12, 14), (155, 3, 22), (175, 0.9, 30), (260, 0.6, 31)]]
    table(ws, [("material_id", "재료 ID", None), ("T_C", "온도\n[°C]", None), ("E_GPa", "E\n[GPa]", "DMA storage modulus"),
               ("cte_x_ppm", "순간 CTE X\n[ppm/K]", "TMA 곡선 미분값 (평균 CTE 아님)"), ("cte_y_ppm", "순간 CTE Y\n[ppm/K]", "비우면 X와 동일"),
               ("note", "비고", None)], rows, widths=[16, 9, 9, 12, 12, 70])

    # ------------------------------------------------------------------ Carrier_Stack
    ws = wb.create_sheet("Carrier_Stack")
    cs = [("Organic", 1, "OC_Cu1", "Cu_foil", None, None, None, 18, "아래→위 순서. Cu 평면 (잔존율 100%)"),
          ("Organic", 2, "OC_PPG1", "PPG", None, None, None, 300, ""),
          ("Organic", 3, "OC_Cu2", "Cu_foil", None, None, None, 18, ""),
          ("Organic", 4, "OC_PPG2", "PPG", None, None, None, 300, ""),
          ("Organic", 5, "OC_Cu3", "Cu_foil", None, None, None, 18, ""),
          ("Organic", 6, "OC_PPG3", "PPG", None, None, None, 300, ""),
          ("Organic", 7, "OC_Cu4", "Cu_foil", None, None, None, 18, "총 972 µm (대표값). Cu 잔존율 < 100%면 matrix=PPG, incl=Cu_foil로 입력"),
          ("Glass", 1, "GC", "Glass_carrier", None, None, None, 1000, "두께 대표값(교체 필요)"),
          ("Ceramic", 1, "CC", "Ceramic_carrier", None, None, None, 1000, "두께 대표값(교체 필요)")]
    table(ws, [("carrier_option", "Carrier 옵션", None), ("order", "순서\n(아래→위)", None), ("layer_id", "층 ID", None),
               ("matrix", "기지재", "Materials id"), ("incl1", "포함재", "Materials id"), ("incl1_pct", "포함재 면적비율\n[%]", None),
               ("rule", "혼합규칙", "voigt / halpin / reuss"), ("thickness_um", "두께\n[µm]", None), ("note", "비고", None)],
          cs, widths=[14, 9, 11, 16, 12, 12, 10, 10, 60])

    # ------------------------------------------------------------------ Layers
    ws = wb.create_sheet("Layers")
    L = [
        ("REL1", "CARRIER1", "1st Carrier release/temporary bonding층", 10, "Release1", None, None, None, None, None, None, None, "voigt", "★★★", ""),
        ("LRDL_L", "LRDL", "LRDL Cu 배선층 (LPR 내 Cu line)", 5, "LPR", None, "Cu_plated", 55, 30, None, None, None, "voigt", "★★★", "Cu 잔존율 Unit/Edge 영역 구분"),
        ("LRDL_D", "LRDL", "LRDL 유전체 + Via", 7, "LPR", None, "Cu_plated", 5, 2, None, None, None, "halpin", "★★★", "Via 면적비율"),
        ("M1_DIE", "MOLD1", "Bridge Die 높이 구간 (Si + Cu Post + EMC1)", 60, "EMC1", None, "Si", 8, 0, "Cu_plated", 6, 0, "halpin", "★★★", "Bridge die(+DAF) 두께, die/post 면적비율"),
        ("M1_TOP", "MOLD1", "Bridge Die 위 몰드 (Cu Post + EMC1) — grinding 대상", 200, "EMC1", None, "Cu_plated", 6, 0, None, None, None, "halpin", "★★★", "몰드 직후 두께. Grinding 후 두께는 Process에 입력"),
        ("URDL1_L", "URDL", "URDL 1층 Cu 배선", 5, "LPR", None, "Cu_plated", 50, 30, None, None, None, "voigt", "★★★", ""),
        ("URDL1_D", "URDL", "URDL 1층 유전체 + Via", 7, "LPR", None, "Cu_plated", 5, 2, None, None, None, "halpin", "★★★", ""),
        ("URDL2_L", "URDL", "URDL 2층 Cu 배선 + 패드", 5, "LPR", None, "Cu_plated", 45, 30, None, None, None, "voigt", "★★★", ""),
        ("URDL2_D", "URDL", "URDL 2층 유전체 + Via", 7, "LPR", None, "Cu_plated", 5, 2, None, None, None, "halpin", "★★★", ""),
        ("UBUMP", "COP", "CoP 범프 갭 (Underfill + 범프), Edge는 EMC2", 30, "Underfill", "EMC2", "Cu_plated", 8, 0, None, None, None, "halpin", "★★", "CUF: die 아래 underfill, 나머지 EMC2"),
        ("COP_DIE", "COP", "IOD/CCD Die 높이 구간 (Si + EMC2)", 400, "EMC2", None, "Si", 65, 0, None, None, None, "halpin", "★★★", "Die 두께, Unit 내 die 면적비율"),
        ("M2_TOP", "MOLD2", "Die 위 2nd Mold (over-mold)", 100, "EMC2", None, None, None, None, None, None, None, "voigt", "★★★", "Over-mold 두께"),
        ("ADH2", "CARRIER2", "2nd Carrier 접합 접착층", 20, "Adhesive2", None, None, None, None, None, None, None, "voigt", "★★★", "2nd Carrier 본체는 Panel.carrier2_option 적층 사용"),
    ]
    table(ws, [("layer_id", "층 ID", None), ("group", "그룹", "REMOVE 단계에서 그룹명으로 한번에 제거 가능"),
               ("description", "설명", None), ("thickness_um", "두께\n[µm]", "생성 시 두께"),
               ("matrix_unit", "기지재\n(Unit 영역)", "Materials id"), ("matrix_edge", "기지재\n(Edge 영역)", "비우면 Unit과 동일"),
               ("incl1", "포함재1", "Materials id"), ("incl1_unit_pct", "포함재1 비율\nUnit [%]", "면적비율 (Cu 잔존율, die 점유율 등)"),
               ("incl1_edge_pct", "포함재1 비율\nEdge [%]", None), ("incl2", "포함재2", None), ("incl2_unit_pct", "포함재2 비율\nUnit [%]", None),
               ("incl2_edge_pct", "포함재2 비율\nEdge [%]", None), ("rule", "혼합규칙", "voigt: 연속 배선/평면, halpin: 기둥/블록, reuss: 하한"),
               ("priority", "우선순위", None), ("note", "비고", None)],
          L, widths=[11, 11, 42, 9, 12, 12, 11, 11, 11, 11, 11, 11, 9, 9, 44], prio_col=13)
    dv3 = DataValidation(type="list", formula1='"voigt,halpin,reuss"', allow_blank=True); ws.add_data_validation(dv3); dv3.add("M3:M200")

    # ------------------------------------------------------------------ Process
    ws = wb.create_sheet("Process")
    P = [
        (1, "1st Carrier 준비", "START", "REL1", 25, None, None, "Carrier_Stack + 지정층을 T에서 무응력 생성"),
        (2, "LRDL 형성 (LPR 경화)", "ADD", "LRDL_L,LRDL_D", 200, None, None, "T = LPR 경화 온도 (무응력 생성 온도)"),
        (3, "냉각", "TEMP", None, 25, None, None, ""),
        (4, "Bridge Die 실장 (흡착)", "CHUCK", None, 25, None, "EQ_DB", "T = 척 온도"),
        (5, "1st Mold + PMC", "ADD", "M1_DIE,M1_TOP", 175, None, None, "Bridge die, Cu post는 몰드 시점에 패널 강성에 기여"),
        (6, "냉각", "TEMP", None, 25, None, None, ""),
        (7, "Grinding 전 흡착", "CHUCK", None, 25, None, "EQ_GR", ""),
        (8, "Grinding", "GRIND", "M1_TOP", 25, 40, None, "value = grinding 후 남는 두께 [µm]"),
        (9, "URDL 1층 (경화)", "ADD", "URDL1_L,URDL1_D", 200, None, None, ""),
        (10, "냉각", "TEMP", None, 25, None, None, ""),
        (11, "URDL 2층 노광 (흡착)", "CHUCK", None, 25, None, "EQ_LITHO", ""),
        (12, "URDL 2층 (경화)", "ADD", "URDL2_L,URDL2_D", 200, None, None, ""),
        (13, "냉각", "TEMP", None, 25, None, None, ""),
        (14, "CoP 본딩 (흡착)", "CHUCK", None, 25, None, "EQ_COP", "본딩 스테이지 온도로 수정"),
        (15, "CoP Reflow", "TEMP", None, 250, None, None, "Reflow 피크 온도"),
        (16, "냉각", "TEMP", None, 25, None, None, ""),
        (17, "Underfill 경화", "ADD", "UBUMP", 150, None, None, "MUF이면 이 단계를 2nd Mold로 통합"),
        (18, "2nd Mold + PMC", "ADD", "COP_DIE,M2_TOP", 175, None, None, ""),
        (19, "냉각", "TEMP", None, 25, None, None, ""),
        (20, "2nd Carrier 접합 전 흡착", "CHUCK", None, 25, None, "EQ_BOND2", ""),
        (21, "반전", "FLIP", None, None, None, None, "이후 보는 방향 기준 warpage 부호 반전"),
        (22, "2nd Carrier 접합", "ADD_CARRIER2", "ADH2", 120, None, None, "접합 온도 (UV 접합이면 25)"),
        (23, "냉각", "TEMP", None, 25, None, None, ""),
        (24, "1st Carrier 분리", "REMOVE", "CARRIER1", 25, None, None, "그룹명/층ID. 1st Carrier 적층 전체 = CARRIER1"),
        (25, "MIP Bump 공정 (흡착)", "CHUCK", None, 25, None, "EQ_BUMP", ""),
        (26, "MIP Bump Reflow", "TEMP", None, 250, None, None, ""),
        (27, "냉각 (최종)", "TEMP", None, 25, None, None, ""),
    ]
    table(ws, [("step", "No", None), ("name", "공정명", None),
               ("type", "유형", "START / ADD / ADD_CARRIER2 / TEMP / GRIND / REMOVE / FLIP / CHUCK"),
               ("targets", "대상 층/그룹", "쉼표 구분"), ("T_C", "온도\n[°C]", "ADD: 생성(무응력) 온도, TEMP: 목표 온도, CHUCK: 척 온도"),
               ("value", "값", "GRIND: 남는 두께 [µm]"), ("equipment", "설비 ID", "CHUCK 단계: Equipment 시트 ID"), ("note", "비고", None)],
          P, widths=[5, 26, 15, 20, 9, 8, 12, 55])
    dv4 = DataValidation(type="list", formula1='"START,ADD,ADD_CARRIER2,TEMP,GRIND,REMOVE,FLIP,CHUCK"', allow_blank=True)
    ws.add_data_validation(dv4); dv4.add("C3:C300")

    # ------------------------------------------------------------------ Equipment
    ws = wb.create_sheet("Equipment")
    E = [(eid, name, "Porous ceramic", 80, 10, 30, 20, "대표값(교체 필요) — 흡착 이력으로 보정")
         for eid, name in [("EQ_DB", "Bridge Die Bonder"), ("EQ_GR", "Grinder"), ("EQ_LITHO", "노광기"),
                           ("EQ_COP", "CoP Bonder"), ("EQ_BOND2", "2nd Carrier Bonder"), ("EQ_BUMP", "Bump 공정")]]
    table(ws, [("equipment", "설비 ID", None), ("name", "설비명", None), ("chuck_type", "척 형식", "Porous / Groove / Pin 등"),
               ("vacuum_kPa", "공급 진공\n[kPa]", "게이지 기준 진공도"),
               ("capture_gap_um", "포착 gap\n[µm]", "이 gap 이하에서 흡착력이 작용 (설비 상수, 보정 대상)"),
               ("leak_beta", "누설계수 β\n[-]", "덮이지 않은 척 면의 누설/펌프 능력 비. 0 = 누설 없음 (보정 대상)"),
               ("seal_tol_um", "흡착 판정 허용 gap\n[µm]", "최대 잔여 gap 판정 기준"), ("note", "비고", None)],
          E, widths=[11, 20, 15, 10, 10, 10, 12, 40])

    # ------------------------------------------------------------------ Measured
    ws = wb.create_sheet("Measured")
    table(ws, [("step", "공정 No", "Process 시트 No"), ("carrier_option", "Carrier 옵션", None), ("panel_id", "패널 ID", None),
               ("T_C", "측정 온도\n[°C]", None), ("warpage_um", "Warpage\n(보는 방향 기준, +가장자리 up) [µm]", "코너 - 중앙 높이차"),
               ("shape", "형상", "bowl / dome / saddle / cylinder"), ("chuck_result", "흡착 결과", "PASS / FAIL"),
               ("note", "비고", None)],
          [(7, "Glass", "예시-001", 25, 850, "bowl", "PASS", "예시 행 — 실제 데이터로 교체/삭제")],
          widths=[8, 13, 12, 10, 18, 10, 10, 40])

    wb.save(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
