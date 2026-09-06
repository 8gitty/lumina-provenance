# LUMINA: Face ID + Blockchain Verification

LUMINA is a decentralized identity and provenance protocol designed to map digital assets securely to their web origins. By combining facial recognition (Face ID) with decentralized blockchain anchoring, it establishes a verifiable, tamper-evident record linking a face to the web assets it was matched against.

Whether you're verifying identity, tracing image provenance, or securing digital copyright, LUMINA creates an immutable cryptographic footprint.

**🔗 Live Demo:** [lumina-provenance.vercel.app](https://lumina-provenance.vercel.app/) (frontend) · **API:** [lumina-provenance.onrender.com](https://lumina-provenance.onrender.com) (backend)

> Note: the backend is hosted on Render's free tier, so the first request after a period of inactivity may take 30–60 seconds to respond while the service spins up.

---

## ✨ Features

- **Kinetic UI & Zero-Lag UX**
  A stunning, hardware-accelerated frontend built with React and Vite. It features a cinematic visual design, smooth scroll transitions, dynamic sound toggles, and a fully custom, zero-lag interactive cursor designed for a premium user experience.

- **DeepFace Identity Embeddings**
  Generates a face embedding using the DeepFace machine learning library, used to identify and match a face against publicly indexed web images.

- **Web Provenance Search**
  Automatically scrapes the web to trace the origin of digital assets, finding matches across social media and web domains to detect unauthorized usage and establish origin points.

- **Polygon Amoy Ledger Anchoring**
  Write records directly to the Polygon Amoy blockchain. Every verified asset is stored via smart contracts with IPFS (InterPlanetary File System) hashes, providing tamper-evident, decentralized storage.

- **Local Simulated Chain Fallback**
  If a real Amoy transaction fails (e.g. insufficient testnet gas), the backend transparently falls back to a local `simulated_chain.json` ledger and clearly labels the result as **simulated** rather than on-chain, so it's always clear which records are independently verifiable on Polygonscan and which are local-only.

- **Demo Mode**
  If no `WALLET_PRIVATE_KEY` is detected, LUMINA securely boots into an automatic Demo Mode, allowing users to experience the full pipeline and provenance search without requiring Web3 credentials.

---

## 🛠 Tech Stack

- **Frontend:** React, Vite, CSS Animations (Hardware Accelerated) — deployed on Vercel
- **Backend:** Python, FastAPI, Uvicorn — deployed on Render
- **Machine Learning:** DeepFace, TensorFlow/Keras
- **Web3 & Blockchain:** Web3.py, Solidity (solcx), Polygon Amoy Testnet
- **Storage:** IPFS integration

---

## 🚀 Getting Started

### 1. Prerequisites
- Node.js (v18+)
- Python 3.10+
- Google Cloud Vision API credentials (service account JSON — set as `GOOGLE_APPLICATION_CREDENTIALS`) for web search
- Polygon Amoy RPC URL & Wallet Private Key (optional, falls back to Simulation/Demo Mode)

### 2. Backend Setup
```bash
# Clone the repository
# Create a virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# OR source venv/bin/activate  # Mac/Linux

# Install requirements
pip install -r requirements.txt

# Setup Environment Variables
cp .env.example .env
# Edit .env with your keys

# Start the FastAPI Server (with auto-reload)
python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 4. Running the App
1. Navigate to `http://localhost:5173` (or the [live demo](https://lumina-provenance.vercel.app/))
2. Enter the LUMINA gate (with or without sound)
3. Proceed to **Asset Ingestion** to upload an image.
4. View the DeepFace analysis and the **Provenance Search** results.
5. Select a match to securely anchor the asset footprint to the **Ledger** — the result will be labeled **ON-CHAIN** or **SIMULATED** depending on whether the Amoy transaction succeeded.

---

## 🛡 Blockchain Fallback Architecture

LUMINA guarantees high availability via an intelligent, transparently-disclosed gas-monitoring fallback:
1. The backend attempts to compile and deploy the `Verification.sol` contract (if no address is saved).
2. It attempts to anchor the data via Web3.py to the Amoy testnet.
3. If an `Exception` is thrown (e.g., `-32000 gas required exceeds allowance`), the backend immediately catches it.
4. `USE_SIMULATION` activates, generating a pseudo-transaction hash and IPFS CID, saving the record to `simulated_chain.json`.
5. The UI updates with a clearly labeled **SIMULATED** badge, so it's always obvious to the user which records are independently verifiable on Polygonscan and which are local-only.

---

## ⚠️ Known Limitations

- DeepFace accuracy depends on image quality, lighting, and angle; best results come from clear, front-facing photos.
- The web search stage depends on external API quota (Google Cloud Vision); heavy repeated testing may hit rate limits.
- Public Polygon Amoy faucets are frequently rate-limited or gated behind mainnet-balance checks; when live testnet gas isn't available, the app falls back to a clearly-labeled local simulated chain (see above) rather than a real Polygonscan-verifiable transaction.
- The consent gate is an application-level UX safeguard before running a search, not a cryptographic enforcement mechanism.
- The backend is hosted on a free-tier instance and may cold-start slowly after inactivity.

---

## 📄 License
This project is open-source and available under the MIT License.
