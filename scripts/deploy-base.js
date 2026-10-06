const fs = require("fs");
const path = require("path");
const { ethers } = require("hardhat");

async function deploy(name, ...args) {
  const F = await ethers.getContractFactory(name);
  const c = await F.deploy(...args);
  await c.waitForDeployment();
  return c;
}

async function main() {
  const [d] = await ethers.getSigners();
  const verifier = await deploy("OmniRepVerifier", d.address);
  const loan = await deploy("OmniRepLoanPool");
  const gov = await deploy("OmniRepGovernor");
  const con = await deploy("OmniRepContributionLog");

  const result = {
    network: "base-sepolia",
    chainId: 84532,
    deployer: d.address,
    attestor: d.address,
    verifier: await verifier.getAddress(),
    loanPool: await loan.getAddress(),
    governor: await gov.getAddress(),
    contributionLog: await con.getAddress(),
    deployedAt: new Date().toISOString(),
  };

  fs.mkdirSync(path.join(__dirname, "..", "deployments"), { recursive: true });
  fs.writeFileSync(
    path.join(__dirname, "..", "deployments", "base-sepolia.json"),
    JSON.stringify(result, null, 2) + "\n"
  );
  console.log(JSON.stringify(result, null, 2));
}

main().catch((e) => {
  console.error(e);
  process.exitCode = 1;
});
