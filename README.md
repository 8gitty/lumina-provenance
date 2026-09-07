<div align="center">

# 💠 Lumina Provenance

### Face-based provenance verification, anchored to the blockchain.

![Status](https://img.shields.io/badge/Status-Active-success) ![License](https://img.shields.io/badge/License-MIT-blue) ![Version](https://img.shields.io/badge/Version-1.0.0-purple) ![Chain](https://img.shields.io/badge/Chain-Polygon%20Amoy-8247E5)

**[🔗 View Frontend Preview →](https://lumina-provenance.vercel.app/)**

</div>

---

> **What this link is:** the deployed page at the button above is a **static UI preview of the frontend only** — it renders the full interface, styling, and interaction design, but is **not connected to a live backend**. Uploading an image there will not complete a real analysis. It exists purely so the interface can be viewed without running anything locally.
>
> **Where the real, fully working pipeline lives:** running locally, and demonstrated end-to-end in the submitted screen recording — that recording is the authoritative proof of functionality, not this link. See [Getting Started](#-getting-started-local-development) to run it yourself, or [Known Limitations](#️-known-limitations) for the full picture.

## Table of Contents

- [What It Does](#what-it-does)
- [Architecture](#architecture)
- [Features](#-features)
- [Tech Stack](#️-architecture-stack)
- [API Endpoints](#api-endpoints)
- [Getting Started](#-getting-started-local-development)
- [Project Structure](#-project-structure)
- [Blockchain Details](#️-blockchain-details)
- [Testing](#-testing)
- [Consent & Scope](#consent--scope)
- [Known Limitations](#️-known-limitations)
- [Demo Recording](#demo)

---

## What It Does

1. **Face Detection & Encoding** — extracts a face embedding from an uploaded image using DeepFace (OpenFace model).
2. **Web Search** — runs a genuine reverse-image search and returns real matching web pages with similarity scores. No hardcoded results.
3. **Blockchain Anchoring** — on a selected match, hashes the source data and writes it to a smart contract on Polygon Amoy, with a re-verification step that independently re-fetches and confirms the on-chain record.

A consent step is required in the UI before any search runs.

## Architecture

```
 Image Upload
      │
      ▼
 POST /api/analyze  ──────►  face embedding → ranked search matches + scores
      │  (consent required client-side before this fires)
      ▼
 POST /api/anchor  ───────►  hash → on-chain write (or disclosed local fallback)
      │
      ▼
 On-chain re-verification ──► fetch record → recompute hash → confirm match
```

---

## ✨ Features

| | |
|---|---|
| 🧠 **AI-Powered Face Analysis** | `DeepFace` (OpenFace model) extracts facial embeddings for downstream matching. |
| 🔍 **Cross-Reference Web Search** | Genuine reverse-image search against public web sources — no hardcoded results. |
| ⛓️ **Blockchain Anchoring** | Cryptographically hashes matched data and anchors it to Polygon Amoy for tamper-evident, independently re-verifiable provenance. |
| 🔄 **Dynamic Local Fallback** | If a live testnet transaction can't complete, the backend falls back to a local simulated ledger — **always clearly labeled as such in the UI**, never presented as a real on-chain write. |
| 🎨 **Cinematic UI** | React + Vite frontend with a dark atmospheric aesthetic, layered sound design, and a staged scroll-through pipeline visualization. |

---

## 🏗️ Architecture Stack

**Frontend:** React 18 · Vite · vanilla CSS
**Backend:** Python 3 · FastAPI · Uvicorn
**AI:** DeepFace (OpenFace model)
**Search:** Google Cloud Vision API (Web Detection) · SerpApi fallback
**Storage:** IPFS via Pinata
**Blockchain:** Polygon Amoy testnet · Web3.py · Solidity (`Verification.sol`)

---

## API Endpoints

- **`POST /api/analyze`** — accepts an image file, returns a face embedding and ranked real web matches with similarity scores.
- **`POST /api/anchor`** — accepts a selected match, hashes and anchors it, returns the transaction hash / IPFS CID / contract address (or the disclosed local-fallback equivalent).

Full interactive schema available at `/docs` when running the backend locally.

---

## 🚀 Getting Started (Local Development)

<details>
<summary><strong>Click to expand full setup instructions</strong></summary>

### 1. Clone the Repository
```bash
git clone https://github.com/8gitty/lumina-provenance.git
cd lumina-provenance
```

### 2. Backend Setup
```bash
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate # Mac/Linux

pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env` with your own credentials:
```env
GOOGLE_APPLICATION_CREDENTIALS=./gcp-service-account.json
SERPAPI_API_KEY=your_serpapi_key
PINATA_API_KEY=your_pinata_api_key
PINATA_SECRET_API_KEY=your_pinata_secret
POLYGON_AMOY_RPC_URL=https://polygon-amoy-bor-rpc.publicnode.com
WALLET_PRIVATE_KEY=your_testnet_wallet_private_key
```

Start the backend:
```bash
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend Setup
```bash
cd frontend
npm install
```

Create `frontend/.env.development`:
```env
VITE_API_URL=http://localhost:8000
```

Start the frontend:
```bash
npm run dev
```

App available at `http://localhost:5173`.

</details>

---

## 📂 Project Structure

<details>
<summary><strong>Click to expand file tree</strong></summary>

```text
lumina-provenance/
├── frontend/               # React + Vite frontend
│   ├── src/                # Components & app logic
│   ├── public/              # Static assets (sounds, favicon)
│   └── package.json
├── tests/                   # Pytest suite
├── server.py                # FastAPI application entrypoint
├── face_id.py                # DeepFace embedding logic
├── web_search.py             # Reverse image search + fallback
├── chain_verify.py           # Web3 hashing, anchoring, re-verification
├── Verification.sol          # On-chain provenance contract
└── requirements.txt
```

</details>

---

## ⛓️ Blockchain Details

- **Network:** Polygon Amoy testnet (chain ID `80002`)
- **Contract:** `Verification.sol` — stores a data hash per record, emits an event on write
- **Verification:** `chain_verify.py` includes a re-verification path that independently re-fetches the on-chain record and confirms it against the original hash — this is the actual tamper-evidence check, not a one-time write trusted blindly
- **Local Simulated Chain fallback:** if a live transaction fails (e.g. insufficient testnet gas), the backend falls back to a local ledger. **This is always visibly distinguished in the UI** ("LEDGER SYNCHRONIZATION COMPLETE" with a real tx hash + explorer link, vs. "RECORD READY · DEMO MODE" for the fallback) — never presented ambiguously.

---

## 🧪 Testing

```bash
pytest
```

---

## Consent & Scope

Before any search runs, the UI requires an explicit consent checkbox: *"I authorize the cryptographic hashing of this asset. This protocol strictly verifies provenance and does not execute facial recognition on private individuals."* This is an **application-level UX gate confirmed by the user before each run** — a policy commitment, not a cryptographic or technical enforcement mechanism.

---

## ⚠️ Known Limitations

- DeepFace accuracy depends on image quality, lighting, and angle; best results come from clear, front-facing photos.
- The web search stage depends on external API quota (Vision API / SerpApi); heavy repeated testing may hit rate limits.
- Public Polygon Amoy faucets are frequently rate-limited or gated behind mainnet-balance checks.
- **No backend is hosted for this submission** — the deployed frontend link is a static UI preview only. The full pipeline is run and demonstrated locally, shown end-to-end in the submitted recording.
- The consent step is an application-level safeguard, not a cryptographic enforcement mechanism.

---

## Demo

Full end-to-end screen recording (authoritative demonstration of the working pipeline):

- [Watch on Loom](https://www.loom.com/share/5e1ec34faa39420daf066db43d74f34f)
- [Watch on Google Drive](https://drive.google.com/file/d/1CNcsOk6XlMzMI3igPkkGJtH1N5KGa7tk/view?usp=sharing)

---

<div align="center">

*Built with precision. Anchored in trust.*

**License: MIT**

</div>
