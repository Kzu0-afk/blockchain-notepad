# Wallet Integration Documentation

## Status: ✅ FULLY INTEGRATED & DEBUGGING SIGNATURES

The application now supports full wallet connection and transaction building. We are currently debugging an issue related to transaction submission where the Cardano network reports missing signatures.

### 1. Implementation Details

#### Frontend (`notes/static/js/wallet-connection.js`)
- **Library:** Uses `window.cardano` object (CIP-30).
- **Connection:** Connects to **Lace Wallet**.
- **Address Retrieval:** Gets the raw Hex address from the wallet (`api.getChangeAddress()`).
- **Transaction Flow:**
    1.  **Connect:** Prompts user to connect wallet.
    2.  **Build:** Sends recipient & amount to backend (`/api/build-transaction/`). Returns full unsigned `CardanoTransaction` CBOR.
    3.  **Sign:** Prompts user to sign the returned CBOR transaction in Lace. Uses `partialSign=true` to get only the witness set.
    4.  **Submit:** Sends *both* the `unsigned_tx_cbor` (from build) and the `witness_cbor` (from sign) to backend (`/api/submit-transaction/`).

#### Backend (`notes/api_views.py`)
- **Library:** Uses `pycardano>=0.10.0` and `blockfrost-python>=0.6.0`.
- **Network:** Configured for **Preview Testnet**.
- **Transaction Building:**
    -   Uses `pycardano.TransactionBuilder`.
    -   Wraps the `TransactionBody` in a full `CardanoTransaction` object (CBOR Type 4) to satisfy Lace wallet requirements.
- **Transaction Submission:**
    -   Receives `unsigned_tx_cbor` and `witness_cbor`.
    -   Reconstructs the full `CardanoTransaction` by deserializing the `unsigned_tx_cbor`, deserializing `witness_cbor` into a `TransactionWitnessSet`, and attaching this `witness_set` to the `CardanoTransaction`.
    -   Writes the CBOR of the **fully reconstructed signed transaction** to a temporary file.
    -   Submits this file to Blockfrost using `api.transaction_submit(file_path)`.

### 2. Current Issue: `MissingVKeyWitnessesUTXOW` / Signature Problem

The backend is receiving the `witness_cbor` from the frontend, deserializing it, and attaching it to the transaction. However, the Cardano network (via Blockfrost) is still reporting `MissingVKeyWitnessesUTXOW` when the transaction is submitted. This indicates that the signature of the sender's payment key is not correctly present in the final transaction submitted to the blockchain.

### 3. Debugging Steps Implemented
- **Enhanced Logging:** Extensive logging has been added to the `submit_transaction` function in `notes/api_views.py`. This logging will now capture:
    -   The raw `unsigned_tx_cbor` and `witness_cbor` received.
    -   The deserialized `witness_set` object.
    -   The contents of `witness_set.vkey_witnesses` (checking for actual signatures).
    -   The full `CardanoTransaction` object after `witness_set` is attached.
    -   The `full_signed_tx_cbor_hex` ready for submission.
- **`AttributeError` Fix:** Resolved `AttributeError: 'VerificationKeyHash' object has no attribute 'hex'` in logging statements.

### 4. Next Steps

To pinpoint the exact cause of the missing signature, please perform another transaction attempt and then **provide the full logs from your Django server console**. This information is critical to determine whether the wallet is not sending the signature, or if there's an issue in how the backend is processing or attaching it.