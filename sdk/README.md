# OmniRep PassportGate SDK

```solidity
interface IPassportGate {
    function meets(uint256 passportId, uint16 minScore, uint64 maxAge) external view returns (bool);
}
```

A consumer can gate a feature with one read from OmniRepRegistry.
