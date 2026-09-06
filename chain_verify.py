import os
import json
import hashlib
import requests
from web3 import Web3
import solcx

def hash_data(data: dict) -> str:
    """Returns SHA-256 hash of a dictionary (JSON stringified)."""
    data_str = json.dumps(data, sort_keys=True)
    return hashlib.sha256(data_str.encode('utf-8')).hexdigest()

def pin_to_ipfs(data: dict) -> str:
    """Pins data to IPFS via Pinata and returns the CID."""
    api_key = os.environ.get("PINATA_API_KEY")
    api_secret = os.environ.get("PINATA_SECRET_API_KEY")
    if not api_key or not api_secret:
        raise ValueError("Pinata credentials not found in environment variables.")

    url = "https://api.pinata.cloud/pinning/pinJSONToIPFS"
    headers = {
        "pinata_api_key": api_key,
        "pinata_secret_api_key": api_secret,
    }
    payload = {
        "pinataContent": data
    }
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()["IpfsHash"]

def get_abi():
    """Compiles the Verification.sol contract and returns its ABI."""
    solcx.install_solc('0.8.0')
    solcx.set_solc_version('0.8.0')
    
    with open("Verification.sol", "r") as f:
        contract_source = f.read()
        
    compiled_sol = solcx.compile_source(
        contract_source,
        output_values=['abi', 'bin']
    )
    
    contract_id, contract_interface = compiled_sol.popitem()
    return contract_interface['abi'], contract_interface['bin']

def deploy_contract(w3, account):
    """Compiles and deploys the Verification.sol contract."""
    abi, bytecode = get_abi()
    
    VerificationContract = w3.eth.contract(abi=abi, bytecode=bytecode)
    
    # Get current gas price and add a small buffer
    base_fee = w3.eth.get_block('latest')['baseFeePerGas']
    max_priority_fee = w3.eth.max_priority_fee
    max_fee_per_gas = base_fee + max_priority_fee
    
    # Build transaction
    construct_txn = VerificationContract.constructor().build_transaction({
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address),
        'maxFeePerGas': max_fee_per_gas,
        'maxPriorityFeePerGas': max_priority_fee
    })
    
    # Sign & send
    signed = account.sign_transaction(construct_txn)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    return tx_receipt.contractAddress, abi

def store_on_chain(contract_address, abi, data_hash: str, ipfs_cid: str):
    """Stores the data hash and IPFS CID on Polygon Amoy testnet."""
    rpc_url = os.environ.get("POLYGON_AMOY_RPC_URL")
    private_key = os.environ.get("WALLET_PRIVATE_KEY")
    
    if not rpc_url or not private_key:
        raise ValueError("Polygon Amoy credentials not found in environment variables.")
        
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    account = w3.eth.account.from_key(private_key)
    
    contract = w3.eth.contract(address=contract_address, abi=abi)
    
    bytes32_hash = Web3.to_bytes(hexstr=data_hash)
    
    base_fee = w3.eth.get_block('latest')['baseFeePerGas']
    max_priority_fee = w3.eth.max_priority_fee
    max_fee_per_gas = base_fee + max_priority_fee
    
    store_txn = contract.functions.storeVerification(bytes32_hash, ipfs_cid).build_transaction({
        'from': account.address,
        'nonce': w3.eth.get_transaction_count(account.address),
        'maxFeePerGas': max_fee_per_gas,
        'maxPriorityFeePerGas': max_priority_fee
    })
    
    signed = account.sign_transaction(store_txn)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    return tx_hash.hex()

def verify_on_chain(contract_address, abi, data_hash: str, expected_data: dict):
    """Fetches the IPFS CID from the contract and verifies the data hash matches."""
    rpc_url = os.environ.get("POLYGON_AMOY_RPC_URL")
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    contract = w3.eth.contract(address=contract_address, abi=abi)
    bytes32_hash = Web3.to_bytes(hexstr=data_hash)
    
    result = contract.functions.getVerification(bytes32_hash).call()
    stored_ipfs_cid, timestamp = result
    
    if not stored_ipfs_cid:
        return False, "Hash not found on chain."
        
    # Re-hash the expected_data to ensure it matches the stored hash
    computed_hash = hash_data(expected_data)
    if computed_hash != data_hash:
        return False, "Data hash mismatch."
        
    return True, {
        "stored_cid": stored_ipfs_cid,
        "timestamp": timestamp,
        "computed_hash": computed_hash
    }
