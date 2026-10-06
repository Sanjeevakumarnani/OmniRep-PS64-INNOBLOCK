from __future__ import annotations

import hashlib
import json
import secrets
import time
from datetime import datetime, timezone

import requests
from eth_account import Account
from eth_account.messages import encode_defunct, encode_typed_data
from flask import Flask, jsonify, request
from flask_cors import CORS
from web3 import Web3

from config import *
from db import Activity, AuthChallenge, Passport, ScoreRun, SessionLocal, WalletLink, engine, init_db
from indexer import decode_and_collect, fetch_generic_metrics, w3_for
from scoring import CONFIG, canonical_json, compute_risk, score_reputation

app = Flask(__name__)
CORS(
    app,
    resources={
        r"/api/*": {
            "origins": [FRONTEND_ORIGIN, "http://localhost:5173", "http://127.0.0.1:5173"]
        }
    },
)
init_db()

REGISTRY_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint256", "name": "id", "type": "uint256"},
            {"indexed": True, "internalType": "address", "name": "owner", "type": "address"},
        ],
        "name": "PassportCreated",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint256", "name": "id", "type": "uint256"},
            {"indexed": True, "internalType": "uint32", "name": "version", "type": "uint32"},
            {"indexed": False, "internalType": "uint16", "name": "score", "type": "uint16"},
            {"indexed": False, "internalType": "uint8", "name": "tier", "type": "uint8"},
            {"indexed": False, "internalType": "uint8", "name": "sybilRisk", "type": "uint8"},
            {"indexed": False, "internalType": "bytes32", "name": "inputHash", "type": "bytes32"},
            {"indexed": False, "internalType": "bytes32", "name": "linksHash", "type": "bytes32"},
        ],
        "name": "ScorePublished",
        "type": "event",
    },
    {
        "inputs": [],
        "name": "count",
        "outputs": [{"type": "uint256", "name": ""}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"name": "id", "type": "uint256"}],
        "name": "getPassport",
        "outputs": [
            {
                "components": [
                    {"name": "owner", "type": "address"},
                    {"name": "score", "type": "uint16"},
                    {"name": "tier", "type": "uint8"},
                    {"name": "sybilRisk", "type": "uint8"},
                    {"name": "algoVersion", "type": "uint16"},
                    {"name": "version", "type": "uint32"},
                    {"name": "updatedAt", "type": "uint64"},
                    {"name": "linkedCount", "type": "uint8"},
                    {"name": "inputHash", "type": "bytes32"},
                    {"name": "linksHash", "type": "bytes32"},
                ],
                "name": "",
                "type": "tuple",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"name": "id", "type": "uint256"}],
        "name": "ownerOfPassport",
        "outputs": [{"type": "address", "name": ""}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"name": "id", "type": "uint256"},
            {"name": "minScore", "type": "uint16"},
            {"name": "maxAge", "type": "uint64"},
        ],
        "name": "meets",
        "outputs": [{"type": "bool", "name": ""}],
        "stateMutability": "view",
        "type": "function",
    },
]

ATTESTATION_TYPES = {
    "Attestation": [
        {"name": "id", "type": "uint256"},
        {"name": "score", "type": "uint16"},
        {"name": "sybilRisk", "type": "uint8"},
        {"name": "algoVersion", "type": "uint16"},
        {"name": "linkedCount", "type": "uint8"},
        {"name": "inputHash", "type": "bytes32"},
        {"name": "linksHash", "type": "bytes32"},
        {"name": "version", "type": "uint32"},
        {"name": "deadline", "type": "uint64"},
    ]
}

PORTABLE_TYPES = {
    "PortableAttestation": [
        {"name": "subject", "type": "address"},
        {"name": "id", "type": "uint256"},
        {"name": "score", "type": "uint16"},
        {"name": "sybilRisk", "type": "uint8"},
        {"name": "version", "type": "uint32"},
        {"name": "deadline", "type": "uint64"},
        {"name": "proofHash", "type": "bytes32"},
    ]
}


def now_ts() -> int:
    return int(time.time())


def checksum(address: str) -> str:
    return Web3.to_checksum_address(address)


def sha256_hex(value: str) -> str:
    return "0x" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def serialize_activity(a: Activity) -> dict:
    try:
        details = json.loads(a.details or "{}")
    except Exception:
        details = {}
    return {
        "id": a.id,
        "passportId": a.passport_id,
        "chainId": a.chain_id,
        "chainName": a.chain_name,
        "address": a.address,
        "txHash": a.tx_hash,
        "blockNumber": a.block_number,
        "timestamp": a.timestamp,
        "activityType": a.activity_type,
        "source": a.source,
        "contractAddress": a.contract_address,
        "amount": a.normalized_amount,
        "qualityGrade": a.quality_grade,
        "details": details,
    }


def get_passport(s, pid: str):
    p = s.get(Passport, pid)
    if not p:
        return None, (jsonify({"error": "passport_not_found"}), 404)
    return p, None


