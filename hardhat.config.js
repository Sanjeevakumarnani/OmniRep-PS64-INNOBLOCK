require("dotenv").config();
require("@nomicfoundation/hardhat-toolbox");

const networks = {};
if (process.env.DEPLOYER_PRIVATE_KEY && process.env.ETH_SEPOLIA_RPC_URL) {
  networks.sepolia = { url: process.env.ETH_SEPOLIA_RPC_URL, accounts: [process.env.DEPLOYER_PRIVATE_KEY], chainId: 11155111 };
}
if (process.env.DEPLOYER_PRIVATE_KEY && process.env.BASE_SEPOLIA_RPC_URL) {
  networks.baseSepolia = { url: process.env.BASE_SEPOLIA_RPC_URL, accounts: [process.env.DEPLOYER_PRIVATE_KEY], chainId: 84532 };
}

module.exports = {
  solidity: {
    version: "0.8.24",
    settings: { evmVersion: "cancun", optimizer: { enabled: true, runs: 200 } },
  },
  networks,
  paths: { sources: "./contracts", tests: "./test", cache: "./cache", artifacts: "./artifacts" },
};
