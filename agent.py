import json
import requests
import time
import threading
from flask import Flask, request, jsonify
from web3 import Web3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
from flask_cors import CORS

# Load environment variables from the .env file
load_dotenv()

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])

# Web3 & UMA Contract Setup
ALCHEMY_URL = os.getenv("ALCHEMY_URL")
UMA_CONTRACT_ADDRESS = "0x60eAEB512121c73E9eb8Dd68Ef9D80576b0b03f2"
TESTNET_USDC = "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238"

web3 = Web3(Web3.HTTPProvider(ALCHEMY_URL))

# Private Keys
AGENT_PRIVATE_KEY = os.getenv("AGENT_PRIVATE_KEY")  # Agent's Wallet
DISPUTER_PRIVATE_KEY = os.getenv("DISPUTER_PRIVATE_KEY")
AGENT_ADDRESS = Web3(Web3.HTTPProvider(ALCHEMY_URL)).eth.account.from_key(AGENT_PRIVATE_KEY).address

# Load contract ABI
with open("artifacts/contracts/UMAPoolOracle.sol/UMAPoolOracle.json") as f:
    contract_abi = json.load(f)["abi"]

uma_contract = web3.eth.contract(address=UMA_CONTRACT_ADDRESS, abi=contract_abi)

# Hardcoded pools data
pools = [
    {"pool_name": "Pool A", "APY": 15.2},
    {"pool_name": "Pool B", "APY": 18.5},
    {"pool_name": "Pool C", "APY": 9.8},
    {"pool_name": "Pool D", "APY": 22.1},
    {"pool_name": "Pool E", "APY": 14.3}
]

# Global requiredBond (must match what was deployed in the contract)
# For example, if requiredBond was set to 0.0001 ETH:
requiredBond = web3.to_wei("0.0001", "ether")
email = ""

def send_email(email, subject, body):
    """Send email notification to user."""
    sender_email = "axalapp@gmail.com"
    password = os.getenv("EMAIL_PASSWORD")

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, email, msg.as_string())
        server.quit()
        print(f"Email sent to {email}")
    except Exception as e:
        print(f"Error sending email: {e}")


# --- Updated Functions Below ---

def submit_claim(agent_address, highest_pool_name, user_address):
    """Agent submits a claim with its own wallet and includes the user's address.
       Sends the required bond (in ETH) with the transaction.
    """
    timestamp = int(time.time())
    tx = uma_contract.functions.submitClaim(highest_pool_name, timestamp, user_address).build_transaction({
        'from': agent_address,
        'gas': 200000,
        'gasPrice': web3.to_wei('10', 'gwei'),
        'nonce': web3.eth.get_transaction_count(agent_address),
        'value': requiredBond,  # Agent sends the required bond in ETH
    })

    signed_tx = web3.eth.account.sign_transaction(tx, AGENT_PRIVATE_KEY)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    return tx_hash.hex(), timestamp

def finalize_claim_after_delay(claim_id_bytes32, user_address):
    """Waits for dispute window and finalizes the claim."""
    time.sleep(5 * 60)  # Wait for dispute window
    finalize_claim(claim_id_bytes32, user_address)

    
def finalize_claim(claim_id_bytes32, user_address):
    """Finalize claim and notify user of the outcome.
       If the claim is not disputed, the contract returns the bond and transfers the reward directly to the user.
       If disputed, the agent is slashed.
    """
    global email
    # Convert the claim ID from hex string to bytes32
    # claim_id_bytes32 = bytes.fromhex(claim_id)
    tx = uma_contract.functions.finalizeClaim(claim_id_bytes32).build_transaction({
        'from': AGENT_ADDRESS,
        'gas': 200000,
        'gasPrice': web3.to_wei('10', 'gwei'),
        'nonce': web3.eth.get_transaction_count(AGENT_ADDRESS),
    })
    signed_tx = web3.eth.account.sign_transaction(tx, AGENT_PRIVATE_KEY)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"Finalize Claim Transaction: {tx_hash.hex()}")
    
    # Wait for the transaction to be mined/confirmed
    time.sleep(60)
    
    # Retrieve the claim details; assuming disputed is at index 4
    claim = uma_contract.functions.claims(claim_id_bytes32).call()
    if claim[4]:  # claim.disputed is True
        print("Claim was disputed. Agent slashed. No reward for user.")
        send_email(email, "Claim Disputed", "Your claim was disputed. No rewards issued.")
    else:
        print(f"Reward has been transferred directly to {user_address} by the contract.")
        send_email(email, "Reward Received", "Your 1 USDC reward has been successfully sent.")


