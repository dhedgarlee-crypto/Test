# 대면적 Panel Warpage · 진공 흡착 판정 시뮬레이터

유기 / Glass / Ceramic 코어 패널의 **CTE mismatch warpage**와 **굽힘 강성**을 함께 계산해
설비 **진공 흡착 가능 여부**를 판정합니다.

## 해석 체인

| 단계 | 모듈 | 내용 |
|---|---|---|
| 1. 열변형 | `laminate.py` | 다층 CLT, 온도 의존 물성(Tg 전이)으로 냉각 경로를 증분 적분 → 곡률 κ, 층별 응력 |
| 2. 실제 자유 형상 | `ritz.py` | von Kármán 비선형 Rayleigh-Ritz (Hyer형) → 대면적 패널의 돔→원통 분기, 실제 PV warpage |
| 3. 흡착 | `plate_fe.py` | Kirchhoff 판 FE(BFS C1 요소, 1/4 대칭, 가장자리 세분화) + 척 일방향 접촉 + 자중 + 진공 포착(zipping) + 밀폐영역 배기 + **누설 제한 진공** + 진공 램프 |
| 4. 판정 | `model.py` | 필요 진공압, 80 kPa에서 잔여 gap/plenum 진공, 평탄화 후 응력 vs 허용응력 |

## 핵심 물리 (검증 포함)

* 흡착 후 가장자리 들뜸: **δ = D·κ² / (2p)** → 필요 압력은 *warpage 크기*가 아니라 **강성 × 곡률²**,
  패널 크기와 무관. FE가 이 해석해와 2~6% 이내로 일치 (`plate_fe.py` 검증).
* 흡착 실패의 지배 메커니즘은 대개 **초기 포착 실패 → 누설 → 진공 미형성**:
  고강성 판은 자중으로 처지지 않아 놓인 직후 척과 닿는 면적이 작고,
  덮이지 않은 척 면으로 공기가 새어 plenum 진공이 형성되지 않음.
  `p_plenum = p_supply / (1 + β·f_open)`

## 공정 순차 해석 (I-Cube E형 구조, v2)

`templates/ICubeE_warpage_input.xlsx` 에 물성·적층·공정·설비를 입력하고 실행합니다.

```bash
python3 make_template.py                 # 빈 템플릿(대표값 포함) 재생성
python3 run_process.py templates/ICubeE_warpage_input.xlsx           # → outputs/process/
python3 run_process.py templates/ICubeE_warpage_input.xlsx --quick   # 빠른 확인(필요압 탐색 생략)
python3 run_process.py templates/ICubeE_warpage_input.xlsx --sweep COP_DIE=100,200,300,400,600  # 층 두께 스윕
```

* **필요정보_체크리스트** 시트: 신뢰도 있는 해석에 필요한 54개 항목 (영향·측정법·입력 위치). 노란 칸에 보유 여부/값 기입
* **3D 형상**: `fig_3d_shapes.png` (Process 시트 `plot3d = Y` 단계), `warpage_3d_viewer.html`
  (브라우저에서 열기: 공정 슬라이더, 3종 비교/단일, 높이 과장, 흡착 단계의 척 위 놓인 상태 보기, 공정별 추이 클릭 이동)
* **CoP 변곡점 모델**: die는 솔더 응고 온도(Process 16)에서 die 사이가 빈 '섬'으로 결합(`Void` 기지, voigt) →
  Underfill / 2nd Mold는 `ADD_FILL`로 같은 높이 구간을 병렬 충진. **Process 16의 온도 = 유효 결합 온도**로,
  솔더 크리프 완화가 없어 217 °C 그대로면 CoP 후 warpage가 과대 → CoP 전/후 실측으로 보정 권장

| 모듈 | 내용 |
|---|---|
| `process.py` | 층 생성(생성 온도에서 무응력) → 경화수축 → 온도이력 → Grinding(절삭분 응력 해방) → Carrier 분리 → 반전. 매 단계 힘/모멘트 평형 잔차 출력 |
| `materials.py` | `CompositeMaterial`: Cu 잔존율, Via/Post/Die 면적비율 균질화 (voigt / halpin / reuss), `TabulatedMaterial`: DMA/TMA 곡선 보간 |
| `plate_fe.py` | Unit 영역 / Edge frame 영역별 강성·곡률·질량을 갖는 판 FE |
| `xlsx_io.py` | 템플릿 읽기 |
| `run_process.py` | Carrier 옵션별 병렬 실행, 흡착 단계마다 판정 → `process_results.xlsx`, `summary.md`, 그림 |

출력: 단계별 warpage(선형 FE / 비선형 Ritz), 강성 D*, 흡착 단계별 놓인 gap·진공 후 gap·plenum 진공·필요 진공·
평탄화 응력 판정, `Measured` 시트가 있으면 모델 vs 실측 비교.

## 사용법 (v1: 단순 적층 비교)

```bash
pip install -r requirements.txt
python3 run_compare.py            # cases.json 기준 3종 비교 + 두께 스윕 → outputs/
python3 run_compare.py --quick    # 거친 격자 빠른 확인
python3 run_ceramic_case.py       # 같은 warpage, 다른 강성 비교 (300 mm 세라믹 이력 재현)

# 실측 warpage로 바로 판정 (물성 불확실성 우회 — 가장 신뢰도 높은 경로)
python3 assess_measured.py --size 300 300 --E 340 --nu 0.22 --t 1.0 --rho 3750 \
    --pv 1000 --shape bowl --vacuum 80 --gcap 10 --beta 30
```

## 입력 (cases.json)

* `materials`: E(GPa), ν, CTE(ppm/K) 유리/고무 상태, Tg, 밀도, 허용응력(MPa). **현재 값은 문헌 대표값(placeholder)**
* `top_stack_bottom_to_top`: 코어 위 적층 [재료, 두께 mm]
* `T_stress_free_C`, `T_chuck_C`: 무응력 온도(경화), 흡착 온도
* `equipment`: 공급 진공, `capture_gap_um`, `leak_beta`, `seal_tolerance_um`
  → **`capture_gap_um`, `leak_beta`는 설비 고유 상수로, 흡착 성공/실패 이력으로 보정해야 함**

## 한계 (신뢰도 향상을 위한 다음 단계)

1. 고분자 **점탄성 응력완화, 경화수축** 미반영 (현재 온도의존 탄성) → Prony series/경화모델 추가 필요
2. 면내 불균일은 Unit/Edge 2영역까지만 반영 (1/4 대칭). 영역 간 면내(멤브레인) 상호작용은 무시, 영역별 CLT 후 판 FE에서 굽힘만 결합
3. 흡착 FE는 선형 굽힘 (최종 평탄 상태는 정확, 경로는 근사). 자유 형상은 비선형 Ritz로 별도 예측
4. 진공 누설 모델은 집중 상수(β) 모델 → 존 밸브/그루브 배치/유동 저항 상세화 가능
5. 척 마찰, 로딩 순서(lift pin, 롤러) 미반영
6. 복합층 균질화는 패널 수준 등가물성이며 die 개별 응력은 해석하지 않음 → 필요시 Unit 단위 상세 FE로 보정
