require('@nomicfoundation/hardhat-toolbox');
require('dotenv').config(); // Load environment variables from .env

module.exports = {
  solidity: "0.8.28",
  networks: {
    hardhat: {},
    sepolia: {
      // url: `https://eth-sepolia.g.alchemy.com/v2/${process.env.ALCHEMY_API_KEY}`,
      url: `https://eth-sepolia.g.alchemy.com/v2/sGaeYWfELFOMnPP4br8eYIROUqb_Ypmz`,
      accounts: [`0x${process.env.PRIVATE_KEY}`] // Use environment variable
    },
  },
};