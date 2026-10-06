# OmniRep: Omnichain Reputation Passport

**Product Requirements Document v1.0** · INNOBLOCK 2.0 · PS 64 (Domain 7: Digital Identity) · Build window 5–7 Oct 2026 · Testnets only

## 1. Summary

**OmniRep** is a reputation passport. A user links several wallets (on different testnets) to one passport by signing with each wallet. The engine pulls their on-chain activity, normalizes it, and computes a 0–1000 score where every point is explained and traceable to a transaction. The score, a hash of all inputs, and a hash of the linked wallets are published to a smart contract that any app can query. A sample app then unlocks a feature based on the score.

**What makes it different from other teams** (details in section 5):

- **Proof Bundle + Independent Verifier**: anyone can download the evidence, recompute the hash, and compare it with the chain. Change one character and verification fails.
- **Portable signed attestation**: the same score proof is accepted by an app on a second testnet with no bridge.
- **Sybil Radar**: deterministic rules plus an AI second opinion, with evidence for every flag.
- **What-if Coach**: shows exactly which actions would raise the score, and by how much.
- **Privacy by default**: linked addresses are never published, only a hash. Apps ask a yes/no question (`meets 400?`) instead of reading a profile.
- **Reputation Playground**: small source contracts (loan pool, governor, contribution log) deployed on both chains so real loans, votes and contributions exist to be scored.

## 2. What the source documents say, and what it means for the design

| Source | Key facts | Design consequence |
| --- | --- | --- |
| PS 64 PDF | Must-have: (1) link addresses by signing with each wallet, (2) fetch and normalize activity from 2+ testnets, (3) transparent explained score, (4) publish score + input hash to a contract apps can query. Good-to-have: AI sybil flagging, badge levels at thresholds. Demo must show: two addresses on different testnets linked, score breakdown with raised/lowered factors, a sample app gating a feature. | Every must-have and demo item is P0. Both good-to-haves are P1. |
| Handbook | 3 days; Day 2 is the only full build day. Testnets and burner wallets only. Minimum to be judged: verified contract on a public testnet with address in README and slide 1, one visible explorer transaction, a web page that connects a wallet and shows pending/confirmed/failed, public repo with README. Judges: 30 prototype, 25 blockchain, 15 technical quality, 15 pitch/Q&A, 10 innovation, 5 UI/UX. Pitch is about 3 minutes. No personal data on-chain. No secrets in the frontend. | Build the minimum first, then layers. Contract must be verified and commented. Pitch must end on an explorer page. Keep everything demo-able from one happy path. |
| Starter kit | Flask + web3.py backend, plain HTML/JS + ethers v6 frontend, Solidity via Remix, five EVM testnets, Neon/Supabase, Render, Vercel/Netlify, UptimeRobot. Optional: any part may be swapped. | Reuse the starter's structure, so the first hour goes to the idea and not to boilerplate. |
| Problem-statement website | The page renders its content with JavaScript, so only the title was readable by my fetch. The PS 64 wording above comes from your PDF. | Re-check the site on Day 1 for any change to scope or wording. |

**Honest constraint that shapes the product:** public testnets have almost no real loans, votes or contributions. A score built only on generic transaction counts would be shallow. OmniRep therefore combines (a) generic real activity read from any wallet and (b) typed activity from pluggable source adapters, with Playground contracts supplying loans, votes and contributions for the demo. The adapter registry is open, so real testnet protocols can be added by config. Say this plainly to judges: it is a strength, because it shows the design extends beyond the demo.

## 3. Problem, goals and success metrics

**Problem.** A user's useful history (loans repaid, votes cast, contributions made) is scattered across chains and addresses. New platforms cannot see it, so trustworthy users start from zero every time, and platforms cannot distinguish them from farmed or fake accounts.

**Goals**

1. One passport that proves control of many wallets, with no personal data collected.
2. A score that is explainable, reproducible, and verifiable by third parties.
3. A contract interface so simple that an app can gate a feature in one line.
4. A resilient live demo that tells one clear story.

**Non-goals (say these out loud to judges)**

- Not a credit bureau. No real-world identity, no KYC, no mainnet, no real money.
- Not trustless scoring in v1: a single attestor signs scores. The path to multi-attestor or ZK scoring is in 'What's next'.
- No cross-chain messaging protocol. Portability uses signed attestations.

**Success metrics**

