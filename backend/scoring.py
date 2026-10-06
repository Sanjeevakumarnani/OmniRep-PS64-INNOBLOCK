from __future__ import annotations
from collections import Counter
from datetime import datetime, timezone
import json, math
from typing import Any

CONFIG = {
    "model": "omnirep_scoring_v2",
    "version": 20001,
    "scale": 1000,
    "weights": {
        "repayments": 220,
        "governance": 90,
        "contributions": 90,
        "wallet_longevity": 170,
        "activity_quality": 130,
        "cross_chain": 110,
        "counterparty": 70,
        "consistency": 120,
        "penalties": -200,
    },
    "freshnessFloor": 0.60,
    "sybilMaxPenalty": 0.50,
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def clamp(v: float, lo: int = 0, hi: int = 1000) -> int:
    return max(lo, min(hi, int(round(v))))


def exp_score(x: float, k: float) -> float:
    return 1 - math.exp(-max(0.0, x) / k)


def classify_risk(r: int) -> str:
    return "high" if r >= 60 else "medium" if r >= 30 else "low"


def _metric_rows(generic_metrics: dict | None) -> list[dict]:
    rows: list[dict] = []
    for chain, addresses in (generic_metrics or {}).items():
        for address, metric in (addresses or {}).items():
            row = dict(metric or {})
            row["chain"] = chain
            row["address"] = address
            rows.append(row)
    return rows


def _chain_id_key(value: Any) -> str:
    aliases = {
        "ethereum-sepolia": "11155111",
        "base-sepolia": "84532",
    }
    return aliases.get(str(value), str(value))


def compute_risk(activities: list[dict], wallet_count: int) -> dict:
    if not activities:
        return {
            "risk": 0,
            "label": "low",
            "reasons": ["No activity available yet."],
            "features": {"burstRatio": 0, "counterpartyDiversity": 0, "repeatRatio": 0},
        }

    ts = sorted(int(a.get("timestamp", 0)) for a in activities)
    total = max(1, len(activities))

    burst_count = 0
    j = 0
    for i, t in enumerate(ts):
        while j < i and ts[j] < t - 3600:
            j += 1
        burst_count = max(burst_count, i - j + 1)
    r1 = 20 if burst_count / total > 0.60 else 0

    linked = {str(a.get("address", "")).lower() for a in activities}
    r2 = 25 if any(str(a.get("details", {}).get("counterparty", "")).lower() in linked for a in activities) else 0

    r3 = 0
    for a in activities:
        d = a.get("details", {})
        if a.get("activityType", "").startswith("loan_") and str(d.get("counterparty", "")).lower() in linked:
            r3 = 25
            break

    cps = [
        str(a.get("details", {}).get("counterparty", "")).lower()
        for a in activities
        if a.get("details", {}).get("counterparty")
    ]
    counts = Counter(cps)
    r4 = 15 if cps and max(counts.values()) / len(cps) > 0.80 else 0

    gaps = [ts[i] - ts[i - 1] for i in range(1, len(ts)) if ts[i] > ts[i - 1]]
    cadence_cv = 0.0
    if len(gaps) >= 2:
        mean = sum(gaps) / len(gaps)
        stdev = math.sqrt(sum((x - mean) ** 2 for x in gaps) / len(gaps))
        cadence_cv = stdev / max(1, mean)
    repeats = sum(
        c - 1
        for c in Counter(
            (
                a.get("activityType"),
                str(a.get("amount", 0)),
                a.get("contractAddress", ""),
            )
            for a in activities
        ).values()
        if c > 1
    )
    r5 = 15 if (cadence_cv < 0.05 and len(gaps) >= 2) or repeats / total > 0.60 else 0

    age_days = max(0, (int(datetime.now(timezone.utc).timestamp()) - ts[0]) / 86400)
    r6 = 10 if age_days < 7 and len(activities) > 20 else 0

    risk = min(100, r1 + r2 + r3 + r4 + r5 + r6)
    reasons: list[str] = []
    for label, val, text in [
        ("R1", r1, "High temporal burst"),
        ("R2", r2, "Circular flow involving linked wallets"),
        ("R3", r3, "Self-dealing loan pattern"),
        ("R4", r4, "Single-counterparty concentration"),
        ("R5", r5, "Script-like cadence or repetitive values"),
        ("R6", r6, "Fresh account with unusually high volume"),
    ]:
        if val:
            reasons.append(f"{label}: {text}")
    if not reasons:
        reasons = ["No strong deterministic farming indicators"]

    return {
        "risk": risk,
        "label": classify_risk(risk),
        "reasons": reasons,
        "rules": {"R1": r1, "R2": r2, "R3": r3, "R4": r4, "R5": r5, "R6": r6},
        "features": {
            "burstRatio": round(burst_count / total, 3),
            "counterpartyDiversity": len(counts),
            "repeatRatio": round(repeats / total, 3),
            "cadenceCv": round(cadence_cv, 3),
            "activityCount": total,
            "linkedWallets": wallet_count,
        },
    }


def _first_seen_and_tx(metrics: dict) -> tuple[int | None, int, int, float]:
    rows = _metric_rows(metrics)
    first_seen = [int(r["firstSeen"]) for r in rows if r.get("firstSeen")]
    tx_count = sum(int(r.get("txCount") or 0) for r in rows)
    success_contracts = sum(int(r.get("successfulContractInteractions") or 0) for r in rows)
    gas_eth = sum(float(r.get("gasSpentEth") or 0) for r in rows)
    return (min(first_seen) if first_seen else None, tx_count, success_contracts, gas_eth)


def _quality_grade_score(activities: list[dict]) -> float:
    if not activities:
        return 0.0
    weights = {"A": 1.0, "B": 0.8, "C": 0.55}
    return sum(weights.get(str(a.get("qualityGrade", "C")).upper(), 0.5) for a in activities) / len(activities)


def score_reputation(
    activities: list[dict],
    wallet_count: int,
    generic_metrics: dict | None = None,
    now_ts: int | None = None,
) -> dict:
    now_ts = now_ts or int(datetime.now(timezone.utc).timestamp())
    metrics = generic_metrics or {}

    if not activities and not _metric_rows(metrics):
        breakdown = {
            "repayments": {"points": 0, "max": 220, "reason": "No recognized loan repayment outcomes"},
            "governance": {"points": 0, "max": 90, "reason": "No governance votes"},
            "contributions": {"points": 0, "max": 90, "reason": "No contribution signals"},
            "wallet_longevity": {"points": 0, "max": 170, "reason": "Insufficient observed history"},
            "activity_quality": {"points": 0, "max": 130, "reason": "No indexed activity yet"},
            "cross_chain": {"points": 0, "max": 110, "reason": "No chain activity yet"},
            "counterparty": {"points": 0, "max": 70, "reason": "No counterparty evidence"},
            "consistency": {"points": 0, "max": 120, "reason": "Insufficient activity cadence"},
            "penalties": {"points": 0, "max": -200, "reason": "No negative outcomes"},
        }
        return {
            "score": 0,
            "baseScore": 0,
            "sybilRisk": 0,
            "freshnessMultiplier": 1,
            "breakdown": breakdown,
            "confidence": 0,
            "risk": compute_risk([], wallet_count),
            "features": {},
            "config": CONFIG,
        }

    rep = [a for a in activities if a.get("activityType") == "loan_repaid" and a.get("details", {}).get("onTime", True)]
    late = [a for a in activities if a.get("activityType") == "loan_repaid" and not a.get("details", {}).get("onTime", True)]
    defaults = [a for a in activities if a.get("activityType") == "loan_defaulted"]
    votes = len({a.get("details", {}).get("proposalId", a.get("txHash")) for a in activities if a.get("activityType") == "vote"})
    contributions = sum(1 for a in activities if a.get("activityType") == "contribution")
    chains = {_chain_id_key(a.get("chainId")) for a in activities if a.get("chainId")}
    chains.update(_chain_id_key(r.get("chain")) for r in _metric_rows(metrics) if int(r.get("txCount") or 0) > 0)
    active_weeks = len({int(a.get("timestamp", 0)) // 604800 for a in activities})
    cp = {
        str(a.get("details", {}).get("counterparty", "")).lower()
        for a in activities
        if a.get("details", {}).get("counterparty")
    }
    for row in _metric_rows(metrics):
        cp.update(str(x).lower() for x in (row.get("counterparties") or []) if x)

    first_seen, tx_count, successful_contracts, gas_eth = _first_seen_and_tx(metrics)
    oldest_activity = min([int(a.get("timestamp", now_ts)) for a in activities], default=first_seen or now_ts)
    if first_seen is None:
        first_seen = oldest_activity
    age_days = max(0, (now_ts - first_seen) / 86400)
    observed_days = max(0, (now_ts - oldest_activity) / 86400)

    repayment_points = 220 * exp_score(len(rep) + 0.5 * len(late), 4)
    governance_points = 90 * exp_score(votes, 6)
    contribution_points = 90 * exp_score(contributions, 5)
    longevity_points = 110 * min(1, age_days / 180) + 60 * min(1, active_weeks / 12)
    quality = _quality_grade_score(activities)
    tx_signal = min(1, math.log1p(tx_count) / math.log1p(120)) if tx_count else 0
    contract_signal = min(1, successful_contracts / 35) if successful_contracts else 0
    activity_points = 130 * (0.55 * quality + 0.25 * tx_signal + 0.20 * contract_signal)
    cross_chain_points = {0: 0, 1: 45, 2: 85}.get(len(chains), 110)
    counterparty_points = 70 * exp_score(len(cp), 10)

    if len(activities) >= 2:
        days = sorted({int(a.get("timestamp", 0)) // 86400 for a in activities})
        span_days = max(1, days[-1] - days[0] + 1)
        active_day_ratio = min(1.0, len(days) / max(1, span_days))
    else:
        active_day_ratio = 0.0
    consistency_points = 120 * (0.55 * min(1, active_weeks / 10) + 0.45 * active_day_ratio)

    penalty = -min(200, 70 * len(defaults))
    breakdown = {
        "repayments": {
            "points": round(repayment_points),
            "max": 220,
            "reason": f"{len(rep)} on-time + {len(late)} late repayment outcomes",
        },
        "governance": {
            "points": round(governance_points),
            "max": 90,
            "reason": f"{votes} distinct governance proposals",
        },
        "contributions": {
            "points": round(contribution_points),
            "max": 90,
            "reason": f"{contributions} contribution signals",
        },
        "wallet_longevity": {
            "points": round(longevity_points),
            "max": 170,
            "reason": f"Wallet observed for {age_days:.0f} days with {active_weeks} active weeks",
        },
        "activity_quality": {
            "points": round(activity_points),
            "max": 130,
            "reason": f"{tx_count} tx indexed, {successful_contracts} successful contract interactions" + (f", {gas_eth:.4f} ETH gas" if gas_eth else ""),
        },
        "cross_chain": {
            "points": round(cross_chain_points),
            "max": 110,
            "reason": f"Activity observed on {len(chains)} chain(s)",
        },
        "counterparty": {
            "points": round(counterparty_points),
            "max": 70,
            "reason": f"{len(cp)} distinct interaction counterparties",
        },
        "consistency": {
            "points": round(consistency_points),
            "max": 120,
            "reason": f"{len({int(a.get('timestamp', 0)) // 86400 for a in activities})} active day(s) across {active_weeks} week(s)",
        },
        "penalties": {
            "points": round(penalty),
            "max": -200,
            "reason": f"{len(defaults)} default outcome(s)" if defaults else "No default outcome",
        },
    }

    base = max(0, sum(v["points"] for v in breakdown.values()))
    risk = compute_risk(activities, wallet_count)
    sybil_multiplier = max(CONFIG["sybilMaxPenalty"], 1 - risk["risk"] / 200)
    latest = max([int(a.get("timestamp", 0)) for a in activities], default=first_seen or now_ts)
    idle_days = max(0, (now_ts - latest) / 86400)
    freshness = max(CONFIG["freshnessFloor"], 0.5 ** (idle_days / 120))
    final = clamp(base * sybil_multiplier * freshness)

    rows = _metric_rows(metrics)
    metric_quality = sum(1 for row in rows if row.get("ok")) / max(1, len(rows))
    evidence_quality = _quality_grade_score(activities)
    confidence = min(
        100,
        round(
            100
            * (
                0.30 * min(1, len(activities) / 12)
                + 0.25 * min(1, len(chains) / 2)
                + 0.20 * evidence_quality
                + 0.15 * metric_quality
                + 0.10 * min(1, wallet_count / 2)
            )
        ),
    )

    features = {
        "ageDays": round(age_days, 2),
        "observedDays": round(observed_days, 2),
        "activeWeeks": active_weeks,
        "activeDayRatio": round(active_day_ratio, 3),
        "chains": len(chains),
        "counterpartyDiversity": len(cp),
        "repayments": len(rep),
        "lateRepayments": len(late),
        "defaults": len(defaults),
        "votes": votes,
        "contributions": contributions,
        "indexedTxCount": tx_count,
        "successfulContractInteractions": successful_contracts,
        "gasSpentEth": round(gas_eth, 6),
        "evidenceQuality": round(evidence_quality, 3),
    }
    return {
        "score": final,
        "baseScore": round(base),
        "sybilRisk": risk["risk"],
        "freshnessMultiplier": round(freshness, 3),
        "breakdown": breakdown,
        "confidence": confidence,
        "risk": risk,
        "features": features,
        "config": CONFIG,
    }
