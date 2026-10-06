// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {ECDSA} from "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";

/// @title OmniRep Portable Verifier
/// @notice Accepts a OmniRep wallet-scoped attestation on another testnet, no bridge required.
contract OmniRepVerifier {
    using ECDSA for bytes32;

    string private constant NAME = "OmniRep Passport";
    string private constant VERSION = "1";
    bytes32 private constant SALT = keccak256("OmniRep.Portable.Attestation.v1");
    bytes32 private constant DOMAIN_TYPEHASH = keccak256("EIP712Domain(string name,string version,bytes32 salt)");
    bytes32 private constant TYPEHASH = keccak256(
        "PortableAttestation(address subject,uint256 id,uint16 score,uint8 sybilRisk,uint32 version,uint64 deadline,bytes32 proofHash)"
    );
    bytes32 private immutable DOMAIN_SEPARATOR;

    address public immutable attestor;

    struct PortableAttestation {
        address subject;
        uint256 id;
        uint16 score;
        uint8 sybilRisk;
        uint32 version;
        uint64 deadline;
        bytes32 proofHash;
    }
    struct Accepted { uint256 id; uint16 score; uint8 sybilRisk; uint32 version; uint64 acceptedAt; bytes32 proofHash; }
    mapping(address => Accepted) public accepted;

    event AttestationAccepted(address indexed subject, uint256 indexed id, uint16 score, uint8 sybilRisk, uint32 version, bytes32 proofHash);

    constructor(address _attestor) { require(_attestor != address(0), "attestor required"); attestor=_attestor; DOMAIN_SEPARATOR=keccak256(abi.encode(DOMAIN_TYPEHASH,keccak256(bytes(NAME)),keccak256(bytes(VERSION)),SALT)); }

    function accept(PortableAttestation calldata a, bytes calldata sig) external {
        require(block.timestamp <= a.deadline, "attestation expired");
        require(a.subject == msg.sender, "subject must submit");
        require(a.version > accepted[msg.sender].version, "old attestation");
        require(_recover(a,sig)==attestor, "bad attestor signature");
        accepted[msg.sender]=Accepted(a.id,a.score,a.sybilRisk,a.version,uint64(block.timestamp),a.proofHash);
        emit AttestationAccepted(a.subject,a.id,a.score,a.sybilRisk,a.version,a.proofHash);
    }

    function meets(address subject,uint16 minScore,uint64 maxAge) external view returns(bool){
        Accepted memory a=accepted[subject];
        if(a.version==0 || a.score<minScore) return false;
        if(maxAge!=0 && block.timestamp-a.acceptedAt>maxAge) return false;
        return true;
    }

    function _recover(PortableAttestation calldata a, bytes calldata sig) internal view returns(address){
        bytes32 structHash=keccak256(abi.encode(TYPEHASH,a.subject,a.id,a.score,a.sybilRisk,a.version,a.deadline,a.proofHash));
        return keccak256(abi.encodePacked("\x19\x01",DOMAIN_SEPARATOR,structHash)).recover(sig);
    }
}
