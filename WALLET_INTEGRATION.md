Project Plan: Cardano Wallet Integration
1. Project Goal
The primary objective is to integrate Cardano wallet functionality into our Django Note App. This will enable users to connect their wallet, and then use that connection to build, sign, and submit a live transaction to the Cardano Preview Testnet.
2. Core Technologies & Tools
This is the official toolkit for our project. Everyone should be familiar with what each tool does.
Lace Wallet: The primary Cardano wallet we will use for testing. Any CIP-30 compatible wallet should work.
CIP-30 Standard (cardano-caniuse.io): This is our JavaScript API Reference Guide. We will use this website to look up the exact functions available in the window.cardano object (e.g., .enable(), .getChangeAddress(), .signTx()). We are not "calling" caniuse.io; we are using it as documentation.
Blockfrost.io: This is our main backend service. It provides the API that our Python server will use to communicate with the Cardano blockchain. We will use it to get blockchain data (like wallet UTXOs) and to submit our final, signed transactions. The API key for Blockfrost must be kept secret on the backend.
Blaze Provider/SDK (Reference Only): The initial example code used this high-level JavaScript library. We will not use the SDK directly. Instead, we are implementing its logical flow by splitting the responsibilities between our frontend JavaScript and our backend Python.
Cardano Scan (Preview): This is our final verifier. It's a block explorer where we will paste our transaction hash to get visual confirmation that our transaction was successfully posted to the blockchain.
CBOR Playground: A debugging tool. If we encounter errors with our transaction structure, we can use this to inspect the raw CBOR data and diagnose the problem.
3. High-Level Workflow (Client-Server Architecture)
This diagram shows how our frontend and backend will communicate.