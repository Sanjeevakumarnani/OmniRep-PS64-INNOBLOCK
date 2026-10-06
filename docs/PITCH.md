# OmniRep — Pitch

## One line
**Your history should not reset when your wallet changes.**

## 90-second story
On-chain reputation is fragmented: activity lives behind addresses and across networks. A new dApp that knows nothing about those old addresses has to treat a returning user like a new user.

OmniRep turns that fragmented trail into a portable reputation passport. The user proves control of multiple wallets with signatures, OmniRep normalizes activity from two or more EVM testnets, and a transparent scoring engine produces a 0–1000 score with a human-readable Proof of Why.

The detailed evidence stays off-chain in PostgreSQL. Only a cryptographic SHA-256 commitment, score and verification metadata are anchored in the registry. That lets another application read the passport without trusting OmniRep's private database.

We also separate reputation from evidence confidence and add a Sybil Radar that explains suspicious patterns. A portable EIP-712 attestation can be accepted on another testnet, and a consumer app such as LendLite gates access using the on-chain policy.

## Judge demo beats

**Beat 1 — Link**: two wallets, two chains, two signatures.

**Beat 2 — Explain**: the score breakdown shows exactly which evidence raised or lowered the score.

**Beat 3 — Prove**: publish the SHA-256 commitment, then mutate one input and show verification fail.

**Beat 4 — Compose**: LendLite reads the registry and unlocks a feature without access to the private evidence database.

## Q&A anchors

- **Why not put everything on-chain?** Only the proof commitment and compact decision data belong on-chain; the detailed record is cheaper and easier to evolve off-chain.
- **Can AI manipulate the score?** No. The deterministic rules calculate the score; AI is advisory for Sybil pattern analysis.
- **Can the same wallet be linked to two passports?** The backend rejects an already-verified address assigned to another passport.
- **What happens when evidence changes?** The input hash changes, so the previous publication no longer matches the current bundle until a new score version is published.
