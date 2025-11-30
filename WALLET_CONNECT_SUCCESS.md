# Wallet Integration Documentation

## Status: ✅ FULLY INTEGRATED

The application now supports full wallet connection, address storage, and transaction sending on the **Cardano Preview Testnet**.

### 1. Implementation Details

#### Frontend (`notes/static/js/wallet-connection.js`)
- **Library:** Uses `window.cardano` object (CIP-30).
- **Connection:** Connects to **Lace Wallet**.
- **Address Retrieval:** Gets the raw Hex address from the wallet (`api.getChangeAddress()`).
- **Transaction Flow:**
    1.  **Connect:** Prompts user to connect wallet.
    2.  **Build:** Sends recipient & amount to backend (`/api/build-transaction/`).
    3.  **Sign:** Prompts user to sign the returned CBOR transaction in Lace.
    4.  **Submit:** Sends signed CBOR to backend (`/api/submit-transaction/`).

#### Backend (`notes/api_views.py`)
- **Library:** Uses `pycardano` and `blockfrost-python`.
- **Network:** Configured for **Preview Testnet**.
- **Endpoints:**
    -   `POST /api/save-wallet/`: Accepts Hex or Bech32 addresses. Converts Hex -> Bech32 for storage.
    -   `POST /api/build-transaction/`: Uses stored user address. Fetches UTXOs via Blockfrost. Returns **Hex-encoded CBOR** string.
    -   `POST /api/submit-transaction/`: Submits signed CBOR to Blockfrost.

### 2. Key Configuration
- **Blockfrost Project ID:** Must start with `preview...` for Preview Testnet.
- **Base URL:** Explicitly set to `ApiUrls.preview.value` in all Blockfrost initializations to avoid defaulting to Mainnet.

### 3. Usage Guide
1.  **Login** to the application.
2.  Navigate to **Wallet Profile**.
3.  Click **Connect Wallet** (approves in Lace).
4.  Status updates to: `Connected: addr_test1...`
5.  Enter **Recipient Address** (`addr_test1...`) and **Amount** (in Lovelace, e.g., 1000000 = 1 ADA).
6.  Click **Build & Sign Transaction**.
7.  Sign the transaction in the Lace popup.
8.  Transaction hash is displayed with a link to **CardanoScan**.