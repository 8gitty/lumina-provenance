// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Verification {
    struct DataInfo {
        string ipfsCID;
        uint256 timestamp;
    }

    // Mapping from a SHA-256 hash (bytes32) to DataInfo
    mapping(bytes32 => DataInfo) public verifications;

    event DataVerified(bytes32 indexed dataHash, string ipfsCID, uint256 timestamp);

    function storeVerification(bytes32 dataHash, string memory ipfsCID) public {
        require(bytes(verifications[dataHash].ipfsCID).length == 0, "Hash already verified");
        
        verifications[dataHash] = DataInfo({
            ipfsCID: ipfsCID,
            timestamp: block.timestamp
        });

        emit DataVerified(dataHash, ipfsCID, block.timestamp);
    }

    function getVerification(bytes32 dataHash) public view returns (string memory, uint256) {
        DataInfo memory info = verifications[dataHash];
        return (info.ipfsCID, info.timestamp);
    }
}