def passport_payload(s, pid: str) -> dict:
    p = s.get(Passport, pid)
    wallets = (
        s.query(WalletLink)
        .filter(WalletLink.passport_id == pid, WalletLink.status == "verified")
        .order_by(WalletLink.verified_at.asc())
        .all()
    )
    activities = (
        s.query(Activity)
        .filter(Activity.passport_id == pid)
        .order_by(Activity.timestamp.desc())
        .all()
    )
    latest_run = (
        s.query(ScoreRun)
        .filter(ScoreRun.passport_id == pid)
        .order_by(ScoreRun.created_at.desc())
        .first()
    )
    return {
        "passportId": pid,
        "ownerAddress": p.owner_address,
        "score": p.score,
        "confidence": p.confidence,
        "sybilRisk": p.sybil_risk,
        "tier": p.tier,
        "inputHash": p.input_hash,
        "linksHash": p.links_hash,
        "modelVersion": p.model_version,
        "version": p.version,
        "updatedAt": p.updated_at.isoformat(),
        "lastSyncAt": p.last_sync_at.isoformat(),
        "publishedTxHash": p.published_tx_hash,
        "publishedChain": p.published_chain,
        "linkedCount": len(wallets),
        "wallets": [
            {
                "address": w.address,
                "chainId": w.chain_id,
                "verifiedAt": w.verified_at.isoformat(),
            }
            for w in wallets
        ],
        "activityCount": len(activities),
        "activities": [serialize_activity(a) for a in activities[:250]],
        "genericMetrics": json.loads(p.generic_metrics or "{}"),
        "lastBreakdown": json.loads(latest_run.breakdown_json) if latest_run else {},
        "lastRisk": json.loads(latest_run.risk_json) if latest_run else {},
    }


def build_hash_input(s, pid: str) -> tuple[dict, list[WalletLink], list[dict], dict]:
    wallets = (
        s.query(WalletLink)
        .filter(WalletLink.passport_id == pid, WalletLink.status == "verified")
        .order_by(WalletLink.address.asc(), WalletLink.chain_id.asc())
        .all()
    )
    activities = [
        serialize_activity(a)
        for a in s.query(Activity).filter(Activity.passport_id == pid).order_by(Activity.id.asc()).all()
    ]
    metrics = json.loads(s.get(Passport, pid).generic_metrics or "{}")
    hash_input = {
        "schema": "omnirep-proof-input-v1",
        "passportId": pid,
        "wallets": sorted(
            [{"address": w.address.lower(), "chainId": w.chain_id} for w in wallets],
            key=lambda x: (x["address"], x["chainId"]),
        ),
        "activities": activities,
        "genericMetrics": metrics,
        "scoringConfig": CONFIG,
    }
    return hash_input, wallets, activities, metrics


def tier_for(score: int) -> int:
    if score >= 800:
        return 4
    if score >= 600:
        return 3
    if score >= 400:
        return 2
    if score >= 200:
        return 1
    return 0


def deterministic_ai_fallback(features: dict) -> dict:
    suspicion = 0
    reasons = []
    if float(features.get("burstRatio", 0)) > 0.6:
        suspicion += 35
        reasons.append("High temporal burst")
    if float(features.get("repeatRatio", 0)) > 0.6:
        suspicion += 35
        reasons.append("Repeated transaction signature")
    if float(features.get("counterpartyDiversity", 0)) <= 1 and int(features.get("activityCount", 0)) >= 4:
        suspicion += 20
        reasons.append("Single counterparty concentration")
    return {
        "provider": "deterministic-fallback",
        "suspicion": min(100, suspicion),
        "patterns": reasons or ["No strong farming pattern"],
        "explanation": "Rule-based second opinion; it never changes the final reputation score by itself.",
    }


