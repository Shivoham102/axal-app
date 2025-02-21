require('dotenv').config();
const { ethers } = require("hardhat");

async function main() {
    // Get deployer signer from Hardhat's configuration
    const [deployer] = await ethers.getSigners();
    console.log("Deploying contracts with the account:", deployer.address);

    // Set the address for the testnet USDC
    const testnetUSDCAddress = "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238";

    // Add required bond amount (e.g., 0.0001 ETH)
    const requiredBond = ethers.parseEther("0.0001");

    // Get the contract factory using Hardhat's ethers integration
    const UMAPoolOracle = await ethers.getContractFactory("UMAPoolOracle");
    
    // Deploy the contract
    console.log("Deploying UMAPoolOracle...");
    const umAPoolOracle = await UMAPoolOracle.deploy(testnetUSDCAddress, requiredBond);

    // Wait for the deployment to complete
    await umAPoolOracle.waitForDeployment();

    // Get the deployed contract address
    const contractAddress = await umAPoolOracle.getAddress();
    console.log("Contract deployed to:", contractAddress);

    const usdc = await ethers.getContractAt("IERC20", testnetUSDCAddress, deployer);
    console.log("Approving contract to spend USDC...");

    // Send the approval transaction
    const approveTx = await usdc.approve(contractAddress, ethers.parseUnits("10", 6));
    await approveTx.wait();

    console.log("USDC approval complete.");

}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
