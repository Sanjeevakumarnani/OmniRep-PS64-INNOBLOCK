from __future__ import annotations
import requests
from datetime import datetime, timezone
from web3 import Web3
from config import CHAINS, ETHERSCAN_API_KEY

EVENT_ABIS = {
    "LoanPool": [
        {"anonymous": False, "inputs": [{"indexed": True, "internalType": "uint256", "name": "loanId", "type": "uint256"}, {"indexed": True, "internalType": "address", "name": "borrower", "type": "address"}, {"indexed": False, "internalType": "uint256", "name": "amount", "type": "uint256"}, {"indexed": False, "internalType": "uint64", "name": "dueAt", "type": "uint64"}], "name": "Borrowed", "type": "event"},
        {"anonymous": False, "inputs": [{"indexed": True, "internalType": "uint256", "name": "loanId", "type": "uint256"}, {"indexed": True, "internalType": "address", "name": "borrower", "type": "address"}, {"indexed": False, "internalType": "bool", "name": "onTime", "type": "bool"}], "name": "Repaid", "type": "event"},
        {"anonymous": False, "inputs": [{"indexed": True, "internalType": "uint256", "name": "loanId", "type": "uint256"}, {"indexed": True, "internalType": "address", "name": "borrower", "type": "address"}], "name": "Defaulted", "type": "event"},
    ],
    "Governor": [
        {"anonymous": False, "inputs": [{"indexed": True, "internalType": "uint256", "name": "id", "type": "uint256"}, {"indexed": True, "internalType": "address", "name": "voter", "type": "address"}, {"indexed": False, "internalType": "bool", "name": "support", "type": "bool"}], "name": "Voted", "type": "event"},
    ],
    "ContributionLog": [
        {"anonymous": False, "inputs": [{"indexed": True, "internalType": "address", "name": "contributor", "type": "address"}, {"indexed": True, "internalType": "bytes32", "name": "projectId", "type": "bytes32"}, {"indexed": False, "internalType": "uint256", "name": "units", "type": "uint256"}, {"indexed": False, "internalType": "uint256", "name": "timestamp", "type": "uint256"}], "name": "Contributed", "type": "event"},
    ],
}


def w3_for(key):
    return Web3(Web3.HTTPProvider(CHAINS[key].rpc_url, request_kwargs={"timeout": 20}))


def event_signature(item):
    return f'{item["name"]}({",".join(x["type"] for x in item["inputs"])})'


def actor_field(contract_name, event_name):
    if contract_name == "LoanPool":
        return "borrower"
    if contract_name == "Governor":
        return "voter"
    return "contributor"


def fetch_generic_metrics(key, address):
    cfg = CHAINS[key]
    w3 = w3_for(key)
    result = {
        "source": "rpc",
        "fetchedAt": int(datetime.now(timezone.utc).timestamp()),
        "ok": False,
        "txCount": 0,
        "firstSeen": None,
        "counterparties": [],
        "successfulContractInteractions": 0,
        "gasSpentEth": 0.0,
    }
    if not w3.is_connected():
        return result | {"error": "rpc_unavailable"}

    result["ok"] = True
    checksum = Web3.to_checksum_address(address)
    try:
        result["txCount"] = int(w3.eth.get_transaction_count(checksum, "latest"))
    except Exception:
        pass

    if ETHERSCAN_API_KEY:
        try:
            params = {
                "chainid": cfg.explorer_chain_id,
                "module": "account",
                "action": "txlist",
                "address": address,
                "startblock": 0,
                "endblock": 99999999,
                "page": 1,
                "offset": 1000,
                "sort": "asc",
                "apikey": ETHERSCAN_API_KEY,
            }
            data = requests.get(cfg.explorer_api, params=params, timeout=20).json()
            txs = data.get("result", []) if isinstance(data.get("result"), list) else []
            if txs:
                result["source"] = "etherscan-v2"
                result["firstSeen"] = int(txs[0].get("timeStamp", 0) or 0) or None
                result["txCount"] = max(result["txCount"], len(txs))
                cps = set()
                gas_wei = 0
                contract_success = 0
                for tx in txs:
                    tx_from = str(tx.get("from", "")).lower()
                    tx_to = str(tx.get("to", "")).lower()
                    if tx_to and tx_to != address.lower():
                        cps.add(tx_to)
                    if tx_from and tx_from != address.lower():
                        cps.add(tx_from)
                    try:
                        gas_used = int(tx.get("gasUsed", 0) or 0)
                        gas_price = int(tx.get("gasPrice", 0) or 0)
                        gas_wei += gas_used * gas_price
                    except Exception:
                        pass
                    if tx_to and tx.get("isError", "0") == "0" and tx.get("txreceipt_status", "1") != "0":
                        contract_success += 1
                result["counterparties"] = sorted(cps)[:200]
                result["gasSpentEth"] = float(Web3.from_wei(gas_wei, "ether"))
                result["successfulContractInteractions"] = contract_success
        except Exception as exc:
            result["warning"] = str(exc)
    return result


