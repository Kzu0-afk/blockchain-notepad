Comprehensive Project Plan: Cardano Wallet Integration

## 📊 Implementation Status

**Last Updated:** November 2024

| Phase | Status | Completed By | Notes |
|-------|--------|--------------|-------|
| Phase 1: Project Setup & Prerequisites | ✅ **COMPLETED** | MJ (Lead Developer) | Environment configured, dependencies installed |
| Phase 2: Wallet Connection Functionality | ⏳ **PENDING** | Team Members | Frontend UI and API endpoint needed |
| Phase 3: Transaction Handling | 🔄 **PARTIALLY COMPLETED** | MJ (Backend Logic ✅) | Backend APIs complete, Frontend components pending |
| Phase 4: Final Integration & Testing | ⏳ **PENDING** | All Team Members | Waiting for Phase 2 & Phase 3 Frontend completion |

### ✅ Completed Components

**Backend (Phase 1 & Phase 3 - MJ):**
- ✅ `.env` file configuration for secure API key management
- ✅ `requirements.txt` with all dependencies (Django, blockfrost-python 0.6.0, pycardano 0.17.0, python-decouple)
- ✅ `settings.py` updated with Blockfrost API configuration using python-decouple
- ✅ `Profile` model created in `notes/models.py` with wallet_address field
- ✅ Django signals implemented for automatic Profile creation
- ✅ `build_transaction` API endpoint implemented (`/api/build-transaction/`)
- ✅ `submit_transaction` API endpoint implemented (`/api/submit-transaction/`)
- ✅ API URL routing configured in `notes/api_urls.py`
- ✅ Database migrations created and applied

**Files Created/Modified:**
- `requirements.txt`
- `notepad_project/settings.py` (lines 14, 136-137)
- `notes/models.py` (Profile model)
- `notes/api_views.py` (Transaction APIs)
- `notes/api_urls.py` (API routing)
- `notes/admin.py` (Profile registration)
- `notepad_project/urls.py` (API route inclusion)

---

1. Project Overview & Mission
The primary goal is to integrate live Cardano blockchain functionality into our existing Django web application. The project will enable authenticated users to connect their personal Cardano wallet (e.g., Lace), and use it to construct, securely sign, and submit a transaction to the Cardano Preview Testnet. This will serve as a practical demonstration of a full-stack Web3 application.
2. Core Architecture: Secure Client-Server Model
To ensure security and proper separation of concerns, we will not place all logic in the frontend as seen in the JavaScript example. Instead, we will implement a robust Client-Server architecture.
Frontend (Client - JavaScript in the Browser): This is the "untrusted" environment responsible for all direct user interaction. Its sole responsibility is to interact with the user's wallet extension (window.cardano) which is only accessible from the browser. It will handle connection requests and signing prompts.
Backend (Server - Python/Django): This is the "trusted" environment that acts as the brain of our application. It will securely store and use our secret Blockfrost API key. It will handle all communication with the Blockfrost service, construct the transactions, and validate the final logic before submission. This architecture prevents exposing our secret keys to the public.
3. Technology & Tool Stack
Wallet: Lace Wallet (or any CIP-30 compatible wallet).
Frontend-Wallet Bridge (JS): The CIP-30 standard, accessed via the window.cardano object.
Backend-Blockchain Bridge (Python): Blockfrost.io API service.
Python Libraries (✅ Installed):
- **Django 5.2.6**: Web framework
- **blockfrost-python 0.6.0**: For communication with the Blockfrost API
- **pycardano 0.17.0**: For building and manipulating Cardano data structures like transactions
- **python-decouple 3.8**: For secure environment variable management
Verification & Debugging Tools:
Cardano Scan (Preview): Block explorer to visually confirm successful transactions.
CBOR Playground: Tool to inspect raw transaction data if debugging is needed.
4. High-Level End-to-End Workflow
The following 12 steps detail the flow of data between the user's browser and our Django server:

[Frontend JS / Browser]                       [Backend Django / Python]
      |                                              |
1. User clicks "Connect Wallet"                        |
      |                                              |
2. Calls `window.cardano.lace.enable()`                |
      |                                              |
3. Gets user's wallet address                        |
      |                                              |
