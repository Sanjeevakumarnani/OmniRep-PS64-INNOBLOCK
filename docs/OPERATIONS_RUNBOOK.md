# OmniRep Operations Runbook

This is the end-to-end operator guide for running, testing, deploying, and demoing
OmniRep — the PS64 omnichain reputation passport.

The commands below are written for Windows PowerShell. OmniRep uses public testnets
only:

- Ethereum Sepolia (`11155111`)
- Base Sepolia (`84532`)

Never use a mainnet wallet or a wallet that has held real funds.

## 1. System requirements

Install the following:

- Node.js 20 or newer
- npm
- Python 3.11 or newer
- MetaMask browser extension
- Git (optional)

The repository root is:

```text
C:\Users\Nanda Kishore\OneDrive\Desktop\SSK\PS64\OmniRep-PS64-INNOBLOCK
```

Open PowerShell and move to the project:

```powershell
cd "C:\Users\Nanda Kishore\OneDrive\Desktop\SSK\PS64\OmniRep-PS64-INNOBLOCK"
```

## 2. Install dependencies

Install the root Node dependencies:

```powershell
npm install
```

Install frontend dependencies:

```powershell
Set-Location .\frontend
npm install
Set-Location ..
```

Create or restore the backend virtual environment:

```powershell
if (-not (Test-Path .\backend\.venv\Scripts\python.exe)) {
  python -m venv .\backend\.venv
}
& .\backend\.venv\Scripts\python.exe -m pip install -r .\backend\requirements.txt
```

## 3. Environment files

There are three runtime environment files:

- `.env` — Hardhat deployment settings and shared local settings
- `backend\.env` — Flask, database, RPC, contract, and attestor settings
- `frontend\.env.local` — browser-safe API and contract addresses

Never put private keys in `frontend\.env.local`.

### 3.1 Root `.env`

Copy the template if needed:

```powershell
Copy-Item .\.env.example .\.env
```

Required deployment values:

```env
DEPLOYER_PRIVATE_KEY=0x<64 hexadecimal characters>
ETH_SEPOLIA_RPC_URL=https://ethereum-sepolia.publicnode.com
BASE_SEPOLIA_RPC_URL=https://sepolia.base.org
```

The private key must contain exactly 64 hexadecimal characters after `0x`.
Do not add spaces or print the value in logs.

### 3.2 Backend `.env`

Copy the backend template if needed:

```powershell
Copy-Item .\backend\.env.example .\backend\.env
```

For local operation, these values are sufficient:

```env
PORT=5000
FRONTEND_ORIGIN=http://localhost:5173
DATABASE_URL=sqlite:///omnirep.db
ETH_RPC_URL=https://ethereum-sepolia.publicnode.com
BASE_RPC_URL=https://sepolia.base.org
```

The backend must also contain:

```env
ATTESTOR_PRIVATE_KEY=0x<same authorized attestor key used by the registry>
OMNIREP_REGISTRY_ADDRESS=<Ethereum Sepolia registry>
OMNIREP_VERIFIER_ADDRESS=<Base Sepolia verifier>
```

The attestor key is backend-only. Never expose it through Vite variables,
browser local storage, API responses, screenshots, or source control.

### 3.3 Frontend `.env.local`

Copy the template if needed:

```powershell
Copy-Item .\frontend\.env.example .\frontend\.env.local
```

The frontend needs:

```env
VITE_API_BASE=http://localhost:5000
VITE_OMNIREP_REGISTRY_ADDRESS=<Ethereum Sepolia registry>
VITE_OMNIREP_VERIFIER_ADDRESS=<Base Sepolia verifier>
VITE_OMNIREP_BADGE_ADDRESS=<Ethereum Sepolia badge>
VITE_LENDLITE_ADDRESS=<Ethereum Sepolia LendLite>
```

It also uses the Ethereum and Base loan, governor, and contribution addresses.
These are public contract addresses and may be placed in frontend variables.

Vite reads `.env.local` only when it starts. Restart Vite after changing it.

## 4. Current deployed public addresses

These are the addresses deployed by the current project configuration.

### Ethereum Sepolia

| Contract | Address |
|---|---|
| Registry | `0x9680058Ace2b364C837ae184214b8f55688A52cA` |
| Loan pool | `0x707450D32c9774d77C3B26D70C6235a6404C9e33` |
| Governor | `0x9b6663eC055CB0638F6Db125500AF99A311998a5` |
| Contribution log | `0xF9E3BCE8a3cEb2A994C43Bea96e971585d5A3F26` |
| LendLite | `0xE7Aa207004B4E1aC17296CE4A4979c4FF50787EF` |
| Badge | `0xd6f69de9806403BD6424ae21c3A6Ba2c2998fDB7` |

