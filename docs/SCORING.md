# OmniRep scoring model

## Score range

Final score is **0–1000**.

The model is deterministic and versioned as `20001` (`omnirep_scoring_v2`).

## Transparent factors

| Factor | Max | What it measures |
|---|---:|---|
| Repayments | 220 | On-time and late repayment outcomes |
| Governance | 90 | Distinct governance proposals voted on |
| Contributions | 90 | Recorded contribution signals |
| Wallet longevity | 170 | Earliest observed history + active weeks |
| Activity quality | 130 | Indexed transactions, evidence quality and successful contract interactions |
| Cross-chain breadth | 110 | Activity observed across independent chains |
| Counterparty diversity | 70 | Distinct interaction counterparties |
| Consistency | 120 | How activity is distributed across days/weeks |
| Outcome penalties | -200 | Defaults and other negative outcomes |

The raw factor total is then adjusted by a deterministic Sybil-risk multiplier and freshness multiplier. The final value is clamped to 0–1000.

## Confidence

Confidence is **not** reputation. It estimates how much trustworthy evidence the engine has: activity count, chain coverage, evidence quality, metric fetch coverage and verified wallet count.

## Sybil Radar

Deterministic indicators include:

- temporal bursts
- circular interaction patterns involving linked addresses
- single-counterparty concentration
- repeated identical event signatures
- unusually loud new accounts

AI may be enabled as a second opinion. It does not replace the deterministic rules and does not produce the final reputation score.

## Tier thresholds

- **Iron:** 0–199
- **Bronze:** 200–399
- **Silver:** 400–599
- **Gold:** 600–799
- **Diamond:** 800–1000
