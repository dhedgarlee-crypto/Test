# Warpage & vacuum-chuck comparison

Stack (bottom→top): core 0.8 mm + RDL (Cu/PI effective) 0.015 mm + EMC 0.15 mm

Cool-down 175 → 25 °C. Vacuum 80 kPa, capture gap 50 µm, seal tolerance 20 µm.

| Core | Panel (mm) | κ (1/m) | Shape | Warpage lin / nonlin (µm) | D* (N·m) | As-placed gap (µm) | p_req FE (kPa) | p_req analytic (kPa) | Gap @ avail. (µm) | Chuck | Flattened stress max core / EMC (MPa) | Stress |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Organic core (BT/glass-epoxy) | 300×300 | +0.141 | center up (dome), dome/bowl (spherical) | 3175 / 2203 | 2.01 | 1207 | 6.8 | 1.0 | 0.1 | PASS | 1 / -7 (allow 250 / 80) | PASS |
| Organic core (BT/glass-epoxy) | 510×515 | +0.141 | center up (dome), cylindrical | 9266 / 5718 | 2.01 | 727 | 0.4 | 1.0 | 0.9 | PASS | 1 / -7 (allow 250 / 80) | PASS |
| Organic core (BT/glass-epoxy) | 600×600 | +0.141 | center up (dome), cylindrical | 12700 / 7770 | 2.01 | 439 | 0.4 | 1.0 | 1.6 | PASS | 1 / -7 (allow 250 / 80) | PASS |
| Glass core (CTE-tuned) | 300×300 | -0.233 | edges up (bowl), cylindrical | 5235 / 3238 | 4.29 | 4645 | 19.0 | 5.8 | 4.9 | PASS | -3 / 12 (allow 50 / 80) | PASS |
| Glass core (CTE-tuned) | 510×515 | -0.233 | edges up (bowl), cylindrical | 15277 / 9540 | 4.29 | 10398 | 20.0 | 5.8 | 4.7 | PASS | -3 / 12 (allow 50 / 80) | PASS |
| Glass core (CTE-tuned) | 600×600 | -0.233 | edges up (bowl), cylindrical | 20938 / 12953 | 4.29 | 12255 | 20.0 | 5.8 | 5.7 | PASS | -3 / 12 (allow 50 / 80) | PASS |
| Ceramic core (96% Al2O3) | 300×300 | -0.081 | edges up (bowl), dome/bowl (spherical) | 1815 / 1443 | 16.27 | 1583 | 8.5 | 2.6 | 2.2 | PASS | -4 / 16 (allow 150 / 80) | PASS |
| Ceramic core (96% Al2O3) | 510×515 | -0.081 | edges up (bowl), cylindrical | 5296 / 3267 | 16.27 | 3404 | 8.8 | 2.6 | 1.9 | PASS | -4 / 16 (allow 150 / 80) | PASS |
| Ceramic core (96% Al2O3) | 600×600 | -0.081 | edges up (bowl), cylindrical | 7259 / 4447 | 16.27 | 3939 | 8.1 | 2.6 | 2.2 | PASS | -4 / 16 (allow 150 / 80) | PASS |
| Glass core (low-CTE, Si-matched) | 300×300 | -0.532 | edges up (bowl), cylindrical | 11960 / 7399 | 4.29 | 11370 | 96.0 | 30.3 | 23.4 | FAIL | -7 / 31 (allow 50 / 80) | PASS |
| Glass core (low-CTE, Si-matched) | 510×515 | -0.532 | edges up (bowl), cylindrical | 34906 / 21804 | 4.29 | 29882 | 80.0 | 30.3 | 19.6 | PASS | -7 / 31 (allow 50 / 80) | PASS |
| Glass core (low-CTE, Si-matched) | 600×600 | -0.532 | edges up (bowl), cylindrical | 47841 / 29597 | 4.29 | 38405 | 90.0 | 30.3 | 21.8 | FAIL | -7 / 31 (allow 50 / 80) | PASS |

## Thickness sweep (510×515 mm)

| Core | t (mm) | κ (1/m) | Warpage nonlin (µm) | D* (N·m) | p_req FE (kPa) | Chuck |
|---|---|---|---|---|---|---|
| Ceramic core (96% Al2O3) | 0.3 | -0.581 | 23391 | 1.04 | 25.0 | PASS |
| Ceramic core (96% Al2O3) | 0.5 | -0.211 | 8589 | 4.21 | 16.0 | PASS |
| Ceramic core (96% Al2O3) | 0.8 | -0.081 | 3267 | 16.27 | 8.8 | PASS |
| Ceramic core (96% Al2O3) | 1.2 | -0.035 | 1913 | 53.50 | 5.1 | PASS |
| Glass core (CTE-tuned) | 0.3 | -1.176 | 49031 | 0.38 | 64.0 | PASS |
| Glass core (CTE-tuned) | 0.5 | -0.531 | 21931 | 1.26 | 26.0 | PASS |
| Glass core (CTE-tuned) | 0.8 | -0.233 | 9540 | 4.29 | 20.0 | PASS |
| Glass core (CTE-tuned) | 1.2 | -0.109 | 4397 | 13.18 | 12.2 | PASS |
| Organic core (BT/glass-epoxy) | 0.3 | +0.345 | 14165 | 0.22 | 0.3 | PASS |
| Organic core (BT/glass-epoxy) | 0.5 | +0.242 | 9697 | 0.66 | 0.5 | PASS |
| Organic core (BT/glass-epoxy) | 0.8 | +0.141 | 5718 | 2.01 | 0.4 | PASS |
| Organic core (BT/glass-epoxy) | 1.2 | +0.079 | 3406 | 5.69 | 0.3 | PASS |