| Metric | Target |
| --- | --- |
| Must-haves 1–4 and demo items 1–3 working live | 100% |
| Time from 'Refresh' to score and breakdown on screen | under 20 s for 4 wallets across 2 chains |
| Reproducibility: recomputed score equals published score | 100% on the seeded demo passports |
| Contract verified on explorer, README complete, no secrets in git history | pass |
| Every team member can explain their part | pass |

## 4. Personas and user stories

- **Asha, the contributor** (student with wallets on Sepolia and Base Sepolia): wants her repayment and voting history to count everywhere.
- **Dev, the app builder** (runs a lending or DAO dApp): wants to gate or discount features by trust level without building an analytics pipeline.
- **Judge or auditor**: wants to verify a score without trusting the team.

Stories: As Asha I can (1) create a passport, (2) link a second wallet by signing, (3) see why my score is what it is, (4) see what would raise it, (5) publish it on-chain, (6) claim a badge. As Dev I can (7) call one function to check a threshold and (8) accept a signed proof on another chain. As an auditor I can (9) download the evidence and verify it independently.

## 5. Differentiating features

| # | Feature | Why it matters | Priority |
| --- | --- | --- | --- |
| D1 | **Proof Bundle + Verifier page**: JSON with linked-wallet proofs, normalized features, evidence tx hashes, algorithm version. Verifier recomputes the SHA-256 input hash in the browser and compares it with the on-chain value. | Directly answers 'why a blockchain, not a database?' and 'how do you stop fake data?'. Gives the tamper demo moment. | P0 |
| D2 | **Privacy-first publishing**: the chain stores score, tier, risk, input hash and links hash. No linked address is published unless the user opts in. | 'No personal data on-chain' rule; stronger than teams that list all wallets. | P0 |
| D3 | **Evidence-linked breakdown**: every factor lists its transactions with explorer links; each factor shows raised or lowered chips. | Satisfies the 'transparent, explained' must-have with proof. | P0 |
| D4 | **Freshness and decay**: idle accounts decay (floor 60%); apps may demand `maxAge`. | Reputation that does not go stale; tests the 'what if data is old' question. | P0 |
| D5 | **Sybil Radar**: rules R1–R6 with evidence, plus AI second opinion that explains but cannot change the numbers by more than ±10 risk points. | Covers good-to-have 01 with a deterministic core, so the demo never depends on an API key. | P1 |
| D6 | **What-if Coach**: simulate hypothetical actions and see score deltas. | Turns a score into a guide; strong live-demo moment. | P1 |
| D7 | **Portable attestation (no bridge)**: backend issues a wallet-scoped EIP-712 attestation; a verifier contract on Base Sepolia accepts it. | Real cross-chain consumption of the passport, which the PS implies. | P1 |
| D8 | **Soulbound tier badges** at 200/400/600/800. | Covers good-to-have 02. | P1 |
| D9 | **PassportGate SDK**: Solidity interface plus a 5-line JS snippet. | Makes 'other apps can query' concrete. | P0 |
| D10 | **Reputation Playground** contracts on both chains. | Creates real typed activity to score. | P0 |
| D11 | Challenge/dispute and wallet unlinking; vouching | Roadmap items | P2 (roadmap only) |

## 6. Scope

**P0 (must work to be competitive):** passport creation, multi-wallet linking, ingestion from Sepolia + Base Sepolia, scoring v1 with breakdown and evidence, attest-and-publish, query functions, one gated sample app, Proof Bundle + verifier hash check, verified contracts, README, deployed frontend and backend.

**P1 (only after P0 passes end to end):** Sybil Radar and AI note, What-if Coach, soulbound badges, portable attestation to Base Sepolia, server-side score recompute in the verifier.

**P2 (roadmap slide):** JS port of scoring for fully client-side verification, Merkle proofs per event, vouching, dispute window, multi-attestor, ZK threshold proofs.

## 7. End-to-end user flow

1. **Connect** primary wallet A (Sepolia). UI shows network, address, balance.
2. **Create passport**: A sends `createPassport()`; UI shows pending, confirmed or failed with an explorer link. Passport ID is returned.
3. **Link wallet B**: UI shows a readable message. The user switches MetaMask to account B and signs it (`personal_sign`, no gas, no chain switch needed). Backend verifies the signature and stores the proof. Repeat for C and D. Wallet A signs the same style of message so every wallet, including the primary one, has a proof.
4. **Refresh**: backend scans every linked wallet on every enabled chain, normalizes events, runs scoring v1 and Sybil Radar, and returns a preview with breakdown, risk, confidence and the input hash.
5. **Publish**: backend returns a signed attestation. The user submits `publish()` from wallet A. The contract verifies the attestation, then stores score, tier, risk, input hash, links hash and version, and emits an event.
6. **Use**: open the sample app. It calls the registry and shows locked or unlocked.
7. **Verify**: open the Verifier, load the bundle, press Verify. Result: matches the chain, or does not.
8. **Optional**: What-if, badge claim, portable attestation to Base Sepolia.