def decode_and_collect(key, addresses):
    cfg = CHAINS[key]
    w3 = w3_for(key)
    if not w3.is_connected():
        raise RuntimeError(f"RPC unavailable for {cfg.name}")

    latest = w3.eth.block_number
    start = max(0, latest - int(__import__("os").getenv("INDEXER_BLOCK_WINDOW", "20000")))
    wanted = {a.lower() for a in addresses}
    out = []

    contract_specs = [
        (cfg.loan_pool, "LoanPool"),
        (cfg.governor, "Governor"),
        (cfg.contribution_log, "ContributionLog"),
    ]
    for contract_addr, contract_name in contract_specs:
        if not contract_addr:
            continue
        try:
            contract = w3.eth.contract(address=Web3.to_checksum_address(contract_addr), abi=EVENT_ABIS[contract_name])
        except Exception:
            continue
        for item in EVENT_ABIS[contract_name]:
            if item.get("type") != "event":
                continue
            name = item["name"]
            event_obj = getattr(contract.events, name)()
            topic0 = w3.keccak(text=event_signature(item)).hex()
            try:
                logs = w3.eth.get_logs({
                    "address": Web3.to_checksum_address(contract_addr),
                    "fromBlock": start,
                    "toBlock": latest,
                    "topics": [topic0],
                })
            except Exception:
                continue
            actor_key = actor_field(contract_name, name)
            for log in logs:
                try:
                    dec = event_obj.process_log(log)
                    args = dec["args"]
                    actor = Web3.to_checksum_address(args[actor_key])
                except Exception:
                    continue
                if actor.lower() not in wanted:
                    continue
                block = int(log["blockNumber"])
                txh = log["transactionHash"].hex()
                try:
                    block_data = w3.eth.get_block(block)
                    ts = int(block_data["timestamp"])
                except Exception:
                    ts = 0

                details = {
                    "counterparty": contract_addr.lower(),
                    "chainKey": key,
                }
                typ = "meaningful_interaction"
                amount = 0
                if contract_name == "LoanPool" and name == "Repaid":
                    typ = "loan_repaid"
                    details.update({"loanId": int(args["loanId"]), "onTime": bool(args["onTime"])})
                elif contract_name == "LoanPool" and name == "Defaulted":
                    typ = "loan_defaulted"
                    details.update({"loanId": int(args["loanId"])})
                elif contract_name == "LoanPool" and name == "Borrowed":
                    typ = "loan_borrowed"
                    amount = float(args["amount"])
                    details.update({"loanId": int(args["loanId"]), "dueAt": int(args["dueAt"])})
                elif contract_name == "Governor":
                    typ = "vote"
                    details.update({"proposalId": int(args["id"]), "support": bool(args["support"])})
                elif contract_name == "ContributionLog":
                    typ = "contribution"
                    amount = float(args["units"])
                    details.update({"projectId": args["projectId"].hex()})

                out.append({
                    "chainId": cfg.chain_id,
                    "chainName": cfg.name,
                    "activityType": typ,
                    "actor": actor,
                    "txHash": txh,
                    "blockNumber": block,
                    "timestamp": ts,
                    "amount": amount,
                    "contractAddress": contract_addr,
                    "source": f"{contract_name.upper()}_EVENT",
                    "qualityGrade": "A",
                    "details": details,
                })
    return out