def transfer_reward(user_address):
    """Transfer USDC reward to user from agent's wallet."""
    global email

    usdc_contract = web3.eth.contract(address=TESTNET_USDC, abi=[{
        "constant": False, 
        "inputs": [{"name": "recipient", "type": "address"}, {"name": "amount", "type": "uint256"}],
        "name": "transfer", 
        "outputs": [{"name": "", "type": "bool"}], 
        "type": "function"
    }])

    # 1 USDC = 1,000,000 smallest units
    amount_in_usdc = 1_000_000  # for 1 USDC

    tx = usdc_contract.functions.transfer(user_address, amount_in_usdc).build_transaction({
        'from': AGENT_ADDRESS,
        'gas': 100000,
        'gasPrice': web3.to_wei('10', 'gwei'),
        'nonce': web3.eth.get_transaction_count(AGENT_ADDRESS),
    })

    signed_tx = web3.eth.account.sign_transaction(tx, AGENT_PRIVATE_KEY)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    
    print(f"Reward sent to {user_address}: {tx_hash.hex()}")
    send_email(email, "Reward Received", "Your 1 USDC reward has been successfully sent.")

def monitor_pools(user_address):
    """Monitor pools & handle claim submission and finalization."""
    highest_pool_name = max(pools, key=lambda x: x['APY'])['pool_name']
    print(f"Agent submitting claim for {highest_pool_name}")

    claim_tx, timestamp = submit_claim(AGENT_ADDRESS, highest_pool_name, user_address)
    print(f"Claim submitted: {claim_tx}. Waiting for dispute window...")

    claim_id_bytes32 = web3.solidity_keccak(
        ['address', 'uint256', 'string', 'address'],
        [AGENT_ADDRESS, timestamp, highest_pool_name, user_address]
    )

    # Convert to hex string
    claim_id_hex = Web3.to_hex(claim_id_bytes32)

    print(f"Claim ID (hex): {claim_id_hex}. Waiting for dispute window...")

     # Run finalize_claim in a background thread
    threading.Thread(target=finalize_claim_after_delay, args=(claim_id_bytes32, user_address)).start()

    return claim_id_hex  

    # time.sleep(5 * 60)  # Wait for dispute window

    
    # finalize_claim(claim_id_bytes32, user_address)

def submit_dispute(disputer_address, claim_id):
    """Disputer submits a dispute for a given claim ID.
       The dispute must be submitted within the allowed dispute window.
    """
    tx = uma_contract.functions.disputeClaim(claim_id).build_transaction({
        'from': disputer_address,
        'gas': 300000,
        'gasPrice': web3.to_wei('10', 'gwei'),
        'nonce': web3.eth.get_transaction_count(disputer_address),
    })

    signed_tx = web3.eth.account.sign_transaction(tx, DISPUTER_PRIVATE_KEY)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    return tx_hash.hex()

@app.route('/submit', methods=['POST'])
def receive_input():
    """Receive user request & start monitoring."""
    data = request.json
    user_address = data.get("user_address")
    global email
    email = data.get("email")
   
    if not user_address:
        return jsonify({"error": "Invalid input"}), 400

    claim_id_hex = monitor_pools(user_address)

    return jsonify({
        "message": "Claim submitted successfully by Agent",
        "user_address": user_address,
        "claim_id": claim_id_hex
    })

@app.route("/dispute", methods=["POST"])
def receive_dispute():
    data = request.json

    # Extract disputer's wallet address and claim ID from request data
    disputer_address = data.get("wallet_address")
    claim_id = data.get("claim_id")  # Should be hex

    if not disputer_address or not claim_id:
        return jsonify({"error": "Missing wallet address or claim ID"}), 400

    try:
        claim_id_bytes = Web3.to_bytes(hexstr=claim_id)
        # Call the dispute function
        tx_hash = submit_dispute(disputer_address, claim_id_bytes)

        return jsonify({"message": "Dispute submitted successfully", "tx_hash": tx_hash}), 200
    except Exception as e:
        print("Error submitting dispute:", str(e))
        return jsonify({"error": "Failed to submit dispute", "details": str(e)}), 500


if __name__ == '__main__':
    app.run(port=5000)