def ai_second_opinion(features: dict) -> dict:
    if not (AI_API_KEY and AI_BASE_URL and AI_MODEL):
        return deterministic_ai_fallback(features)
    payload = {
        "model": AI_MODEL,
        "messages": [
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "task": "Classify likely Sybil/farmed blockchain activity. Never infer real-world identity. Return JSON with suspicion 0-100, patterns array and explanation.",
                        "features": features,
                    }
                ),
            }
        ],
        "temperature": 0,
    }
    try:
        r = requests.post(
            AI_BASE_URL.rstrip("/") + "/chat/completions",
            headers={
                "Authorization": f"Bearer {AI_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=20,
        )
        r.raise_for_status()
        raw = r.json()
        parsed = {}
        try:
            content = str(raw.get("choices", [{}])[0].get("message", {}).get("content", ""))
            content = content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            parsed = json.loads(content) if content else {}
        except Exception:
            parsed = {}
        suspicion = max(0, min(100, int(parsed.get("suspicion", 0) or 0)))
        patterns = parsed.get("patterns", []) if isinstance(parsed.get("patterns", []), list) else []
        explanation = str(parsed.get("explanation", "AI response was not machine-readable."))
        return {
            "provider": "external",
            "suspicion": suspicion,
            "patterns": [str(x) for x in patterns[:6]],
            "explanation": explanation[:800],
        }
    except Exception as exc:
        result = deterministic_ai_fallback(features)
        result["fallbackReason"] = str(exc)
        return result


@app.get("/health")
def health():
    chains = {}
    for key in CHAINS:
        try:
            chains[key] = bool(w3_for(key).is_connected())
        except Exception:
            chains[key] = False
    try:
        with engine.connect() as conn:
            conn.exec_driver_sql("SELECT 1")
        db_ok = True
    except Exception:
        db_ok = False
    return jsonify(
        {
            "ok": db_ok,
            "database": db_ok,
            "chains": chains,
            "registryConfigured": bool(REGISTRY_ADDRESS),
            "verifierConfigured": bool(VERIFIER_ADDRESS),
            "attestorConfigured": bool(ATTESTOR_PRIVATE_KEY),
            "modelVersion": MODEL_VERSION,
        }
    )


@app.get("/")
def api_home():
    return jsonify(
        {
            "service": "OmniRep API",
            "status": "running",
            "frontend": "http://localhost:5173",
            "health": "/health",
            "apiBase": "/api",
        }
    )


@app.post("/api/passports")
def create_passport_local():
    body = request.get_json(silent=True) or {}
    pid = str(body.get("passportId", ""))
    owner = str(body.get("ownerAddress", "")).lower()
    tx_hash = str(body.get("txHash", ""))
    if not pid or not owner or not Web3.is_address(owner):
        return jsonify({"error": "passportId_and_owner_required"}), 400

    chain_verified = False
    if REGISTRY_ADDRESS:
        if not tx_hash:
            return jsonify({"error": "creation_tx_hash_required"}), 400
        try:
            rpc = w3_for("ethereum-sepolia")
            if not rpc.is_connected():
                return jsonify({"error": "sepolia_rpc_unavailable"}), 503
            tx = rpc.eth.get_transaction(tx_hash)
            receipt = rpc.eth.get_transaction_receipt(tx_hash)
            if int(receipt.get("status", 0)) != 1:
                return jsonify({"error": "creation_transaction_failed"}), 400
            if str(tx.get("to") or "").lower() != REGISTRY_ADDRESS.lower():
                return jsonify({"error": "creation_not_sent_to_registry"}), 400
            if str(tx.get("from") or "").lower() != owner:
                return jsonify({"error": "creation_sender_mismatch"}), 400
            contract = rpc.eth.contract(address=REGISTRY_ADDRESS, abi=REGISTRY_ABI)
            events = contract.events.PassportCreated().process_receipt(receipt)
            matching = [e for e in events if int(e["args"]["id"]) == int(pid) and str(e["args"]["owner"]).lower() == owner]
            if not matching:
                return jsonify({"error": "passport_creation_event_mismatch"}), 400
            chain_verified = True
        except Exception as exc:
            return jsonify({"error": "creation_not_confirmed", "message": str(exc)}), 400

    with SessionLocal() as s:
        if s.get(Passport, pid):
            return jsonify({"passportId": pid, "chainVerified": chain_verified})
        existing = s.query(Passport).filter(Passport.owner_address == owner).first()
        if existing:
            return jsonify({"error": "owner_already_has_passport", "passportId": existing.id}), 409
        p = Passport(
            id=pid,
            owner_address=checksum(owner).lower(),
            model_version=MODEL_VERSION,
        )
        s.add(p)
        s.commit()
    return jsonify({"passportId": pid, "chainVerified": chain_verified})


@app.post("/api/passports/recover")
def recover_passport():
    body = request.get_json(silent=True) or {}
    pid = str(body.get("passportId", ""))
    owner = str(body.get("ownerAddress", "")).lower()
    if not pid or not Web3.is_address(owner):
        return jsonify({"error": "passportId_and_owner_required"}), 400
    if not REGISTRY_ADDRESS:
        return jsonify({"error": "registry_not_configured"}), 503
    try:
        rpc = w3_for("ethereum-sepolia")
        contract = rpc.eth.contract(address=REGISTRY_ADDRESS, abi=REGISTRY_ABI)
        chain_owner = str(contract.functions.ownerOfPassport(int(pid)).call()).lower()
        if chain_owner != owner:
            return jsonify({"error": "passport_owner_mismatch"}), 403
    except Exception as exc:
        return jsonify({"error": "passport_recovery_failed", "message": str(exc)}), 400

    with SessionLocal() as s:
        existing = s.get(Passport, pid)
        if existing:
            if existing.owner_address != owner:
                return jsonify({"error": "passport_owner_mismatch"}), 403
            return jsonify({"passportId": pid, "recovered": False})
        owner_passport = s.query(Passport).filter(Passport.owner_address == owner).first()
        if owner_passport and owner_passport.id != pid:
            return jsonify({"error": "owner_already_has_passport", "passportId": owner_passport.id}), 409
        s.add(Passport(id=pid, owner_address=checksum(owner).lower(), model_version=MODEL_VERSION))
        s.commit()
    return jsonify({"passportId": pid, "recovered": True})


@app.post("/api/auth/challenge")
def challenge():
    body = request.get_json(silent=True) or {}
    address = str(body.get("address", "")).lower()
    pid = str(body.get("passportId", ""))
    chain_id = int(body.get("chainId", 0))
    if not Web3.is_address(address):
        return jsonify({"error": "invalid_address"}), 400
    if chain_id not in (11155111, 84532):
        return jsonify({"error": "unsupported_chain"}), 400
    with SessionLocal() as s:
        p, err = get_passport(s, pid)
        if err:
            return err
        existing = (
            s.query(WalletLink)
            .filter(WalletLink.passport_id == pid, WalletLink.status == "verified", WalletLink.address == address)
            .first()
        )
        if existing:
            return jsonify({"error": "address_already_linked", "chainId": existing.chain_id}), 409
        nonce = secrets.token_urlsafe(24)
        issued = now_ts()
        expires = issued + 300
        message = (
            f"OmniRep Reputation Passport\n\n"
            f"Link wallet {checksum(address)} to passport #{pid}.\n"
            f"Chain ID: {chain_id}\n"
            f"Nonce: {nonce}\n"
            f"Issued: {issued}\n"
            f"Expires: {expires}\n\n"
            "I understand this signature proves control of this wallet only and transfers no funds."
        )
        s.add(
            AuthChallenge(
                nonce=nonce,
                passport_id=pid,
                address=address,
                chain_id=chain_id,
                message=message,
                expires_at=expires,
            )
        )
        s.commit()
    return jsonify({"message": message, "nonce": nonce, "expiresAt": expires})


@app.post("/api/auth/verify")
def verify_auth():
    body = request.get_json(silent=True) or {}
    address = str(body.get("address", "")).lower()
    signature = str(body.get("signature", ""))
    message = str(body.get("message", ""))
    pid = str(body.get("passportId", ""))
    chain_id = int(body.get("chainId", 0))
    nonce = str(body.get("nonce", ""))
    with SessionLocal() as s:
        c = s.get(AuthChallenge, nonce)
        if not c:
            return jsonify({"error": "challenge_missing"}), 400
        if c.expires_at < now_ts():
            s.delete(c)
            s.commit()
            return jsonify({"error": "challenge_expired"}), 400
        if c.passport_id != pid or c.address != address or c.chain_id != chain_id or c.message != message:
            return jsonify({"error": "challenge_mismatch"}), 400
        try:
            recovered = Account.recover_message(encode_defunct(text=message), signature=signature).lower()
        except Exception:
            return jsonify({"error": "signature_invalid"}), 400
        if recovered != address:
            return jsonify({"error": "ownership_not_proved"}), 400
        p, err = get_passport(s, pid)
        if err:
            return err
        owner_conflict = (
            s.query(WalletLink)
            .filter(
                WalletLink.address == address,
                WalletLink.status == "verified",
                WalletLink.passport_id != pid,
            )
            .first()
        )
        if owner_conflict:
            return jsonify({"error": "wallet_already_linked_to_other_passport"}), 409
        exists = (
            s.query(WalletLink)
            .filter(
                WalletLink.passport_id == pid,
                WalletLink.address == address,
                WalletLink.chain_id == chain_id,
                WalletLink.status == "verified",
            )
            .first()
        )
        if not exists:
            s.add(
                WalletLink(
                    passport_id=pid,
                    address=address,
                    chain_id=chain_id,
                    signature=signature,
                    nonce=nonce,
                )
            )
        s.delete(c)
        s.commit()
    return jsonify({"ok": True, "address": checksum(address), "chainId": chain_id})


@app.get("/api/passports/<pid>")
def passport(pid):
    with SessionLocal() as s:
        p, err = get_passport(s, pid)
        if err:
            return err
        return jsonify(passport_payload(s, pid))


@app.post("/api/passports/<pid>/sync")
def sync(pid):
    with SessionLocal() as s:
        p, err = get_passport(s, pid)
        if err:
            return err
        wallets = (
            s.query(WalletLink)
            .filter(WalletLink.passport_id == pid, WalletLink.status == "verified")
            .all()
        )
        if len(wallets) < 2:
            return jsonify({"error": "link_two_wallets_first"}), 400
        if len({w.chain_id for w in wallets}) < 2:
            return jsonify({"error": "link_two_testnets"}), 400

        addresses = [w.address for w in wallets]
        all_found: list[dict] = []
        errors: list[str] = []
        metrics: dict = {}
        for key, cfg in CHAINS.items():
            try:
                all_found.extend(decode_and_collect(key, addresses))
            except Exception as exc:
                errors.append(f"{cfg.name}: {exc}")
            metrics[key] = {a: fetch_generic_metrics(key, a) for a in addresses}

        added = []
        for item in all_found:
            chain_id = int(item["chainId"])
            aid = f"{chain_id}:{item['txHash']}:{item['activityType']}"
            if s.get(Activity, aid):
                continue
            row = Activity(
                id=aid,
                passport_id=pid,
                chain_id=chain_id,
                chain_name=item["chainName"],
                address=item["actor"].lower(),
                tx_hash=item["txHash"],
                block_number=int(item["blockNumber"]),
                timestamp=int(item["timestamp"]),
                activity_type=item["activityType"],
                source=item["source"],
                contract_address=item["contractAddress"].lower(),
                normalized_amount=float(item.get("amount", 0)),
                quality_grade=item.get("qualityGrade", "C"),
                details=json.dumps(item.get("details", {}), sort_keys=True),
            )
            s.add(row)
            added.append(serialize_activity(row))

        p.last_sync_at = datetime.now(timezone.utc)
        p.generic_metrics = json.dumps(metrics, sort_keys=True)
        s.commit()
        return jsonify(
            {
                "ok": True,
                "addedCount": len(added),
                "added": added,
                "errors": errors,
                "genericMetrics": metrics,
                "chainsRequested": list(CHAINS.keys()),
            }
        )


@app.post("/api/passports/<pid>/score")
def score(pid):
    with SessionLocal() as s:
        p, err = get_passport(s, pid)
        if err:
            return err
        activities = [
            serialize_activity(a)
            for a in s.query(Activity).filter(Activity.passport_id == pid).all()
        ]
        wallets = (
            s.query(WalletLink)
            .filter(WalletLink.passport_id == pid, WalletLink.status == "verified")
            .all()
        )
        metrics = json.loads(p.generic_metrics or "{}")
        result = score_reputation(activities, len(wallets), metrics)
        result["modelVersion"] = MODEL_VERSION
        result["evidenceCount"] = len(activities)
        result["tier"] = tier_for(result["score"])

        hash_input = {
            "schema": "omnirep-proof-input-v1",
            "passportId": pid,
            "wallets": sorted(
                [{"address": w.address.lower(), "chainId": w.chain_id} for w in wallets],
                key=lambda x: (x["address"], x["chainId"]),
            ),
            "activities": sorted(activities, key=lambda x: x["id"]),
            "genericMetrics": metrics,
            "scoringConfig": CONFIG,
        }
        input_hash = sha256_hex(canonical_json(hash_input))
        links_payload = canonical_json(
            sorted(
                [{"address": w.address.lower(), "chainId": w.chain_id} for w in wallets],
                key=lambda x: (x["address"], x["chainId"]),
            )
        )
        links_hash = sha256_hex(links_payload)

        p.input_hash = input_hash
        p.links_hash = links_hash
        p.score = result["score"]
        p.confidence = result["confidence"]
        p.sybil_risk = result["sybilRisk"]
        p.tier = result["tier"]
        p.model_version = MODEL_VERSION
        p.updated_at = datetime.now(timezone.utc)
        s.add(
            ScoreRun(
                passport_id=pid,
                score=p.score,
                confidence=p.confidence,
                model_version=MODEL_VERSION,
                input_hash=p.input_hash,
                breakdown_json=json.dumps(result["breakdown"], sort_keys=True),
                risk_json=json.dumps(result["risk"], sort_keys=True),
            )
        )
        s.commit()
        return jsonify({**result, "inputHash": input_hash, "linksHash": links_hash})


@app.get("/api/passports/<pid>/risk")
def risk(pid):
    with SessionLocal() as s:
        p, err = get_passport(s, pid)
        if err:
            return err
        activities = [
            serialize_activity(a)
            for a in s.query(Activity).filter(Activity.passport_id == pid).all()
        ]
        wallet_count = (
            s.query(WalletLink)
            .filter(WalletLink.passport_id == pid, WalletLink.status == "verified")
            .count()
        )
        result = compute_risk(activities, wallet_count)
        result["aiSecondOpinion"] = ai_second_opinion(result.get("features", {}))
        return jsonify(result)


def attestor_account():
    if not ATTESTOR_PRIVATE_KEY:
        raise RuntimeError("ATTESTOR_PRIVATE_KEY not configured")
    return Web3().eth.account.from_key(ATTESTOR_PRIVATE_KEY)


def typed_attestation(p, passport_id: str, linked_count: int):
    deadline = now_ts() + 900
    message = {
        "id": int(passport_id),
        "score": int(p.score),
        "sybilRisk": int(p.sybil_risk),
        "algoVersion": int(p.model_version),
        "linkedCount": int(linked_count),
        "inputHash": p.input_hash,
        "linksHash": p.links_hash,
        "version": int(p.version + 1),
        "deadline": deadline,
    }
    domain = {
        "name": "OmniRep Passport",
        "version": "1",
        "salt": "0x" + Web3.keccak(text="OmniRep.Portable.Attestation.v1").hex(),
    }
    typed = {
        "types": {
            "EIP712Domain": [
                {"name": "name", "type": "string"},
                {"name": "version", "type": "string"},
                {"name": "salt", "type": "bytes32"},
            ],
            **ATTESTATION_TYPES,
        },
        "primaryType": "Attestation",
        "domain": domain,
        "message": message,
    }
    signed = attestor_account().sign_message(encode_typed_data(full_message=typed))
    return message, "0x" + signed.signature.hex(), typed


@app.post("/api/passports/<pid>/attestation")
def attestation(pid):
    return signed_attestation(pid, require_chain=False)


def signed_attestation(pid: str, require_chain: bool = False):
    body = request.get_json(silent=True) or {}
    if require_chain and int(body.get("chainId", 0)) != 11155111:
        return jsonify({"error": "ethereum_sepolia_required"}), 400
    with SessionLocal() as s:
        p, err = get_passport(s, pid)
        if err:
            return err
        wallets = (
            s.query(WalletLink)
            .filter(WalletLink.passport_id == pid, WalletLink.status == "verified")
            .all()
        )
        if len(wallets) < 2:
            return jsonify({"error": "two_wallets_required"}), 400
        if not p.input_hash or not p.links_hash:
            return jsonify({"error": "score_before_publish"}), 400
        if REGISTRY_ADDRESS:
            try:
                rpc = w3_for("ethereum-sepolia")
                if not rpc.is_connected():
                    return jsonify({"error": "sepolia_rpc_unavailable"}), 503
                chain_passport = rpc.eth.contract(
                    address=REGISTRY_ADDRESS, abi=REGISTRY_ABI
                ).functions.getPassport(int(pid)).call()
                chain_owner = str(chain_passport[0]).lower()
                if chain_owner != p.owner_address.lower():
                    return jsonify({"error": "passport_owner_mismatch"}), 409
                chain_version = int(chain_passport[5])
                if chain_version > p.version:
                    p.version = chain_version
                    p.updated_at = datetime.now(timezone.utc)
                    s.commit()
            except Exception as exc:
                return jsonify({"error": "registry_state_unavailable", "message": str(exc)}), 503
        try:
            message, sig, typed = typed_attestation(p, pid, len(wallets))
            account = attestor_account()
        except Exception as exc:
            return jsonify({"error": "attestation_failed", "message": str(exc)}), 400
        return jsonify(
            {
                "message": message,
                "signature": sig,
                "typedData": typed,
                "attestor": account.address,
            }
        )


@app.post("/api/passports/<pid>/publish")
def publish_attestation(pid):
    return signed_attestation(pid, require_chain=True)


@app.get("/api/passports/<pid>/bundle")
def bundle(pid):
    with SessionLocal() as s:
        p, err = get_passport(s, pid)
        if err:
            return err
        hash_input, wallets, activities, metrics = build_hash_input(s, pid)
        activity_result = score_reputation(activities, len(wallets), metrics)
        return jsonify(
            {
                "schema": "omnirep-proof-bundle-v1",
                "passportId": pid,
                "owner": p.owner_address,
                "walletProofs": [
                    {
                        "address": w.address,
                        "chainId": w.chain_id,
                        "signature": w.signature,
                        "nonce": w.nonce,
                        "verifiedAt": w.verified_at.isoformat(),
                    }
                    for w in wallets
                ],
                "activities": activities,
                "genericMetrics": metrics,
                "algorithm": {
                    "version": p.model_version,
                    "name": CONFIG["model"],
                    "weights": CONFIG["weights"],
                },
                "scored": {
                    "score": activity_result["score"],
                    "confidence": activity_result["confidence"],
                    "sybilRisk": activity_result["sybilRisk"],
                    "tier": tier_for(activity_result["score"]),
                    "breakdown": activity_result["breakdown"],
                    "risk": activity_result["risk"],
                    "features": activity_result["features"],
                    "freshnessMultiplier": activity_result["freshnessMultiplier"],
                },
                "hashInput": hash_input,
                "inputHash": p.input_hash,
                "published": {
                    "score": p.score,
                    "confidence": p.confidence,
                    "sybilRisk": p.sybil_risk,
                    "inputHash": p.input_hash,
                    "linksHash": p.links_hash,
                    "version": p.version,
                    "txHash": p.published_tx_hash,
                    "chain": p.published_chain,
                },
            }
        )


@app.post("/api/passports/<pid>/portable-attestation")
def portable_attestation(pid):
    with SessionLocal() as s:
        p, err = get_passport(s, pid)
        if err:
            return err
        wallets = (
            s.query(WalletLink)
            .filter(WalletLink.passport_id == pid, WalletLink.status == "verified")
            .all()
        )
        if not wallets:
            return jsonify({"error": "wallet_required"}), 400
        if not p.input_hash or p.version == 0:
            return jsonify({"error": "publish_primary_proof_first"}), 400
        deadline = now_ts() + 900
        msg = {
            "subject": checksum(p.owner_address),
            "id": int(pid),
            "score": int(p.score),
            "sybilRisk": int(p.sybil_risk),
            "version": int(p.version),
            "deadline": deadline,
            "proofHash": p.input_hash,
        }
        domain = {
            "name": "OmniRep Passport",
            "version": "1",
            "salt": "0x" + Web3.keccak(text="OmniRep.Portable.Attestation.v1").hex(),
        }
        typed = {
            "types": {
                "EIP712Domain": [
                    {"name": "name", "type": "string"},
                    {"name": "version", "type": "string"},
                    {"name": "salt", "type": "bytes32"},
                ],
                **PORTABLE_TYPES,
            },
            "primaryType": "PortableAttestation",
            "domain": domain,
            "message": msg,
        }
        try:
            signed = attestor_account().sign_message(encode_typed_data(full_message=typed))
            account = attestor_account()
        except Exception as exc:
            return jsonify({"error": "portable_attestation_failed", "message": str(exc)}), 400
        return jsonify(
            {
                "message": msg,
                "signature": "0x" + signed.signature.hex(),
                "typedData": typed,
                "attestor": account.address,
            }
        )


@app.post("/api/passports/<pid>/published")
def published(pid):
    body = request.get_json(silent=True) or {}
    tx_hash = str(body.get("txHash", ""))
    version = int(body.get("version", 0))
    if not tx_hash or not version:
        return jsonify({"error": "txHash_and_version_required"}), 400
    if REGISTRY_ADDRESS and not Web3.is_address(REGISTRY_ADDRESS):
        return jsonify({"error": "registry_address_invalid"}), 500

    with SessionLocal() as s:
        p, err = get_passport(s, pid)
        if err:
            return err
        if version != p.version + 1:
            return jsonify({"error": "version_mismatch"}), 409

        chain_verified = False
        if REGISTRY_ADDRESS:
            try:
                rpc = w3_for("ethereum-sepolia")
                if not rpc.is_connected():
                    return jsonify({"error": "sepolia_rpc_unavailable"}), 503
                tx = rpc.eth.get_transaction(tx_hash)
                receipt = rpc.eth.get_transaction_receipt(tx_hash)
                if int(receipt.get("status", 0)) != 1:
                    return jsonify({"error": "publication_transaction_failed"}), 400
                if str(tx.get("to") or "").lower() != REGISTRY_ADDRESS.lower():
                    return jsonify({"error": "publication_not_sent_to_registry"}), 400
                if str(tx.get("from") or "").lower() != p.owner_address.lower():
                    return jsonify({"error": "publication_sender_mismatch"}), 400
                contract = rpc.eth.contract(address=REGISTRY_ADDRESS, abi=REGISTRY_ABI)
                events = contract.events.ScorePublished().process_receipt(receipt)
                matching = [
                    e for e in events
                    if int(e["args"]["id"]) == int(pid)
                    and int(e["args"]["version"]) == version
                    and int(e["args"]["score"]) == int(p.score)
                    and int(e["args"]["sybilRisk"]) == int(p.sybil_risk)
                    and str(e["args"]["inputHash"]).lower() == p.input_hash.lower()
                    and str(e["args"]["linksHash"]).lower() == p.links_hash.lower()
                ]
                if not matching:
                    return jsonify({"error": "publication_event_mismatch"}), 400
                chain_verified = True
            except Exception as exc:
                return jsonify({"error": "publication_not_confirmed", "message": str(exc)}), 400

        p.version = version
        p.published_tx_hash = tx_hash
        p.published_chain = "ethereum-sepolia"
        p.updated_at = datetime.now(timezone.utc)
        s.commit()
        return jsonify({"ok": True, "version": p.version, "txHash": tx_hash, "chainVerified": chain_verified})


@app.post("/api/passports/<pid>/verify")
def verify_proof(pid):
    body = request.get_json(silent=True) or {}
    supplied = str(body.get("hash", "")).lower()
    with SessionLocal() as s:
        p, err = get_passport(s, pid)
        if err:
            return err
        hash_input, _, _, _ = build_hash_input(s, pid)
        computed = sha256_hex(canonical_json(hash_input)).lower()
        return jsonify({
            "passportId": pid,
            "computedHash": computed,
            "committedHash": p.input_hash.lower(),
            "match": computed == p.input_hash.lower(),
            "suppliedHashMatch": bool(supplied) and supplied == p.input_hash.lower(),
            "version": p.version,
        })


@app.get("/api/passports/<pid>/history")
def history(pid):
    with SessionLocal() as s:
        p, err = get_passport(s, pid)
        if err:
            return err
        rows = (
            s.query(ScoreRun)
            .filter(ScoreRun.passport_id == pid)
            .order_by(ScoreRun.created_at.desc())
            .limit(50)
            .all()
        )
        return jsonify(
            {
                "history": [
                    {
                        "score": r.score,
                        "confidence": r.confidence,
                        "modelVersion": r.model_version,
                        "inputHash": r.input_hash,
                        "createdAt": r.created_at.isoformat(),
                    }
                    for r in rows
                ]
            }
        )


@app.get("/api/passports/<pid>/receipt")
def receipt(pid):
    with SessionLocal() as s:
        p, err = get_passport(s, pid)
        if err:
            return err
        activities = s.query(Activity).filter(Activity.passport_id == pid).all()
        wallets = s.query(WalletLink).filter(WalletLink.passport_id == pid).all()
        return jsonify(
            {
                "passportId": pid,
                "score": p.score,
                "confidence": p.confidence,
                "sybilRisk": p.sybil_risk,
                "tier": p.tier,
                "modelVersion": p.model_version,
                "version": p.version,
                "inputHash": p.input_hash,
                "linksHash": p.links_hash,
                "evidenceCount": len(activities),
                "chains": sorted(set(a.chain_name for a in activities)),
                "wallets": len(wallets),
                "publishedTxHash": p.published_tx_hash,
                "publishedChain": p.published_chain,
            }
        )


@app.post("/api/passports/<pid>/what-if")
def whatif(pid):
    body = request.get_json(silent=True) or {}
    action = str(body.get("action", ""))
    templates = {
        "repay_on_time": {
            "activityType": "loan_repaid",
            "details": {"onTime": True, "counterparty": "0x0000000000000000000000000000000000000001"},
        },
        "vote": {
            "activityType": "vote",
            "details": {"proposalId": 999001, "counterparty": "0x0000000000000000000000000000000000000002"},
        },
        "contribution": {
            "activityType": "contribution",
            "details": {"projectId": "0x" + "00" * 32, "counterparty": "0x0000000000000000000000000000000000000003"},
        },
    }
    with SessionLocal() as s:
        p, err = get_passport(s, pid)
        if err:
            return err
        activities = [
            serialize_activity(a)
            for a in s.query(Activity).filter(Activity.passport_id == pid).all()
        ]
        wallet_count = s.query(WalletLink).filter(WalletLink.passport_id == pid).count()
        metrics = json.loads(p.generic_metrics or "{}")
        before = score_reputation(activities, wallet_count, metrics)["score"]
        canonical_action = {"link_third_chain": "third_chain", "vote_3": "vote_3"}.get(action, action)
        if canonical_action == "third_chain":
            extras = [{
                "id": "whatif-third-chain", "passportId": pid, "chainId": 421614,
                "chainName": "Arbitrum Sepolia (simulated)", "address": p.owner_address,
                "txHash": "0x" + "00" * 32, "blockNumber": 0, "timestamp": now_ts(),
                "activityType": "meaningful_interaction", "source": "WHAT_IF",
                "contractAddress": "0x" + "00" * 20, "amount": 0, "qualityGrade": "A",
                "details": {"counterparty": "0x0000000000000000000000000000000000000004"},
            }]
            after = score_reputation(activities + extras, wallet_count, metrics)["score"]
        elif canonical_action == "vote_3":
            extras = []
            for i in range(3):
                extras.append({
                    "id": f"whatif-vote-{i}", "passportId": pid, "chainId": 11155111,
                    "chainName": "Ethereum Sepolia", "address": p.owner_address,
                    "txHash": "0x" + (f"{i+1:02x}" * 32), "blockNumber": 0,
                    "timestamp": now_ts() - i * 3600, "activityType": "vote", "source": "WHAT_IF",
                    "contractAddress": "0x" + "00" * 20, "amount": 0, "qualityGrade": "A",
                    "details": {"proposalId": 900001 + i, "counterparty": "0x0000000000000000000000000000000000000002"},
                })
            after = score_reputation(activities + extras, wallet_count, metrics)["score"]
        else:
            template = templates.get(canonical_action)
            if not template:
                return jsonify({"error": "unsupported_action"}), 400
            fake = {
                "id": "whatif", "passportId": pid, "chainId": 11155111,
                "chainName": "Ethereum Sepolia", "address": p.owner_address,
                "txHash": "0x" + "00" * 32, "blockNumber": 0, "timestamp": now_ts(),
                "activityType": template["activityType"], "source": "WHAT_IF",
                "contractAddress": "0x" + "00" * 20, "amount": 0, "qualityGrade": "A",
                "details": template["details"],
            }
            after = score_reputation(activities + [fake], wallet_count, metrics)["score"]
        return jsonify({"action": action, "currentScore": before, "projectedScore": after, "delta": after - before, "simulated": True})


@app.post("/api/ai/analyze")
def ai_analyze():
    body = request.get_json(silent=True) or {}
    features = body.get("features", {})
    return jsonify(ai_second_opinion(features))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=False)
