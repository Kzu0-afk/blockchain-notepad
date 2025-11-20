Comprehensive Project Plan: Cardano Wallet Integration

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
Python Libraries:
blockfrost-python: For easy communication with the Blockfrost API.
pycardano: For building and manipulating Cardano data structures like transactions.
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

I. Phase 1: Project Setup & Prerequisites
Description: To ensure every team member has the necessary tools, accounts, and a foundational understanding of the technologies we will use. This phase must be completed before any coding begins.
1. MJ (Project Lead):
Task: Initialize the project's environment for secure API key management.
Create the .env file in the project's root directory.
Add the line BLOCKFROST_PROJECT_ID='YOUR_KEY_HERE' to the .env file.
Verify that the .env file is listed in .gitignore to prevent committing secret keys.
All Team Members (Vincent, Luis, Rainric):
Task: Set up individual development environments.
Install the Lace wallet browser extension.
Create a personal project on Blockfrost.io and select the Preview Testnet.
Acquire test ADA from the official Cardano Testnet Faucet to fund your Lace wallet on the Preview network.
Provide your Blockfrost Project ID to MJ for the central .env file.

II. Phase 2: Wallet Connection Functionality
Description: To implement the initial user feature: connecting their Lace wallet to their account in our application and saving their wallet address to the database.

1. Luis Miguel A. Jaca (UI/UX):
Git Branch: feature/ui/wallet-connection
Task: Create the necessary frontend user interface elements.
In the user profile template, add a <button> with the ID connect-wallet-btn and text "Connect Wallet".
Add a <div> with the ID wallet-address-display to show the user's connected address. It should initially display "Status: Not Connected".

2. Vincent B. Pacaña (Backend API Scaffolding):
Git Branch: feature/api/save-wallet-endpoint
Task: Prepare the backend to store wallet data.
Model: Modify the User/Profile model by adding a new field: wallet_address = models.CharField(max_length=103, unique=True, null=True, blank=True).
Database: Run the commands python manage.py makemigrations and python manage.py migrate.
API Endpoint: Create the URL and an empty, login-protected view function for a POST request at /api/save-wallet/.

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

1. Luis Miguel A. Jaca (UI/UX):
Git Branch: feature/ui/transaction-form
Task: Create the user interface for sending ADA.
Create an HTML <form> with the ID transaction-form.
Inside the form, add an <input> for "Recipient Address" (ID: recipient-address-input).
Add another <input type="number"> for "Amount (Lovelace)" (ID: amount-input).
Add a <button type="submit"> with the text "Build & Sign Transaction".
Create a <div> with the ID tx-hash-display to show the final transaction hash and a link to Cardano Scan.

2. Vincent B. Pacaña (Backend API Scaffolding):
Git Branch: feature/api/transaction-endpoints
Task: Create the backend API endpoint structures for transaction processing.
URL: Define a path for a POST request at /api/build-transaction/.
URL: Define a path for a POST request at /api/submit-transaction/.
Views: Create the corresponding empty, login-protected view functions for both URLs in views.py.

3. Rainric Randy P. Yu (Frontend Logic):
Git Branch: feature/js/sign-submit-script
Task: Implement the client-side JavaScript for the transaction lifecycle.
Write a JavaScript event listener for the #transaction-form submission.
Build Step: Prevent default form submission, then fetch the /api/build-transaction/ endpoint, sending the recipient and amount. Await the response containing the unsigned transaction CBOR.
Sign Step: Use the wallet's api.signTx(unsignedTxCbor, true) function to prompt the user to sign.
Submit Step: fetch the /api/submit-transaction/ endpoint, sending the signed transaction CBOR from the previous step.
Display Step: On a successful response, display the final transaction hash in the #tx-hash-display div, formatted as a clickable link to https://preview.cardanoscan.io/transaction/THE_HASH.

4. MJ (Backend Logic):
Git Branch: feature/backend/transaction-logic
Task: Implement the secure, server-side transaction processing logic.
Install Libraries: pip install blockfrost-python pycardano.
Implement build_transaction View:
Read the BLOCKFROST_PROJECT_ID from settings.
Use blockfrost-python to get the UTXOs for the logged-in user's wallet_address.
Use pycardano to construct the transaction body.
Return the transaction's CBOR representation in the JSON response.
Implement submit_transaction View:
Receive the signed transaction CBOR from the request.
Use blockfrost-python's submit_tx function to send it to the Cardano network.
Return the transaction hash from the Blockfrost response.

IV. Phase 4: Final Integration & Testing
Description: The final phase where all completed components are merged, tested together, and the project is finalized for presentation.

1. MJ (Project Lead):
Task: Oversee the final integration and verification.
Code Review: Review all pull requests from team members, ensuring code quality and adherence to the plan.
Merge: Merge all approved feature branches into the main branch.
End-to-End Testing: Perform a full user workflow: Register -> Login -> Connect Wallet -> Send ADA.
Verification: Use Cardano Scan (Preview) to confirm the test transaction is visible and successful on the blockchain.
Debugging: If necessary, use the CBOR Playground to analyze any problematic transaction data and statuses.