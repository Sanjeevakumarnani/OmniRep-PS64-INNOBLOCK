# OmniRep — INNOBLOCK 2.0 Day-2 Deployment Run

This runbook is aligned to the INNOBLOCK 2.0 participant handbook and the PS64 requirements.

## 0. Non-negotiable rules

- Public testnets only. Never mainnet.
- Fresh burner wallets only. Never use a wallet that has held real funds.
- Never commit `.env`, private keys, database URLs, or AI keys.
- No personal/real-world identity data on-chain. Only cryptographic hashes and reputation metadata.
- Every teammate must understand their assigned part.

## 1. Accounts to prepare

Use separate burner accounts for:

1. Deployment/attestor wallet — used by Hardhat to deploy and authorize reputation publication.
2. Demo wallet A — Ethereum Sepolia passport owner.
3. Demo wallet B — Base Sepolia linked wallet.

Keep the deployment/attestor key backend-only. The demo wallets remain user wallets controlled by MetaMask.

## 2. Fund the burners

The handbook says about 0.05 Sepolia ETH per wallet is enough for a full day. Fund the deployer and demo wallets on the networks they actually use.

Required:
- Deployment wallet: Ethereum Sepolia ETH + Base Sepolia ETH if the same account deploys both.
- Demo wallet A: Ethereum Sepolia ETH.
- Demo wallet B: Base Sepolia ETH.

## 3. Local checks

From the project root in PowerShell:

```powershell
npm install
npm run contracts:compile
npm run contracts:test
npm run deployment:preflight
```

Do not proceed if compilation or contract tests fail.

## 4. Configure deployment environment

Create `.env` from `.env.example` and set only local/backend/deployment secrets.

```text
DEPLOYER_PRIVATE_KEY=<burner deployment wallet private key>
ETH_SEPOLIA_RPC_URL=<working Sepolia RPC>
BASE_SEPOLIA_RPC_URL=<working Base Sepolia RPC>
```

Never put this private key in `frontend/.env` or any VITE variable.

## 5. Deploy Ethereum Sepolia

```powershell
npm run contracts:deploy
```

This deploys:
- OmniRepRegistry
- OmniRepLoanPool
- OmniRepGovernor
- OmniRepContributionLog
- LendLite
- OmniRepBadge

Save the printed addresses and the generated deployment JSON.

## 6. Deploy Base Sepolia

```powershell
npm run contracts:deploy:base
```

Save the printed addresses.

## 7. Verify contracts

Verify every deployed contract on its matching explorer using the exact compiler configuration in `hardhat.config.js`:

- Solidity 0.8.24
- optimizer enabled
- 200 runs

A verified contract is required for the blockchain-quality score and makes the code readable to judges.

## 8. PostgreSQL

Create a Neon or Supabase PostgreSQL database.

Set backend:

```text
DATABASE_URL=postgresql+psycopg://...
```

Do not rely on Render's local disk for the final demo because the handbook states that Render disk is wiped on restart.

## 9. Backend environment

Set:

```text
FRONTEND_ORIGIN=https://<vercel-frontend>
DATABASE_URL=postgresql+psycopg://...
ETH_RPC_URL=<Sepolia RPC>
BASE_RPC_URL=<Base Sepolia RPC>
ATTESTOR_PRIVATE_KEY=<deployment/attestor burner key>
OMNIREP_REGISTRY_ADDRESS=<Sepolia registry>
OMNIREP_VERIFIER_ADDRESS=<Base verifier>
OMNIREP_BADGE_ADDRESS=<Sepolia badge>
LENDLITE_ADDRESS=<Sepolia LendLite>
ETH_LOAN_POOL_ADDRESS=<Sepolia loan pool>
BASE_LOAN_POOL_ADDRESS=<Base loan pool>
ETH_GOVERNOR_ADDRESS=<Sepolia governor>
BASE_GOVERNOR_ADDRESS=<Base governor>
ETH_CONTRIBUTION_ADDRESS=<Sepolia contribution log>
BASE_CONTRIBUTION_ADDRESS=<Base contribution log>
```

AI variables are optional. The deterministic Sybil fallback must remain functional without an AI key.

## 10. Backend smoke test

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open:

```text
http://localhost:5000/health
```

The result must report `ok: true`.

## 11. Frontend environment

Set:

```text
VITE_API_BASE=https://<render-backend>
VITE_OMNIREP_REGISTRY_ADDRESS=<Sepolia registry>
VITE_OMNIREP_VERIFIER_ADDRESS=<Base verifier>
VITE_OMNIREP_BADGE_ADDRESS=<Sepolia badge>
VITE_LENDLITE_ADDRESS=<Sepolia LendLite>
VITE_ETH_LOAN_POOL_ADDRESS=<Sepolia loan pool>
VITE_BASE_LOAN_POOL_ADDRESS=<Base loan pool>
VITE_ETH_GOVERNOR_ADDRESS=<Sepolia governor>
VITE_BASE_GOVERNOR_ADDRESS=<Base governor>
VITE_ETH_CONTRIBUTION_ADDRESS=<Sepolia contribution log>
VITE_BASE_CONTRIBUTION_ADDRESS=<Base contribution log>
```

Then:

```powershell
npm run frontend:build
```

## 12. Required PS64 demo flow

Run exactly this sequence:

1. Connect demo wallet A on Ethereum Sepolia.
2. Create the OmniRep passport on Ethereum Sepolia.
3. Sign the wallet-link challenge.
4. Switch MetaMask to Base Sepolia.
5. Connect demo wallet B and sign its wallet-link challenge.
6. Create at least one real semantic signal on each chain.
7. Sync/index both chains.
8. Show normalized cross-chain activity.
9. Generate the transparent 0–1000 score.
10. Open Score Breakdown / Proof of Why.
11. Open Sybil Radar.
12. Publish the reputation attestation to Ethereum Sepolia.
13. Open the registry transaction on the explorer.
14. Open Verifier and prove the hash matches.
15. Change one character in the proof and verify again; it must fail.
16. Open LendLite; it must read the on-chain score and gate access.
17. Optionally demonstrate the portable Base Sepolia attestation.
18. Open the shareable passport link.

## 13. Minimum judge-visible evidence

Have these browser tabs ready:

1. Live OmniRep frontend.
2. Verified OmniRepRegistry explorer page.
3. A successful publication transaction explorer page.
4. GitHub repository.
5. Slides PDF.

Keep a 1–2 minute backup video offline.

## 14. Freeze point

Once the complete live flow works, stop adding features. Only fix blockers, verify the repository, rehearse the pitch, and record the backup demo.

## 15. Final security check

```powershell
git status
```

Confirm:
- no `.env` is tracked
- no private key appears in the repository
- no database URL appears in frontend source
- no AI key appears in frontend source
- only testnet addresses are configured
- contract addresses in frontend/backend match the deployed contracts

## 16. Pitch order

Keep the presentation to the handbook's structure:

1. Hook — fragmented reputation problem.
2. Solution — OmniRep cross-chain reputation passport.
3. Live demo — two wallets, two chains, score, proof, verifier, gate.
4. Architecture — wallet → backend/indexer → scoring → hash → registry → consumer.
5. What's next — broader chains, integrations, production attestations.
