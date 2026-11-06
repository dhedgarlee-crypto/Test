"""Information checklist for a reliable warpage / chuck simulation (used by make_template.py).
Columns: category, item, why it matters, priority, form/unit, recommended method/conditions,
where it goes in the template, prefilled user info."""

U = "사용자 제공"
ITEMS = [
    # ---------------- A. 구조/형상 ----------------
    ("A. 구조·형상", "패널 크기, 두께 공차", "판 강성·자중·흡착 면적의 기준", "★★★", "mm", "도면", "Panel", "415 × 512 mm (사용자 제공)"),
    ("A. 구조·형상", "Unit 배열 영역 크기 / 외곽 frame 폭, Unit 크기·개수·배치도", "Unit 영역과 Edge 영역의 강성·CTE가 달라 형상(돔/안장)이 바뀜", "★★★", "도면(mm)", "패널 레이아웃 도면", "Panel", None),
    ("A. 구조·형상", "Edge frame dummy 패턴 (Cu dummy, dummy die 유무)", "Edge 영역 강성/CTE → 가장자리 들뜸(흡착 누설)에 직접 영향", "★★", "도면, 잔존율 %", "레이아웃", "Layers (Edge 비율)", None),
    ("A. 구조·형상", "Bridge Die 크기·두께, Unit당 개수·위치, DAF 두께", "1st Mold 층의 국부 강성·저CTE 성분", "★★★", "mm, µm, 개수", "도면", "Layers: M1_DIE", None),
    ("A. 구조·형상", "Cu Post 직경·높이·pitch (면적비율)", "1st Mold 층 등가 E/CTE", "★★★", "µm, %", "도면", "Layers: M1_DIE, M1_TOP", None),
    ("A. 구조·형상", "IOD/CCD Die 크기·두께, Unit당 개수·배치, die 간 간격", "두꺼운 die(저CTE·고강성)가 CoP 전/후 warpage 변곡점을 결정", "★★★", "mm, µm", "도면", "Layers: COP_DIE", "Die 두께 약 400 µm (사용자 제공, 확인 필요)"),
    ("A. 구조·형상", "μBump 높이·직경·pitch·개수, 재질 (Cu pillar + solder 비율)", "Die-패널 결합 강성, 범프 구간 등가물성", "★★", "µm, %", "도면", "Layers: UBUMP", None),
    ("A. 구조·형상", "MIP Bump 높이·pitch·면적비율", "최종 단계 하중(작음), Bump 신뢰성 해석 시 필요", "★", "µm", "도면", "(참고)", None),
    ("A. 구조·형상", "1st Mold 두께 (몰드 직후 / grinding 후)", "Grinding으로 강성 h³ 감소, 잔류응력 해방", "★★★", "µm", "단면 측정", "Layers: M1_TOP, Process: GRIND", None),
    ("A. 구조·형상", "2nd Mold over-mold 두께, 2nd Mold grinding 유무", "상부 비대칭 층 두께 → 2nd Mold 후 warpage", "★★★", "µm", "단면 측정", "Layers: M2_TOP", None),
    ("A. 구조·형상", "LRDL/URDL 층별 두께 (유전체, Cu 배선)", "RDL 층의 굽힘 모멘트 기여", "★★★", "µm", "단면 SEM", "Layers", None),
    ("A. 구조·형상", "층별 Cu 잔존율 (Unit/Edge 구분, 가능하면 영역 맵)", "Cu(17 ppm)는 고강성·고CTE → warpage 주요 인자", "★★★", "%", "Gerber 추출", "Layers (incl1 비율)", None),
    ("A. 구조·형상", "층별 Via 면적비율", "유전체 층 등가물성", "★★", "%", "Gerber 추출", "Layers", None),
    # ---------------- B. Carrier ----------------
    ("B. Carrier", "유기 Carrier stack-up: PPG 종류(glass cloth style), 층수·두께, Cu 층 두께·잔존율", "유기 Carrier 등가 E/CTE 계산", "★★★", "µm, %", "Carrier 사양서", "Carrier_Stack", "PPG + Cu 적층 구조 (사용자 제공)"),
    ("B. Carrier", "유기 Carrier 적층체 등가물성 실측: E(T), CTE x/y(T)", "적층 계산보다 실측 등가값이 훨씬 신뢰도 높음", "★★★", "곡선", "DMA 3점굽힘 1 Hz 3 °C/min −50~260 °C, TMA 5 °C/min", "Materials / Mat_T_Table", None),
    ("B. Carrier", "Glass 제품명·등급, CTE(T), E, ν, 두께", "CTE 3~10 ppm 범위로 결과가 크게 바뀜", "★★★", "ppm/K, GPa, µm", "업체 Datasheet", "Materials: Glass_carrier", None),
    ("B. Carrier", "Ceramic 재질 (Al2O3 %, AlN 등), CTE(T), E, ν, 두께", "고강성 → 흡착 포착 실패 위험 (300 mm 이력)", "★★★", "ppm/K, GPa, µm", "업체 Datasheet", "Materials: Ceramic_carrier", "300×300 mm에서 warpage 작지만 진공 미형성 이력 (사용자 제공)"),
    ("B. Carrier", "Carrier 초기 평탄도/warpage (입고 상태)", "초기 형상 오프셋", "★★", "µm, 형상", "3D 형상 측정", "Measured", None),
    ("B. Carrier", "Glass/Ceramic 파괴강도 (엣지 가공 조건별, Weibull)", "흡착 평탄화 시 크랙 판정", "★★", "MPa, Weibull m", "4점 굽힘 (n≥15)", "Materials: allowable", None),
    ("B. Carrier", "2nd Carrier 종류·두께", "Carrier 교체 후 warpage, 최종 공정 흡착", "★★★", "-", "공정 사양", "Panel: carrier2_option", None),
    # ---------------- C. 접착/Release ----------------
    ("C. 접착·Release", "1st Release/temporary bonding 재료: 두께, E(T), CTE(T), Tg", "고온에서 연화되면 Carrier와 패널이 분리 거동 → 결과 좌우", "★★★", "µm, 곡선", "DMA 인장/전단, TMA", "Materials: Release1, Layers: REL1", None),
    ("C. 접착·Release", "2nd Carrier 접착제: 두께, E(T), CTE(T), Tg", "Carrier 교체 후 결합 강성", "★★★", "µm, 곡선", "DMA, TMA", "Materials: Adhesive2", None),
    ("C. 접착·Release", "접합·분리 방식과 온도 (Laser / Thermal / UV / 기계식)", "층 생성/제거 온도", "★★★", "°C", "공정 사양", "Process: ADD_CARRIER2, REMOVE", None),
    # ---------------- D. 유전체 ----------------
    ("D. 유전체 (LPR)", "E(T), CTE α1/α2, Tg, ν", "RDL 층 열변형", "★★★", "곡선", "DMA 인장 필름, TMA 필름", "Materials: LPR", None),
    ("D. 유전체 (LPR)", "경화 프로파일 (온도·시간), 경화 수축률", "층 생성(무응력) 온도와 수축 eigenstrain", "★★★", "°C, %", "공정 사양, 필름 수축 측정", "Process T, Materials 경화수축", None),
    ("D. 유전체 (LPR)", "점탄성 (DMA 주파수 스윕 → master curve)", "고온 hold 중 응력 완화", "★", "Prony 계수", "DMA multi-frequency", "(향후)", None),
    # ---------------- E. Cu ----------------
    ("E. Cu", "도금 Cu E, 항복강도·경화곡선(T)", "고온 소성 → 잔류 warpage", "★★", "GPa, MPa", "인장시험/나노인덴테이션", "Materials: Cu_plated", None),
    ("E. Cu", "도금 후 annealing 조건 / 수축", "Grain growth 수축 → 추가 warpage", "★", "°C, %", "공정 사양", "(향후)", None),
    # ---------------- F. EMC ----------------
    ("F. EMC (1st/2nd)", "E(T) DMA 전체 곡선 (−50~260 °C)", "Tg 부근 강성 변화가 warpage 형성 지배", "★★★", "곡선", "DMA 3점굽힘 1 Hz 3 °C/min", "Mat_T_Table: EMC1, EMC2", None),
    ("F. EMC (1st/2nd)", "CTE α1/α2 TMA 곡선, Tg", "CTE mismatch 주인자", "★★★", "곡선", "TMA 5 °C/min, 2nd heating", "Mat_T_Table", None),
    ("F. EMC (1st/2nd)", "경화 수축 (겔화 이후 선형 수축)", "몰드 직후 warpage의 큰 비중", "★★★", "%", "PVT 또는 Shadow moiré 역추정", "Materials 경화수축", None),
    ("F. EMC (1st/2nd)", "몰드/PMC 조건 (온도·시간·압력)", "층 생성 온도, 경화도", "★★★", "°C, min", "공정 사양", "Process", None),
    ("F. EMC (1st/2nd)", "점탄성 master curve (응력 완화, Prony, WLF/shift)", "Reflow 다회에서 응력 완화 → 현재 모델 과대예측 보정", "★★", "Prony 계수", "DMA 주파수/온도 스윕", "(향후 모델 확장)", None),
    ("F. EMC (1st/2nd)", "Filler 함량, 흡습 팽창 계수", "대기 중 흡습 warpage", "★", "wt%, %/wt%", "TGA, 흡습 시험", "(참고)", None),
    ("F. EMC (1st/2nd)", "2nd Mold가 MUF인지 CUF+Mold인지", "Die 아래 충진재 → 공정 단계 구성", "★★★", "-", "공정 사양", "Process: UF 단계", None),
    # ---------------- G. Underfill/DAF/Si ----------------
    ("G. Underfill·DAF·Si", "Underfill E(T), CTE, Tg, 경화 조건·수축", "CoP 후 die-패널 결합 강성", "★★", "곡선, °C", "DMA, TMA", "Materials: Underfill", None),
    ("G. Underfill·DAF·Si", "DAF (Bridge Die 접착) E(T), CTE, 두께", "Bridge die 결합 (영향 작음)", "★", "곡선, µm", "DMA", "Layers: M1_DIE", None),
    ("G. Underfill·DAF·Si", "Si 물성", "대표값 사용 가능", "★", "-", "문헌", "Materials: Si", None),
    # ---------------- H. 공정 열이력 ----------------
    ("H. 공정 열이력", "공정 단계별 온도 프로파일 (경화·몰드·reflow 피크·냉각 속도·hold)", "모든 층의 무응력 온도와 열하중", "★★★", "°C, min", "공정 레시피", "Process", None),
    ("H. 공정 열이력", "CoP 방식 (Mass reflow / TCB), 솔더 응고 온도, 본딩 스테이지 온도", "Die-패널 결합 무응력 온도 → CoP 전/후 변곡점", "★★★", "°C", "공정 레시피", "Process 16 (솔더 응고)", "CoP 전/후 warpage 변곡점 발생 (사용자 제공)"),
    ("H. 공정 열이력", "공정 사이 대기 시간·환경 (흡습)", "흡습 팽창", "★", "h, %RH", "-", "(참고)", None),
    ("H. 공정 열이력", "경화 중 지지 조건 (척 위 / 오븐 랙 / 클램프)", "경화 중 형상 구속 → 초기 형상", "★★", "-", "공정 사양", "(참고)", None),
    # ---------------- I. 설비/흡착 ----------------
    ("I. 설비·흡착", "흡착이 필요한 공정 목록과 순서", "판정 대상 단계", "★★★", "-", "공정 흐름도", "Process: CHUCK", None),
    ("I. 설비·흡착", "척 형식 (Porous / Groove / Pin), 진공 존 구성, 존 순차 on 여부", "포착·누설 거동", "★★★", "도면", "설비 사양서", "Equipment", None),
    ("I. 설비·흡착", "공급 진공, 진공 알람 임계값, 펌프 용량", "누설 모델 (plenum 진공)", "★★★", "kPa, L/min", "설비 사양서", "Equipment", None),
    ("I. 설비·흡착", "척 온도, 로딩 방식 (lift pin, 롤러, 누름), 패널 방향(face up/down)", "흡착 시점 온도와 초기 접촉", "★★", "°C", "설비 사양서", "Process T, Equipment", None),
    ("I. 설비·흡착", "설비사 허용 warpage spec", "판정 비교 기준", "★★", "µm", "설비 사양서", "Equipment 비고", None),
    # ---------------- J. 실측/검증 ----------------
    ("J. 실측·검증", "단계별 warpage 실측 full-field: Mold1 후, Grinding 후, URDL 후, CoP 전/후, Mold2 후, Carrier 교체 후, 최종", "모델 보정·검증의 핵심", "★★★", "µm, 형상 맵", "Shadow moiré / 3D 형상 측정", "Measured", None),
    ("J. 실측·검증", "온도별 warpage (RT → 260 °C → RT) 주요 단계", "온도의존 물성·무응력 온도 검증", "★★", "µm vs °C", "Shadow moiré 가열", "Measured", None),
    ("J. 실측·검증", "측정 시 지지 조건 (자중 처짐 보정)", "대면적 패널은 자중 영향 큼", "★★", "-", "측정 조건 기록", "Measured 비고", None),
    ("J. 실측·검증", "로트/패널 간 산포 (n ≥ 3)", "판정 마진, 불확실도", "★★", "µm", "-", "Measured", None),
    ("J. 실측·검증", "흡착 성공/실패 이력 + 해당 패널 warpage·형상", "설비 상수(포착 gap, 누설 β) 보정 → 판정 신뢰도", "★★★", "PASS/FAIL", "설비 로그", "Measured", "300×300 mm Ceramic: warpage 작으나 진공 미형성 (사용자 제공)"),
    ("J. 실측·검증", "CoP 전/후 변곡점 관찰 데이터 (die 두께별 warpage 방향·크기)", "Die 결합 모델·무응력 온도 보정", "★★★", "µm, 형상", "Shadow moiré", "Measured (step 13, 17)", "Die ~400 µm에서 변곡점 발생 (사용자 제공)"),
    ("J. 실측·검증", "흡착 후 크랙·박리 불량 이력", "평탄화 응력 허용치 보정", "★", "-", "불량 이력", "Materials: allowable", None),
]
