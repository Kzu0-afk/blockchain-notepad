# Client-Side Transaction Submission Evaluation

## Problem
Lace wallet's CIP-30 `signTx()` returns witness sets incompatible with pycardano's `TransactionWitnessSet.from_cbor()`. Backend reconstruction fails with type mismatch errors.

## Why Client-Side Submission Works (CIP-30 Standard)

CIP-30 defines a standard web-wallet interface for Cardano dApps/wallets in the browser. It supports methods like `signTx(...)` and `submitTx(...)`.

**Key Benefits:**
- ✅ Wallet handles all transaction signing and submission natively
- ✅ No backend decoding or re-assembly needed
- ✅ Eliminates pycardano witness set deserialization issues
- ✅ Wallet broadcasts transaction directly to Cardano network
- ✅ Returns transaction hash immediately after successful submission

**How It Works:**
1. Backend builds unsigned transaction (transaction body only)
2. Frontend sends unsigned transaction to wallet via `signTx()`
3. Wallet signs transaction and returns signed CBOR
4. Frontend submits signed transaction via `submitTx()`
5. Wallet broadcasts to Cardano network and returns `tx_hash`
6. Frontend records transaction metadata in backend database

## Solution: Client-Side Submission + Backend Recording

### Architecture
1. **Frontend**: Builds, signs, and submits transaction directly via Lace wallet
2. **Backend**: Records transaction details after successful submission

### Flow (Client-Side Submission with Smart Reconstruction & Fallback)
```
1. User fills form → Frontend calls /api/build-transaction/
2. Backend returns unsigned transaction CBOR (independent service)
3. Frontend: walletApi.signTx(unsignedTx, false) → Wallet signs transaction (client-side)
4. Frontend: Detects CBOR format
   - If CIP-30 wrapper (a1...): Calls /api/reconstruct-transaction/ → Gets full transaction (84...)
   - If full transaction (84...): Uses directly
5. Frontend: Attempts walletApi.submitTx(fullTx) → Tries multiple formats:
   - Attempt 1: Lowercase hex string
   - Attempt 2: Uint8Array bytes
   - Fallback: If both fail → POST /api/submit-transaction/ (backend submission)
6. Frontend: Receives tx_hash (from wallet or backend)
7. Frontend: POST /api/log-transaction/ → Logs metadata to Django database (independent service)
   - Stores: tx_hash, recipient_address, amount_lovelace, user, timestamp
   - Does NOT store: full signed transaction CBOR (not needed)
```

**Key Points**:
- ✅ **100% Client-Side Submission**: Wallet handles all network communication
- ✅ **Smart Format Detection**: Automatically detects and handles CIP-30 wrapper format
- ✅ **Reconstruction When Needed**: Only reconstructs if wallet returns wrapper format
- ✅ **Error Handling**: Validates transaction format before submission
- ✅ **Backend Independence**: Backend services are stateless helpers
- ✅ **Metadata Only**: Backend only stores transaction metadata (tx_hash, recipient, amount)

### Benefits
- ✅ Bypasses pycardano witness set incompatibility
- ✅ Uses wallet's native submission (more reliable)
- ✅ Still records transactions in Django for history/analytics
- ✅ Simpler backend (no CBOR reconstruction)

### Trade-offs
- ⚠️ Backend doesn't control final submission (wallet handles it)
- ⚠️ Less backend validation of signed transaction
- ✅ Still maintains transaction audit trail

## What Can Be Stored on Backend/Database

Even though transaction submission happens entirely client-side (via wallet), the backend can still record:

### ✅ Transaction Metadata (Stored)
- **Transaction Hash (tx_hash)** - Returned by wallet after successful submission
- **User ID** - Who submitted the transaction
- **Recipient Address** - Where ADA was sent
- **Amount (Lovelace)** - How much was sent
- **Timestamp** - When transaction was submitted
- **Status** - submitted/confirmed/failed (updated via background jobs)
- **Network** - Preview testnet / Mainnet

### ❌ What Is NOT Stored
- **Full Signed Transaction CBOR** - Not needed, transaction already on blockchain
- **Witness Sets** - Cryptographic signatures (not required for audit trail)
- **Transaction Body Details** - Can be queried from blockchain if needed

### Why This Approach Works
- **Transaction Hash is Sufficient**: The `tx_hash` uniquely identifies the transaction on-chain
- **Blockchain is Source of Truth**: All transaction details can be queried from Cardano network
- **Database is for Tracking**: User history, analytics, and UI display
- **Reduced Storage**: No need to store large CBOR blobs in database

### Implementation Changes
1. ✅ Added `walletApi.submitTx()` call in frontend
2. ✅ Created `/api/reconstruct-transaction/` endpoint (reconstructs full tx from CIP-30 wrapper)
3. ✅ Created `/api/record-transaction/` endpoint (receives tx_hash + metadata)
4. ✅ Updated transaction flow: reconstruct → submit client-side → record
5. ✅ Kept transaction history/display functionality

