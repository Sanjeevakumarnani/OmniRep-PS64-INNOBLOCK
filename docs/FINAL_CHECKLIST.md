# OmniRep — Final Hackathon Checklist

## PS64 mandatory

- [ ] Create passport on Ethereum Sepolia.
- [ ] Link a wallet on Ethereum Sepolia by signature.
- [ ] Link a second wallet on Base Sepolia by signature.
- [ ] Refresh and normalize activity from both testnets.
- [ ] Generate transparent 0–1000 score with factor explanations.
- [ ] Publish score + SHA-256 input hash to the Ethereum Sepolia registry.
- [ ] Show an independent consumer dApp reading the contract.

## Strong differentiators

- [ ] Sybil Radar with deterministic reasons.
- [ ] AI second opinion shown as advisory only.
- [ ] Iron / Bronze / Silver / Gold / Diamond tiers.
- [ ] What-if Coach.
- [ ] Score history / trajectory.
- [ ] Proof of Why evidence timeline.
- [ ] Tamper Lab: mutate input -> SHA-256 mismatch.
- [ ] Shareable `?passport=<id>` verification link.
- [ ] Portable EIP-712 attestation accepted by Base Sepolia verifier.

## Deployment

- [ ] Deploy `OmniRepRegistry` to Ethereum Sepolia.
- [ ] Deploy `OmniRepVerifier` to Base Sepolia.
- [ ] Deploy LoanPool / Governor / ContributionLog on both chains.
- [ ] Deploy LendLite + Badge on Ethereum Sepolia.
- [ ] Verify contracts on the matching explorer.
- [ ] Configure backend `ATTESTOR_PRIVATE_KEY` with the same authorized attestor used by deployment.
- [ ] Configure Neon/Supabase PostgreSQL.
- [ ] Configure Render backend secrets.
- [ ] Configure Vercel frontend `VITE_*` addresses/API base.

## Demo sequence

1. Create passport.
2. Sign Ethereum wallet.
3. Sign Base wallet.
4. Create one real semantic signal on each chain.
5. Refresh evidence and score.
6. Open Score Breakdown / Proof of Why.
7. Open Sybil Radar.
8. Publish proof to Ethereum Sepolia.
9. Open Verifier and toggle tamper.
10. Carry portable proof to Base Sepolia.
11. Open LendLite and demonstrate contract-based access.
12. Open Share Passport link.

## Security checks

- No private keys in frontend.
- No API secrets in frontend.
- Testnet/burner wallets only.
- No personal data committed on-chain.
- Publication transaction independently checked by backend when registry is configured.