Explorer links:

- Registry: <https://sepolia.etherscan.io/address/0x9680058Ace2b364C837ae184214b8f55688A52cA>
- LendLite: <https://sepolia.etherscan.io/address/0xE7Aa207004B4E1aC17296CE4A4979c4FF50787EF>

### Base Sepolia

| Contract | Address |
|---|---|
| Portable verifier | `0x9680058Ace2b364C837ae184214b8f55688A52cA` |
| Loan pool | `0x707450D32c9774d77C3B26D70C6235a6404C9e33` |
| Governor | `0x9b6663eC055CB0638F6Db125500AF99A311998a5` |
| Contribution log | `0xF9E3BCE8a3cEb2A994C43Bea96e971585d5A3F26` |

Explorer links:

- Verifier: <https://sepolia.basescan.org/address/0x9680058Ace2b364C837ae184214b8f55688A52cA>

The authoritative machine-readable manifests are:

- `deployments\ethereum-sepolia.json`
- `deployments\base-sepolia.json`

## 5. Validate before running

Run the deployment preflight:

```powershell
node .\scripts\deployment-preflight.js
```

Run contract compilation and tests:

```powershell
npm run contracts:compile
npm run contracts:test
```

Run frontend build:

```powershell
npm run frontend:build
```

Run static and offline backend validation:

```powershell
& .\backend\.venv\Scripts\python.exe .\scripts\validate.py
& .\backend\.venv\Scripts\python.exe .\scripts\offline_smoke.py
```

Expected contract test result:

```text
3 passing
```

## 6. Start the application locally

Use two PowerShell windows.

### Window 1 — backend

From the repository root:

```powershell
& .\backend\.venv\Scripts\python.exe .\backend\app.py
```

The backend listens on:

```text
http://127.0.0.1:5000
```

Check health:

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:5000/health |
  Select-Object -ExpandProperty Content
```

The response should contain:

```json
{
  "ok": true,
  "database": true,
  "chains": {
    "ethereum-sepolia": true,
    "base-sepolia": true
  }
}
```

### Window 2 — frontend

From the repository root:

```powershell
npm run frontend:dev
```

Open:

```text
http://localhost:5173
```

If the frontend was already running when `.env.local` changed, stop it with
`Ctrl+C` and run the command again.

## 7. First-time browser setup

1. Install or open MetaMask.
2. Create fresh burner wallets for the demo.
3. Fund only those wallets with Sepolia testnet ETH.
4. Keep the Ethereum Sepolia demo wallet separate from the Base Sepolia linked wallet.
5. Connect MetaMask to Ethereum Sepolia.
6. Open OmniRep at `http://localhost:5173`.

The browser needs the wallet that owns the Ethereum Sepolia passport when creating,
publishing, or accessing the primary passport.

## 8. Normal demo flow

### 8.1 Create or recover the passport

1. Click **Create passport**.
2. Approve the transaction on Ethereum Sepolia.
3. Wait for confirmation.
4. The app stores the passport ID and opens **Link wallets**.

Each wallet can create only one passport. If the browser lost its local passport ID,
clicking **Create passport** now checks `passportOf(address)` and recovers the
existing on-chain passport instead of submitting a duplicate transaction.

### 8.2 Link the second wallet

1. Open **Link wallets**.
2. Select Base Sepolia.
3. Switch MetaMask to the second burner wallet.
4. Sign the challenge message.
5. No funds are transferred by the linking signature.

### 8.3 Generate evidence

1. Open **Playground**.
2. Select Ethereum Sepolia or Base Sepolia.
3. Generate a repayment, governance vote, or contribution event.
4. Confirm the MetaMask transaction.
5. Return to **Overview**.
6. Click **Refresh evidence**.

### 8.4 Inspect reputation

Use:

- **Overview** — score, confidence, cross-chain evidence, and recent activity.
- **Sybil Radar** — deterministic risk rules and bounded optional AI analysis.
- **What-if Coach** — explainable score improvement scenarios.

The deterministic scoring model remains the source of truth. AI does not directly
set the final score.

### 8.5 Publish the proof

1. Open **Publish**.
2. Review the score, risk, version, and commitment hashes.
3. Sign the publication transaction on Ethereum Sepolia.
4. Wait for confirmation.

The registry stores compact commitments and score metadata. Personal data and the
detailed evidence bundle remain off-chain.