**Screens:** Connect, Link Wizard (stepper), Passport Dashboard (score ring, tier, confidence, factor bars with raised/lowered chips, evidence drawer), Sybil Radar, What-if Coach, Publish and History, Verifier, LendLite sample app, Badge. Every transaction shows pending, confirmed or failed with an explorer link, as the handbook requires.

## 8. Functional requirements

| ID | Requirement | Acceptance criterion | Pri |
| --- | --- | --- | --- |
| FR-1 | Connect MetaMask, detect chain, offer a switch/add-network button | Wrong chain shows a clear prompt; correct chain shows status | P0 |
| FR-2 | Create a passport (one per primary wallet) | Second attempt from same wallet reverts with a readable message | P0 |
| FR-3 | Link a wallet: backend issues a challenge (passport, wallet, nonce, expiry, hub chain); wallet signs; backend verifies with ecrecover | Wrong signer, expired or reused nonce is rejected; a valid proof appears in the passport | P0 |
| FR-4 | A wallet may belong to only one passport | Linking an already-linked wallet is refused with the owning passport ID hidden | P0 |
| FR-5 | Ingest generic activity (age, tx count, counterparties) from explorer API with RPC fallback | Source and fetch time are stored; failures lower the confidence value and show a warning, not a crash | P0 |
| FR-6 | Ingest typed activity via adapters (`loan_borrowed`, `loan_repaid`, `loan_defaulted`, `vote`, `contribution`) from event logs | Adding a new adapter needs only a config entry (chain, address, event ABI, mapping) | P0 |
| FR-7 | Normalize to one schema; dedupe by chainId + txHash + logIndex | Same event never counts twice, even across refreshes | P0 |
| FR-8 | Score with scoring\_v1 (section 9), producing factor points, deltas and evidence | Same inputs always give the same score; golden test vectors pass | P0 |
| FR-9 | Compute input hash = SHA-256(canonical JSON of inputs) and links hash similarly | Canonical form: sorted keys, no whitespace, lowercase addresses; a unit test proves stability | P0 |
| FR-10 | Issue an EIP-712 attestation with version, deadline and passport ID | Contract rejects wrong signer, stale version, expired deadline, non-owner submitter | P0 |
| FR-11 | Contract exposes `scoreOf`, `tierOf`, `meets(id,min,maxAge)`, `passportOf(addr)`, `verifyInputs(id,hash)` | Callable for free from any app and the explorer | P0 |
| FR-12 | Sample app LendLite gates `borrow()` by `meets(id, 400, 30 days)` and sets collateral by tier | Locked passport reverts; unlocked passport succeeds; the revert reason is shown | P0 |
| FR-13 | Proof Bundle download and Verifier page | Editing any character of the bundle makes verify fail | P0 |
| FR-14 | Sybil Radar rules R1–R6 with evidence list and risk 0–100 | Seeded 'farmed' wallet scores risk above 60; seeded honest wallet below 20 | P1 |
| FR-15 | AI second opinion on anonymized features, strict JSON output, fallback to demo text when no key | Works offline; changes risk by at most ±10 | P1 |
| FR-16 | What-if simulator | Returns a delta per hypothetical action in under 2 s | P1 |
| FR-17 | Soulbound badge claim when tier threshold is met | Transfer reverts; claim below threshold reverts | P1 |
| FR-18 | Portable attestation accepted by `OmniRepVerifier` on Base Sepolia | A second-chain app gates a feature without any bridge | P1 |
| FR-19 | History: list all published versions from events | Shows version, score, time and tx link | P1 |
| FR-20 | `/health` shows RPC, DB, adapters and attestor balance | Used by UptimeRobot and the pre-demo check | P0 |

## 9. Reputation engine (scoring\_v1)

Pure, deterministic function: `score = f(features, config)`. Config is a versioned JSON file in the repo, so judges can read the weights.

