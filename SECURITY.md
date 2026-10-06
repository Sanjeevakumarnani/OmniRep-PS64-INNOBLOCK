# OmniRep Security Rules

- Public testnets and fresh burner wallets only for the hackathon.
- Never commit `.env`, private keys, API keys or database credentials.
- Never put personal data on-chain.
- Wallet linking uses nonce + expiry challenge signatures.
- Reputation publication uses a bounded EIP-712 attestation signed by the backend attestor and submitted by the passport owner.
- Deterministic scoring is the source of truth; the optional AI layer is a bounded second opinion.
- OmniRep reputation is not KYC and does not prove real-world identity.