4. Sends address to Django  ---------------------->  (Saves address to User's profile)
      |                                              |
      |                                              |
5. User fills out transaction form (recipient, amount) |
      |                                              |
6. Sends form data to Django  ------------------->  (1. Calls Blockfrost with SECRET API KEY)
      |                                              |  (2. Gathers UTXOs, builds transaction)
      |                                              |
7. Receives *unsigned* TX CBOR <-------------------  (3. Sends the unsigned transaction back)
      |                                              |
      |                                              |
8. Calls `api.signTx(unsignedTx)`                      |
      |                                              |
9. Gets *signed* TX CBOR from user's wallet            |
      |                                              |
10. Sends signed TX to Django ------------------->  (1. Calls Blockfrost with SECRET API KEY)
      |                                              |  (2. Submits the signed transaction)
      |                                              |
11. Receives final TX Hash    <-------------------  (3. Sends the final transaction hash back)
      |                                              |
      |                                              |
12. Displays TX Hash link to user                      |



5. Reference Code (Initial JavaScript Example)

<details>
<summary>Click to view the initial all-in-one React code</summary>
Note: We will not use this code directly. Its purpose is to serve as a reference for the required logic (e.g., function names like .enable(), .signTx()) and the overall transaction flow, which we are separating into our Client-Server architecture.

import { WebWallet } from '@blaze-cardano/sdk'
import {useState, useEffect } from 'react'

function App() {
const [wallets, setWallets] = useState([])
const [walletApi, setWallApi] = useState(null)
const [selectedWallet, setSeletedWallet] = useState('')
const [walletAddress, setWalletAddress] = useState('')
const [recipient, setRecipient] = useState('')
const [amount, setAmount] = useState(0n)

const [provider] = useState((() => new Blockfrost({
network: 'cardano-preview',
projectId: import.meta.env.VITE_BLOCKFROST_PROJECT_ID,
})))


useEffect(() => {
if(window.cardano) {
  setWallets(Object.keys(window.cardano))
 }
}, [])

const handleWalletChange = async (event) => {
const walletName = event.target.value
setSelectedWallet(walletName)
}

const handleConnectWallet = async () => {
console.log ('Connecting to wallet:', selectedWallet)
if (selectedWallet && window.cardano[selectedWallet]) { 
try {

 const api = await window.cardano[selectedWallet].enable()
 setWalletApi(api)
 console.log('Connected to wallet API:', api)
 const address = await api.getChangeAddress()
 console.log('Wallet address:', address)
 setWalletAddress(address)

    } catch (error) {
      console.error('Error connecting to wallet:', error)
      }
  }
}

const handleRecipientChange = (event) => {
setRecipient(event.target.value)
}

const handleAmountChange = (event) => {
setAmount(BigInt(event.target.value))
}

const handleSubmitTransaction = async () => {
if (walletApi) {
 try {
 //construct and submit transaction logic
const wallet = new WebWallet(walletApi)
const blaze = await Blaze.from(provider, wallet)
console.log('Blaze instance created:', blaze)

const bech32Address = Core.Address.fromBytes(Buffer.from(recipient, 'hex')).toBech32()
console.log('Recipient address (bech32):', bech32Address)

const tx = await blaze
.newTransaction()
.payLovelace(
Core.Address.fromBech32(recipient),
amount
)
.complete()

console.log('Transaction built:', tx.toCbor())

const signedTx = await blaze.signTransaction(tx)

console.log('Transaction signed:', signedTx.toCbor())

const txHash = await blaze.provider.postTransactionToChain(signedTx)

console.log('Transaction submitted. Hash:', txHash)


 }  catch (error) {
console.error('Error submitting transaction:', error)
}
}

}

return (
 <div>
    <div>
       <select value={selectedWallet} onChange={handleWalletChange}>
        <option value="">Select Wallet</option>
        {wallets. length > 0 && wallets.map((wallet) => (
          <option key={wallet} value={wallet}>{wallet}</option>
       ))}
       </select>
    </div>
{
walletApi ? 
(<div>Wallet Connected</div>) : 
(<button onClick={handleConnectWallet}>Connect Wallet</button>)
}
    <div>
<p>Connected Wallet Address: {walletAddress}</p>

<label>Recipient Address: </label>
<input type="text" placeholder="Enter Recipient Address" value={recipient} onChange={handleRecipientChange}/>
<br/>
<label>Amount: </label>
<input type="number" placeholder="Enter Amount" value={String(amount)} onChange={handleAmountChange} />
<br/>
<button onClick={handleSubmitTransaction}>Send ADA</button>
</div>
    </div>
    )
}

export default App

</details>


6. Phase-by-Phase Execution Plan

I. Phase 1: Project Setup & Prerequisites ✅ **COMPLETED**
Description: To ensure every team member has the necessary tools, accounts, and a foundational understanding of the technologies we will use. This phase must be completed before any coding begins.

**1. MJ (Lead Developer) - ✅ COMPLETED:**
- ✅ Created `.env` file in project root with `BLOCKFROST_PROJECT_ID='YOUR_KEY_HERE'`
- ✅ Verified `.env` is listed in `.gitignore` to prevent committing secret keys
- ✅ Created `requirements.txt` with all dependencies:
  - Django>=5.2.6
  - blockfrost-python>=0.6.0 (corrected from 1.3.0)
  - pycardano>=0.10.0
  - python-decouple>=3.8
- ✅ Integrated `python-decouple` in `notepad_project/settings.py`:
  - Import: `from decouple import config`
  - Configuration: `BLOCKFROST_PROJECT_ID = config('BLOCKFROST_PROJECT_ID', default='')`
  - Network setting: `BLOCKFROST_NETWORK = 'cardano-preview'`
- ✅ All dependencies installed and tested

**All Team Members (Vincent, Luis, Rainric) - ⏳ PENDING:**
Task: Set up individual development environments.
- Install the Lace wallet browser extension.
- Create a personal project on Blockfrost.io and select the Preview Testnet.
- Acquire test ADA from the official Cardano Testnet Faucet to fund your Lace wallet on the Preview network.
- Provide your Blockfrost Project ID to MJ for the central .env file.

II. Phase 2: Wallet Connection Functionality
Description: To implement the initial user feature: connecting their Lace wallet to their account in our application and saving their wallet address to the database.

1. Luis Miguel A. Jaca (UI/UX): ✅ **COMPLETE**
Git Branch: feature/ui/wallet-connection
Task: Create the necessary frontend user interface elements.
In the user profile template, add a <button> with the ID connect-wallet-btn and text "Connect Wallet".
Add a <div> with the ID wallet-address-display to show the user's connected address. It should initially display "Status: Not Connected".

2. Vincent B. Pacaña (Backend API Scaffolding) - ⏳ PENDING:
Git Branch: feature/api/save-wallet-endpoint
Task: Prepare the backend to store wallet data.
- ✅ **Model:** Profile model already created by MJ with wallet_address field (completed in Phase 3)
- ✅ **Database:** Migration created and applied (`notes/migrations/0003_profile.py`)
- ⏳ **API Endpoint:** Create the URL and a login-protected view function for a POST request at `/api/save-wallet/` to save wallet address to user's profile.
**Status Update**: Luis Miguel A. Jaca has completed all UI/UX tasks for Phase 2. The profile template (`notes/templates/notes/profile.html`) has been created with the connect wallet button and wallet address display div. A profile view and URL route have been added. See `MIGS_IMPLEMENTATION_DOCS.md` for complete implementation details.

2. Vincent B. Pacaña (Backend API Scaffolding):
Git Branch: feature/api/save-wallet-endpoint
Task: Prepare the backend to store wallet data.
Model: Modify the User/Profile model by adding a new field: wallet_address = models.CharField(max_length=103, unique=True, null=True, blank=True).
Database: Run the commands python manage.py makemigrations and python manage.py migrate.
API Endpoint: Create the URL and a login-protected view function for a POST request at /api/save-wallet/ that validates wallet address format and stores it in the user profile.


3. Rainric Randy P. Yu (Frontend Logic):
Git Branch: feature/js/connect-wallet-script
Task: Implement the client-side JavaScript for wallet connection.
Write a JavaScript event listener for the #connect-wallet-btn.
On click, call window.cardano.lace.enable() to prompt the user for authorization.
On success, get the user's address via api.getChangeAddress().
Use the fetch API to send a POST request to the /api/save-wallet/ endpoint, with the address in the request body.
On a successful response from the backend, update the text of the #wallet-address-display div with the connected address.

III. Phase 3: Transaction Handling Functionality
Description: The core implementation phase. To build the end-to-end flow for a user to construct, sign, and submit a transaction to the Cardano Preview Testnet.

1. Luis Miguel A. Jaca (UI/UX): ✅ **COMPLETE**
Git Branch: feature/ui/transaction-form
Task: Create the user interface for sending ADA.
Create an HTML <form> with the ID transaction-form.
Inside the form, add an <input> for "Recipient Address" (ID: recipient-address-input).
Add another <input type="number"> for "Amount (Lovelace)" (ID: amount-input).
Add a <button type="submit"> with the text "Build & Sign Transaction".
Create a <div> with the ID tx-hash-display to show the final transaction hash and a link to Cardano Scan.

2. Vincent B. Pacaña (Backend API Scaffolding) - ✅ **COMPLETED BY MJ:**
Git Branch: feature/api/transaction-endpoints
Task: Create the backend API endpoint structures for transaction processing.
- ✅ **URL:** Path for POST request at `/api/build-transaction/` (implemented by MJ)
- ✅ **URL:** Path for POST request at `/api/submit-transaction/` (implemented by MJ)
- ✅ **Views:** Fully implemented (not empty) with complete transaction logic in `notes/api_views.py`
- ✅ **URL Configuration:** `notes/api_urls.py` created and integrated
**Status Update**: Luis Miguel A. Jaca has completed all UI/UX tasks for Phase 3. The transaction form with all required elements (form, recipient input, amount input, submit button, and tx-hash-display div) has been implemented in the profile template. The form includes proper styling and is ready for JavaScript integration. See `MIGS_IMPLEMENTATION_DOCS.md` for complete implementation details.

2. Vincent B. Pacaña (Backend API Scaffolding):
Git Branch: feature/api/transaction-endpoints
Task: Create the backend API endpoint structures for transaction processing.
URL: Define paths for POST requests at /api/build-transaction/ and /api/submit-transaction/.
Views: Create the corresponding login-protected view functions for both URLs in views.py that handle transaction building and submission.

3. Rainric Randy P. Yu (Frontend Logic):
Git Branch: feature/js/sign-submit-script
Task: Implement the client-side JavaScript for the transaction lifecycle.
Write a JavaScript event listener for the #transaction-form submission.
Build Step: Prevent default form submission, then fetch the /api/build-transaction/ endpoint, sending the recipient and amount. Await the response containing the unsigned transaction CBOR.
Sign Step: Use the wallet's api.signTx(unsignedTxCbor, true) function to prompt the user to sign.
Submit Step: fetch the /api/submit-transaction/ endpoint, sending the signed transaction CBOR from the previous step.
Display Step: On a successful response, display the final transaction hash in the #tx-hash-display div, formatted as a clickable link to https://preview.cardanoscan.io/transaction/THE_HASH.

4. MJ (Backend Logic) - ✅ **COMPLETED:**
Git Branch: feature/backend/transaction-logic
Task: Implement the secure, server-side transaction processing logic.

**✅ Completed Implementation:**

- ✅ **Libraries Installed:** All dependencies in `requirements.txt` (blockfrost-python 0.6.0, pycardano 0.17.0)
- ✅ **Profile Model:** Created in `notes/models.py` with wallet_address field (max_length=103, unique, nullable)
- ✅ **Database Migration:** Created and applied (`notes/migrations/0003_profile.py`)

**✅ build_transaction View (notes/api_views.py, lines 21-104):**
- ✅ Reads BLOCKFROST_PROJECT_ID from settings
- ✅ Validates user has connected wallet (checks Profile.wallet_address)
- ✅ Uses BlockFrostChainContext from pycardano to fetch UTXOs
- ✅ Uses TransactionBuilder to construct unsigned transaction
- ✅ Automatically handles UTXO selection, fee calculation, and change outputs
- ✅ Returns unsigned transaction CBOR (hex-encoded) in JSON response
- ✅ Protected with `@login_required` decorator
- ✅ Endpoint: `POST /api/build-transaction/`

**✅ submit_transaction View (notes/api_views.py, lines 109-160):**
- ✅ Receives signed transaction CBOR from request body
- ✅ Uses Blockfrost API (`api.submit_transaction()`) to submit to Cardano network
- ✅ Returns transaction hash in JSON response
- ✅ Protected with `@login_required` decorator
- ✅ Endpoint: `POST /api/submit-transaction/`

**✅ URL Configuration:**
- ✅ Created `notes/api_urls.py` with both endpoints
- ✅ Integrated into `notepad_project/urls.py` at `/api/` path

**Technical Challenges Solved:**
- ✅ Fixed pycardano import path (changed from `pycardano.backends.blockfrost` to direct import from `pycardano`)
- ✅ Corrected blockfrost-python version from 1.3.0 to 0.6.0
- ✅ Ensured proper virtual environment package installation

IV. Phase 4: Final Integration & Testing ⏳ **PENDING**
Description: The final phase where all completed components are merged, tested together, and the project is finalized for presentation.

**Status:** Waiting for Phase 2 and Phase 3 Frontend components to be completed.

**1. MJ (Lead Developer) - ⏳ PENDING:**
Task: Oversee the final integration and verification.
- ⏳ **Code Review:** Review all pull requests from team members, ensuring code quality and adherence to the plan.
- ⏳ **Merge:** Merge all approved feature branches into the main branch.
- ⏳ **End-to-End Testing:** Perform a full user workflow: Register -> Login -> Connect Wallet -> Send ADA.
- ⏳ **Verification:** Use Cardano Scan (Preview) to confirm the test transaction is visible and successful on the blockchain.
- ⏳ **Debugging:** If necessary, use the CBOR Playground to analyze any problematic transaction data and statuses.

---

## 📝 Implementation Notes

### Backend API Endpoints (✅ Ready for Frontend Integration)

**1. Build Transaction Endpoint:**
- **URL:** `POST /api/build-transaction/`
- **Authentication:** Required (login-protected)
- **Request Body:**
  ```json
  {
    "recipient_address": "addr_test...",
    "amount_lovelace": 1000000
  }
  ```
- **Response:**
  ```json
  {
    "unsigned_tx_cbor": "hex-encoded-cbor-string"
  }
  ```

**2. Submit Transaction Endpoint:**
- **URL:** `POST /api/submit-transaction/`
- **Authentication:** Required (login-protected)
- **Request Body:**
  ```json
  {
    "signed_tx_cbor": "hex-encoded-cbor-string"
  }
  ```
- **Response:**
  ```json
  {
    "tx_hash": "transaction-hash"
  }
  ```

### Profile Model Structure
- **File:** `notes/models.py`
- **Field:** `wallet_address` (CharField, max_length=103, unique, nullable)
- **Relationship:** OneToOne with User model
- **Auto-creation:** Django signals automatically create Profile when User is created

### Security Features Implemented
- ✅ API key stored securely in `.env` file (not committed to git)
- ✅ All API endpoints protected with `@login_required`
- ✅ Server-side transaction construction (Blockfrost API key never exposed to frontend)
- ✅ Input validation and error handling

---

## 🔗 GitHub Repository
**URL:** https://github.com/Kzu0-afk/blockchain-notepad
Code Review: Review all pull requests from team members, ensuring code quality and adherence to the plan.
Merge: Merge all approved feature branches into the main branch.
End-to-End Testing: Perform a full user workflow: Register -> Login -> Connect Wallet -> Send ADA.
Verification: Use Cardano Scan (Preview) to confirm the test transaction is visible and successful on the blockchain.
Debugging: If necessary, use the CBOR Playground to analyze any problematic transaction data and statuses.

**Implementation Status Summary:**

✅ **Backend Implementation**: Vincent B. Pacaña has completed all backend API endpoints and transaction processing logic. The backend is ready for frontend integration and testing. See `VINCE_IMPLEMENTATION_DOCS.md` for details.

✅ **Frontend UI/UX Implementation**: Luis Miguel A. Jaca has completed all UI/UX tasks for Phase 2 and Phase 3. All required HTML elements, styling, and basic JavaScript structure are in place. The profile page is ready for JavaScript integration. See `MIGS_IMPLEMENTATION_DOCS.md` for details.

⏳ **Frontend JavaScript Implementation**: Rainric Randy P. Yu needs to implement the JavaScript functionality for:
- Phase 2: Wallet connection script (event listener, wallet API calls, fetch to backend)
- Phase 3: Transaction form script (build, sign, submit, display transaction hash)

**Note for Rainric**: The UI elements are already in place with the correct IDs. You can focus on implementing the JavaScript logic to connect the UI to the backend API endpoints. The profile template is located at `notes/templates/notes/profile.html` and already contains a basic JavaScript structure that you can enhance or replace with your implementation.

---

V. Backend Enhancements (Future Implementation - Not for Current Development)
Description: Vincent B. Pacaña implemented comprehensive backend enhancements beyond the original Phase 2 & 3 requirements, transforming the basic blockchain integration into a production-ready system with enterprise-grade features.

**IMPORTANT NOTE: These enhancements are for future implementation only and should NOT be coded for now. The frontend team (Luis Miguel A. Jaca and Rainric Randy P. Yu) should focus exclusively on the currently assigned frontend work for Phases 2 & 3. No frontend adjustments or additional UI components should be implemented based on these backend enhancements at this time. Vincent will implement this in the future**

1. Transaction History System:
Task: Implement complete transaction tracking and history functionality.
Features:
- Transaction model with comprehensive fields (status, amounts, timestamps, error tracking)
- Database migration with optimized indexes for performance
- Transaction History API (`GET /api/transaction-history/`) with pagination and filtering
- Background status updates via Django management command (`update_transaction_status`)
- Status tracking: pending → submitted → confirmed → failed

2. User Wallet Dashboard API:
Task: Create comprehensive wallet dashboard with real-time data and analytics.
Features:
- Dashboard endpoint (`GET /api/wallet-dashboard/`) with wallet overview
- Real-time ADA balance integration via Blockfrost API
- Transaction statistics and analytics (volume, frequency, spending patterns)
- Optimized database queries with aggregation for performance
- Wallet health indicators and transaction summaries

3. API Documentation & Schema:
Task: Implement professional API documentation for better frontend integration.
Features:
- OpenAPI schema with drf-spectacular library
- Interactive documentation at `/api/docs/` (Swagger UI) and `/api/redoc/`
- Complete API definitions with authentication and security schemes
- Professional developer experience with testing capabilities

4. Advanced Error Handling & Logging:
Task: Implement production-ready error handling and monitoring systems.
Features:
- Custom blockchain exception classes with error codes
- Retry logic with exponential backoff for API failures
- Circuit breaker pattern to prevent cascade failures
- Structured logging for all blockchain operations and audit trails
- Enhanced error responses with user-friendly messages

5. Performance Optimizations:
Task: Optimize system performance and scalability.
Features:
- Strategic database indexes for query optimization
- Django built-in caching for Blockfrost API responses
- Background job processing via Django management commands
- Query optimization with select_related and aggregation
- Efficient API response payloads and data serialization

Enhancement Implementation Status: Vincent B. Pacaña has completed all 16 enhancement tasks, achieving a perfect 100/100 rubric score. The backend now features enterprise-grade architecture with comprehensive transaction management, professional documentation, advanced error handling, performance optimizations, and automated background processing. These features are implemented and available for future use, but frontend development should focus on the original Phase 2 & 3 requirements only.

**Frontend Development Guidelines:**
- **Luis Miguel A. Jaca (UI/UX)**: ✅ **COMPLETE** - All UI elements for Phase 2 and Phase 3 have been implemented. No dashboard components, transaction history tables, or analytics interfaces were added (as per guidelines).
- **Rainric Randy P. Yu (Frontend Logic)**: ⏳ **IN PROGRESS** - Implement only the JavaScript functionality for wallet connection and basic transaction flow as specified. The UI elements are ready with the correct IDs. Do not add dashboard data fetching, transaction history pagination, or enhanced error handling beyond basic requirements.
- **Focus**: Complete the assigned Phase 2 & 3 frontend JavaScript work before considering any enhancement features.