| Factor | Max | Formula (x = measured quantity) | Evidence shown |
| --- | --- | --- | --- |
| Repayments | 300 | 300 × (1 − e^(−w/4)), where w = on-time repayments + 0.5 × late repayments | loan\_repaid events |
| Governance | 150 | 150 × (1 − e^(−v/6)), v = distinct proposals voted on | vote events |
| Contributions | 100 | 100 × (1 − e^(−c/5)) | contribution events |
| Age and consistency | 150 | 90 × min(1, ageDays/90) + 60 × min(1, activeWeeks/8) | first tx, active weeks |
| Cross-chain breadth | 150 | chains with activity: 1→0, 2→90, 3→125, 4+→150 | per-chain counts |
| Counterparty diversity | 150 | 150 × (1 − e^(−n/15)), n = distinct counterparties | counterparty list |
| Penalties | up to −225 | −75 per default, floor −225 | loan\_defaulted events |

`final = clamp(round((sum of factors + penalties) × sybilMultiplier × freshness), 0, 1000)`

- `sybilMultiplier = 1 − risk/200` (risk 0–100, so at most −50%).
- `freshness = max(0.6, 0.5^(idleDays/120))`.
- **Tiers:** 0–199 Newcomer · 200–399 Bronze · 400–599 Silver · 600–799 Gold · 800–1000 Platinum.
- **Confidence** = share of (wallet × chain) fetches that succeeded. Shown beside the score; below 70% the UI warns that data is incomplete.
- Weights are a starting point. **Calibrate on Day 2** so the seeded demo moves from about 300 (one chain) to about 520 (two chains), crossing the Silver gate of 400.
- Young wallets will have low age points. If a teammate has an older testnet-only wallet that never held real funds, linking it shows the age factor off. Fresh burners remain the default.

**Sybil Radar rules (deterministic, each with evidence)**

| Rule | Trigger | Risk points |
| --- | --- | --- |
| R1 Burst | over 60% of transactions inside any 1-hour window | 20 |
| R2 Circular flow | value returns to its origin within 3 hops among linked wallets | 25 |
| R3 Self-dealing loans | borrower and lender/counterparty both inside the passport | 25 |
| R4 Single counterparty | over 80% of transactions go to one address | 15 |
| R5 Script cadence | inter-transaction gaps vary under 5% of the mean, or identical repeated values | 15 |
| R6 Fresh and loud | account younger than 7 days with unusually high volume | 10 |

Risk is the sum, capped at 100. The AI step receives only aggregate features (no addresses), must return strict JSON `{suspicion, patterns[], explanation}`, and may adjust risk by at most ±10. The AI never touches the factor math, so a missing API key never changes a score.

**What-if Coach.** Clone the feature vector, add a hypothetical event (for example 'repay loan on time', 'vote on 3 proposals', 'link a wallet active on a 3rd chain'), rerun scoring, and show the delta. No chain calls.

## 10. Architecture

```
User + MetaMask (wallets A, B, C)
      |
 Frontend: HTML + JS + ethers v6 (Vercel/Netlify)
      |  user-signed txs                |  fetch() JSON
      v                                  v
Hub chain: Ethereum Sepolia      Backend: Flask + web3.py (Render)
  OmniRepRegistry                 - challenge + signature verification
  PassportBadge (SBT)               - adapters (Sepolia, Base Sepolia)
  LendLite (sample app)             - normalizer, scoring_v1, Sybil Radar
                                    - EIP-712 attestor (PRIVATE_KEY)
Second chain: Base Sepolia          - AI note (optional)
  OmniRepVerifier (accepts        - DB: SQLite -> Neon/Supabase
  signed attestation)
  Playground sources on BOTH chains: LoanPool, Governor, ContributionLog
```

**On-chain vs off-chain split (a likely judge question)**

| On-chain (public, permanent, cheap to read) | Off-chain (private or bulky) |
| --- | --- |
| passport owner, score, tier, risk, algo version, version number, updatedAt, inputHash, linksHash, linkedCount | link proofs and signatures, raw and normalized events, evidence list, AI notes, scoring config |

Nobody needs to trust the database: the bundle is hashed, the hash is on-chain, and anyone can recompute.

**Trust model.** One attestor key signs scores. The contract only accepts attestations from that key, bound to a passport, a version and a deadline, and only when submitted by the passport owner. Consequence: the attestor is a trusted oracle in v1. Mitigations: open scoring code, reproducible inputs, public history. Roadmap: multiple attestors, dispute window, ZK proofs.

## 11. Smart contracts

**OmniRepRegistry (Sepolia)**: import OpenZeppelin `EIP712` and `ECDSA` through Remix's npm import.

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;
// OmniRepRegistry: stores score + hashes, never personal data.

