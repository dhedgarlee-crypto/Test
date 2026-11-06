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

## 사용법

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
2. **Cu 잔존율 맵** 등 면내 불균일 미반영 (현재 균일 κ, 1/4 대칭) → 요소별 κ_nat 입력은 구조상 지원 가능
3. 흡착 FE는 선형 굽힘 (최종 평탄 상태는 정확, 경로는 근사). 자유 형상은 비선형 Ritz로 별도 예측
4. 진공 누설 모델은 집중 상수(β) 모델 → 존 밸브/그루브 배치/유동 저항 상세화 가능
5. 척 마찰, 로딩 순서(lift pin, 롤러) 미반영
