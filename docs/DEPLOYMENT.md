# OmniRep deployment runbook

## Required external inputs

- funded burner deployment account
- Ethereum Sepolia RPC
- Base Sepolia RPC
- optional Etherscan/Basescan V2 API key
- optional AI API key/base URL/model
- Neon/Supabase PostgreSQL URL for hosted backend

## Ethereum Sepolia

```bash
export DEPLOYER_PRIVATE_KEY=...
export ETH_SEPOLIA_RPC_URL=...
npm run contracts:compile
npm run contracts:test
npm run contracts:deploy
```

Copy the printed addresses into backend and frontend environment variables.

## Base Sepolia

```bash
export DEPLOYER_PRIVATE_KEY=...
export BASE_SEPOLIA_RPC_URL=...
npm run contracts:deploy:base
```

Copy the Base verifier and semantic source addresses into the environment.

## Backend

Set:

```text
DATABASE_URL=postgresql+psycopg://...
ATTESTOR_PRIVATE_KEY=<same signing account used as attestor at deployment>
OMNIREP_REGISTRY_ADDRESS=<Sepolia registry>
OMNIREP_VERIFIER_ADDRESS=<Base verifier>
OMNIREP_BADGE_ADDRESS=<Sepolia badge>
LENDLITE_ADDRESS=<Sepolia consumer>
ETH_LOAN_POOL_ADDRESS=<Sepolia source>
BASE_LOAN_POOL_ADDRESS=<Base source>
ETH_GOVERNOR_ADDRESS=<Sepolia source>
BASE_GOVERNOR_ADDRESS=<Base source>
ETH_CONTRIBUTION_ADDRESS=<Sepolia source>
BASE_CONTRIBUTION_ADDRESS=<Base source>
```

Run:

```bash
python app.py
```

## Frontend

Set:

```text
VITE_API_BASE=https://<backend-host>
VITE_OMNIREP_REGISTRY_ADDRESS=<Sepolia registry>
VITE_OMNIREP_VERIFIER_ADDRESS=<Base verifier>
VITE_OMNIREP_BADGE_ADDRESS=<Sepolia badge>
VITE_LENDLITE_ADDRESS=<Sepolia consumer>
...semantic source addresses...
```

Build with:

```bash
npm run build
```

## Explorer verification

Use the same Solidity compiler version and optimizer settings declared in `hardhat.config.js` (`0.8.24`, optimizer 200 runs). Verify each deployed contract before the live rehearsal.

## Final rehearsal checklist

- create passport works
- two different wallets link
- each wallet shows the correct chain
- semantic events are visible on both chains
- score is non-zero after evidence
- score breakdown is intelligible in under 20 seconds
- hash match works
- tamper mismatch works
- registry explorer transaction exists
- LendLite gate reads published score
- optional Base portable attestation verifies
- no secret appears in browser devtools or frontend bundle
