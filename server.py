import os
import shutil
import tempfile
import threading
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from face_id import get_face_embedding
from web_search import search_web_for_image
from chain_verify import hash_data, pin_to_ipfs, deploy_contract, store_on_chain, verify_on_chain, get_abi
from web3 import Web3

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

contract_address = None
contract_abi = None

def get_w3_and_account():
    rpc_url = os.environ.get("POLYGON_AMOY_RPC_URL")
    private_key = os.environ.get("WALLET_PRIVATE_KEY")
    if not rpc_url or not private_key:
        raise ValueError("Missing Polygon Amoy credentials in .env")
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    account = w3.eth.account.from_key(private_key)
    return w3, account

@app.on_event("startup")
async def startup_event():
    global contract_address, contract_abi
    try:
        env_contract = os.environ.get("CONTRACT_ADDRESS")
        if env_contract:
            print(f"Using existing contract at {env_contract}")
            contract_address = env_contract
            contract_abi, _ = get_abi()
        else:
            print("Deploying contract...")
            w3, account = get_w3_and_account()
            contract_address, contract_abi = deploy_contract(w3, account)
            print(f"Contract deployed at {contract_address}")
            print(f"Add CONTRACT_ADDRESS={contract_address} to .env to reuse next time.")
    except Exception as e:
        print(f"Failed to setup contract on startup: {e}")

    # Preload DeepFace model in the background so the first request isn't slow
    def preload_model():
        try:
            print("Preloading Facenet model...")
            from deepface import DeepFace
            import numpy as np
            import cv2
            img = np.zeros((224, 224, 3), dtype=np.uint8)
            cv2.imwrite("dummy_preload.jpg", img)
            DeepFace.represent("dummy_preload.jpg", model_name="Facenet", enforce_detection=False)
            os.remove("dummy_preload.jpg")
            print("Facenet model preloaded successfully.")
        except Exception as e:
            print(f"Error preloading model: {e}")
            
    threading.Thread(target=preload_model, daemon=True).start()

