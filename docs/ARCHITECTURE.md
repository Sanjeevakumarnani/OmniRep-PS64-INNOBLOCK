# OmniRep architecture

```text
                 ┌─────────────────────────────────────┐
                 │              React UI               │
                 │  wallet linking · score · verifier  │
                 └──────────────────┬──────────────────┘
                                    │ REST + ethers.js
                 ┌──────────────────▼──────────────────┐
                 │             Flask API                │
                 │ auth · indexer · scoring · proofs  │
                 └──────┬──────────────┬───────────────┘
                        │              │
          ┌─────────────▼───┐   ┌────▼─────────────────┐
          │ PostgreSQL/SQLite│   │ Ethereum Sepolia RPC │
          │ detailed records │   │ + Base Sepolia RPC   │
          └─────────────┬───┘   └────┬─────────────────┘
                        │              │
                        │        normalized activity
                        │              │
                        └──────┬───────┘
                               ▼
                   ┌─────────────────────┐
                   │ Reputation Engine   │
                   │ score + risk +      │
                   │ confidence + why    │
                   └──────────┬──────────┘
                              │ canonical JSON
                              ▼
                     SHA-256 proof input
                              │
                    EIP-712 attestation
                              │
              ┌───────────────▼────────────────┐
              │   OmniRepRegistry            │
              │ score · tier · risk · hash     │
              │ version · linked-count         │
              └───────────────┬────────────────┘
                              │ read-only
                    ┌─────────▼─────────┐
                    │    LendLite       │
                    │  consumer dApp    │
                    └───────────────────┘

                  Base Sepolia side path
                  ───────────────────────
                  attestor EIP-712 proof
                           │
                           ▼
                  OmniRepVerifier
                           │
                     meets(subject)
```

## Data boundary

**Off-chain:** linked addresses, signatures, normalized activity, generic metrics, scoring breakdown, Sybil features, AI explanation, proof bundle.

**On-chain:** final score, tier, Sybil risk, model/version metadata, linked count, SHA-256 proof hash, linked-wallet-set hash and timestamp.

This keeps the expensive public ledger compact while preserving a verifiable fingerprint of the detailed record.

## Trust model

1. The user wallet proves control by signing a server-issued nonce challenge.
2. The indexer derives evidence from public blockchain data.
3. The deterministic engine calculates the score.
4. Optional AI receives aggregate behavioral features only and produces a second opinion.
5. The backend signs a bounded EIP-712 attestation.
6. The passport owner publishes the attestation on-chain.
7. Consumer applications read the on-chain registry instead of trusting OmniRep's UI.
