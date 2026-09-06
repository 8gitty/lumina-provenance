import streamlit as st
import os
import tempfile
from dotenv import load_dotenv

# Load env before importing modules that might use them
load_dotenv()

from face_id import get_face_embedding
from web_search import search_web_for_image
from chain_verify import hash_data, pin_to_ipfs, deploy_contract, store_on_chain, verify_on_chain
from web3 import Web3

st.set_page_config(page_title="Identity Pipeline", layout="wide")

st.title("Face ID & Web Verification Pipeline")

# Initialize session state
if "contract_address" not in st.session_state:
    st.session_state.contract_address = None
if "contract_abi" not in st.session_state:
    st.session_state.contract_abi = None

def get_w3_and_account():
    rpc_url = os.environ.get("POLYGON_AMOY_RPC_URL")
    private_key = os.environ.get("WALLET_PRIVATE_KEY")
    if not rpc_url or not private_key:
        st.error("Missing Polygon Amoy credentials in .env")
        st.stop()
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    account = w3.eth.account.from_key(private_key)
    return w3, account

uploaded_file = st.file_uploader("Upload an Image", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name
        
    st.image(uploaded_file, caption="Uploaded Image", use_container_width=True)
    
    st.subheader("Stage 1: Face ID")
    if st.button("Run Face ID"):
        with st.spinner("Detecting face and generating embedding..."):
            result = get_face_embedding(tmp_path)
            if result["success"]:
                st.success(result["message"])
                st.write(f"Embedding generated (first 5 values): {result['embedding'][:5]}...")
                st.session_state.face_detected = True
            else:
                st.error(result["message"])
                st.session_state.face_detected = False

    if st.session_state.get("face_detected", False):
        st.subheader("Stage 2: Web Search")
        st.warning("This stage will upload the image to external services (Google Cloud Vision/SerpApi) to search the web.")
        consent = st.checkbox("I consent to uploading this image for web search.")
        
        if consent:
            if st.button("Search Web"):
                with st.spinner("Searching the web..."):
                    search_results = search_web_for_image(tmp_path)
                    st.session_state.search_results = search_results
                    
        if "search_results" in st.session_state:
            results = st.session_state.search_results
            
            # Filter by a threshold, e.g., 0.50
            valid_results = [r for r in results if r["score"] >= 0.50]
            
            if not valid_results:
                st.info("No matches found that clear the similarity threshold.")
            else:
                st.success(f"Found {len(valid_results)} matches!")
                for idx, res in enumerate(valid_results):
                    with st.expander(f"{res['page_title']} (Score: {res['score']})"):
                        st.write(f"**URL:** {res['url']}")
                        st.write(f"**Score:** {res['score']}")
                        st.write(f"**Source:** {res['source']}")
                        
                        if st.button(f"Verify on Blockchain (Result {idx})", key=f"verify_{idx}"):
                            with st.spinner("Deploying contract (if not deployed)..."):
                                if not st.session_state.contract_address:
                                    w3, account = get_w3_and_account()
                                    addr, abi = deploy_contract(w3, account)
                                    st.session_state.contract_address = addr
                                    st.session_state.contract_abi = abi
                                    st.success(f"Contract deployed at: {addr}")
                            
                            with st.spinner("Hashing and pinning to IPFS..."):
                                data_to_hash = {
                                    "url": res["url"],
                                    "page_title": res["page_title"],
                                    "score": res["score"]
                                }
                                data_hash = hash_data(data_to_hash)
                                cid = pin_to_ipfs(data_to_hash)
                                st.write(f"**Data Hash:** {data_hash}")
                                st.write(f"**IPFS CID:** {cid}")
                                
                            with st.spinner("Storing on Polygon Amoy..."):
                                tx_hash = store_on_chain(
                                    st.session_state.contract_address,
                                    st.session_state.contract_abi,
                                    data_hash,
                                    cid
                                )
                                st.success(f"Stored on chain! Transaction Hash: {tx_hash}")
                                
                            with st.spinner("Verifying data back from chain..."):
                                success, verify_res = verify_on_chain(
                                    st.session_state.contract_address,
                                    st.session_state.contract_abi,
                                    data_hash,
                                    data_to_hash
                                )
                                if success:
                                    st.balloons()
                                    st.success("Verification successful! Data hash matches stored IPFS CID on-chain.")
                                    st.json(verify_res)
                                else:
                                    st.error(f"Verification failed: {verify_res}")