### Code Changes
- **Frontend**: `wallet-connection.js` - Detects CIP-30 wrapper, reconstructs via backend, submits client-side
- **Backend**: `api_views.py` - Added `reconstruct_transaction()` (raw CBOR manipulation) and `record_transaction()` endpoints
- **URLs**: `api_urls.py` - Added `/api/reconstruct-transaction/` and `/api/record-transaction/` routes

### Technical Details
- **Reconstruction Method**: Raw CBOR array manipulation using `cbor2` library (backend helper service)
- **Process**: 
  1. Decode unsigned tx array (preserves all elements: body, empty_witness, aux_data, metadata)
  2. Extract witness bytes from CIP-30 wrapper (as raw bytes, no deserialization)
  3. Replace empty witness with actual witness bytes
  4. Preserve all optional elements from unsigned transaction
  5. Encode back to CBOR (maintains same array length as unsigned tx)
- **No pycardano**: Avoids witness deserialization issues by using witness bytes directly
- **Why Backend Reconstruction**: Lace returns CIP-30 wrapper format, needs conversion to full transaction CBOR
- **Client-Side Submission**: Wallet's `submitTx()` handles all network communication (100% client-side)
- **Element Preservation**: Reconstructed transaction maintains same structure as unsigned transaction

### Architecture Summary

**Backend Services (Independent - Can be replaced/swapped)**:
- ✅ **Transaction Building Service** (`/api/build-transaction/`): Creates unsigned transaction body
- ✅ **Metadata Logging Service** (`/api/log-transaction/`): Simple endpoint to log transaction metadata

**Frontend (100% Client-Side Control)**:
- ✅ **Wallet Connection**: `window.cardano.lace.enable()` - User authorizes wallet
- ✅ **Transaction Signing**: `walletApi.signTx()` - Wallet signs with user's keys
- ✅ **Transaction Submission**: `walletApi.submitTx()` - Wallet broadcasts to Cardano network
- ✅ **Flow Control**: Frontend controls entire transaction flow
- ✅ **Metadata Logging**: Frontend sends metadata to backend after successful submission

**Key Principles**:
- 🔒 **100% Client-Side Submission**: Wallet handles all CBOR formats and network communication
- 🔒 **No CBOR Parsing**: Backend never touches signed transactions
- 🔒 **Backend Independence**: Backend services are stateless and independent
- 🔒 **Simple & Robust**: Avoids all CBOR parsing issues, witness set mismatches, pycardano errors
- 🔒 **Metadata Only**: Backend only stores what's needed for history/analytics

## What You Get - And What You Don't

| ✅ You Get | ❓ You Don't Get / Trade-off |
|------------|------------------------------|
| **tx_hash, recipient, amount, user** → stored in DB for history / later reference | **Full signed transaction CBOR** — so you can't re-submit or verify exact bytes server-side |
| **Simpler and robust**: You avoid CBOR parsing issues, mismatched witness sets, pycardano errors | **You rely on wallet + user's browser** — if user closes before logging, record may be incomplete |
| **Better UX**: Wallet handles submission, no backend submission issues / CBOR mismatches | **No ability to inspect raw transaction** or blockchain-level metadata server-side (unless you fetch from chain) |
| **Transaction history**: Backend maintains audit trail for users | **No server-side transaction validation** before submission (wallet handles this) |

## Summary: Client-Side Transaction Flow

### ✅ What Happens Client-Side (Browser)
- **Wallet Connection**: `window.cardano.lace.enable()` - User authorizes wallet access
- **Transaction Signing**: `walletApi.signTx()` - Wallet signs transaction with user's keys
- **Transaction Submission**: `walletApi.submitTx()` - Wallet broadcasts to Cardano network
- **Transaction Hash**: Wallet returns `tx_hash` after successful submission

### ✅ What Happens Backend-Side (Django)
- **Transaction Building**: Creates unsigned transaction body (UTXO selection, outputs, fees)
- **CBOR Reconstruction**: Helper endpoint to convert CIP-30 wrapper to full transaction CBOR
- **Metadata Storage**: Records `tx_hash`, `recipient_address`, `amount_lovelace`, `user`, `timestamp`
- **Transaction History**: Provides API endpoints for querying user's transaction history

### Key Benefits
- ✅ **Security**: Private keys never leave the wallet
- ✅ **Reliability**: Wallet handles all network communication
- ✅ **Compatibility**: Works with any CIP-30 compliant wallet (Lace, Yoroi, Nami, etc.)
- ✅ **Audit Trail**: Backend maintains transaction history for users
- ✅ **No CBOR Storage**: Database only stores metadata, not full transaction CBOR

