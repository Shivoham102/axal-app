"use client"; 
import { useState } from "react";
import axios from "axios";

export default function Home() {
  const [email, setEmail] = useState("");
  const [walletAddress, setWalletAddress] = useState("");
  const [disputerAddress, setDisputerAddress] = useState("")
  // const [selectedPool, setSelectedPool] = useState("");
  const [status, setStatus] = useState(<></>);
  const [claimId, setClaimId] = useState("");
  const [disputeStatus, setDisputeStatus] = useState("");

  // List of pools
  const pools = [
    { "pool_name": "Pool A", "APY": 15.2, "TVL": 5000000 },
    { "pool_name": "Pool B", "APY": 18.5, "TVL": 3200000 },
    { "pool_name": "Pool C", "APY": 9.8, "TVL": 10000000 },
    { "pool_name": "Pool D", "APY": 22.1, "TVL": 1200000 },
    { "pool_name": "Pool E", "APY": 14.3, "TVL": 8000000 }
  ];

  // Handle pool monitoring submission
  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!walletAddress) {
      setStatus(<>Please fill in all required fields.</>);
      return;
    }

    try {
      const response = await axios.post("http://localhost:5000/submit", {
        email: email,
        user_address: walletAddress,
        // selected_pool: selectedPool,
      });
      
      // setStatus(`Monitoring started for wallet: ${walletAddress}`);

      // Extract data from the response
      const { message, pool_name, user_address, claim_id } = response.data;

      // Update status with claim ID
      // setStatus(`<>${message} <br/> Claim ID: ${claim_id} </>`);
      setStatus(
        <>
          <strong>{message} for {pool_name}</strong>
          <br />
          Claim ID: <code>{claim_id}</code>
        </>
      );
      

      
    } catch (error) {
      console.error("Error submitting request:", error);
      setStatus(<>Failed to start monitoring. Please try again.</>);
    }
  };

  // Handle dispute submission
  const handleDispute = async (e) => {
    e.preventDefault();

    if (!claimId || !disputerAddress) {
      setDisputeStatus("Please enter both Claim ID and Wallet Address.");
      return;
    }

    try {
      const response = await axios.post("http://localhost:5000/dispute", {
        claim_id: claimId,
        wallet_address: disputerAddress,
      });

      setDisputeStatus(`Dispute submitted successfully for Claim ID: ${claimId}`);
    } catch (error) {
      console.error("Error submitting dispute:", error);
      setDisputeStatus("Failed to submit dispute. Please try again.");
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gray-100 p-6">
      {/* Pool Monitoring Form */}
      <div className="bg-white p-8 rounded-lg shadow-lg w-full max-w-md mb-6">
        <h1 className="text-2xl font-bold text-center mb-6">Pool Monitoring</h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Email</label>
            <input
              type="email"
              placeholder="Enter your email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Wallet Address</label>
            <input
              type="text"
              placeholder="Enter your wallet address"
              value={walletAddress}
              onChange={(e) => setWalletAddress(e.target.value)}
              className="mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
              required
            />
          </div>
          {/*
            <div>
                <label className="block text-sm font-medium text-gray-700">Select Pool</label>
                <select
                  value={selectedPool}
                  onChange={(e) => setSelectedPool(e.target.value)}
                  className="mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                  required
                >
                  <option value="" disabled>Select a pool</option>
                  {pools.map((pool, index) => (
                    <option key={index} value={pool.pool_name}>
                      {pool.pool_name}
                    </option>
                  ))}
                </select>
            </div>
          */}

          <button
            type="submit"
            className="w-full bg-blue-500 text-white py-2 px-4 rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            Start Monitoring
          </button>
        </form>
        {status && <p className="mt-4 text-center text-gray-600">{status}</p>}
      </div>

      {/* Dispute Form */}
      <div className="bg-white p-8 rounded-lg shadow-lg w-full max-w-md">
        <h2 className="text-xl font-bold text-center mb-4">Raise a Dispute</h2>
        <form onSubmit={handleDispute} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Claim ID</label>
            <input
              type="text"
              placeholder="Enter Claim ID"
              value={claimId}
              onChange={(e) => setClaimId(e.target.value)}
              className="mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-red-500 focus:border-red-500"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Wallet Address</label>
            <input
              type="text"
              placeholder="Enter Your Wallet Address"
              value={disputerAddress}
              onChange={(e) => setDisputerAddress(e.target.value)}
              className="mt-1 block w-full px-4 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-red-500 focus:border-red-500"
              required
            />
          </div>
          <button
            type="submit"
            className="w-full bg-red-500 text-white py-2 px-4 rounded-md hover:bg-red-600 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
          >
            Submit Dispute
          </button>
        </form>
        {disputeStatus && <p className="mt-4 text-center text-gray-600">{disputeStatus}</p>}
      </div>
    </div>
  );
}
