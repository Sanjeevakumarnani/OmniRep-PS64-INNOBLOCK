// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract OmniRepContributionLog {
    event Contributed(address indexed contributor, bytes32 indexed projectId, uint256 units, uint256 timestamp);
    function contribute(bytes32 projectId, uint256 units) external {
        require(projectId != bytes32(0), "project required");
        emit Contributed(msg.sender, projectId, units, block.timestamp);
    }
}