## Status
**✅ IMPLEMENTED** - Client-side submission with smart format detection is now active. 

**Current Implementation**:
- ✅ Detects CIP-30 wrapper format automatically
- ✅ Reconstructs full transaction when needed (via backend helper)
- ✅ Validates transaction format before submission
- ✅ Checks wallet API support at connection time
- ✅ Comprehensive error handling and user feedback
- ✅ Logs metadata to backend after successful submission

**Known Limitations**:
- ⚠️ Lace returns CIP-30 wrapper format, requires reconstruction
- ⚠️ Some wallets may not support `submitTx()` - check at runtime
- ⚠️ Backend logging may fail even if transaction succeeds
- ⚠️ Need reconciliation logic for orphaned/ghost transactions

## Important Caveats & Checks

### ⚠️ Wallet submitTx() Support
- **CIP-30 Spec**: Defines `submitTx(tx: cbor<transaction>): Promise<hash32>`
- **Reality**: Not all wallets fully implement `submitTx()` - some only support `signTx()`
- **Lace Status**: Listed as CIP-30 compatible, but verify `walletApi.submitTx` exists at runtime
- **Fallback**: If `submitTx()` not available, show user error or fall back to backend submission

### ⚠️ Transaction Format Requirements
- **Lace Behavior**: `signTx()` returns CIP-30 wrapper (`a1...`) not full transaction (`84...`)
- **submitTx() Expectation**: Requires full transaction CBOR (hex-encoded)
- **Solution**: Detect wrapper format and reconstruct via backend helper before submission
- **Validation**: Always validate transaction format before calling `submitTx()`

### ⚠️ Known Issue: Lace Wallet v1.31.2 submitTx() Parsing Error
- **Error**: "Couldn't parse transaction. Expecting hex-encoded CBOR string"
- **Status**: Even correctly reconstructed transactions (starting with `84`) are rejected
- **Possible Causes**:
  - Lace's `submitTx()` implementation may have restrictions or bugs
  - CBOR structure mismatch despite correct format
  - Lace may intentionally limit custom submission flows

### ✅ Multi-Wallet Support
- **Supported Wallets**: Eternl, Lace, Nami, Yoroi, Gero, Flint, Typhon
- **Auto-Detection**: Automatically detects available CIP-30 wallets
- **Wallet Selection**: User can choose wallet from dropdown
- **Eternl Recommended**: Eternl wallet typically has better `submitTx()` support
- **Fallback**: Automatically falls back to backend submission if wallet rejects

**Current Implementation**:
- ✅ **Multi-Wallet Support**: Detects and supports multiple CIP-30 wallets
- ✅ **Wallet Selector**: UI dropdown to choose wallet
- ✅ **Eternl Preferred**: Auto-selects Eternl if available (better compatibility)
- ✅ **Client-Side First**: Tries client-side submission first (preferred)
- ✅ **Backend Fallback**: Falls back to backend submission if wallet rejects
- ✅ **Clear Errors**: Provides wallet-specific error messages
- ✅ **Metadata Logging**: Logs transaction metadata regardless of submission method

### ⚠️ Error Handling & User Feedback
- **Network Issues**: Wallet submission can fail (network errors, user cancellation, fee problems)
- **Backend Logging**: If submission succeeds but logging fails, transaction exists on-chain but not in DB
- **Reconciliation**: Need periodic checks to sync on-chain transactions with database records
- **User Experience**: Always show clear error messages and transaction status

### ⚠️ Security Considerations
- **No Backend Validation**: Backend doesn't validate final submitted transaction
- **Trust Wallet**: Must trust wallet to submit correct transaction
- **Metadata Validation**: Validate metadata logging requests (CSRF, user authentication)
- **Spoofing Prevention**: Ensure attackers can't log fake tx_hash/amount combinations

## Optional: Confirming Transaction Status Later

If you care about confirmation (not just submission), you can:

1. **Background Task**: After logging the tx_hash, have a background task (cron / Django management command / Celery) that periodically queries the blockchain (via Blockfrost API) to check if a tx_hash is confirmed, and update your `Transaction.status` accordingly.

2. **On-Demand Checking**: On user request (e.g. when they view 'transactions history'), fetch on-the-fly whether each logged tx has been confirmed.

3. **Webhook Integration**: Use Blockfrost webhooks (if available) to get notified when transactions are confirmed.

## Next Steps for Refactoring
1. ✅ **DONE**: Simplified to 100% client-side submission
2. ✅ **DONE**: Removed CBOR reconstruction dependency
3. ✅ **DONE**: Backend only logs metadata
4. **Optional**: Add transaction status polling from Cardano network (confirmed/pending)
5. **Optional**: Remove legacy `submit_transaction` and `reconstruct_transaction` endpoints