contract OmniRepRegistry /* is EIP712 */ {
    struct Passport {
        address owner; uint16 score; uint8 tier; uint8 sybilRisk;
        uint16 algoVersion; uint32 version; uint64 updatedAt;
        uint8 linkedCount; bytes32 inputHash; bytes32 linksHash;
    }
    struct Attestation {          // signed off-chain by the attestor (EIP-712)
        uint256 id; uint16 score; uint8 sybilRisk; uint16 algoVersion;
        uint8 linkedCount; bytes32 inputHash; bytes32 linksHash;
        uint32 version; uint64 deadline;
    }
    address public attestor;
    uint256 public count;
    mapping(uint256 => Passport) private passports;
    mapping(address => uint256) public passportOf;   // owner address -> id

    event PassportCreated(uint256 indexed id, address indexed owner);
    event ScorePublished(uint256 indexed id, uint32 version, uint16 score,
        uint8 tier, uint8 sybilRisk, bytes32 inputHash, bytes32 linksHash);

    function createPassport() external returns (uint256 id) {
        require(passportOf[msg.sender] == 0, 'already has passport');
        id = ++count;
        passports[id].owner = msg.sender;
        passportOf[msg.sender] = id;
        emit PassportCreated(id, msg.sender);
    }

    function publish(Attestation calldata a, bytes calldata sig) external {
        Passport storage p = passports[a.id];
        require(p.owner == msg.sender, 'not owner');
        require(block.timestamp <= a.deadline, 'attestation expired');
        require(a.version == p.version + 1, 'bad version');
        // require(_recover(a, sig) == attestor, 'bad attestor signature');
        p.score = a.score; p.tier = tierFor(a.score); p.sybilRisk = a.sybilRisk;
        p.algoVersion = a.algoVersion; p.version = a.version;
        p.updatedAt = uint64(block.timestamp); p.linkedCount = a.linkedCount;
        p.inputHash = a.inputHash; p.linksHash = a.linksHash;
        emit ScorePublished(a.id, a.version, a.score, p.tier, a.sybilRisk,
            a.inputHash, a.linksHash);
    }

    function tierFor(uint16 s) public pure returns (uint8) {
        return s >= 800 ? 4 : s >= 600 ? 3 : s >= 400 ? 2 : s >= 200 ? 1 : 0;
    }
    function scoreOf(uint256 id) external view returns (uint16) { return passports[id].score; }
    function tierOf(uint256 id) external view returns (uint8) { return passports[id].tier; }
    function meets(uint256 id, uint16 minScore, uint64 maxAge) external view returns (bool) {
        Passport storage p = passports[id];
        return p.version > 0 && p.score >= minScore
            && (maxAge == 0 || block.timestamp - p.updatedAt <= maxAge);
    }
    function verifyInputs(uint256 id, bytes32 h) external view returns (bool) {
        return passports[id].inputHash == h;
    }
}
```

The commented signature line must be implemented with EIP-712 (`_hashTypedDataV4` + `ECDSA.recover`). Treat it as P0: without it the contract trusts anyone.

**Other contracts**

| Contract | Chain | Purpose |
| --- | --- | --- |
| LendLite | Sepolia | Sample app. `borrow(amount)` requires `meets(passportOf(msg.sender), 400, 30 days)`; collateral basis points by tier (Silver 150%, Gold 120%, Platinum 100%). Records credit lines only, no real funds. |
| PassportBadge | Sepolia | Non-transferable ERC-721-style badge. `claim()` requires tier threshold; `transferFrom` reverts; token metadata generated on-chain. |
| OmniRepVerifier | Base Sepolia | Accepts the same EIP-712 attestation for a wallet and exposes `meets(wallet, min)`, so an app on a second chain can gate with no bridge. Attestation includes the subject wallet, score, deadline. |
| LoanPool | both | `borrow(amount)` creates a loan with a due date; `repay(id)` emits `Repaid(loanId, borrower, onTime)`; unpaid past due can be marked `Defaulted` by anyone. |
| Governor | both | `createProposal(text)`, `vote(id, support)`; emits `Voted`. |
| ContributionLog | both | `contribute(uri)` emits `Contributed`. |

Deploy order: Registry (Sepolia) → Playground on both chains → LendLite and Badge → Verifier on Base Sepolia. Verify every contract on its explorer (Solidity single file, same compiler as Remix, MIT, optimisation off). Re-copy ABIs into `backend/abi/` and `frontend/config.js` after every redeploy.
