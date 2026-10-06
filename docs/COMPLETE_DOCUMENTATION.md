# OmniRep Passport — Complete Project Documentation

> **Everything in one document.** Consolidated from the full source tree: contracts, backend, frontend, SDK, scripts, CI, deployments, and every file in `docs/`.
>
> Project: **OmniRep — Omnichain Reputation Passport**
> Track: **INNOBLOCK 2.0 · PS64 · Domain 7: Digital Identity**
> Build window: 5–7 Oct 2026 · Testnets only
> License: MIT — `Copyright (c) 2026 OmniRep Contributors`

---

## Table of Contents

1. [Overview](#1-overview)
2. [Repository Structure](#2-repository-structure)
3. [Architecture & Trust Model](#3-architecture--trust-model)
4. [Smart Contracts](#4-smart-contracts)
5. [Deployed Contract Addresses](#5-deployed-contract-addresses)
6. [Backend (Flask API)](#6-backend-flask-api)
7. [Scoring Model](#7-scoring-model)
8. [Indexer & Evidence Ingestion](#8-indexer--evidence-ingestion)
9. [Frontend (React/Vite)](#9-frontend-reactvite)
10. [SDK](#10-sdk)
11. [Scripts, CI & Deployment Automation](#11-scripts-ci--deployment-automation)
12. [Environment Variables](#12-environment-variables)
13. [Local Development Guide](#13-local-development-guide)
14. [Demo Scripts & Pitch](#14-demo-scripts--pitch)
15. [Checklists & Phase Status](#15-checklists--phase-status)
16. [Security Model](#16-security-model)
17. [Tests & Validation](#17-tests--validation)
18. [Known Gaps & Observations](#18-known-gaps--observations)
19. [Source Documents Index](#19-source-documents-index)

---

## 1. Overview

### 1.1 Positioning

> "OmniRep turns fragmented EVM wallet history into a portable, explainable reputation passport. A user proves control of multiple testnet addresses with signatures, the backend normalizes activity from Ethereum Sepolia + Base Sepolia, a transparent scoring engine produces a 0–1000 score, and a SHA-256 proof commitment is published on-chain for another application to consume."

One-line pitch: **"Your history should not reset when your wallet changes."**

### 1.2 What the system does (end-to-end)

1. A user creates a **passport** (an on-chain numeric ID) on Ethereum Sepolia.
2. The user **links multiple wallets** across two testnets by signing readable nonce challenges (`personal_sign`, no gas, no asset transfer).
3. The backend **indexes on-chain evidence** (loans, repayments, defaults, votes, contributions) plus generic wallet metrics (age, tx count, counterparties, gas).
4. A **deterministic scoring engine** (`omnirep_scoring_v2`) computes a 0–1000 score with a full per-factor breakdown, a confidence value, and a Sybil risk score.
5. A **SHA-256 proof commitment** (`inputHash`) over canonical JSON of all inputs is computed; `linksHash` commits to the linked-wallet set (addresses themselves are never published).
6. The backend signs an **EIP-712 attestation** with the attestor key; the passport owner submits `publish()` on-chain (owner pays gas).
7. `OmniRepRegistry` stores score, tier, risk, model/version metadata, hashes, version counter and linked count.
8. **Consumers** call one read — `meets(id, minScore, maxAge)` — to gate features. `LendLite` is the reference consumer.
9. An **independent verifier** recomputes the SHA-256 in the browser and compares it against the committed hash; mutating one character breaks the match.
10. A **portable attestation** can be accepted by `OmniRepVerifier` on Base Sepolia **without a bridge** (shared EIP-712 domain).

### 1.3 PS64 requirement coverage

| Requirement | Implementation |
|---|---|
| Wallet linking by signing with each wallet | Readable nonce + 300 s expiry challenge, `personal_sign`, verified server-side with `ecrecover` |
| Activity from 2+ testnets | Ethereum Sepolia + Base Sepolia RPC `eth_getLogs` adapters + optional Etherscan V2 enrichment |
| Explainable score | 0–1000 deterministic model: repayments, governance, contributions, longevity, activity quality, cross-chain, counterparty, consistency, penalties |
| Publish score + input hash to a queryable contract | `OmniRepRegistry` stores score, tier, risk, `inputHash`, `linksHash`, version; exposes `scoreOf`, `tierOf`, `meets`, `verifyInputs` |
| Consumer dApp gating a feature | `LendLite.borrow()` requires `meets(id, 400, 30 days)` |
| Good-to-have: AI sybil flagging | Sybil Radar rules R1–R6 + bounded, advisory AI second opinion |
| Good-to-have: badge levels | Soulbound ERC-721 `OmniRepBadge` at tiers 200/400/600/800 |

### 1.4 Key design principles

- **Passport-centric, not wallet-centric** — the passport is the identity object; secondary addresses stay off-chain.
- **Privacy by default** — only a commitment hash of the wallet set is published; consumers ask `meets 400?`, not "who is this?".
- **Deterministic scoring is the source of truth** — AI never generates or changes the final score.
- **Reputation ≠ confidence** — score and evidence confidence are separate reported concepts.
- **Sparse/new is not malicious** — evidence level and risk are reported separately from score.
- **Playground contracts** create semantic testnet events without moving real funds, so the demo is reproducible.
- **Testnets and burner wallets only. No personal data on-chain.**

---

## 2. Repository Structure

```
OmniRep-PS64-INNOBLOCK/
├── .env                          # Root deployment/backend env (gitignored)
├── .env.example                  # 28 variable names + non-secret defaults
├── .gitignore                    # node_modules, .env*, .venv, *.db, dist, artifacts, cache
├── .nvmrc                        # 22
├── .python-version               # 3.12
├── LICENSE                       # MIT (2026 OmniRep Contributors)
├── README.md                     # Landing page, setup, demo order
├── SECURITY.md                   # 7 security rules
├── hardhat.config.js             # Solidity 0.8.24, cancun, optimizer 200 runs, 2 networks
├── package.json                  # Root npm scripts + hardhat devDeps
├── render.yaml                   # Render blueprint (omnirep-api)
├── omnirep.db                    # Local SQLite runtime state (should not be committed)
├── .github/workflows/quality.yml # CI: syntax, py_compile, validate, frontend build, hardhat test
│
├── contracts/                    # 7 Solidity contracts (pragma ^0.8.24)
│   ├── OmniRepRegistry.sol       # Core registry (Ethereum Sepolia)
│   ├── OmniRepVerifier.sol       # Portable verifier (Base Sepolia)
│   ├── OmniRepBadge.sol          # Soulbound tier badge
│   ├── OmniRepContributionLog.sol# Contribution evidence source
│   ├── OmniRepGovernor.sol       # Governance evidence source
│   ├── OmniRepLoanPool.sol       # Loan evidence source
│   └── LendLite.sol              # Consumer dApp (gate demo)
│
├── backend/
│   ├── app.py                    # Flask app, all API routes
│   ├── config.py                 # env loading, CHAINS, MODEL_VERSION
│   ├── db.py                     # SQLAlchemy models / schema
│   ├── indexer.py                # event decoding + generic metrics
│   ├── scoring.py                # omnirep_scoring_v2 + Sybil radar + canonical JSON
│   ├── requirements.txt          # pinned dependencies
│   ├── .env / .env.example
│   └── omnirep.db                # local SQLite
│
├── frontend/
│   ├── index.html / vite.config.ts / tsconfig*.json / package.json
│   ├── .env.example / .env.local
│   ├── dist/                     # production build output
│   └── src/
│       ├── App.tsx               # entire SPA (10 screens)
│       ├── main.tsx / styles.css / vite-env.d.ts
│       ├── components/BrandMark.tsx
│       ├── components/ui/{SpotlightCard,ShimmerButton,BorderBeam,NumberTicker}.tsx
│       └── lib/{api.ts,config.ts}
│
├── sdk/
│   ├── PassportGate.sol          # IPassportGate interface
│   ├── omnirep.js                # meetsOmniRep() helper
│   └── README.md
│
├── scripts/
│   ├── deploy.js                 # Ethereum Sepolia deploy (6 contracts)
│   ├── deploy-base.js            # Base Sepolia deploy (4 contracts)
│   ├── deployment-preflight.js   # env/key validation before deploy
│   ├── deploy.sh / deploy.ps1    # shell orchestration
│   ├── validate.py               # static project validation (CI)
│   └── offline_smoke.py          # dependency-light logic smoke test
│
├── deployments/
│   ├── ethereum-sepolia.json     # authoritative address manifest
│   └── base-sepolia.json
│
├── test/OmniRep.js               # Hardhat + Chai suite (3 tests)
├── artifacts/ cache/             # build outputs
└── docs/                         # 13 documents (see §19)
    ├── ARCHITECTURE.md  PRD.md  PITCH.md  DEMO_SCRIPT.md
    ├── DEPLOYMENT.md  FINAL_CHECKLIST.md  IMPLEMENTATION_NOTES.md
    ├── INNOBLOCK_DAY2_RUN.md  LIVE_RUNBOOK.md  OPERATIONS_RUNBOOK.md
    ├── PHASE_STATUS.md  SCORING.md  UI_SOURCES.md
    └── COMPLETE_DOCUMENTATION.md (this file)
```

---

## 3. Architecture & Trust Model

### 3.1 System diagram

```
React UI (wallet linking · score · verifier)
   │ REST + ethers.js
Flask API (auth · indexer · scoring · proofs)
   ├──► PostgreSQL/SQLite (detailed records)
   └──► Ethereum Sepolia RPC + Base Sepolia RPC
             │ normalized activity
             ▼
      Reputation Engine (score + risk + confidence + why)
             │ canonical JSON
             ▼
      SHA-256 proof input
             │ EIP-712 attestation
             ▼
      OmniRepRegistry (score · tier · risk · hash · version · linked-count)
             │ read-only
             ▼
      LendLite (consumer dApp)

Base Sepolia side path:
   attestor EIP-712 proof → OmniRepVerifier → meets(subject)
```

### 3.2 On-chain vs off-chain data boundary

| Off-chain (private DB) | On-chain (public, compact) |
|---|---|
| Linked wallet addresses + signatures | Passport owner address |
| Raw + normalized events | Final score, tier, Sybil risk |
| Evidence list with explorer links | Model version + version counter |
| Generic wallet metrics | SHA-256 `inputHash`, `linksHash` |
| Scoring breakdown & config | Linked count, `updatedAt` timestamp |
| Sybil features, AI explanation | — |
| Full proof bundle | — |

Rationale: *"keeps the expensive public ledger compact while preserving a verifiable fingerprint of the detailed record."* Nobody needs to trust the database — the bundle is hashed, the hash is on-chain, and anyone can recompute it.

### 3.3 Trust model (7 steps)

1. User wallet proves control by signing a server-issued nonce challenge.
2. Indexer derives evidence from public blockchain data.
3. Deterministic engine calculates the score.
4. Optional AI receives aggregate behavioral features only → second opinion (advisory).
5. Backend signs a bounded EIP-712 attestation.
6. Passport owner publishes the attestation on-chain (owner pays gas).
7. Consumer applications read the on-chain registry instead of trusting OmniRep's UI.

The attestor is a **trusted oracle in v1**; mitigations: open scoring code, reproducible inputs, public version history. Roadmap: multiple attestors, dispute window, ZK proofs.

### 3.4 EIP-712 domain (shared across chains)

```
name     = "OmniRep Passport"
version  = "1"
salt     = keccak256("OmniRep.Portable.Attestation.v1")
typehash = EIP712Domain(string name,string version,bytes32 salt)   // no chainId, no verifyingContract
```

Because the domain deliberately omits `chainId`/`verifyingContract`, signatures are chain-portable. Replay is prevented by payload guards instead: `msg.sender == owner` (Registry) or `subject == msg.sender` (Verifier) plus a strictly monotonic `version` and a `deadline` (900 s).

Two struct types share the domain:

- **`Attestation`** (Registry): `(uint256 id, uint16 score, uint8 sybilRisk, uint16 algoVersion, uint8 linkedCount, bytes32 inputHash, bytes32 linksHash, uint32 version, uint64 deadline)`
- **`PortableAttestation`** (Verifier): `(address subject, uint256 id, uint16 score, uint8 sybilRisk, uint32 version, uint64 deadline, bytes32 proofHash)`

---

## 4. Smart Contracts

All contracts: `// SPDX-License-Identifier: MIT`, `pragma solidity ^0.8.24`.

### 4.1 `OmniRepRegistry.sol` — core registry

Cross-chain reputation anchor. *Linked wallet addresses are never published.* Inherits OpenZeppelin `Ownable`; uses `ECDSA`.

**Constants**
| Name | Value |
|---|---|
| `NAME` | `"OmniRep Passport"` |
| `VERSION` | `"1"` |
| `SALT` | `keccak256("OmniRep.Portable.Attestation.v1")` |
| `DOMAIN_TYPEHASH` | `keccak256("EIP712Domain(string name,string version,bytes32 salt)")` |
| `ATTESTATION_TYPEHASH` | `keccak256("Attestation(uint256 id,uint16 score,uint8 sybilRisk,uint16 algoVersion,uint8 linkedCount,bytes32 inputHash,bytes32 linksHash,uint32 version,uint64 deadline)")` |
| `DOMAIN_SEPARATOR` | immutable, computed in constructor |

**Structs**
```solidity
struct Passport {
    address owner; uint16 score; uint8 tier; uint8 sybilRisk;
    uint16 algoVersion; uint32 version; uint64 updatedAt;
    uint8 linkedCount; bytes32 inputHash; bytes32 linksHash;
}
struct Attestation {
    uint256 id; uint16 score; uint8 sybilRisk; uint16 algoVersion;
    uint8 linkedCount; bytes32 inputHash; bytes32 linksHash;
    uint32 version; uint64 deadline;
}
```

**State:** `uint256 public count` (IDs start at 1; 0 = no passport), `address public attestor`, `mapping(uint256 => Passport) private passports`, `mapping(address => uint256) public passportOf`.

**Events**
```solidity
event PassportCreated(uint256 indexed id, address indexed owner);
event AttestorUpdated(address indexed attestor);
event ScorePublished(uint256 indexed id, uint32 indexed version, uint16 score,
    uint8 tier, uint8 sybilRisk, bytes32 inputHash, bytes32 linksHash);
```

**Functions**
| Signature | Behavior |
|---|---|
| `createPassport() external returns (uint256)` | Reverts `"already has passport"`; assigns `id = ++count`, maps `passportOf[msg.sender]`, emits `PassportCreated`. Permissionless, one per address. |
| `setAttestor(address) external onlyOwner` | Reverts `"attestor required"` if zero; emits `AttestorUpdated`. |
| `publish(Attestation calldata a, bytes calldata sig) external` | Checks in order: owner match → deadline not expired → `a.version == p.version + 1` (replay protection) → `score <= 1000` → `sybilRisk <= 100` → `linkedCount > 0` → `inputHash != 0` → `linksHash != 0` → `_recover(a,sig) == attestor`. Writes all fields, `tier = tierFor(score)`, `updatedAt = block.timestamp`; emits `ScorePublished`. |
| `tierFor(uint16) public pure returns (uint8)` | `≥800→4`, `≥600→3`, `≥400→2`, `≥200→1`, else `0`. |
| `meets(uint256 id, uint16 minScore, uint64 maxAge) external view returns (bool)` | **Consumer gate.** false if never attested (`version==0`) or `score < minScore`; if `maxAge != 0`, false when `block.timestamp - updatedAt > maxAge`. |
| `scoreOf / tierOf / ownerOfPassport / getPassport` | View accessors. |
| `verifyInputs(uint256 id, bytes32 h) view returns (bool)` | `inputHash == h`. |
| `verifyInputBytes(uint256 id, bytes calldata raw) view returns (bool)` | `inputHash == sha256(raw)` (SHA-256 precompile). |

**Access control:** owner → `setAttestor`; attestor key → signs; passport owner → submits `publish`; anyone → `createPassport` + views.

### 4.2 `OmniRepVerifier.sol` — portable verifier (Base Sepolia)

Accepts a wallet-scoped attestation on another testnet — **no bridge required**. No Ownable; `attestor` is `immutable` at deploy time.

**Structs:** `PortableAttestation {subject, id, score, sybilRisk, version, deadline, proofHash}`, `Accepted {id, score, sybilRisk, version, acceptedAt, proofHash}`.

**Event:** `AttestationAccepted(address indexed subject, uint256 indexed id, uint16 score, uint8 sybilRisk, uint32 version, bytes32 proofHash)`.

| Signature | Behavior |
|---|---|
| `accept(PortableAttestation a, bytes sig) external` | Requires deadline valid, `a.subject == msg.sender` ("subject must submit"), `a.version > accepted[msg.sender].version` ("old attestation"), valid attestor signature. Stores record, emits event. |
| `meets(address subject, uint16 minScore, uint64 maxAge) view returns (bool)` | Same semantics as Registry, keyed by address. |

### 4.3 `OmniRepBadge.sol` — soulbound tier badge

Non-transferable ERC-721 (`"OmniRep Reputation Badge"`, symbol `OMNI`) gated by Registry tier via local interface `IRegistryTier { passportOf, tierOf }`.

| Signature | Behavior |
|---|---|
| `claim() external returns (uint256)` | Requires a passport (`"no passport"`) and `tier >= 1` (`"bronze required"`); `tokenId = ++nextTokenId`; snapshots `tokenTier[tokenId]`; `_safeMint`; emits `BadgeClaimed(owner, tokenId, tier)`. Unlimited claims per address (no cap). |
| `_update(to, tokenId, auth) internal override` | Soulbound: reverts `"soulbound"` on any transfer where both `from` and `to` are non-zero (mint and burn allowed). |
| `tokenURI(uint256) public view override` | Fully on-chain data URI: base64 JSON + base64 `image` (`data:text/plain;base64,...` of "OMNIREP BADGE"). |

### 4.4 `OmniRepContributionLog.sol` — contribution evidence

No state, no imports. Single function:

```solidity
event Contributed(address indexed contributor, bytes32 indexed projectId, uint256 units, uint256 timestamp);
function contribute(bytes32 projectId, uint256 units) external;  // reverts "project required" if projectId == 0
```

Fully permissionless; consumed by the off-chain indexer.

### 4.5 `OmniRepGovernor.sol` — governance evidence

```solidity
struct Proposal { string text; uint256 yes; uint256 no; }
uint256 public nextId;
mapping(uint256 => Proposal) public proposals;
mapping(uint256 => mapping(address => bool)) public voted;
event ProposalCreated(uint256 indexed id, address indexed creator, string text);
event Voted(uint256 indexed id, address indexed voter, bool support);

function createProposal(string calldata text) external returns (uint256 id);
function vote(uint256 id, bool support) external;   // "proposal missing" / "already voted"
```

One address, one vote, forever — no quorum, no period, no execution. Demo/evidence only.

### 4.6 `OmniRepLoanPool.sol` — loan evidence ledger

*Never holds or moves funds* — records loan lifecycle and emits typed events.

```solidity
struct Loan { address borrower; uint256 amount; uint64 dueAt; bool repaid; }
event Borrowed(uint256 indexed loanId, address indexed borrower, uint256 amount, uint64 dueAt);
event Repaid(uint256 indexed loanId, address indexed borrower, bool onTime);
event Defaulted(uint256 indexed loanId, address indexed borrower);
```

| Function | Behavior |
|---|---|
| `borrow(uint256 amount, uint64 duration)` | Creates loan, `dueAt = now + duration`, emits `Borrowed`. |
| `borrowAndRepay(uint256 amount)` | **Demo helper** — creates and repays in one tx without moving funds; emits `Borrowed` + `Repaid(onTime=true)`. |
| `borrowAndDefault(uint256 amount)` | **Demo helper** — creates a loan already past due; emits `Borrowed` + `Defaulted`. |
| `repay(uint256 id)` | Only recorded borrower; `"already repaid"` guard; emits `Repaid(onTime = now <= dueAt)`. |
| `markDefaulted(uint256 id)` | Anyone; requires borrower set and `!repaid && now > dueAt`; emits `Defaulted` (event-only, no flag set — can be re-emitted). |

### 4.7 `LendLite.sol` — consumer dApp

*"Demo consumer app. It records credit lines, never transfers real funds."* Uses local interface `IOmniRepRegistry { passportOf, meets, tierOf }`.

```solidity
mapping(address => uint256) public creditLine;
event BorrowApproved(address indexed borrower, uint256 passportId, uint256 amount,
                     uint8 tier, uint256 collateralBps);

function borrow(uint256 amount) external {
    id = registry.passportOf(msg.sender);              // "no OmniRep passport" if 0
    require(registry.meets(id, 400, 30 days),          // Silver + fresh proof required
            "OmniRep Silver + fresh proof required");
    tier = registry.tierOf(id);
    collateralBps = tier==4 ? 10000 : tier==3 ? 12000 : tier==2 ? 15000 : 20000;
    creditLine[msg.sender] += amount;
    emit BorrowApproved(...);
}
```

Gate: **score ≥ 400 (Silver) attested within the last 30 days (2,592,000 s)**. Collateral bps values are informational (emitted only, never enforced).

### 4.8 Cross-contract interaction map

```
            (off-chain attestor signs EIP-712 with ATTESTOR_PRIVATE_KEY)
                                 │
   ┌─────────────────────────────┼──────────────────────────────┐
   ▼                             ▼                              ▼
OmniRepRegistry ◄─ IRegistryTier ─ OmniRepBadge     OmniRepVerifier (Base Sepolia)
(Ethereum Sepolia)  passportOf/tierOf (soulbound)    accepts PortableAttestation,
   │              ◄─ IOmniRepRegistry ─┐             same domain, immutable attestor
   │  passportOf / meets / tierOf      ▼
   ▼                               LendLite gate: score ≥ 400, maxAge 30 d

Standalone (no on-chain deps), deployed on both chains, consumed by the indexer:
  OmniRepLoanPool        → Borrowed / Repaid / Defaulted
  OmniRepGovernor        → ProposalCreated / Voted
  OmniRepContributionLog → Contributed
```

The SDK's `IPassportGate.meets(uint256,uint16,uint64)` matches `OmniRepRegistry.meets` exactly, so the Registry satisfies the SDK interface directly.

---

## 5. Deployed Contract Addresses

Authoritative manifests: `deployments/ethereum-sepolia.json`, `deployments/base-sepolia.json`.

**Ethereum Sepolia (chainId 11155111)** — deployed 2026-10-06T12:10:50.798Z
| Contract | Address |
|---|---|
| OmniRepRegistry | `0x9680058Ace2b364C837ae184214b8f55688A52cA` |
| OmniRepLoanPool | `0x707450D32c9774d77C3B26D70C6235a6404C9e33` |
| OmniRepGovernor | `0x9b6663eC055CB0638F6Db125500AF99A311998a5` |
| OmniRepContributionLog | `0xF9E3BCE8a3cEb2A994C43Bea96e971585d5A3F26` |
| LendLite | `0xE7Aa207004B4E1aC17296CE4A4979c4FF50787EF` |
| OmniRepBadge | `0xd6f69de9806403BD6424ae21c3A6Ba2c2998fDB7` |

**Base Sepolia (chainId 84532)** — deployed 2026-10-06T12:11:15.294Z
| Contract | Address |
|---|---|
| OmniRepVerifier | `0x9680058Ace2b364C837ae184214b8f55688A52cA` |
| OmniRepLoanPool | `0x707450D32c9774d77C3B26D70C6235a6404C9e33` |
| OmniRepGovernor | `0x9b6663eC055CB0638F6Db125500AF99A311998a5` |
| OmniRepContributionLog | `0xF9E3BCE8a3cEb2A994C43Bea96e971585d5A3F26` |

**Deployer / attestor (both chains):** `0x99f7eCb07E5c405c0d24Ca0416E9BaE58f6075cF`

Explorer links:
- Registry: `https://sepolia.etherscan.io/address/0x9680058Ace2b364C837ae184214b8f55688A52cA`
- LendLite: `https://sepolia.etherscan.io/address/0xE7Aa207004B4E1aC17296CE4A4979c4FF50787EF`
- Verifier: `https://sepolia.basescan.org/address/0x9680058Ace2b364C837ae184214b8f55688A52cA`

> Identical addresses across both chains are expected: same deployer, aligned nonces, deterministic CREATE addresses (nonce 0 → Registry/Verifier, 1 → LoanPool, 2 → Governor, 3 → ContributionLog, 4 → LendLite, 5 → Badge).

**Verification settings:** Solidity `0.8.24`, optimizer enabled, **200 runs**, EVM `cancun` (must match `hardhat.config.js` when verifying on the explorer).

---

## 6. Backend (Flask API)

Stack: Flask 3.1.2 · flask-cors 6.0.1 · SQLAlchemy 2.0.43 · web3 7.14.0 · eth-account 0.13.7 · python-dotenv 1.1.1 · requests 2.32.5 · gunicorn 23.0.0 · psycopg[binary] (Postgres).

Runs on `0.0.0.0:$PORT` (default 5000). CORS for `/api/*` allows `FRONTEND_ORIGIN` (default `http://localhost:5173`) and `http://127.0.0.1:5173`.

Error convention: JSON `{"error": "<code>"}` (sometimes with `"message"`) + proper HTTP status. Missing passport → `404 passport_not_found`.

### 6.1 Endpoint reference

| # | Method & path | Purpose |
|---|---|---|
| 1 | `GET /health` | DB + per-chain RPC + config booleans + `modelVersion` |
| 2 | `GET /` | Service banner |
| 3 | `POST /api/passports` | Create/verify local passport record |
| 4 | `POST /api/passports/recover` | Re-create passport row from on-chain ownership |
| 5 | `POST /api/auth/challenge` | Issue SIWE-style linking message + nonce (300 s) |
| 6 | `POST /api/auth/verify` | Verify signature, insert `WalletLink` |
| 7 | `GET /api/passports/<pid>` | Full passport payload |
| 8 | `POST /api/passports/<pid>/sync` | Index both chains + generic metrics |
| 9 | `POST /api/passports/<pid>/score` | Compute + persist score and hashes |
| 10 | `GET /api/passports/<pid>/risk` | Sybil radar + AI second opinion |
| 11 | `POST /api/passports/<pid>/attestation` | Sign EIP-712 `Attestation` |
| 12 | `GET /api/passports/<pid>/bundle` | Portable proof bundle |
| 13 | `POST /api/passports/<pid>/portable-attestation` | Sign `PortableAttestation` for Base |
| 14 | `POST /api/passports/<pid>/published` | Record on-chain publication (verified) |
| 15 | `POST /api/passports/<pid>/verify` | Recompute and compare proof hash |
| 16 | `GET /api/passports/<pid>/history` | Last 50 score runs |
| 17 | `GET /api/passports/<pid>/receipt` | Compact audit receipt |
| 18 | `POST /api/passports/<pid>/what-if` | Simulated score delta (never persists) |
| 19 | `POST /api/ai/analyze` | Explicit AI second opinion |

### 6.2 Endpoint details

**`GET /health`**
```json
{"ok": true, "database": true,
 "chains": {"ethereum-sepolia": true, "base-sepolia": true},
 "registryConfigured": true, "verifierConfigured": true,
 "attestorConfigured": true, "modelVersion": 20001}
```

**`POST /api/passports`** — body `{passportId, ownerAddress, txHash?}`. When `REGISTRY_ADDRESS` is configured, `txHash` is required and verified on Sepolia: receipt `status == 1`, `to == registry`, `from == owner`, and a matching `PassportCreated(id, owner)` event. Errors: `passportId_and_owner_required`, `creation_tx_hash_required`, `sepolia_rpc_unavailable` (503), `creation_transaction_failed`, `creation_not_sent_to_registry`, `creation_sender_mismatch`, `passport_creation_event_mismatch`, `creation_not_confirmed`, `owner_already_has_passport` (409). Idempotent for an existing identical record → `{"passportId", "chainVerified"}`.

**`POST /api/passports/recover`** — body `{passportId, ownerAddress}`. Reads `ownerOfPassport(pid)` on-chain; mismatch → `403 passport_owner_mismatch`; owner already has a different passport → `409`; row created → `{"recovered": true}`.

**`POST /api/auth/challenge`** — body `{address, passportId, chainId}`; chainId must be `11155111` or `84532`. Generates a `token_urlsafe(24)` nonce, 300 s expiry. Message format:

```
OmniRep Reputation Passport

Link wallet {checksummed address} to passport #{pid}.
Chain ID: {chain_id}
Nonce: {nonce}
Issued: {issued}
Expires: {expires}

I understand this signature proves control of this wallet only and transfers no funds.
```
Response `{message, nonce, expiresAt}`. Errors: `invalid_address`, `unsupported_chain`, `passport_not_found`, `address_already_linked` (409).

**`POST /api/auth/verify`** — body `{address, signature, message, passportId, chainId, nonce}`. Loads challenge by nonce, checks expiry/match, recovers signer with `encode_defunct`, rejects links already bound to another passport. Response `{ok: true, address, chainId}`. Errors: `challenge_missing/expired/mismatch`, `signature_invalid`, `ownership_not_proved`, `wallet_already_linked_to_other_passport`.

**`GET /api/passports/<pid>`** — returns `passportPayload`: `passportId, ownerAddress, score, confidence, sybilRisk, tier, inputHash, linksHash, modelVersion, version, updatedAt, lastSyncAt, publishedTxHash, publishedChain, linkedCount, wallets[] (verified only, sorted), activityCount, activities[] (max 250, newest first), genericMetrics, lastBreakdown, lastRisk`.

Activity shape: `{id, passportId, chainId, chainName, address, txHash, blockNumber, timestamp, activityType, source, contractAddress, amount, qualityGrade, details}`.

**`POST /api/passports/<pid>/sync`** — requires ≥2 verified wallets (`link_two_wallets_first`) on ≥2 distinct chains (`link_two_testnets`). Runs `decode_and_collect` per chain plus `fetch_generic_metrics` per wallet. Activity IDs are `"{chainId}:{txHash}:{activityType}"` (deduped). Response `{ok, addedCount, added[], errors[], genericMetrics, chainsRequested}`. Per-chain failures are non-fatal.

**`POST /api/passports/<pid>/score`** — runs `score_reputation`, adds `modelVersion`, `evidenceCount`, `tier`; builds canonical hash input (`schema: omnirep-proof-input-v1`) and computes `inputHash`/`linksHash`; persists to `Passport` and appends a `ScoreRun`. Returns the full scoring result plus both hashes.

**`GET /api/passports/<pid>/risk`** — `{risk 0–100, label, reasons[], rules{R1..R6}, features{burstRatio, counterpartyDiversity, repeatRatio, cadenceCv, activityCount, linkedWallets}, aiSecondOpinion{provider, suspicion, patterns, explanation, fallbackReason?}}`.

**`POST /api/passports/<pid>/attestation`** — requires ≥2 wallets (`two_wallets_required`) and a prior score (`score_before_publish`). Signs EIP-712 `Attestation` with `version = p.version + 1`, `deadline = now + 900`. Returns `{message, signature, typedData, attestor}`.

**`GET /api/passports/<pid>/bundle`** — `{schema: "omnirep-proof-bundle-v1", passportId, owner, walletProofs[], activities[], genericMetrics, algorithm{version, name, weights}, scored{score, confidence, sybilRisk, tier, breakdown, risk, features, freshnessMultiplier}, hashInput, inputHash, published{...}}`.

**`POST /api/passports/<pid>/portable-attestation`** — requires ≥1 wallet (`wallet_required`) and a published primary proof (`publish_primary_proof_first`); signs `PortableAttestation` with `proofHash = input_hash`, `deadline = now + 900`.

**`POST /api/passports/<pid>/published`** — body `{txHash, version}`. Verifies the publication tx on-chain (status, `to`, `from`, matching `ScorePublished` event fields) before recording. `version` must equal `p.version + 1` else `409 version_mismatch`.

**`POST /api/passports/<pid>/verify`** — optional body `{hash}`; returns `{passportId, computedHash, committedHash, match, suppliedHashMatch, version}`.

**`GET /api/passports/<pid>/history`** — `{history: [{score, confidence, modelVersion, inputHash, createdAt}]}` (latest 50).

**`GET /api/passports/<pid>/receipt`** — `{passportId, score, confidence, sybilRisk, tier, modelVersion, version, inputHash, linksHash, evidenceCount, chains[], wallets, publishedTxHash, publishedChain}`.

**`POST /api/passports/<pid>/what-if`** — body `{action}`; supported actions/aliases:
| Action | Simulation |
|---|---|
| `repay_on_time` | 1 `loan_repaid` with `details.onTime: true` |
| `vote` / `vote_3` | 3 `vote` activities, 1 h apart, proposalIds 900001–900003 |
| `contribution` | 1 `contribution` activity |
| `third_chain` / `link_third_chain` | quality-A activity on chainId 421614 (Arbitrum Sepolia, simulated) |
| other | `400 unsupported_action` |

Response `{action, currentScore, projectedScore, delta, simulated: true}`.

**`POST /api/ai/analyze`** — body `{features}`. If `AI_API_KEY` + `AI_BASE_URL` + `AI_MODEL` set: POST `{AI_BASE_URL}/chat/completions`, `temperature: 0`, 20 s timeout, JSON parsed from fenced content, suspicion clamped 0–100. Any failure → deterministic fallback (`burstRatio>0.6 → +35`, `repeatRatio>0.6 → +35`, `counterpartyDiversity≤1 && activityCount≥4 → +20`, cap 100) with `fallbackReason`. **Never changes the reputation score.**

### 6.3 Database schema (SQLAlchemy)

**`passports`** — `id` (String 80, PK), `owner_address` (42, indexed), `created_at`, `score` (0–1000), `confidence`, `sybil_risk`, `tier`, `input_hash` (66), `links_hash` (66), `model_version` (default 10001; code writes 20001), `version`, `updated_at`, `last_sync_at`, `published_tx_hash` (80), `published_chain` (default `ethereum-sepolia`), `generic_metrics` (JSON text).

**`auth_challenges`** — `nonce` (120, PK), `passport_id`, `address`, `chain_id`, `message` (text), `expires_at` (unix, indexed).

**`wallet_links`** — `id` (PK auto), `passport_id`, `address`, `chain_id`, `signature`, `nonce`, `verified_at`, `status` (default `verified`); unique `(passport_id, address, chain_id)`; index `(passport_id, status)`.

**`activities`** — `id` (140, PK = `chainId:txHash:activityType`), `passport_id`, `chain_id`, `chain_name`, `address`, `tx_hash`, `block_number`, `timestamp`, `activity_type`, `source` (e.g. `LOANPOOL_EVENT`, `WHAT_IF`), `contract_address`, `normalized_amount`, `quality_grade` (default `C`, indexed events stored as `A`), `details` (JSON: counterparty, chainKey, loanId, onTime, proposalId, support, projectId, dueAt); indexes on `(passport_id, timestamp)` and `(passport_id, activity_type)`.

**`score_runs`** — `id`, `passport_id`, `score`, `confidence`, `model_version`, `input_hash`, `breakdown_json`, `risk_json`, `created_at`.

### 6.4 Registry ABI used by the backend

Events `PassportCreated(uint256 id indexed, address owner indexed)`, `ScorePublished(uint256 id indexed, uint32 version indexed, uint16 score, uint8 tier, uint8 sybilRisk, bytes32 inputHash, bytes32 linksHash)`; views `count()`, `getPassport(uint256)`, `ownerOfPassport(uint256)`, `meets(uint256,uint16,uint64)`.

---

## 7. Scoring Model

Model: **`omnirep_scoring_v2`**, version **20001**, scale **0–1000**, fully deterministic.

### 7.1 Configuration (embedded in the proof hash)

```python
CONFIG = {
  "model": "omnirep_scoring_v2",
  "version": 20001,
  "scale": 1000,
  "weights": {
    "repayments": 220, "governance": 90, "contributions": 90,
    "wallet_longevity": 170, "activity_quality": 130, "cross_chain": 110,
    "counterparty": 70, "consistency": 120, "penalties": -200,
  },
  "freshnessFloor": 0.60,
  "sybilMaxPenalty": 0.50,
}
```

Changing any weight changes every proof hash — weights are part of the committed input.

### 7.2 Helpers

- `canonical_json(v)` = `json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=True)`
- `clamp(v, 0, 1000)`
- `exp_score(x, k) = 1 - exp(-max(0,x)/k)` — saturating curve
- `classify_risk(r)`: `high ≥ 60`, `medium ≥ 30`, else `low`
- Quality grades: `A=1.0`, `B=0.8`, `C=0.55`, unknown `=0.5`

### 7.3 Feature extraction

- **Repayments:** on-time (`details.onTime` truthy), late (`onTime` falsy), defaults (`loan_defaulted`).
- **Votes:** distinct `proposalId` (fallback `txHash`) among `vote` activities.
- **Contributions:** count of `contribution` activities.
- **Chains:** normalized chain keys from activities + any metric row with `txCount > 0`.
- **Active weeks:** distinct `timestamp // 604800` buckets.
- **Counterparties:** distinct `details.counterparty` + all metric `counterparties[]`.
- **Longevity:** `firstSeen` = min metric firstSeen else oldest activity; `age_days`, `observed_days`, `idle_days`.
- **Tx signals:** sum `txCount`, `successfulContractInteractions`, `gasSpentEth`.

### 7.4 Factor formulas

| # | Factor | Max | Formula |
|---|---|---|---|
| 1 | Repayments | 220 | `220 × (1 − e^(−(onTime + 0.5×late)/4))` |
| 2 | Governance | 90 | `90 × (1 − e^(−votes/6))` |
| 3 | Contributions | 90 | `90 × (1 − e^(−contributions/5))` |
| 4 | Wallet longevity | 170 | `110 × min(1, ageDays/180) + 60 × min(1, activeWeeks/12)` |
| 5 | Activity quality | 130 | `130 × (0.55×quality + 0.25×txSignal + 0.20×contractSignal)` where `txSignal = min(1, log1p(tx)/log1p(120))`, `contractSignal = min(1, successful/35)` |
| 6 | Cross-chain | 110 | `0 chains → 0`, `1 → 45`, `2 → 85`, `3+ → 110` |
| 7 | Counterparty diversity | 70 | `70 × (1 − e^(−counterparties/10))` |
| 8 | Consistency | 120 | `120 × (0.55×min(1, activeWeeks/10) + 0.45×activeDayRatio)` |
| 9 | Penalties | −200 | `−min(200, 70 × defaults)` |

Empty state (no activities and no metrics): score 0, confidence 0, risk 0.

### 7.5 Multipliers and final score

```
sybil_multiplier = max(0.50, 1 − risk/200)          # risk 0 → 1.0; 60 → 0.70; 100 → 0.50
freshness        = max(0.60, 0.5 ^ (idle_days/120)) # 120-day half-life, floor 60%
final            = clamp(base × sybil_multiplier × freshness, 0, 1000)
```

### 7.6 Confidence (0–100)

```
confidence = min(100, round(100 × (0.30×min(1, activities/12)
                                 + 0.25×min(1, chains/2)
                                 + 0.20×evidence_quality
                                 + 0.15×metric_quality
                                 + 0.10×min(1, wallets/2))))
```
`metric_quality` = fraction of generic-metric rows with `ok == true`.

### 7.7 Sybil Radar (deterministic rules)

| Rule | Trigger | Points |
|---|---|---|
| R1 Burst | >60% of activity inside any 1-hour window (`burstRatio`) | 20 |
| R2 Circular flow | an activity's `counterparty` is itself a linked address | 25 |
| R3 Self-dealing loans | `loan_*` activity whose counterparty is linked | 25 |
| R4 Single counterparty | max share of transactions to one address > 80% | 15 |
| R5 Script cadence | `cadenceCv < 0.05` OR `repeatRatio > 0.60` | 15 |
| R6 Fresh & loud | account age < 7 days AND > 20 activities | 10 |

Total capped at 100. Features exposed: `burstRatio, counterpartyDiversity, repeatRatio, cadenceCv, activityCount, linkedWallets`. Labels: low < 30 ≤ medium < 60 ≤ high.

### 7.8 AI second opinion (advisory only)

Receives aggregate features only (no addresses), returns `{suspicion 0–100, patterns[≤6], explanation[≤800]}`. Bounded and non-binding: **it never changes the score.** Deterministic fallback rules (burst +35, repeat +35, single-counterparty +20, cap 100) guarantee the demo works with no API key. PRD bound: AI may adjust risk by at most ±10 points.

### 7.9 Tiers

| Tier | Name | Score |
|---|---|---|
| 4 | Diamond | 800–1000 |
| 3 | Gold | 600–799 |
| 2 | Silver | 400–599 |
| 1 | Bronze | 200–399 |
| 0 | Iron | 0–199 |

(Identical thresholds to `tierFor()` on-chain. The PRD's older naming used "Newcomer"/"Platinum" for tiers 0/4; the checklist standardizes on **Iron/Bronze/Silver/Gold/Diamond**.)

### 7.10 Proof hashing

```
hashInput = {
  schema: "omnirep-proof-input-v1",
  passportId,
  wallets: [(address.lower(), chainId)...] sorted,
  activities: serialized, sorted by id,
  genericMetrics,
  scoringConfig: CONFIG
}
inputHash = "0x" + sha256(canonical_json(hashInput))
linksHash = "0x" + sha256(canonical_json(sorted wallet list))
```

`POST .../verify` and the browser Verifier both recompute this exact value.

---

## 8. Indexer & Evidence Ingestion

**No background daemon** — indexing is request-driven by `POST /api/passports/<pid>/sync`. Each call performs a single-pass `eth_getLogs` scan over a lookback window (`INDEXER_BLOCK_WINDOW`, default 20000 blocks).

### 8.1 Chains

| Key | Chain ID | Name | RPC env | Explorer tx prefix |
|---|---|---|---|---|
| `ethereum-sepolia` | 11155111 | Ethereum Sepolia | `ETH_RPC_URL` | `https://sepolia.etherscan.io/tx/` |
| `base-sepolia` | 84532 | Base Sepolia | `BASE_RPC_URL` | `https://sepolia.basescan.org/tx/` |

### 8.2 Indexed contracts and events (only if the env address is set)

| Contract | Events → activity type | Actor field |
|---|---|---|
| LoanPool | `Borrowed` → `loan_borrowed`; `Repaid` → `loan_repaid` (details.onTime); `Defaulted` → `loan_defaulted` | `borrower` |
| Governor | `Voted` → `vote` (details: proposalId, support) | `voter` |
| ContributionLog | `Contributed` → `contribution` (amount = units) | `contributor` |

All decoded events get `qualityGrade: "A"`, `source: "<CONTRACT>_EVENT"`.

### 8.3 Scan algorithm

1. `Web3.HTTPProvider(rpc, timeout=20)`.
2. `start = max(0, latest − INDEXER_BLOCK_WINDOW)`.
3. For each contract/event: `topic0 = keccak("Name(type,...)")` → `eth_getLogs({address, fromBlock, toBlock, topics})`; failures silently skipped.
4. Decode via `process_log`; filter actors against the linked wallet set (case-insensitive); block timestamp fetched (`0` on failure).

### 8.4 Generic wallet metrics (`fetch_generic_metrics`)

Skeleton: `{source: "rpc", fetchedAt, ok, txCount, firstSeen, counterparties: [], successfulContractInteractions: 0, gasSpentEth: 0.0}`.

- RPC `get_transaction_count` for `txCount`.
- With `ETHERSCAN_API_KEY`: Etherscan V2 `module=account&action=txlist` (page 1, offset 1000, startblock 0, sort asc) → `source: "etherscan-v2"`, `firstSeen`, richer `txCount`, up to 200 unique counterparties, `gasSpentEth` (sum gasUsed × gasPrice → ether), `successfulContractInteractions` (has `to`, `isError == "0"`, `txreceipt_status != "0"`). Exceptions produce a `warning` and partial results.

Stored under `passport.generic_metrics` as `{chainKey: {address: metric}}`.

---

## 9. Frontend (React/Vite)

### 9.1 Tech stack

| Layer | Choice (declared → locked) |
|---|---|
| UI | React 19 (^19.1.1 → 19.3.0), function components + hooks, `StrictMode` |
| Language | TypeScript 5.9 (^5.9.2 → 5.9.3), `strict: true` |
| Bundler | Vite 7 (^7.1.7 → 7.3.7) + `@vitejs/plugin-react` |
| Styling | Hand-written single-file `styles.css` (Tailwind v4 installed/wired but unused in markup) |
| Animation | framer-motion 12 (→ 12.43.0) + CSS keyframes |
| Icons | lucide-react 0.548.0 |
| Web3 | ethers 6 (^6.15.0 → 6.17.0) |
| Routing | none — internal `Screen` state + `?passport=` query param |
| State | `useState/useEffect/useMemo` + `localStorage["omnirep.pid"]` + `CustomEvent("omnirep:toast")` |

**Commands:** `npm run dev` (port 5173, host 0.0.0.0) · `npm run build` (`tsc -b && vite build`) · `npm run preview`.
**Env:** `VITE_API_BASE` (default `http://localhost:5000`) + 10 contract address vars. Vite reads `.env.local` only at start — restart after changes.

### 9.2 Screens (`App.tsx`, `Screen = home|dashboard|link|signals|risk|coach|publish|verify|gate|badge`)

**App shell:** CSS grid `238px 1fr`; sticky sidebar (BrandMark, `TESTNET MODE` live dot, 9 nav buttons with icons, footer showing passport ID + network); sticky topbar (breadcrumb `OMNIREP › <SCREEN>`, wallet pill); `AnimatePresence mode="wait"` screen transitions; bottom-right toast. If no `pid`, every non-home screen renders `SetupRequired` ("PASSPORT REQUIRED").

| # | Screen | Contents & behavior |
|---|---|---|
| 1 | **home** | Hero: eyebrow `PS 64 · DIGITAL IDENTITY`, headline "Your history should travel.", `ShimmerButton` Create/Open passport (disabled while busy or if registry unset), network note, orbit visual (`ETH`/`BASE`/`PROOF` nodes) inside `SpotlightCard` + `BorderBeam`. |
| 2 | **dashboard** | Bento grid: **score card** (`NumberTicker` 0–1000 at 92 px + tier pill + wallet/evidence/version footer), **evidence card** (9 factor rows with reason + signed points, "Inspect proof" link), **risk card** (conic ring, `{risk}/100`, label), **chain card** (ETH ↔ passport ↔ BASE map), **trajectory card** (history bars + delta), **activity card** (6 recent evidence rows linking to explorers). Actions: **Recalculate** (`POST /score`), **Refresh evidence** (`POST /sync` → `POST /score` → dashboard). |
| 3 | **link** | Stepper (Passport / Ethereum / Base), signature preview "Link my wallet to OmniRep passport #N.", two link buttons (challenge → `personal_sign` → verify), privacy card ("Your addresses stay off-chain", `linksHash → 0x7f…c2`, `addresses → never published`). Shows `{n}/2` progress badge. |
| 4 | **signals** | 4 playground cards: Repayable loan (`borrowAndRepay(100)`), Loan default (`borrowAndDefault(100)`), Governance (`createProposal` → `vote`), Contribution (`contribute`). Each shows target chain based on current `chainId`. Callout reminding users to link one wallet per chain before refreshing. |
| 5 | **risk** | Big `{risk}/100`, status pill (green <30 else amber), numbered rule reasons, feature vector list, AI panel (provider, suspicion, explanation, pattern chips). |
| 6 | **coach** | 4 what-if cards (repay on time / vote on 3 proposals / contribute / add third chain) → `POST /what-if`, shows signed delta per action. |
| 7 | **publish** | Score/Confidence/Risk tiles, Input hash + Linked-wallet commitment blocks, **Publish on Ethereum Sepolia** (attestation → `registry.publish` → `POST /published`), **Carry proof to Base** (`verifier.accept`), trust-model rows (1 authorized key, version+deadline replay protection, hashes not addresses, read-only `meets()`). |
| 8 | **verify** | Loads bundle, recomputes SHA-256 **in the browser** (`sha256(toUtf8Bytes(JSON.stringify(canon(hashInput))))`), canonicalizes with sorted keys, compares with `passport.inputHash` → `MATCH`/`MISMATCH`. **Change one character** button mutates `activities[0].activityType` (or bumps config version) and shows mismatch; **Restore exact bundle** reverses it. Also: **Share passport** (copies `?passport=<id>` link), **Download bundle** (JSON file), receipt card, copy-bundle + explorer link. |
| 9 | **gate** | LendLite consumer view: reads `registry.getPassport` + `registry.meets(id, threshold, 30d)` via public RPC and `verifier.meets(owner, threshold, 30d)` on Base; threshold `<input type="range" 0–1000>` (default 400); `ACCESS GRANTED/BLOCKED` with reason; **Execute LendLite borrow** (`lendLite.borrow(100)`); developer snippet `registry.meets(passportId, threshold, 30 days)`. |
| 10 | **badge** | Tier tiles (0 Iron / 200 Bronze / 400 Silver / 600 Gold / 800 Diamond), **Claim available badge** → `badge.claim()`; design-choice card "Soulbound, not tradable." |

### 9.3 Core actions & API/contract calls

| Function | API | Contract |
|---|---|---|
| `create()` | `recoverPassport` or `createPassport` | `registry.passportOf`, `registry.createPassport()` |
| `link(target)` | `challenge` → `verify` → refresh | wallet `personal_sign` only (no gas) |
| `syncAndScore()` | `sync`, `score` | — |
| `publish()` | `attestation`, `published` | `registry.publish(attestation, sig)` |
| `portable()` | `portableAttestation` | `verifier.accept(msg, sig)` |
| `callSignal(kind)` | — | loan/governor/contribution contracts per chain |
| `recalc()` | `score` | — |
| `downloadBundle()` | `bundle` | — |

Single-flight `busy` string (`create`, `sync`, `publish`, `portable`, `recalc`, `link-<chain>`, signal kind) drives spinners and disabled states.

### 9.4 API client (`src/lib/api.ts`)

`request<T>` helper: JSON headers, error extraction `message → error → HTTP <status>` (surfaced as toasts). 15 functions: `createPassport, recoverPassport, challenge, verify, passport, sync, score, risk, attestation, portableAttestation, bundle, history, receipt, published, whatIf`.

### 9.5 On-chain config (`src/lib/config.ts`)

`NETWORKS` (both testnets with chainId hex, RPC, explorer), `CONTRACTS` (10 env-driven addresses with legacy `TRAILMARK_*` fallbacks), and human-readable ABIs: `REGISTRY_ABI` (9 entries incl. tuple `getPassport` and `publish`), `LOAN_ABI`, `GOV_ABI`, `CONTRIB_ABI`, `LEND_ABI`, `BADGE_ABI`, `VERIFIER_ABI`.

### 9.6 Reusable components

- **`BrandMark`** — gradient tile + fingerprint, `OMNIREP / REPUTATION PASSPORT`.
- **`SpotlightCard`** — pointer position written straight to CSS vars `--mx/--my` via `style.setProperty` (no React re-render per pointer frame).
- **`ShimmerButton`** — primary action with animated `.shimmer-ring`.
- **`BorderBeam`** — rotating conic-gradient beam masked to a 1 px ring.
- **`NumberTicker`** — rAF count-up, 650 ms, ease-out cubic, `toLocaleString()`.

### 9.7 Design system (`styles.css`)

- **Background:** `#070708` with radial violet/blue glows.
- **Accent:** violet `#a78bfa` (brand gradient `linear-gradient(135deg,#a78bfa,#2563eb)`), success `#6ee7b7`/`#34d399`, warning `#fbbf24`, danger `#fb7185`, primary button light `#f8fafc` on dark.
- **Type:** sans stack `Inter, ui-sans-serif, system-ui, …` (Inter not actually loaded → system UI), mono `ui-monospace, monospace`. Hero h1 72 px/−.06em; section h2 34 px; big numbers 92/88/84 px; micro labels 8–11 px uppercase.
- **Layout:** `238px 1fr` shell; bento `1.18fr .82fr .82fr` (score card spans 2 rows); two-column screens `1.2fr .8fr`; 3-col signal/coach grids; radii 20 px cards, 999 px pills.
- **Motion:** shimmer 2.8 s infinite; border beam 6 s linear; `.spin` 1 s; spotlight radial 260 px; framer-motion `.18s` transitions; live/wallet/timeline glow dots.
- **Responsive:** ≤1100 px → 76 px icon rail + 2-col bento; ≤760 px → sidebar becomes a fixed 66 px bottom bar, all grids 1 column, hero visual hidden.

**Provenance (`docs/UI_SOURCES.md`):** patterns source-adapted from the **21st.dev** community registry (Spotlight Card, Shimmer Button, Border Beam, Number Ticker, Timeline), with OmniRep-specific information architecture.

---

## 10. SDK

**`sdk/PassportGate.sol`**
```solidity
interface IPassportGate {
    function meets(uint256 passportId, uint16 minScore, uint64 maxAge) external view returns (bool);
}
```

**`sdk/omnirep.js`**
```js
export async function meetsOmniRep(registry, passportId, minimum, maxAge = 0) {
  return registry.meets(passportId, minimum, maxAge);
}
// const allowed = await meetsOmniRep(registry, passportId, 400, 30*24*60*60);
```

**`sdk/README.md`:** *"A consumer can gate a feature with one read from OmniRepRegistry."*

---

## 11. Scripts, CI & Deployment Automation

### 11.1 npm scripts (root `package.json`, name `omnirep-passport` v1.0.0)

| Script | Command |
|---|---|
| `dev` | `npm run frontend:dev` |
| `frontend:dev` / `frontend:build` | `npm --prefix frontend run dev/build` |
| `contracts:compile` | `hardhat compile` |
| `contracts:test` | `hardhat test` |
| `contracts:deploy` | `hardhat run scripts/deploy.js --network sepolia` |
| `contracts:deploy:base` | `hardhat run scripts/deploy-base.js --network baseSepolia` |
| `deployment:preflight` | `node scripts/deployment-preflight.js` |
| `hardhat:base` | alias of `contracts:deploy:base` |

devDependencies: `hardhat ^2.26.3`, `@nomicfoundation/hardhat-toolbox ^6.1.0`, `@openzeppelin/contracts ^5.4.0`, `dotenv ^16.6.1`.

### 11.2 Hardhat config

- Networks defined **only** when env vars exist: `sepolia` (chainId 11155111, `ETH_SEPOLIA_RPC_URL`) and `baseSepolia` (chainId 84532, `BASE_SEPOLIA_RPC_URL`), both using `DEPLOYER_PRIVATE_KEY`.
- Solidity `0.8.24`, `evmVersion: "cancun"`, optimizer `enabled: true, runs: 200`.
- Paths: sources `./contracts`, tests `./test`, cache `./cache`, artifacts `./artifacts`.

### 11.3 Deploy scripts

- **`scripts/deploy.js`** (Ethereum Sepolia): deploys Registry(owner=attestor=deployer) → LoanPool → Governor → ContributionLog → LendLite(registry) → Badge(registry); writes `deployments/ethereum-sepolia.json` (2-space indent) and prints it.
- **`scripts/deploy-base.js`** (Base Sepolia): deploys Verifier(attestor=deployer) → LoanPool → Governor → ContributionLog; writes `deployments/base-sepolia.json`.
- **`scripts/deployment-preflight.js`**: requires `DEPLOYER_PRIVATE_KEY`, `ETH_SEPOLIA_RPC_URL`, `BASE_SEPOLIA_RPC_URL`; validates key format `/^0x[0-9a-fA-F]{64}$/`; prints `DEPLOYMENT PREFLIGHT: PASS` or `BLOCKED` + missing keys (exit 1). Confirms no private key is written to deployment JSON.
- **`scripts/deploy.sh`**: `set -euo pipefail` → npm install → compile → deploy Sepolia → best-effort Base deploy → reminds to copy addresses into env files.
- **`scripts/deploy.ps1`**: same but stops if `DEPLOYER_PRIVATE_KEY` unset; Base deploy left manual.

### 11.4 `scripts/validate.py` (static validation, used in CI)

- Requires **18 files** (README, SECURITY, render.yaml, backend core files, 4 contracts, App.tsx, 4 UI components, 6 docs) — exits with `Missing required files` otherwise.
- Fails if any `*.db` file is committed (skips `.git`, `node_modules`, `.venv`, `__pycache__`, `artifacts`, `cache`).
- Content assertions:
  - `scoring.py` must contain `"model": "omnirep_scoring_v2"`, `"scale": 1000`, `"repayments"`, `"wallet_longevity"`, `compute_risk`.
  - `OmniRepRegistry.sol` must contain `sha256(raw)`, `verifyInputBytes`, `function meets`, `bytes32 inputHash`, `uint16 score`.
  - `App.tsx` must contain `OmniRep`, `DIAMOND`, `Change one character`, `Share passport`, `LendLite`, `Sybil Radar`.
  - `render.yaml` must contain `gunicorn app:app`, `DATABASE_URL`, `ATTESTOR_PRIVATE_KEY`.
- Prints `OmniRep static validation: PASS`, `Files checked: 18`, and the PS64 proof path line.

### 11.5 `scripts/offline_smoke.py` (no network needed)

Imports `canonical_json` + `score_reputation` from the backend; builds 3 sample activities and metrics for 2 wallets at fixed `NOW = 1_760_000_000`; asserts `0 ≤ score ≤ 1000`, `confidence > 0`, `cross_chain.points > 0`; round-trips the proof hash; mutates an activity and asserts the hash changes (tamper detection). Prints `Offline OmniRep smoke: PASS` with score/confidence/risk/proof values.

### 11.6 CI (`.github/workflows/quality.yml` — "OmniRep Quality")

Triggers: `push` (all branches) + `pull_request`. Job `quality` on `ubuntu-latest`:
1. `actions/checkout@v4`
2. `actions/setup-node@v4` → Node 22
3. `actions/setup-python@v5` → Python 3.12
4. `npm install` (root)
5. `npm --prefix frontend install`
6. `pip install -r backend/requirements.txt`
7. `node --check` on hardhat.config.js, deploy.js, deploy-base.js, test/OmniRep.js
8. `python -m py_compile backend/*.py`
9. `python scripts/validate.py`
10. `npm --prefix frontend run build` (includes `tsc -b` type checking)
11. `npm run contracts:test`

No deploy steps, no secrets required.

### 11.7 `render.yaml` — Render blueprint

Service `omnirep-api`: `type: web`, `env: python`, `rootDir: backend`, build `pip install -r requirements.txt`, start `gunicorn app:app --timeout 120 --workers 2`.

23 env keys (all `sync: false` — set manually in the dashboard):
- **Secrets:** `DATABASE_URL`, `FRONTEND_ORIGIN`, `ATTESTOR_PRIVATE_KEY`, `ETHERSCAN_API_KEY`, `AI_API_KEY`, `AI_BASE_URL`, `AI_MODEL`
- **Addresses:** `OMNIREP_REGISTRY_ADDRESS`, `TRAILMARK_REGISTRY_ADDRESS`, `OMNIREP_VERIFIER_ADDRESS`, `TRAILMARK_VERIFIER_ADDRESS`, `OMNIREP_BADGE_ADDRESS`, `TRAILMARK_BADGE_ADDRESS`, `LENDLITE_ADDRESS`, `ETH_LOAN_POOL_ADDRESS`, `BASE_LOAN_POOL_ADDRESS`, `ETH_GOVERNOR_ADDRESS`, `BASE_GOVERNOR_ADDRESS`, `ETH_CONTRIBUTION_ADDRESS`, `BASE_CONTRIBUTION_ADDRESS`
- **RPC:** `ETH_RPC_URL`, `BASE_RPC_URL`

---

## 12. Environment Variables

> Only variable **names** and non-secret defaults are listed. Never commit `.env`, `backend/.env`, or private keys.

### 12.1 Root `.env` (Hardhat deployment) — 28 keys

| Variable | Default / notes |
|---|---|
| `DEPLOYER_PRIVATE_KEY` | (empty) — 32-byte hex, testnet burner only |
| `ETH_SEPOLIA_RPC_URL` | `https://ethereum-sepolia.publicnode.com` |
| `BASE_SEPOLIA_RPC_URL` | `https://sepolia.base.org` |
| `ETH_RPC_URL` / `BASE_RPC_URL` | same RPCs, used by backend indexer |
| `DATABASE_URL` | `sqlite:///omnirep.db` (use Postgres in production) |
| `ATTESTOR_PRIVATE_KEY` | (empty) — backend-only signing key |
| `OMNIREP_REGISTRY_ADDRESS` (+ `TRAILMARK_*` legacy variants) | deployed addresses |
| `OMNIREP_VERIFIER_ADDRESS`, `OMNIREP_BADGE_ADDRESS` (+ legacy) | |
| `LENDLITE_ADDRESS` | |
| `ETH_LOAN_POOL_ADDRESS`, `BASE_LOAN_POOL_ADDRESS` | |
| `ETH_GOVERNOR_ADDRESS`, `BASE_GOVERNOR_ADDRESS` | |
| `ETH_CONTRIBUTION_ADDRESS`, `BASE_CONTRIBUTION_ADDRESS` | |
| `ETHERSCAN_API_KEY` | optional enrichment |
| `AI_API_KEY`, `AI_BASE_URL`, `AI_MODEL` | optional AI second opinion |
| `FRONTEND_ORIGIN` | `http://localhost:5173` |
| `PORT` | `5000` |
| `INDEXER_BLOCK_WINDOW` | `20000` |

Address env vars have legacy fallback chains in code: `OMNIREP_*` → `TRAILMARK_*` → (registry only) `REPUTATION_*`. `ATTESTOR_PRIVATE_KEY` falls back to `PUBLISHER_PRIVATE_KEY`.

### 12.2 Backend `.env` (minimum local set)

```env
PORT=5000
FRONTEND_ORIGIN=http://localhost:5173
DATABASE_URL=sqlite:///omnirep.db
ETH_RPC_URL=https://ethereum-sepolia.publicnode.com
BASE_RPC_URL=https://sepolia.base.org
ATTESTOR_PRIVATE_KEY=0x<same key used as attestor at deployment>
OMNIREP_REGISTRY_ADDRESS=<Sepolia registry>
OMNIREP_VERIFIER_ADDRESS=<Base verifier>
```

### 12.3 Frontend `.env.local` (browser-safe — `VITE_` prefix required)

```env
VITE_API_BASE=http://localhost:5000
VITE_OMNIREP_REGISTRY_ADDRESS=<Sepolia registry>
VITE_OMNIREP_VERIFIER_ADDRESS=<Base verifier>
VITE_OMNIREP_BADGE_ADDRESS=<Sepolia badge>
VITE_LENDLITE_ADDRESS=<Sepolia LendLite>
VITE_ETH_LOAN_POOL_ADDRESS=...  VITE_BASE_LOAN_POOL_ADDRESS=...
VITE_ETH_GOVERNOR_ADDRESS=...   VITE_BASE_GOVERNOR_ADDRESS=...
VITE_ETH_CONTRIBUTION_ADDRESS=...  VITE_BASE_CONTRIBUTION_ADDRESS=...
```

Only `VITE_`-prefixed variables are readable by the browser bundle. **Never put private keys here.**

---

## 13. Local Development Guide

### 13.1 Requirements

Node.js **20+** (repo pins **22** via `.nvmrc`), Python **3.11+** (repo pins **3.12** via `.python-version`), npm, MetaMask, Git. Networks: Ethereum Sepolia (11155111) and Base Sepolia (84532). **Testnets and fresh burner wallets only.**

### 13.2 Install (PowerShell)

```powershell
npm install
Set-Location .\frontend; npm install; Set-Location ..
if (-not (Test-Path .\backend\.venv\Scripts\python.exe)) { python -m venv .\backend\.venv }
& .\backend\.venv\Scripts\python.exe -m pip install -r .\backend\requirements.txt
```

### 13.3 Configure the three env files

```powershell
Copy-Item .\.env.example .\.env
Copy-Item .\backend\.env.example .\backend\.env
Copy-Item .\frontend\.env.example .\frontend\.env.local
```

### 13.4 Validate before running

```powershell
node .\scripts\deployment-preflight.js
npm run contracts:compile
npm run contracts:test                 # expected: 3 passing
npm run frontend:build
& .\backend\.venv\Scripts\python.exe .\scripts\validate.py
& .\backend\.venv\Scripts\python.exe .\scripts\offline_smoke.py
```

### 13.5 Run (two windows)

```powershell
# Window 1 — backend → http://127.0.0.1:5000
& .\backend\.venv\Scripts\python.exe .\backend\app.py
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:5000/health

# Window 2 — frontend → http://localhost:5173
npm run frontend:dev
```

Expected health: `{"ok": true, "database": true, "chains": {"ethereum-sepolia": true, "base-sepolia": true}, ...}`.

### 13.6 Deploy contracts

```powershell
npm run contracts:compile
npm run contracts:test
npm run contracts:deploy        # Ethereum Sepolia (6 contracts)
npm run contracts:deploy:base   # Base Sepolia (4 contracts)
```
Then copy addresses from `deployments/*.json` into `backend\.env` and `frontend\.env.local`, restart both, rebuild the frontend, and verify bytecode on the explorers.

### 13.7 Production-style deployment

- **Backend:** Render (`render.yaml`), start `gunicorn app:app --timeout 120 --workers 2`; secrets set in the Render dashboard; **use Neon/Supabase PostgreSQL** — never SQLite on ephemeral disk.
- **Frontend:** Vercel/Netlify with `VITE_*` vars; `npm run build`.
- **Monitoring:** `GET /health` for UptimeRobot / pre-demo checks.

---

## 14. Demo Scripts & Pitch

### 14.1 README live demo order (10 steps)

1. Create a passport from a burner wallet on Ethereum Sepolia.
2. Link a second, different burner address on Base Sepolia by signing the challenge.
3. On each chain, use **Playground** to create a real loan+repayment, vote, or contribution.
4. Press **Refresh evidence** — backend fetches and normalizes both chains.
5. Open **Passport overview** — inspect score breakdown and evidence links.
6. Open **Sybil Radar** — deterministic rules + optional AI second opinion.
7. Open **Publish** — sign the EIP-712 attestation; owner pays gas, backend only signs.
8. Open **Verifier** — browser recomputes SHA-256; toggle tamper for a mismatch.
9. Open **LendLite Gate** — consumer reads registry → granted/blocked.
10. Optionally carry a portable attestation to Base Sepolia — verifier accepts with no bridge.

### 14.2 Timed 3-minute script (`docs/DEMO_SCRIPT.md`)

| Time | Segment |
|---|---|
| 0:00 | **Problem** — "Your Web3 history is split across wallets and chains." |
| 0:20 | **Link two wallets** — create passport, sign wallet A (Sepolia), sign wallet B (Base). No transaction, no asset transfer. |
| 0:50 | **Create evidence** — semantic events on both chains → Refresh evidence → normalized cross-chain activity. |
| 1:20 | **Explain the score** — Overview: repayments, longevity+consistency, cross-chain breadth; Sybil Radar. |
| 1:50 | **Publish proof** — EIP-712 attestation → publish → point at the explorer transaction. |
| 2:20 | **Verify / tamper** — hash match → **Change one character** → `MISMATCH` → restore → match. |
| 2:40 | **Consumer dApp** — LendLite gate, threshold slider, portable Base verifier. |
| 2:55 | **Close** — "explainable before publication, verifiable after publication, usable by another app." |

### 14.3 Pitch (`docs/PITCH.md`)

- **Hook:** "Your history should not reset when your wallet changes."
- **90-second story:** fragmented reputation → signatures prove control of multiple wallets → normalize two testnets → transparent 0–1000 score with a **Proof of Why** → evidence off-chain, SHA-256 commitment on-chain → Sybil Radar → portable attestation → LendLite gate.
- **Four demo beats:** **Link** (2 wallets, 2 chains, 2 signatures) · **Explain** (breakdown shows what raised/lowered) · **Prove** (publish hash, mutate input, verification fails) · **Compose** (LendLite unlocks without the private DB).
- **Q&A anchors:** why not everything on-chain (cost/evolvability + verifiable fingerprint); AI cannot manipulate the score (deterministic rules); a wallet can't join two passports (backend rejects); changed evidence changes the input hash, so old publications stop matching until a new version is published.

### 14.4 Day-2 required demo flow (`docs/INNOBLOCK_DAY2_RUN.md`, 18 steps)

Connect wallet A (Sepolia) → create passport → sign wallet-link challenge → switch to Base Sepolia → connect wallet B and sign → create ≥1 semantic signal per chain → sync/index → show normalized cross-chain activity → generate the 0–1000 score → Score Breakdown / Proof of Why → Sybil Radar → publish attestation to Sepolia → open the registry tx on the explorer → Verifier hash matches → change one character → must fail → LendLite gates from the on-chain score → (optional) portable Base attestation → shareable `?passport=<id>` link.

**Judge-visible tabs:** live frontend · verified Registry explorer page · a publication tx · GitHub repo · slides PDF. Plus a **1–2 minute offline backup video**.

**Freeze point:** once the full flow works, stop adding features — only fix blockers, verify the repo, rehearse, record backup.

### 14.5 Burner wallet plan (3 wallets, ≈0.05 Sepolia ETH each)

1. **Deployment/attestor wallet** — Hardhat deploys and signs attestations (key stays backend-only).
2. **Demo wallet A** — Ethereum Sepolia passport owner.
3. **Demo wallet B** — Base Sepolia linked wallet.

---

## 15. Checklists & Phase Status

### 15.1 PS64 mandatory (7)

- [ ] Create passport on Ethereum Sepolia
- [ ] Link a wallet on Ethereum Sepolia by signature
- [ ] Link a second wallet on Base Sepolia by signature
- [ ] Refresh and normalize activity from both testnets
- [ ] Generate transparent 0–1000 score with factor explanations
- [ ] Publish score + SHA-256 input hash to the Sepolia registry
- [ ] Show an independent consumer dApp reading the contract

### 15.2 Strong differentiators (9)

- [ ] Sybil Radar with deterministic reasons
- [ ] AI second opinion shown as advisory only
- [ ] Iron / Bronze / Silver / Gold / Diamond tiers
- [ ] What-if Coach
- [ ] Score history / trajectory
- [ ] Proof of Why evidence timeline
- [ ] Tamper Lab: mutate input → SHA-256 mismatch
- [ ] Shareable `?passport=<id>` verification link
- [ ] Portable EIP-712 attestation accepted by the Base Sepolia verifier

### 15.3 Deployment (9)

- [ ] Deploy Registry (Sepolia) · Verifier (Base) · LoanPool/Governor/ContributionLog (both) · LendLite + Badge (Sepolia)
- [ ] Verify contracts on matching explorers (0.8.24, optimizer 200)
- [ ] Backend `ATTESTOR_PRIVATE_KEY` matches the deployed attestor
- [ ] Neon/Supabase PostgreSQL configured
- [ ] Render backend secrets configured
- [ ] Vercel frontend `VITE_*` addresses + API base configured

### 15.4 Security checks (5)

- [ ] No private keys in frontend · no API secrets in frontend
- [ ] Testnet/burner wallets only
- [ ] No personal data committed on-chain
- [ ] Publication transaction independently verified by the backend

### 15.5 Final rehearsal (12)

create passport ✓ · two wallets link ✓ · correct chain per wallet ✓ · semantic events on both chains ✓ · non-zero score ✓ · breakdown intelligible in <20 s ✓ · hash match ✓ · tamper mismatch ✓ · registry explorer tx ✓ · LendLite reads published score ✓ · optional Base portable attestation ✓ · no secret in devtools/bundle ✓.

### 15.6 Phase status board (`docs/PHASE_STATUS.md`)

| Phase | Name | Status |
|---|---|---|
| 0 | PS64 + OmniRep source lock | ✅ Complete |
| 1 | Blockchain (registry, verifier, sources, LendLite, badge) | ✅ Source complete |
| 2 | Backend (auth, indexer, scoring, proofs, attestation, APIs) | ✅ Source complete |
| 3 | Frontend (all 10 screens) | ✅ Source complete |
| 4 | Automated local validation | ✅ Source checked |
| 5 | Public testnet deployment | 🟠 External execution required (funded burner + RPCs) |
| 6 | Explorer verification + live rehearsal | 🟠 Follows Phase 5 |
| 7 | Submission hardening | ✅ Source package ready |
| 8 | Deployment automation hardening | ✅ Source complete + 🟠 live run still required |
| 9 | Reliability hardening (real `/health`, DB constraints, verify endpoint, offline smoke) | ✅ Source complete |
| 10 | Live readiness | 🟢 Ready for external execution |

---

## 16. Security Model

### 16.1 `SECURITY.md` rules (verbatim)

1. Public testnets and fresh burner wallets only for the hackathon.
2. Never commit `.env`, private keys, API keys or database credentials.
3. Never put personal data on-chain.
4. Wallet linking uses nonce + expiry challenge signatures.
5. Reputation publication uses a bounded EIP-712 attestation signed by the backend attestor and submitted by the passport owner.
6. Deterministic scoring is the source of truth; the optional AI layer is a bounded second opinion.
7. OmniRep reputation is **not KYC** and does not prove real-world identity.

### 16.2 Mechanisms

| Concern | Mechanism |
|---|---|
| Wallet ownership | SIWE-style challenge: nonce (`token_urlsafe(24)`), 300 s expiry, single-use, `personal_sign`, server-side `ecrecover` |
| Replay of attestations | Strictly monotonic `version` (`p.version + 1`), 900 s `deadline`, submitter must be owner/subject |
| Cross-chain replay | Payload guards (`msg.sender == owner` / `subject == msg.sender`) since the EIP-712 domain omits `chainId` |
| Proof integrity | SHA-256 over canonical JSON (sorted keys, no whitespace); browser independently recomputes |
| Address privacy | Only `linksHash` (commitment) published; linked addresses stay off-chain |
| Key handling | Attestor key backend-only; never in `VITE_*`, localStorage, API responses, screenshots |
| Frontend safety | Contract addresses are public; no secrets in the bundle; errors surfaced via toasts |
| Supply chain | Pinned dependency versions; `.gitignore` blocks `.env*` (except example), `*.db`, `venv`, build outputs |
| DB hygiene | `.gitignore` has `backend/*.db`; `validate.py` fails the build if any `*.db` is committed |

### 16.3 Operational security checklist (from runbooks)

Burner wallets only · testnets only · never paste keys into chat/README/screenshots/issue trackers · never expose `ATTESTOR_PRIVATE_KEY` to the frontend · don't commit `.env` or `backend\.env` · no names/emails/identity data on-chain · don't claim deployment until the explorer confirms it · run a secret scan before any commit.

---

## 17. Tests & Validation

### 17.1 Hardhat tests (`test/OmniRep.js`) — expected result: **3 passing**

1. **`creates passports and accepts only an attestor-signed publication`** — creates a passport, signs an attestation (score 520, risk 12, algoVersion 10001, linkedCount 2, version 1, deadline +900) with `signTypedData`, publishes, asserts `ScorePublished`, `scoreOf == 520`, `tierOf == 2`, `verifyInputs` true, `verifyInputBytes` true (SHA-256 precompile), and that a **different signer** submitting with the same signature reverts `"not passport owner"`.
2. **`rejects replay or bad version`** — publishing the identical payload twice reverts `"bad version"` (version must be strictly `+1`).
3. **`emits the typed evidence events`** — `borrowAndRepay` → `Borrowed`+`Repaid`; `borrowAndDefault` → `Defaulted`; `createProposal`+`vote` → `ProposalCreated`+`Voted`; `contribute` → `Contributed`.

**Not covered by tests:** Badge (claim/soulbound/tokenURI), Verifier (accept/meets), LendLite gate, `setAttestor`, `publish` failure branches (expired, score>1000, risk>100, no links, zero hashes, bad signature), LoanPool `borrow`/`repay`/`markDefaulted`, duplicate `createPassport`, `meets` negative paths.

### 17.2 Validation layers

| Layer | Command | Checks |
|---|---|---|
| JS syntax | `node --check` ×4 | hardhat config, deploy scripts, tests |
| Python compile | `python -m py_compile backend/*.py` | backend syntax |
| Static project validation | `python scripts/validate.py` | 18 required files, no `*.db`, key content markers |
| Offline smoke | `python scripts/offline_smoke.py` | scoring bounds, canonical hash round-trip, tamper detection |
| Frontend build | `npm --prefix frontend run build` | `tsc -b` type check + Vite bundle |
| Contract tests | `npm run contracts:test` | 3 Hardhat tests |
| Live health | `GET /health` | DB + both RPCs + config |

---

## 18. Known Gaps & Observations

Accurate current-state notes (useful for review/Q&A; not blockers for the demo):

1. **EIP-712 domain is non-standard** (no `chainId`/`verifyingContract`) — intentional for portability; replay is prevented by payload guards + deadline, not by the domain.
2. **`attestor == deployer == owner`** in current deployments — one key controls `setAttestor` and attestation signing.
3. **Identical addresses on both chains** — same deployer, aligned nonces (documented, not an error).
4. **`OmniRepBadge` has no per-address claim cap** — unlimited mints, each snapshotting the current tier; transfers permanently blocked.
5. **`LoanPool.markDefaulted` sets no flag** — `Defaulted` can be re-emitted; demo helpers intentionally move no funds.
6. **`LendLite` collateral bps can exceed 10000** (12000/15000/20000) — informational only, never enforced.
7. **`OmniRepGovernor`** has no quorum/period/execution — one address, one vote.
8. **Test coverage ≈ 2 of 7 contracts** plus two Registry negative paths.
9. **`Passport.model_version` column default is 10001** while code writes `MODEL_VERSION = 20001` (stale default only; writes are correct).
10. **Tailwind v4 installed and wired into Vite but unused** in markup/CSS; all styling is hand-written.
11. **`scoreColor()` tier classes (violet/gold/silver/bronze/neutral) have no matching CSS rules** — dormant hook.
12. **No `prefers-reduced-motion` block** in `styles.css` despite the claim in `UI_SOURCES.md`.
13. **`Inter` font referenced but never loaded** — falls back to system UI.
14. **Routing is state-based** — a browser refresh returns to `home` unless `?passport=` or `localStorage.omnirep.pid` exists.
15. **PRD contains an older scoring table** (repayments 300 / governance 150 / etc. and tiers "Newcomer/Platinum"); the implemented model is `omnirep_scoring_v2` (§7) with Iron/Bronze/Silver/Gold/Diamond.
16. **`docs/PRD.md` references an older `frontend/config.js`** — current implementation is `frontend/src/lib/config.ts`.
17. **Local `omnirep.db` and `backend/omnirep.db` exist in the working tree** — `validate.py` fails if any `*.db` is present; they are gitignored, so CI on a clean checkout passes.
18. **Legacy `TRAILMARK_*` env names** remain as fallbacks (prior project name), harmless but worth noting.
19. **Backend `/health` does not report attestor balance** (PRD FR-20 mentions it; current implementation reports `attestorConfigured` only).
20. **Phases 5–6 (live deployment + explorer verification) remain external** — they require the team's funded burner key and RPC credentials.

---

## 19. Source Documents Index

| Document | Purpose |
|---|---|
| `README.md` | Project landing page: overview, PS64 coverage, repo map, setup, live demo order, production notes, design choices |
| `SECURITY.md` | 7 security rules |
| `LICENSE` | MIT, © 2026 OmniRep Contributors |
| `docs/ARCHITECTURE.md` | System diagram, on/off-chain data boundary, 7-step trust model |
| `docs/PRD.md` | Full PRD: source analysis, goals, personas, D1–D11 differentiators, scope P0/P1/P2, FR-1…FR-20, scoring v1, contracts sketch |
| `docs/PITCH.md` | One-line pitch, 90-second story, 4 demo beats, Q&A anchors |
| `docs/DEMO_SCRIPT.md` | Timed 3-minute demo script |
| `docs/DEPLOYMENT.md` | Deployment runbook: env inputs, deploy commands, verification, 12-item rehearsal |
| `docs/FINAL_CHECKLIST.md` | 4 checklists: mandatory, differentiators, deployment, demo sequence, security |
| `docs/IMPLEMENTATION_NOTES.md` | 8 critical design decisions + current constraints |
| `docs/INNOBLOCK_DAY2_RUN.md` | Day-2 run: non-negotiables, burner plan, funding, deploy/verify, 18-step demo flow, judge tabs, freeze point, pitch order |
| `docs/LIVE_RUNBOOK.md` | Shortest path from source to judge-ready demo; offline validation commands |
| `docs/OPERATIONS_RUNBOOK.md` | 14-section operator guide (PowerShell): requirements, install, 3 env files, deployed addresses, validation, run, demo flow, redeploy, Render, troubleshooting, security, shutdown, commands |
| `docs/PHASE_STATUS.md` | Phases 0–10 status board |
| `docs/SCORING.md` | Scoring model documentation (weights, tiers, Sybil rules, AI boundary) |
| `docs/UI_SOURCES.md` | UI pattern attribution (21st.dev) + performance rules |
| `docs/COMPLETE_DOCUMENTATION.md` | **This document — consolidated everything** |

---

*Compiled from the full repository source. Secret values from `.env` files are intentionally excluded; only variable names and non-secret defaults are documented.*
