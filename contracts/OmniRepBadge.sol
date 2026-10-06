// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import {Base64} from "@openzeppelin/contracts/utils/Base64.sol";
import {Strings} from "@openzeppelin/contracts/utils/Strings.sol";

interface IRegistryTier {
    function passportOf(address) external view returns (uint256);
    function tierOf(uint256) external view returns (uint8);
}

contract OmniRepBadge is ERC721 {
    using Strings for uint256;
    IRegistryTier public immutable registry;
    uint256 public nextTokenId;
    mapping(uint256 => uint8) public tokenTier;

    event BadgeClaimed(address indexed owner, uint256 indexed tokenId, uint8 tier);

    constructor(address registryAddress) ERC721("OmniRep Reputation Badge", "OMNI") { registry = IRegistryTier(registryAddress); }

    function claim() external returns (uint256 tokenId) {
        uint256 pid = registry.passportOf(msg.sender);
        require(pid != 0, "no passport");
        uint8 tier = registry.tierOf(pid);
        require(tier >= 1, "bronze required");
        tokenId = ++nextTokenId;
        tokenTier[tokenId] = tier;
        _safeMint(msg.sender, tokenId);
        emit BadgeClaimed(msg.sender, tokenId, tier);
    }

    function _update(address to, uint256 tokenId, address auth) internal override returns (address) {
        address from = _ownerOf(tokenId);
        if (from != address(0) && to != address(0)) revert("soulbound");
        return super._update(to, tokenId, auth);
    }

    function tokenURI(uint256 tokenId) public view override returns (string memory) {
        _requireOwned(tokenId);
        string memory json = string.concat(
            '{"name":"OmniRep Reputation Badge #', tokenId.toString(), '","description":"Non-transferable OmniRep reputation tier badge. Tier ', uint256(tokenTier[tokenId]).toString(), '","image":"data:text/plain;base64,',
            Base64.encode(bytes("OMNIREP BADGE")), '"}'
        );
        return string.concat("data:application/json;base64,", Base64.encode(bytes(json)));
    }
}
