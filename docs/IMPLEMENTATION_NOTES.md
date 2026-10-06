# OmniRep Implementation Notes

## Source of truth
The uploaded OmniRep PRD plus official PS64 problem statement are the implementation source of truth.

## Critical implementation decisions

1. Passport IDs are numeric on-chain IDs.
2. Wallet linking is off-chain proof of control using personal_sign challenges with nonce + expiry.
3. Reputation publication uses EIP-712 signed attestations. The passport owner submits; only the attestor key can authorize a score.
4. The Sepolia registry stores score, tier, risk, hashes, version metadata and linked count; it does not store the linked addresses.
5. Base Sepolia has a portable verifier using a shared fixed signing domain (`OmniRep Passport`, version 1, salt `OmniRep.Portable.Attestation.v1`) and a portable subject-scoped attestation. No bridge is involved.
6. LoanPool, Governor and ContributionLog are testnet-only semantic source contracts so the demo can generate real events without transferring real funds.
7. Deterministic scoring and Sybil rules remain useful without an AI API key.
8. The frontend never receives or handles the attestor private key.

## Current constraints

- Public testnet RPCs and explorer APIs can rate-limit. The indexer therefore has an RPC path plus optional Etherscan V2 enrichment.
- Contract verification must be performed after deployment with the same compiler settings.
- The project must use fresh burner wallets only and testnets only, as required by the handbook.
