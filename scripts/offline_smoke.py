"""Dependency-light OmniRep logic smoke test for environments without npm/pip network access."""
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from scoring import canonical_json, score_reputation  # noqa: E402


def sha(v):
    return "0x" + hashlib.sha256(v.encode()).hexdigest()


NOW = 1_760_000_000
base = [
    {
        "id": "1", "passportId": "1", "chainId": 11155111,
        "chainName": "Ethereum Sepolia", "address": "0xabc",
        "txHash": "0x1", "blockNumber": 1, "timestamp": NOW - 86400 * 180,
        "activityType": "loan_repaid", "source": "TEST", "contractAddress": "0xloan",
        "amount": 100, "qualityGrade": "A", "details": {"onTime": True, "counterparty": "0xlender"},
    },
    {
        "id": "2", "passportId": "1", "chainId": 84532,
        "chainName": "Base Sepolia", "address": "0xdef",
        "txHash": "0x2", "blockNumber": 2, "timestamp": NOW - 86400 * 90,
        "activityType": "vote", "source": "TEST", "contractAddress": "0xgov",
        "amount": 0, "qualityGrade": "A", "details": {"proposalId": 1, "counterparty": "0xgov"},
    },
    {
        "id": "3", "passportId": "1", "chainId": 84532,
        "chainName": "Base Sepolia", "address": "0xdef",
        "txHash": "0x3", "blockNumber": 3, "timestamp": NOW - 86400 * 30,
        "activityType": "contribution", "source": "TEST", "contractAddress": "0xcontrib",
        "amount": 10, "qualityGrade": "A", "details": {"counterparty": "0xproject"},
    },
]
metrics = {
    "ethereum-sepolia": {"0xabc": {"ok": True, "firstSeen": NOW - 86400 * 200, "txCount": 80, "successfulContractInteractions": 30, "counterparties": ["0xlender", "0xgov"]}},
    "base-sepolia": {"0xdef": {"ok": True, "firstSeen": NOW - 86400 * 100, "txCount": 60, "successfulContractInteractions": 25, "counterparties": ["0xproject", "0xgov"]}},
}

r = score_reputation(base, 2, metrics, now_ts=NOW)
assert 0 <= r["score"] <= 1000
assert r["confidence"] > 0
assert r["breakdown"]["cross_chain"]["points"] > 0

payload = {
    "schema": "omnirep-proof-input-v1",
    "passportId": "1",
    "wallets": [{"address": "0xabc", "chainId": 11155111}, {"address": "0xdef", "chainId": 84532}],
    "activities": sorted(base, key=lambda x: x["id"]),
    "genericMetrics": metrics,
}
canonical = canonical_json(payload)
committed = sha(canonical)
parsed = json.loads(canonical)
recomputed = sha(canonical_json(parsed))
assert committed == recomputed
parsed["activities"][0]["activityType"] = "vote"
tampered = sha(canonical_json(parsed))
assert tampered != committed
print("Offline OmniRep smoke: PASS")
print(f"score={r['score']} confidence={r['confidence']} sybilRisk={r['sybilRisk']}")
print(f"proof={committed}")
print(f"tamper_detected={tampered != committed}")