### 8.6 Verify and test tamper resistance

1. Open **Verifier**.
2. Inspect the proof bundle and SHA-256 input hash.
3. Recompute verification in the browser.
4. Enable tamper mode or change one proof field.
5. Confirm that verification fails.

### 8.7 Test the consumer gate

1. Open **LendLite Gate**.
2. Confirm that access is read from the published registry signal.
3. Change the minimum score or proof age in the consumer flow if available.
4. Confirm that access is granted or denied from the on-chain reputation state.

## 9. Deploy contracts again

Only deploy to Sepolia testnets.

Check prerequisites:

```powershell
node .\scripts\deployment-preflight.js
```

Deploy Ethereum Sepolia:

```powershell
npm run contracts:compile
npm run contracts:test
npm run contracts:deploy
```

Deploy Base Sepolia:

```powershell
npm run contracts:deploy:base
```

After deployment:

1. Copy public addresses from the generated deployment manifests.
2. Update `backend\.env`.
3. Update `frontend\.env.local`.
4. Restart the backend.
5. Restart Vite.
6. Run the frontend build.
7. Verify contract bytecode through the appropriate explorer.

Never commit `.env`, `backend\.env`, or any file containing a private key.

## 10. Production-style backend deployment

The repository includes `render.yaml` for a Render web service.

Configure these as server-side secrets/environment values in Render:

- `DATABASE_URL` — use Neon or Supabase PostgreSQL for persistent hosting.
- `FRONTEND_ORIGIN`
- `ATTESTOR_PRIVATE_KEY`
- Both chain RPC URLs
- All deployed contract addresses
- Optional explorer and AI settings

Use the provided start command:

```text
gunicorn app:app --timeout 120 --workers 2
```

Do not use SQLite for a multi-instance production deployment. The local value
`sqlite:///omnirep.db` is suitable for local development and offline testing only.

## 11. Common problems

### `already has passport`

The wallet already owns a passport on the registry. Do not retry the transaction.
Refresh the frontend and click **Create passport** once; the app will recover the
existing passport ID through `passportOf(address)`.

### Frontend options do not change

Make sure the frontend is running the current source and hard-refresh the browser:

```text
Ctrl+Shift+R
```

The app shows the landing hero only on the Overview screen. Other screens show a
passport-required state until a passport is loaded.

### Contract addresses appear empty

Check:

```powershell
Get-Content .\frontend\.env.local
```

Restart Vite after changing the file. Browser-safe variables must start with `VITE_`.

### Backend cannot start with `ModuleNotFoundError`

Restore the virtual environment dependencies:

```powershell
& .\backend\.venv\Scripts\python.exe -m pip install -r .\backend\requirements.txt
```

### Backend health reports `attestorConfigured: false`

Set `ATTESTOR_PRIVATE_KEY` in `backend\.env` to the backend-only attestor key that
matches the registry's configured attestor. Restart the backend.

### Wallet or network errors

Confirm:

- MetaMask is unlocked.
- The selected network is the requested Sepolia network.
- The wallet has testnet ETH.
- The contract address belongs to the selected chain.
- The browser is not connected to a mainnet account for this demo.

## 12. Security checklist

Before sharing the project or recording a demo:

- Use burner wallets only.
- Use testnets only.
- Do not paste private keys into chat, README files, screenshots, or issue trackers.
- Do not expose `ATTESTOR_PRIVATE_KEY` to the frontend.
- Do not commit `.env` or `backend\.env`.
- Do not place names, email addresses, or other personal data on-chain.
- Do not claim a transaction is deployed until an explorer confirms it.
- Run a secret scan before any commit.

## 13. Shutdown

In each running PowerShell window, press:

```text
Ctrl+C
```

The local SQLite database is stored as `omnirep.db` according to
`DATABASE_URL=sqlite:///omnirep.db`. It is local runtime state and should not be
committed or uploaded.

## 14. Useful project commands

```powershell
# Start frontend
npm run frontend:dev

# Build frontend
npm run frontend:build

# Compile contracts
npm run contracts:compile

# Test contracts
npm run contracts:test

# Check deployment prerequisites
node .\scripts\deployment-preflight.js

# Deploy Ethereum Sepolia
npm run contracts:deploy

# Deploy Base Sepolia
npm run contracts:deploy:base

# Validate project files
& .\backend\.venv\Scripts\python.exe .\scripts\validate.py

# Run offline end-to-end smoke test
& .\backend\.venv\Scripts\python.exe .\scripts\offline_smoke.py
```
