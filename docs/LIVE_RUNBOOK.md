# OmniRep PS64 — Live Runbook

This is the shortest path from the source package to a judge-ready live demo.

## 1. Environment

Root `.env`:

- `DEPLOYER_PRIVATE_KEY`
- `ETH_SEPOLIA_RPC_URL`
- `BASE_SEPOLIA_RPC_URL`

Backend:

- `ATTESTOR_PRIVATE_KEY`
- `DATABASE_URL`
- `ETH_RPC_URL`
- `BASE_RPC_URL`
- deployed contract addresses

Frontend:

- `VITE_API_BASE`
- deployed contract addresses

Use fresh burner wallets and public testnets only.

## 2. Preflight

```bash
npm run deployment:preflight
```

Do not deploy if preflight fails.

## 3. Compile + tests

```bash
npm install
npm run contracts:compile
npm run contracts:test
```

## 4. Deploy

```bash
npm run contracts:deploy
npm run contracts:deploy:base
```

Copy the generated `deployments/*.json` addresses into the backend and frontend environment files.

## 5. Backend

```bash
cd backend
pip install -r requirements.txt
python app.py
```

Confirm:

```text
GET /health
```

Expected: database healthy and both chain RPCs reachable.

## 6. Judge rehearsal

1. Create passport on Ethereum Sepolia.
2. Sign/link Ethereum wallet.
3. Switch to Base Sepolia and sign/link the second wallet.
4. Emit at least one semantic event on each testnet.
5. Sync.
6. Generate the 0–1000 score.
7. Show the factor breakdown and Sybil Radar.
8. Publish the EIP-712 attested score to the registry.
9. Open the independent verifier.
10. Toggle the tamper control and show SHA-256 mismatch.
11. Carry the attestation to Base Sepolia.
12. Open LendLite and show the contract gate.

## 7. Offline validation

This environment cannot reach package registries or testnet RPCs. The dependency-light smoke test remains runnable:

```bash
python scripts/offline_smoke.py
python scripts/validate.py
python -m compileall -q backend
```

These checks do not substitute for live blockchain deployment.
