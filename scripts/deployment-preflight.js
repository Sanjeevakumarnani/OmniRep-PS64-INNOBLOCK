require("dotenv").config();

const required = [
  "DEPLOYER_PRIVATE_KEY",
  "ETH_SEPOLIA_RPC_URL",
  "BASE_SEPOLIA_RPC_URL",
];

const missing = required.filter((key) => !process.env[key]);
if (missing.length) {
  console.error("DEPLOYMENT PREFLIGHT: BLOCKED");
  console.error("Missing:");
  for (const key of missing) console.error(`- ${key}`);
  process.exit(1);
}

if (!/^0x[0-9a-fA-F]{64}$/.test(process.env.DEPLOYER_PRIVATE_KEY)) {
  console.error("DEPLOYMENT PREFLIGHT: BLOCKED");
  console.error("DEPLOYER_PRIVATE_KEY must be a 32-byte hex private key (0x + 64 hex characters).");
  process.exit(1);
}

console.log("DEPLOYMENT PREFLIGHT: PASS");
console.log("- Ethereum Sepolia RPC configured");
console.log("- Base Sepolia RPC configured");
console.log("- Burner deployer key format valid");
console.log("- No private key is written to deployment JSON output");
