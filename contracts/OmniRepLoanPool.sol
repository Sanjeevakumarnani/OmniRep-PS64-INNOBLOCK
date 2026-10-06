// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract OmniRepLoanPool {
    struct Loan { address borrower; uint256 amount; uint64 dueAt; bool repaid; }
    uint256 public nextId;
    mapping(uint256 => Loan) public loans;
    event Borrowed(uint256 indexed loanId, address indexed borrower, uint256 amount, uint64 dueAt);
    event Repaid(uint256 indexed loanId, address indexed borrower, bool onTime);
    event Defaulted(uint256 indexed loanId, address indexed borrower);

    function borrow(uint256 amount, uint64 duration) external returns (uint256 id) {
        id = ++nextId;
        uint64 dueAt = uint64(block.timestamp) + duration;
        loans[id] = Loan(msg.sender, amount, dueAt, false);
        emit Borrowed(id, msg.sender, amount, dueAt);
    }

    /// @notice Demo-only helper: creates a loan and repays it in the same transaction.
    /// This emits real Borrowed + Repaid events without moving funds.
    function borrowAndRepay(uint256 amount) external returns (uint256 id) {
        id = ++nextId;
        uint64 dueAt = uint64(block.timestamp);
        loans[id] = Loan(msg.sender, amount, dueAt, true);
        emit Borrowed(id, msg.sender, amount, dueAt);
        emit Repaid(id, msg.sender, true);
    }

    /// @notice Demo-only helper: creates an already-due loan and records a default in the same transaction.
    /// This emits real Borrowed + Defaulted events without moving funds.
    function borrowAndDefault(uint256 amount) external returns (uint256 id) {
        id = ++nextId;
        uint64 dueAt = uint64(block.timestamp - 1);
        loans[id] = Loan(msg.sender, amount, dueAt, false);
        emit Borrowed(id, msg.sender, amount, dueAt);
        emit Defaulted(id, msg.sender);
    }

    function repay(uint256 id) external {
        Loan storage l = loans[id];
        require(l.borrower == msg.sender, "not borrower");
        require(!l.repaid, "already repaid");
        l.repaid = true;
        emit Repaid(id, msg.sender, block.timestamp <= l.dueAt);
    }

    function markDefaulted(uint256 id) external {
        Loan storage l = loans[id];
        require(l.borrower != address(0), "loan missing");
        require(!l.repaid && block.timestamp > l.dueAt, "not defaulted");
        emit Defaulted(id, l.borrower);
    }
}
