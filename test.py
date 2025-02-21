from web3 import Web3
import os
import dotenv

dotenv.load_dotenv()  # Load environment variables

# Load environment variables
ALCHEMY_URL = os.getenv("ALCHEMY_URL")
AGENT_PRIVATE_KEY = os.getenv("AGENT_PRIVATE_KEY")  # Agent's Wallet
CONTRACT_OWNER_PRIVATE_KEY = os.getenv("PRIVATE_KEY")  # Contract owner's private key

# Initialize Web3
web3 = Web3(Web3.HTTPProvider(ALCHEMY_URL))

# Addresses
AGENT_ADDRESS = web3.eth.account.from_key(AGENT_PRIVATE_KEY).address
CONTRACT_OWNER = "0x366648a41eD9AA5A4F7AE478f16F7F401e906cB9"
TESTNET_USDC = "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238"

# USDC Contract ABI (simplified)
usdc_contract = web3.eth.contract(address=TESTNET_USDC, abi=[
    {
        "constant": True,
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}],
        "name": "allowance",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": False,
        "inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function"
    }
])


def check_balance(address):
    """Check USDC balance of an address."""
    balance = usdc_contract.functions.balanceOf(address).call()
    print(f"Balance of {address}: {balance / 1_000_000} USDC")
    return balance


def approve_agent(spender, amount):
    """Approve the agent to spend USDC from the contract."""
    nonce = web3.eth.get_transaction_count(CONTRACT_OWNER)
    
    tx = usdc_contract.functions.approve(spender, amount).build_transaction({
        'from': CONTRACT_OWNER,
        'gas': 100000,
        'gasPrice': web3.to_wei('10', 'gwei'),
        'nonce': nonce,
    })

    signed_tx = web3.eth.account.sign_transaction(tx, CONTRACT_OWNER_PRIVATE_KEY)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"Approved agent: {tx_hash.hex()}")


# # **Check Balances Before Approval**
# print("=== BEFORE APPROVAL ===")
# check_balance(CONTRACT_OWNER)
# check_balance(AGENT_ADDRESS)

# # **Approve 10 USDC (1e6 decimals)**
# approve_agent(AGENT_ADDRESS, 10 * 1_000_000)


# **Check Balances After Approval**
print("=== AFTER APPROVAL ===")
check_balance("0xD98c48934Ec9c4a3EeddB7cBF2D7CaF09dA76D43")
check_balance(CONTRACT_OWNER)
check_balance(AGENT_ADDRESS)
