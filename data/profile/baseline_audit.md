# BPI 2019: baseline audit (candidate labels)

Rule-derived **candidate** labels. They are not ground truth until the two-reviewer check (stage 18).

Config: `{"rel_tol": 0.01, "abs_tol": 1.0, "dup_window_days": 14, "valid_from": "2017-01-01", "valid_to": "2020-01-01"}`

- Cases audited: 251,734
- Cases with at least one candidate exception: 8,602 (3.4%)

| Rule | Cases flagged |
| --- | --- |
| R1_VALUE_MISMATCH | 5,523 |
| R2_OVER_PO_VALUE | 0 |
| R3_IR_BEFORE_GR | 0 |
| R4_PAID_WITHOUT_GR | 693 |
| R6_DUPLICATE_IR | 3,151 |

## By item category

| Category | R1_VALUE_MISMATCH | R2_OVER_PO_VALUE | R3_IR_BEFORE_GR | R4_PAID_WITHOUT_GR | R6_DUPLICATE_IR |
| --- | --- | --- | --- | --- | --- |
| 2-way match | 0 | 0 | 0 | 0 | 0 |
| 3-way match, invoice after GR | 1,340 | 0 | 0 | 7 | 415 |
| 3-way match, invoice before GR | 4,183 | 0 | 0 | 686 | 2,736 |
| Consignment | 0 | 0 | 0 | 0 | 0 |

## Splits (by purchase document)

| Split | Cases | Exception rate |
| --- | --- | --- |
| train | 151,145 | 3.3% |
| val | 49,543 | 3.5% |
| test | 51,046 | 3.6% |
