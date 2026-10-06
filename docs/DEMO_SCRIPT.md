# OmniRep 3-minute demo

### 0:00 — Problem

“Your Web3 history is split across wallets and chains. A new application should not make a user start from zero.”

### 0:20 — Link two wallets

Create the passport on Ethereum Sepolia.

Open **Link wallets**.

Connect burner wallet A on Ethereum Sepolia and sign.

Switch to burner wallet B on Base Sepolia and sign.

Point out: no transaction and no asset transfer — only proof of wallet control.

### 0:50 — Create evidence

On Ethereum, run the loan lifecycle or a governance/contribution event.

On Base, run another semantic event.

Refresh evidence.

Show the normalized cross-chain activity count and recent evidence links.

### 1:20 — Explain the score

Open **Overview**.

Highlight three concrete factors:

- repayments / outcomes
- wallet longevity + consistency
- cross-chain breadth

Then open **Sybil Radar** to show why the risk is low or what triggered a review.

### 1:50 — Publish proof

Open **Publish**.

Sign the EIP-712 attestation from the backend attestor, then publish it with the passport owner wallet.

Point at the transaction on the Sepolia explorer.

### 2:20 — Verify / tamper

Open **Verifier**.

Show the SHA-256 hash match.

Press **Change one character**.

Show `MISMATCH`.

Restore the bundle and show the match again.

### 2:40 — Consumer dApp

Open **LendLite Gate**.

Explain that the consumer is reading the published registry signal.

Change the threshold slider to demonstrate blocked vs granted access.

Optionally carry the attestation to Base and show the portable verifier.

### 2:55 — Close

“OmniRep turns fragmented activity into a portable reputation primitive — explainable before publication, verifiable after publication, and usable by another app.”
