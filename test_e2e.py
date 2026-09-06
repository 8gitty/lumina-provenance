import os
from dotenv import load_dotenv
load_dotenv()

from face_id import get_face_embedding
from web_search import search_web_for_image
from chain_verify import hash_data, pin_to_ipfs, deploy_contract, store_on_chain, verify_on_chain
from web3 import Web3

def test_pipeline():
    image_path = "modi.jpg"
    print("Stage 1: Face ID")
    res1 = get_face_embedding(image_path)
    if not res1["success"]:
        print("Face ID failed:", repr(res1["message"]))
        return
    print("Embedding generated!")

    print("Stage 2: Web Search")
    res2 = search_web_for_image(image_path)
    valid_results = [r for r in res2 if r["score"] >= 0.50]
    if not valid_results:
        print("No matches found clearing threshold.")
        return
    
    top_match = valid_results[0]
    print(f"Top Match: {top_match['url']} (Score: {top_match['score']})")

    print("Stage 3: Blockchain Verification")
    data_to_hash = {
        "url": top_match["url"],
        "page_title": top_match["page_title"],
        "score": top_match["score"]
    }
    
    rpc_url = os.environ.get("POLYGON_AMOY_RPC_URL")
    private_key = os.environ.get("WALLET_PRIVATE_KEY")
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    account = w3.eth.account.from_key(private_key)

    print("Deploying contract...")
    addr, abi = deploy_contract(w3, account)
    print(f"Contract Deployed at: {addr}")

    print("Hashing and pinning to IPFS...")
    data_hash = hash_data(data_to_hash)
    cid = pin_to_ipfs(data_to_hash)
    print(f"Hash: {data_hash}, CID: {cid}")

    print("Storing on chain...")
    tx = store_on_chain(addr, abi, data_hash, cid)
    print(f"Transaction: {tx}")

    print("Verifying on chain...")
    success, res = verify_on_chain(addr, abi, data_hash, data_to_hash)
    if success:
        print("Verification SUCCESS:", res)
    else:
        print("Verification FAILED:", res)

if __name__ == "__main__":
    test_pipeline()
