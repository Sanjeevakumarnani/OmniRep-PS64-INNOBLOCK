import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class ChainConfig:
    key: str
    chain_id: int
    name: str
    rpc_url: str
    explorer_tx: str
    explorer_api: str
    explorer_chain_id: int
    loan_pool: str
    governor: str
    contribution_log: str

CHAINS = {
    "ethereum-sepolia": ChainConfig(
        "ethereum-sepolia", 11155111, "Ethereum Sepolia",
        os.getenv("ETH_RPC_URL", "https://ethereum-sepolia.publicnode.com"),
        "https://sepolia.etherscan.io/tx/", "https://api.etherscan.io/v2/api", 11155111,
        os.getenv("ETH_LOAN_POOL_ADDRESS", ""), os.getenv("ETH_GOVERNOR_ADDRESS", ""), os.getenv("ETH_CONTRIBUTION_ADDRESS", ""),
    ),
    "base-sepolia": ChainConfig(
        "base-sepolia", 84532, "Base Sepolia",
        os.getenv("BASE_RPC_URL", "https://sepolia.base.org"),
        "https://sepolia.basescan.org/tx/", "https://api.etherscan.io/v2/api", 84532,
        os.getenv("BASE_LOAN_POOL_ADDRESS", ""), os.getenv("BASE_GOVERNOR_ADDRESS", ""), os.getenv("BASE_CONTRIBUTION_ADDRESS", ""),
    ),
}

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///omnirep.db")
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
elif DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
ATTESTOR_PRIVATE_KEY = os.getenv("ATTESTOR_PRIVATE_KEY", os.getenv("PUBLISHER_PRIVATE_KEY", ""))
REGISTRY_ADDRESS = os.getenv("OMNIREP_REGISTRY_ADDRESS", os.getenv("TRAILMARK_REGISTRY_ADDRESS", os.getenv("REPUTATION_REGISTRY_ADDRESS", "")))
VERIFIER_ADDRESS = os.getenv("OMNIREP_VERIFIER_ADDRESS", os.getenv("TRAILMARK_VERIFIER_ADDRESS", ""))
BADGE_ADDRESS = os.getenv("OMNIREP_BADGE_ADDRESS", os.getenv("TRAILMARK_BADGE_ADDRESS", ""))
LENDLITE_ADDRESS = os.getenv("LENDLITE_ADDRESS", "")
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY", "")
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_BASE_URL = os.getenv("AI_BASE_URL", "")
AI_MODEL = os.getenv("AI_MODEL", "")
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
PORT = int(os.getenv("PORT", "5000"))
MODEL_VERSION = 20001
INDEXER_BLOCK_WINDOW = int(os.getenv("INDEXER_BLOCK_WINDOW", "20000"))
