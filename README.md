# OmniRep — Omnichain Reputation Passport

**INNOBLOCK 2.0 · PS64 · Domain 7: Digital Identity**

OmniRep turns fragmented EVM wallet history into a portable, explainable reputation passport. A user proves control of multiple testnet addresses with signatures, the backend normalizes activity from Ethereum Sepolia + Base Sepolia, a transparent scoring engine produces a 0–1000 score, and a SHA-256 proof commitment is published on-chain for another application to consume.

## PS64 coverage

- **Wallet linking:** readable nonce + expiry challenge, signed separately by each wallet, no asset transfer.
- **Cross-chain activity:** Ethereum Sepolia and Base Sepolia RPC/event adapters plus optional Etherscan V2 enrichment.
- **Explainable score:** 0–1000 deterministic model with repayments, longevity, activity quality, cross-chain breadth, governance, contributions, counterparties, consistency and penalties.
- **On-chain proof:** `OmniRepRegistry` stores score, tier, Sybil risk, model/version metadata, SHA-256 input hash and linked-wallet-set hash.
- **Consumer gate:** `LendLite` reads the registry directly and gates its feature from the published signal.
- **Good-to-have:** Sybil Radar, bounded AI second opinion, Iron/Bronze/Silver/Gold/Diamond tiers, portable Base attestation, tamper lab, trajectory and what-if coach.

The implementation mirrors the uploaded PS64/OmniRep requirements and keeps the detailed record off-chain while the chain stores compact commitments.

## Repository map

- `contracts/` — registry, portable verifier, semantic evidence sources, LendLite consumer, badge
- `backend/` — Flask API, signature verification, cross-chain indexer, scoring and proof bundle
- `frontend/` — React/Vite UI
- `sdk/` — minimal consumer helper
- `docs/` — architecture, scoring, demo, deployment and UI notes
- `.github/workflows/quality.yml` — syntax checks

## Local development

### 1. Install dependencies

```bash
npm install
cd frontend && npm install
cd ../backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

Copy `.env.example` to `.env` for Hardhat deployment settings.

Copy `backend/.env.example` to `backend/.env` and `frontend/.env.example` to `frontend/.env.local`.

Use a fresh burner wallet and public testnets only.

### 3. Deploy Ethereum Sepolia

Set:

```bash
DEPLOYER_PRIVATE_KEY=...
ETH_SEPOLIA_RPC_URL=...
```

Then:

```bash
npm run contracts:compile
npm run contracts:test
npm run contracts:deploy
```

The deployment script prints JSON containing the registry, semantic source contracts, LendLite and badge addresses.

### 4. Deploy Base Sepolia

```bash
npm run contracts:deploy:base
```

This deploys the portable verifier plus Base Sepolia semantic source contracts.

### 5. Run backend + frontend

```bash
cd backend
source .venv/bin/activate
python app.py
```

In another terminal:

```bash
cd frontend
npm run dev
```

## Live demo order

1. Create an OmniRep passport from a burner wallet on Ethereum Sepolia.
2. Link a second, different burner address on Base Sepolia by signing the challenge.
3. On each chain, open **Playground** and create a real loan+repayment, vote or contribution event.
4. Press **Refresh evidence**. The backend fetches and normalizes both chains.
5. Open **Passport overview** and inspect the score breakdown and recent evidence links.
6. Open **Sybil Radar** and show deterministic rules plus optional AI second opinion.
7. Open **Publish** and sign the EIP-712 attestation. The passport owner pays the publication gas; the backend only supplies the attestor signature.
8. Open **Verifier**. The browser recomputes the exact SHA-256 proof input. Toggle tamper mode to change a proof input and produce a mismatch.
9. Open **LendLite Gate**. The consumer reads the registry signal and shows access granted/blocked from the published score.
10. Optionally carry a portable attestation to Base Sepolia and show the second-chain verifier accepting it without a bridge.

## Production deployment notes

For deployment, use Neon or Supabase PostgreSQL rather than ephemeral disk. Put all private keys and API secrets in backend environment variables. Never place the attestor key, database credentials or explorer API key in frontend variables.

Render configuration is provided in `render.yaml`. Frontend variables belong in the Vercel project.

## Important implementation choices

- The passport is **passport-centric**, not just a renamed wallet address.
- Secondary wallet addresses are kept off-chain; only a commitment to the set is published.
- Deterministic scoring is the source of truth. AI never generates the final score.
- Reputation score and evidence confidence are separate concepts.
- A sparse or new wallet is not automatically treated as malicious; the product reports evidence level and risk separately.
- The playground contracts exist to create semantic testnet events for a reproducible hackathon demo without moving real funds.

## External deployment boundary

The source is deployment-ready, but a live public testnet deployment cannot honestly be fabricated without the team's funded burner wallet, deployment private key and RPC/explorer credentials. The repository therefore includes the deployment scripts and environment contract needed to perform the final external step.
