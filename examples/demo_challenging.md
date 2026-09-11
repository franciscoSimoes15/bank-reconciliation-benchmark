# Explanation of case `case_4a8fef496eea5c328099`

- Seed: `7`
- Scenario: `combined_variation` (P7)
- Perturbations: `entity:typo, amount:+0.25, reference:separators`
- Method: `field_aware` (M4)
- Ground truth used only for evaluation: `cand_fa3851642bc36ebf11d8`

## Bank transaction received by the matcher

| Field | Raw | Normalized |
|---|---|---|
| Amount | `5261.52` | `5261.52` |
| Date | `2026-01-11` | `2026-01-11` |
| Reference | `REC2026.0070001` | `rec20260070001` |
| Counterparty | `Horizonte Enegr` | `horizonte enegr` |
| Description | `TRF SEPA RECEBIDA CONTA EMPRESA` | `trf sepa recebida conta empresa` |

## Candidate ranking

| Display rank | Candidate | True? | Score | Fields | Amount | Date | Reference | Entity | Description | Excluded |
|---:|---|:---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | `cand_fa3851642bc36ebf11d8` | yes | 0.812416 | 5 | 0.9952 | 1.0000 | 1.0000 | 0.9631 | 0.1037 | — |
| 2 | `cand_977c5ed6919d0ab4ac0d` |  | 0.665750 | 5 | 0.9952 | 0.9667 | 0.3000 | 0.9631 | 0.1037 | — |
| 3 | `cand_15b9caea5a85c994de52` |  | 0.625750 | 5 | 0.9952 | 0.7667 | 0.3000 | 0.9631 | 0.1037 | — |
| 4 | `cand_039c54d96f5cce081eca` |  | 0.546461 | 5 | 0.9952 | 1.0000 | 0.3000 | 0.4037 | 0.0334 | — |
| 5 | `cand_0d8f0b07aacdd66b55e9` |  | 0.298629 | 5 | 0.0000 | 0.6333 | 0.3000 | 0.5265 | 0.0334 | — |
| 6 | `cand_0783ddf1d37cad2cc9fd` |  | 0.188636 | 5 | 0.0000 | 0.0000 | 0.3000 | 0.5395 | 0.1037 | — |
| 7 | `cand_d2511cec5475c6191369` |  | 0.183598 | 5 | 0.0000 | 0.0000 | 0.3000 | 0.5846 | 0.0334 | — |
| 8 | `cand_189f01097059892c0870` |  | 0.178734 | 5 | 0.0000 | 0.0000 | 0.3000 | 0.5603 | 0.0334 | — |
| 9 | `cand_032b72743ce978f4687f` |  | 0.169945 | 5 | 0.0000 | 0.0000 | 0.3000 | 0.5164 | 0.0334 | — |
| 10 | `cand_c54a4c0d3e32b17fa882` |  | 0.150921 | 5 | 0.0000 | 0.0000 | 0.1500 | 0.4250 | 0.1796 | — |

The final score is the unweighted mean of available fields. A field missing on either side is excluded. Generation validates that every candidate in the case is compared using the same number of fields.

The matcher receives only the bank transaction and one accounting record. `event_id`, scenario, perturbations, origin and ground truth are consulted only after scoring.