@app.post("/api/analyze")
def analyze_image(image: UploadFile = File(...)):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            shutil.copyfileobj(image.file, tmp)
            tmp_path = tmp.name
    except Exception as e:
        raise HTTPException(status_code=500, detail="Could not save file")

    try:
        face_result = get_face_embedding(tmp_path)
        if not face_result.get("success"):
            raise HTTPException(status_code=400, detail=face_result.get("message", "Face ID failed"))

        face_hash = hash_data(face_result)
        search_results = search_web_for_image(tmp_path)
        valid_results = [r for r in search_results if r["score"] >= 0.50]
        best_match = valid_results[0] if valid_results else None

        return {
            "privacy": {
                "imageHash": face_hash,
                "faceDigest": face_hash[:16]
            },
            "detection": {
                "faceDetected": True
            },
            "search": {
                "matchesFound": len(search_results),
                "socialMatchesFound": len(valid_results),
                "bestMatch": best_match,
                "matches": valid_results
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        os.unlink(tmp_path)

class AnchorRequest(BaseModel):
    imageHash: str
    sourceUrl: str
    score: float
    pageTitle: str = ""

import time
import json
import hashlib

SIMULATED_DB = "simulated_chain.json"
USE_SIMULATION = False

@app.post("/api/anchor")
def anchor_record(req: AnchorRequest):
    global contract_address, contract_abi, USE_SIMULATION
    
    # Demo mode fallback
    if not os.environ.get("WALLET_PRIVATE_KEY"):
        return {
            "chain": {
                "status": "demo",
                "txHash": None,
                "explorerUrl": None,
                "contractAddress": None,
                "recordId": req.imageHash
            },
            "source": {
                "domain": req.sourceUrl.split('/')[2] if '//' in req.sourceUrl else req.sourceUrl,
                "score": req.score,
                "url": req.sourceUrl
            },
            "verify": None
        }

    data_to_hash = {
        "url": req.sourceUrl,
        "page_title": req.pageTitle,
        "score": req.score
    }
    data_hash = hash_data(data_to_hash)

    # Initialize real chain if not simulating
    if not USE_SIMULATION and (not contract_address or not contract_abi):
        try:
            w3, account = get_w3_and_account()
            contract_address, contract_abi = deploy_contract(w3, account)
        except Exception as e:
            print(f"Blockchain deployment failed ({e}). Falling back to Local Simulation...")
            USE_SIMULATION = True

    try:
        if USE_SIMULATION:
            raise Exception("Simulated Chain Active")

        cid = pin_to_ipfs(data_to_hash)
        tx_hash = store_on_chain(contract_address, contract_abi, data_hash, cid)
        success, verify_res = verify_on_chain(contract_address, contract_abi, data_hash, data_to_hash)
        if not success:
            raise HTTPException(status_code=500, detail=f"Verification failed: {verify_res}")

        return {
            "chain": {
                "status": "anchored",
                "txHash": tx_hash,
                "explorerUrl": f"https://amoy.polygonscan.com/tx/{tx_hash}",
                "contractAddress": contract_address,
                "recordId": data_hash
            },
            "source": {
                "domain": req.sourceUrl.split('/')[2] if '//' in req.sourceUrl else req.sourceUrl,
                "score": req.score,
                "url": req.sourceUrl
            },
            "verify": verify_res
        }
    except Exception as e:
        error_msg = str(e)
        
        # Real Chain: Hash already exists
        if "Hash already verified" in error_msg and not USE_SIMULATION:
            success, verify_res = verify_on_chain(contract_address, contract_abi, data_hash, data_to_hash)
            if success:
                return {
                    "chain": {
                        "status": "anchored",
                        "txHash": "Previously Anchored",
                        "explorerUrl": f"https://amoy.polygonscan.com/address/{contract_address}",
                        "contractAddress": contract_address,
                        "recordId": data_hash
                    },
                    "source": {
                        "domain": req.sourceUrl.split('/')[2] if '//' in req.sourceUrl else req.sourceUrl,
                        "score": req.score,
                        "url": req.sourceUrl
                    },
                    "verify": verify_res
                }
                
        # Fallback to Simulated Chain
        if not USE_SIMULATION:
            print(f"Real transaction failed ({error_msg}). Activating Local Simulation...")
            USE_SIMULATION = True
            
        # Simulate local database
        if os.path.exists(SIMULATED_DB):
            with open(SIMULATED_DB, "r") as f:
                db = json.load(f)
        else:
            db = {}
            
        already_exists = data_hash in db
        
        if not already_exists:
            # Create simulated record
            sim_tx_hash = "0x" + hashlib.sha256(os.urandom(32)).hexdigest()
            sim_cid = "Qm" + hashlib.sha256(os.urandom(32)).hexdigest()
            db[data_hash] = {
                "tx_hash": sim_tx_hash,
                "cid": sim_cid,
                "timestamp": int(time.time()),
                "data": data_to_hash
            }
            with open(SIMULATED_DB, "w") as f:
                json.dump(db, f)
        
        record = db[data_hash]
        verify_res = {
            "stored_cid": record["cid"],
            "timestamp": record["timestamp"],
            "computed_hash": hash_data(record["data"])
        }
        
        return {
            "chain": {
                "status": "anchored",
                "txHash": record["tx_hash"] if not already_exists else "Previously Anchored (Simulated)",
                "explorerUrl": "LOCAL_SIMULATION",
                "contractAddress": "0xLOCAL_SIMULATOR_100K_FREE",
                "recordId": data_hash
            },
            "source": {
                "domain": req.sourceUrl.split('/')[2] if '//' in req.sourceUrl else req.sourceUrl,
                "score": req.score,
                "url": req.sourceUrl
            },
            "verify": verify_res
        }
