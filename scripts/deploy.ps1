$ErrorActionPreference = 'Stop'
if (-not $env:DEPLOYER_PRIVATE_KEY) { throw 'Set DEPLOYER_PRIVATE_KEY to a fresh testnet burner key.' }
npm install
npm run contracts:compile
npm run contracts:deploy
Write-Host 'Now run the Base Sepolia deployment script manually and copy addresses into env files.'
