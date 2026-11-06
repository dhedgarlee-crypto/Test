# Process warpage & chuck summary

Input: `templates/ICubeE_warpage_input.xlsx`

| Carrier | Step | 공정 | Warpage corner−center (µm) | Placed gap (µm) | Gap after vacuum (µm) | Plenum (kPa) | p_req (kPa) | 흡착 | 응력 |
|---|---|---|---|---|---|---|---|---|---|
| Organic | 4 | Bridge Die 실장 (흡착) | +2874 | 563 | 0.2 | 80.0 | 5.4 | PASS | PASS |
| Organic | 7 | Grinding 전 흡착 | -19865 | 12965 | 12965.3 | 2.6 | >1024 | **FAIL** | PASS |
| Organic | 11 | URDL 2층 노광 (흡착) | -9674 | 2197 | 2194.5 | 2.6 | >1024 | **FAIL** | PASS |
| Organic | 14 | CoP 본딩 (흡착) | -6900 | 1166 | 1159.9 | 2.6 | >1024 | **FAIL** | PASS |
| Organic | 20 | 2nd Carrier 접합 전 흡착 | -64202 | 61435 | 61434.9 | 2.6 | >1024 | **FAIL** | PASS |
| Organic | 25 | MIP Bump 공정 (흡착) | -22827 | 19573 | 19572.8 | 2.6 | >1024 | **FAIL** | PASS |
| Glass | 4 | Bridge Die 실장 (흡착) | +3225 | 1327 | 0.3 | 80.0 | 26.0 | PASS | PASS |
| Glass | 7 | Grinding 전 흡착 | +9647 | 7524 | 7500.5 | 2.6 | 736.0 | **FAIL** | PASS |
| Glass | 11 | URDL 2층 노광 (흡착) | +7988 | 5633 | 5522.9 | 2.7 | 360.0 | **FAIL** | PASS |
| Glass | 14 | CoP 본딩 (흡착) | +10792 | 8409 | 8380.9 | 2.6 | 720.0 | **FAIL** | PASS |
| Glass | 20 | 2nd Carrier 접합 전 흡착 | -18462 | 16751 | 16750.6 | 2.6 | >1024 | **FAIL** | PASS |
| Glass | 25 | MIP Bump 공정 (흡착) | -7698 | 5720 | 5720.0 | 2.6 | >1024 | **FAIL** | PASS |
| Ceramic | 4 | Bridge Die 실장 (흡착) | +786 | 245 | 0.1 | 80.0 | 4.1 | PASS | PASS |
| Ceramic | 7 | Grinding 전 흡착 | +4142 | 3244 | 3213.2 | 2.6 | 480.0 | **FAIL** | PASS |
| Ceramic | 11 | URDL 2층 노광 (흡착) | +2585 | 1717 | 1540.5 | 2.9 | 130.0 | **FAIL** | PASS |
| Ceramic | 14 | CoP 본딩 (흡착) | +3397 | 2504 | 2435.3 | 2.7 | 260.0 | **FAIL** | PASS |
| Ceramic | 20 | 2nd Carrier 접합 전 흡착 | -7837 | 6742 | 6741.9 | 2.6 | >1024 | **FAIL** | PASS |
| Ceramic | 25 | MIP Bump 공정 (흡착) | -3450 | 2261 | 2260.6 | 2.6 | >1024 | **FAIL** | PASS |

## Final state

- **Organic** (2nd carrier: Organic): warpage corner−center -22827 µm, PV nonlinear 17259 µm (cylindrical), thickness 1658 µm, runtime 146.2 s
- **Glass** (2nd carrier: Glass): warpage corner−center -7698 µm, PV nonlinear 4624 µm (elliptic (transition)), thickness 1686 µm, runtime 329.4 s
- **Ceramic** (2nd carrier: Ceramic): warpage corner−center -3450 µm, PV nonlinear 2822 µm (dome/bowl (spherical)), thickness 1686 µm, runtime 354.3 s
