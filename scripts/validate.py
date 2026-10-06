from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
required = [
    "README.md", "SECURITY.md", "render.yaml", "backend/app.py", "backend/scoring.py",
    "backend/indexer.py", "contracts/OmniRepRegistry.sol", "contracts/OmniRepVerifier.sol",
    "contracts/OmniRepLoanPool.sol", "contracts/LendLite.sol", "frontend/src/App.tsx",
    "frontend/src/components/ui/SpotlightCard.tsx", "frontend/src/components/ui/ShimmerButton.tsx",
    "frontend/src/components/ui/BorderBeam.tsx", "frontend/src/components/ui/NumberTicker.tsx",
    "docs/FINAL_CHECKLIST.md", "docs/PITCH.md", "docs/DEMO_SCRIPT.md", "docs/SCORING.md",
]
missing = [x for x in required if not (ROOT / x).exists()]
if missing:
    raise SystemExit(f"Missing required files: {missing}")

# Project should not carry committed local secrets/database artifacts.
for path in ROOT.rglob("*"):
    if any(part in {".git", "node_modules", ".venv", "__pycache__", "artifacts", "cache"} for part in path.parts):
        continue
    if path.is_file() and path.name.endswith(".db"):
        raise SystemExit(f"Database artifact must not ship: {path}")

text = (ROOT / "backend/scoring.py").read_text(encoding="utf-8")
assert '"model": "omnirep_scoring_v2"' in text
assert '"scale": 1000' in text
assert '"repayments"' in text and '"wallet_longevity"' in text
assert 'compute_risk' in text

sol = (ROOT / "contracts/OmniRepRegistry.sol").read_text(encoding="utf-8")
for needle in ["sha256(raw)", "verifyInputBytes", "function meets", "bytes32 inputHash", "uint16 score"]:
    assert needle in sol, needle

front = (ROOT / "frontend/src/App.tsx").read_text(encoding="utf-8")
for needle in ["OmniRep", "DIAMOND", "Change one character", "Share passport", "LendLite", "Sybil Radar"]:
    assert needle in front, needle

render = (ROOT / "render.yaml").read_text(encoding="utf-8")
assert "gunicorn app:app" in render and "DATABASE_URL" in render and "ATTESTOR_PRIVATE_KEY" in render

print("OmniRep static validation: PASS")
print(f"Files checked: {len(required)}")
print("PS64 proof path: wallet linking -> cross-chain evidence -> score -> SHA-256 -> registry -> consumer gate")
