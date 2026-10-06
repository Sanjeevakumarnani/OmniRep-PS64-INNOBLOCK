export const API_BASE = import.meta.env.VITE_API_BASE || 'https://omnirep-ps64-innoblock.onrender.com';
export const NETWORKS = {
  11155111:{name:'Ethereum Sepolia',short:'Ethereum',chainIdHex:'0xaa36a7',rpc:'https://ethereum-sepolia.publicnode.com',explorer:'https://sepolia.etherscan.io/tx/'},
  84532:{name:'Base Sepolia',short:'Base',chainIdHex:'0x14a34',rpc:'https://sepolia.base.org',explorer:'https://sepolia.basescan.org/tx/'},
} as const;
export const CONTRACTS={
  registry:import.meta.env.VITE_OMNIREP_REGISTRY_ADDRESS||import.meta.env.VITE_TRAILMARK_REGISTRY_ADDRESS||'0x9680058Ace2b364C837ae184214b8f55688A52cA',
  verifier:import.meta.env.VITE_OMNIREP_VERIFIER_ADDRESS||import.meta.env.VITE_TRAILMARK_VERIFIER_ADDRESS||'0x9680058Ace2b364C837ae184214b8f55688A52cA',
  badge:import.meta.env.VITE_OMNIREP_BADGE_ADDRESS||import.meta.env.VITE_TRAILMARK_BADGE_ADDRESS||'0xd6f69de9806403BD6424ae21c3A6Ba2c2998fDB7',
  lendLite:import.meta.env.VITE_LENDLITE_ADDRESS||'0xE7Aa207004B4E1aC17296CE4A4979c4FF50787EF',
  ethLoanPool:import.meta.env.VITE_ETH_LOAN_POOL_ADDRESS||'0x707450D32c9774d77C3B26D70C6235a6404C9e33',
  baseLoanPool:import.meta.env.VITE_BASE_LOAN_POOL_ADDRESS||'0x707450D32c9774d77C3B26D70C6235a6404C9e33',
  ethGovernor:import.meta.env.VITE_ETH_GOVERNOR_ADDRESS||'0x9b6663eC055CB0638F6Db125500AF99A311998a5',
  baseGovernor:import.meta.env.VITE_BASE_GOVERNOR_ADDRESS||'0x9b6663eC055CB0638F6Db125500AF99A311998a5',
  ethContribution:import.meta.env.VITE_ETH_CONTRIBUTION_ADDRESS||'0xF9E3BCE8a3cEb2A994C43Bea96e971585d5A3F26',
  baseContribution:import.meta.env.VITE_BASE_CONTRIBUTION_ADDRESS||'0xF9E3BCE8a3cEb2A994C43Bea96e971585d5A3F26',
};
export const REGISTRY_ABI=[
 'function createPassport() returns (uint256)','function passportOf(address) view returns (uint256)','function getPassport(uint256) view returns (tuple(address owner,uint16 score,uint8 tier,uint8 sybilRisk,uint16 algoVersion,uint32 version,uint64 updatedAt,uint8 linkedCount,bytes32 inputHash,bytes32 linksHash))','function meets(uint256,uint16,uint64) view returns (bool)','function verifyInputs(uint256,bytes32) view returns (bool)','function verifyInputBytes(uint256,bytes) view returns (bool)','function scoreOf(uint256) view returns (uint16)','function tierOf(uint256) view returns (uint8)','function publish((uint256 id,uint16 score,uint8 sybilRisk,uint16 algoVersion,uint8 linkedCount,bytes32 inputHash,bytes32 linksHash,uint32 version,uint64 deadline),bytes)'
];
export const LOAN_ABI=['function borrow(uint256,uint64) returns (uint256)','function borrowAndRepay(uint256) returns (uint256)','function borrowAndDefault(uint256) returns (uint256)','function repay(uint256)','function markDefaulted(uint256)'];
export const GOV_ABI=['function createProposal(string) returns (uint256)','function vote(uint256,bool)'];
export const CONTRIB_ABI=['function contribute(bytes32,uint256)'];
export const LEND_ABI=['function borrow(uint256)'];
export const BADGE_ABI=['function claim() returns (uint256)'];
export const VERIFIER_ABI=['function accept((address subject,uint256 id,uint16 score,uint8 sybilRisk,uint32 version,uint64 deadline,bytes32 proofHash),bytes)','function meets(address,uint16,uint64) view returns(bool)'];
export const OMNIREP_THEME='graphite-inspired';
