# Process warpage & chuck summary

Input: `templates/ICubeE_warpage_input.xlsx`

| Carrier | Step | 공정 | Warpage corner−center (µm) | Placed gap (µm) | Gap after vacuum (µm) | Plenum (kPa) | p_req (kPa) | 흡착 | 응력 |
|---|---|---|---|---|---|---|---|---|---|
| Organic | 4 | Bridge Die 실장 (흡착) | +2874 | 563 | 0.2 | 80.0 | 5.4 | PASS | PASS |
| Organic | 7 | Grinding 전 흡착 | -19828 | 12965 | 12965.3 | 2.6 | >1024 | **FAIL** | PASS |
| Organic | 11 | URDL 2층 노광 (흡착) | -9682 | 2197 | 2194.5 | 2.6 | >1024 | **FAIL** | PASS |
| Organic | 14 | CoP 본딩 (흡착) | -6909 | 1166 | 1159.9 | 2.6 | >1024 | **FAIL** | PASS |
| Organic | 23 | 2nd Carrier 접합 전 흡착 | -99718 | 96871 | 96871.1 | 2.6 | >1024 | **FAIL** | PASS |
| Organic | 28 | MIP Bump 공정 (흡착) | +5068 | 3524 | 3473.4 | 2.7 | 408.0 | **FAIL** | PASS |
| Glass | 4 | Bridge Die 실장 (흡착) | +3231 | 1327 | 0.3 | 80.0 | 26.0 | PASS | PASS |
| Glass | 7 | Grinding 전 흡착 | +9686 | 7524 | 7500.5 | 2.6 | 736.0 | **FAIL** | PASS |
| Glass | 11 | URDL 2층 노광 (흡착) | +8001 | 5633 | 5522.9 | 2.7 | 360.0 | **FAIL** | PASS |
| Glass | 14 | CoP 본딩 (흡착) | +10807 | 8409 | 8380.9 | 2.6 | 720.0 | **FAIL** | PASS |
| Glass | 23 | 2nd Carrier 접합 전 흡착 | -38019 | 36292 | 36292.5 | 2.6 | >1024 | **FAIL** | PASS |
| Glass | 28 | MIP Bump 공정 (흡착) | +4897 | 3945 | 3929.2 | 2.6 | 640.0 | **FAIL** | PASS |
| Ceramic | 4 | Bridge Die 실장 (흡착) | +787 | 245 | 0.1 | 80.0 | 4.1 | PASS | PASS |
| Ceramic | 7 | Grinding 전 흡착 | +4157 | 3244 | 3213.2 | 2.6 | 480.0 | **FAIL** | PASS |
| Ceramic | 11 | URDL 2층 노광 (흡착) | +2590 | 1717 | 1540.5 | 2.9 | 130.0 | **FAIL** | PASS |
| Ceramic | 14 | CoP 본딩 (흡착) | +3403 | 2504 | 2435.3 | 2.7 | 260.0 | **FAIL** | PASS |
| Ceramic | 23 | 2nd Carrier 접합 전 흡착 | -18221 | 17126 | 17125.7 | 2.6 | >1024 | **FAIL** | PASS |
| Ceramic | 28 | MIP Bump 공정 (흡착) | -278 | 16 | 3.6 | 80.0 | 0.0 | PASS | PASS |

## Final state

- **Organic** (2nd carrier: Organic): warpage corner−center +5068 µm, PV nonlinear 3984 µm (elliptic (transition)), thickness 1658 µm, runtime 228.8 s
- **Glass** (2nd carrier: Glass): warpage corner−center +4897 µm, PV nonlinear 3728 µm (dome/bowl (spherical)), thickness 1686 µm, runtime 406.8 s
- **Ceramic** (2nd carrier: Ceramic): warpage corner−center -278 µm, PV nonlinear 429 µm (dome/bowl (spherical)), thickness 1686 µm, runtime 379.0 s
