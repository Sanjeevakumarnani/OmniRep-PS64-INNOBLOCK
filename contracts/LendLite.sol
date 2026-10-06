// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

interface IOmniRepRegistry {
    function passportOf(address owner) external view returns (uint256);
    function meets(uint256 id, uint16 minScore, uint64 maxAge) external view returns (bool);
    function tierOf(uint256 id) external view returns (uint8);
}

/// @title LendLite
/// @notice Demo consumer app. It records credit lines, never transfers real funds.
contract LendLite {
    IOmniRepRegistry public immutable registry;
    mapping(address => uint256) public creditLine;

    event BorrowApproved(address indexed borrower, uint256 passportId, uint256 amount, uint8 tier, uint256 collateralBps);

    constructor(address registryAddress) { registry = IOmniRepRegistry(registryAddress); }

    function borrow(uint256 amount) external {
        uint256 id = registry.passportOf(msg.sender);
        require(id != 0, "no OmniRep passport");
        require(registry.meets(id, 400, 30 days), "OmniRep Silver + fresh proof required");
        uint8 tier = registry.tierOf(id);
        uint256 collateral = tier == 4 ? 10000 : tier == 3 ? 12000 : tier == 2 ? 15000 : 20000;
        creditLine[msg.sender] += amount;
        emit BorrowApproved(msg.sender, id, amount, tier, collateral);
    }
}
