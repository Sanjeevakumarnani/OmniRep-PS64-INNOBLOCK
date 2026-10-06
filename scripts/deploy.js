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
  const registry = await deploy("OmniRepRegistry", d.address, d.address);
  const loan = await deploy("OmniRepLoanPool");
  const gov = await deploy("OmniRepGovernor");
  const con = await deploy("OmniRepContributionLog");
  const lend = await deploy("LendLite", await registry.getAddress());
  const badge = await deploy("OmniRepBadge", await registry.getAddress());

  const result = {
    network: "ethereum-sepolia",
    chainId: 11155111,
    deployer: d.address,
    attestor: d.address,
    registry: await registry.getAddress(),
    loanPool: await loan.getAddress(),
    governor: await gov.getAddress(),
    contributionLog: await con.getAddress(),
    lendLite: await lend.getAddress(),
    badge: await badge.getAddress(),
    deployedAt: new Date().toISOString(),
  };

  fs.mkdirSync(path.join(__dirname, "..", "deployments"), { recursive: true });
  fs.writeFileSync(
    path.join(__dirname, "..", "deployments", "ethereum-sepolia.json"),
    JSON.stringify(result, null, 2) + "\n"
  );
  console.log(JSON.stringify(result, null, 2));
}

main().catch((e) => {
  console.error(e);
  process.exitCode = 1;
});
