// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface IPassportGate {
    function meets(uint256 passportId, uint16 minScore, uint64 maxAge) external view returns (bool);
}
