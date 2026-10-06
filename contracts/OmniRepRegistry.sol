// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {ECDSA} from "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";

/// @title OmniRep Registry
/// @notice Cross-chain reputation anchor. Linked wallet addresses are never published.
contract OmniRepRegistry is Ownable {
    using ECDSA for bytes32;

    string private constant NAME = "OmniRep Passport";
    string private constant VERSION = "1";
    bytes32 private constant SALT = keccak256("OmniRep.Portable.Attestation.v1");
    bytes32 private constant DOMAIN_TYPEHASH = keccak256("EIP712Domain(string name,string version,bytes32 salt)");
    bytes32 private constant ATTESTATION_TYPEHASH = keccak256(
        "Attestation(uint256 id,uint16 score,uint8 sybilRisk,uint16 algoVersion,uint8 linkedCount,bytes32 inputHash,bytes32 linksHash,uint32 version,uint64 deadline)"
    );
    bytes32 private immutable DOMAIN_SEPARATOR;

    struct Passport {
        address owner;
        uint16 score;
        uint8 tier;
        uint8 sybilRisk;
        uint16 algoVersion;
        uint32 version;
        uint64 updatedAt;
        uint8 linkedCount;
        bytes32 inputHash;
        bytes32 linksHash;
    }

    struct Attestation {
        uint256 id;
        uint16 score;
        uint8 sybilRisk;
        uint16 algoVersion;
        uint8 linkedCount;
        bytes32 inputHash;
        bytes32 linksHash;
        uint32 version;
        uint64 deadline;
    }

    uint256 public count;
    address public attestor;
    mapping(uint256 => Passport) private passports;
    /// @notice Primary wallet -> passport ID. Secondary linked addresses stay off-chain.
    mapping(address => uint256) public passportOf;

    event PassportCreated(uint256 indexed id, address indexed owner);
    event AttestorUpdated(address indexed attestor);
    event ScorePublished(uint256 indexed id, uint32 indexed version, uint16 score, uint8 tier, uint8 sybilRisk, bytes32 inputHash, bytes32 linksHash);

    constructor(address initialOwner, address initialAttestor) Ownable(initialOwner) {
        require(initialAttestor != address(0), "attestor required");
        attestor = initialAttestor;
        DOMAIN_SEPARATOR = keccak256(abi.encode(DOMAIN_TYPEHASH, keccak256(bytes(NAME)), keccak256(bytes(VERSION)), SALT));
    }

    function createPassport() external returns (uint256 id) {
        require(passportOf[msg.sender] == 0, "already has passport");
        id = ++count;
        passports[id].owner = msg.sender;
        passportOf[msg.sender] = id;
        emit PassportCreated(id, msg.sender);
    }

    function setAttestor(address next) external onlyOwner {
        require(next != address(0), "attestor required");
        attestor = next;
        emit AttestorUpdated(next);
    }

    function publish(Attestation calldata a, bytes calldata sig) external {
        Passport storage p = passports[a.id];
        require(p.owner == msg.sender, "not passport owner");
        require(block.timestamp <= a.deadline, "attestation expired");
        require(a.version == p.version + 1, "bad version");
        require(a.score <= 1000, "score > 1000");
        require(a.sybilRisk <= 100, "risk > 100");
        require(a.linkedCount > 0, "no linked wallets");
        require(a.inputHash != bytes32(0), "input hash required");
        require(a.linksHash != bytes32(0), "links hash required");
        require(_recover(a, sig) == attestor, "bad attestor signature");

        p.score = a.score;
        p.tier = tierFor(a.score);
        p.sybilRisk = a.sybilRisk;
        p.algoVersion = a.algoVersion;
        p.version = a.version;
        p.updatedAt = uint64(block.timestamp);
        p.linkedCount = a.linkedCount;
        p.inputHash = a.inputHash;
        p.linksHash = a.linksHash;
        emit ScorePublished(a.id, a.version, a.score, p.tier, a.sybilRisk, a.inputHash, a.linksHash);
    }

    function _recover(Attestation calldata a, bytes calldata sig) internal view returns (address) {
        bytes32 structHash = keccak256(abi.encode(
            ATTESTATION_TYPEHASH, a.id, a.score, a.sybilRisk, a.algoVersion, a.linkedCount,
            a.inputHash, a.linksHash, a.version, a.deadline
        ));
        bytes32 digest = keccak256(abi.encodePacked("\x19\x01", DOMAIN_SEPARATOR, structHash));
        return digest.recover(sig);
    }

    function tierFor(uint16 s) public pure returns (uint8) {
        if (s >= 800) return 4;
        if (s >= 600) return 3;
        if (s >= 400) return 2;
        if (s >= 200) return 1;
        return 0;
    }

    function scoreOf(uint256 id) external view returns (uint16) { return passports[id].score; }
    function tierOf(uint256 id) external view returns (uint8) { return passports[id].tier; }
    function ownerOfPassport(uint256 id) external view returns (address) { return passports[id].owner; }
    function getPassport(uint256 id) external view returns (Passport memory) { return passports[id]; }

    function meets(uint256 id, uint16 minScore, uint64 maxAge) external view returns (bool) {
        Passport storage p = passports[id];
        if (p.version == 0 || p.score < minScore) return false;
        if (maxAge != 0 && block.timestamp - p.updatedAt > maxAge) return false;
        return true;
    }

    function verifyInputs(uint256 id, bytes32 h) external view returns (bool) {
        return passports[id].inputHash == h;
    }

    /// @notice Hash arbitrary proof bytes with the EVM SHA-256 precompile and compare with the stored input hash.
    function verifyInputBytes(uint256 id, bytes calldata raw) external view returns (bool) {
        return passports[id].inputHash == sha256(raw);
    }
}
