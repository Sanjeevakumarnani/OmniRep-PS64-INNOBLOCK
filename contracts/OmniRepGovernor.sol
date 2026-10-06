// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract OmniRepGovernor {
    struct Proposal { string text; uint256 yes; uint256 no; }
    uint256 public nextId;
    mapping(uint256 => Proposal) public proposals;
    mapping(uint256 => mapping(address => bool)) public voted;
    event ProposalCreated(uint256 indexed id, address indexed creator, string text);
    event Voted(uint256 indexed id, address indexed voter, bool support);

    function createProposal(string calldata text) external returns (uint256 id) {
        id = ++nextId;
        proposals[id] = Proposal(text, 0, 0);
        emit ProposalCreated(id, msg.sender, text);
    }

    function vote(uint256 id, bool support) external {
        require(id > 0 && id <= nextId, "proposal missing");
        require(!voted[id][msg.sender], "already voted");
        voted[id][msg.sender] = true;
        if (support) proposals[id].yes++; else proposals[id].no++;
        emit Voted(id, msg.sender, support);
    }
}
