// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface IERC20 {
    function transfer(address recipient, uint256 amount) external returns (bool);
    function approve(address spender, uint256 amount) external returns (bool);
    function transferFrom(address sender, address recipient, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
    function allowance(address owner, address spender) external view returns (uint256);
}


contract UMAPoolOracle {
    struct Claim {
        address agent;      // Agent submitting the claim
        address user;       // User to be rewarded if claim is not disputed
        string selectedPool;
        uint256 timestamp;
        bool disputed;
        bool resolved;
        address disputer;
        uint256 bondAmount; // Bond deposited in ETH (in wei)
    }

    mapping(bytes32 => Claim) public claims;
    uint256 public disputeWindow = 5 minutes;
    uint256 public rewardAmount = 1e6;  // 1 USDC reward (USDC assumed to have 6 decimals)
    address public owner;
    address public testnetUSDC;

    // The required bond in ETH (in wei), set at deployment.
    uint256 public requiredBond;

    event ClaimSubmitted(bytes32 claimId, address agent, address user, string pool);
    event ClaimDisputed(bytes32 claimId, address disputer);
    event ClaimFinalized(bytes32 claimId, bool success, address recipient);

    constructor(address _testnetUSDC, uint256 _requiredBond) payable {
        owner = msg.sender;
        testnetUSDC = _testnetUSDC;
        requiredBond = _requiredBond; // e.g., 0.01 ether (in wei)
    }

    // Agent submits a claim by sending the required ETH bond.
    function submitClaim(string memory selectedPool, uint256 timestamp, address user) external payable {
        require(msg.value == requiredBond, "Incorrect bond amount");
        bytes32 claimId = keccak256(abi.encodePacked(msg.sender, timestamp, selectedPool, user));
        require(claims[claimId].timestamp == 0, "Claim already exists");

        claims[claimId] = Claim({
            agent: msg.sender,
            user: user,
            selectedPool: selectedPool,
            timestamp: timestamp,
            disputed: false,
            resolved: false,
            disputer: address(0),
            bondAmount: msg.value
        });
        emit ClaimSubmitted(claimId, msg.sender, user, selectedPool);
    }

    function disputeClaim(bytes32 claimId) external {
        require(claims[claimId].timestamp > 0, "Claim does not exist");
        require(block.timestamp <= claims[claimId].timestamp + disputeWindow, "Dispute window passed");
        require(!claims[claimId].disputed, "Already disputed");

        claims[claimId].disputed = true;
        claims[claimId].disputer = msg.sender;
        emit ClaimDisputed(claimId, msg.sender);
    }

    function finalizeClaim(bytes32 claimId) external {
        Claim storage claim = claims[claimId];
        require(claim.timestamp > 0, "Claim does not exist");
        require(block.timestamp > claim.timestamp + disputeWindow, "Dispute window not over");
        require(!claim.resolved, "Claim already resolved");

        claim.resolved = true;

        if (claim.disputed) {
            // If disputed: agent loses bond, disputer gets bond and reward.
            (bool sentDisputer, ) = payable(claim.disputer).call{value: claim.bondAmount}("");
            require(sentDisputer, "Disputer bond refund failed");

            require(
                IERC20(testnetUSDC).transfer(claim.disputer, rewardAmount),
                "Dispute reward transfer failed"
            );

            emit ClaimFinalized(claimId, false, claim.disputer);
        } else {
            // If not disputed: agent gets bond back, user gets reward.
            (bool sentAgent, ) = payable(claim.agent).call{value: claim.bondAmount}("");
            require(sentAgent, "Agent bond refund failed");

            require(
                IERC20(testnetUSDC).transfer(claim.user, rewardAmount),
                "User reward transfer failed"
            );

            emit ClaimFinalized(claimId, true, claim.user);
        }
    }


}
