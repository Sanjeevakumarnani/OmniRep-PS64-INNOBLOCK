#!/usr/bin/env bash
set -euo pipefail
if [[ -z "${DEPLOYER_PRIVATE_KEY:-}" ]]; then echo "Set DEPLOYER_PRIVATE_KEY to a fresh testnet burner key."; exit 1; fi
npm install
npm run contracts:compile
npm run contracts:deploy
npm run hardhat:base 2>/dev/null || true
echo "Copy the printed addresses into backend/.env and frontend/.env.local, then verify each contract on its explorer."
