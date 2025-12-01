import { setWallet, sendAda } from "./blaze-engine.js";
import { Core } from "@blaze-cardano/sdk";

console.log("🔥 Wallet Connection Script Loaded");

let walletApi = null;

function detectWallets() {
    if (!window.cardano) return [];
    return ["lace", "eternl", "nami", "flint", "typhon", "gero"]
        .filter(name => window.cardano[name])
        .map(name => ({ name }));
}

function updateWalletUI() {
    const select = document.getElementById("wallet-select");
    if (!select) return;

    const wallets = detectWallets();
    select.innerHTML = '<option value="">Select wallet...</option>';
    wallets.forEach(w => {
        const opt = document.createElement("option");
        opt.value = w.name;
        opt.textContent = w.name.toUpperCase();
        select.appendChild(opt);
    });
    if (wallets.some(w => w.name === "lace")) select.value = "lace";
}

export async function connectWallet(name) {
    console.log("🔥 connectWallet called with:", name);

    // Make select visible to the whole function scope
    const select = document.getElementById("wallet-select");

    if (!name) {
        const selected = select ? select.value : null;
        name = selected;
        console.log("🔥 No name provided, got from select:", name);
    }

    if (!name) {
        console.warn("❌ No wallet selected");
        alert("Please select a wallet first!");
        return;
    }

    if (!window.cardano) {
        console.warn("❌ No cardano object found");
        alert("Cardano wallet extension not detected!");
        return;
    }

    if (!window.cardano[name]) {
        console.warn(`❌ Wallet ${name} not found in window.cardano:`, Object.keys(window.cardano));
        alert(`${name.toUpperCase()} wallet is not installed!`);
        return;
    }

    try {
        const wallet = window.cardano[name];
        walletApi = await wallet.enable();
        await setWallet(walletApi);

        const walletStatus = document.getElementById("wallet-status");
        if (walletStatus) {
            walletStatus.innerHTML = `
                <strong>✅ ${name.toUpperCase()} Wallet Connected</strong><br>
                <small>Ready to send ADA</small>
            `;
        }

        // Hide connect button and selector
        const connectBtn = document.getElementById("connectWalletBtn");
        if (connectBtn) connectBtn.style.display = 'none';
        if (select) select.style.display = 'none';

        // Save wallet address to backend
        const hexAddress = await walletApi.getChangeAddress();
        console.log("🔥 Raw wallet address:", hexAddress);

        // Convert hex-encoded CBOR address to Bech32 format (backend expects Bech32)
        let bech32Address;
        try {
            // Check if already Bech32 (starts with 'addr')
            if (hexAddress.startsWith('addr')) {
                bech32Address = hexAddress;
                console.log("🔥 Address already in Bech32 format");
            } else {
                // Convert hex to Bech32
                bech32Address = Core.Address.fromBytes(Buffer.from(hexAddress, 'hex')).toBech32();
                console.log("🔥 Converted to Bech32:", bech32Address);
            }
        } catch (error) {
            console.error("❌ Failed to convert address to Bech32:", error);
            // If conversion fails but address looks like Bech32, use it as-is
            if (hexAddress.startsWith('addr')) {
                bech32Address = hexAddress;
                console.log("🔥 Using address as-is (appears to be Bech32)");
            } else {
                throw new Error(`Invalid address format: ${hexAddress.substring(0, 20)}...`);
            }
        }

        await saveWalletAddress(bech32Address);

        console.log(`✅ ${name} wallet connected successfully`);
    } catch (error) {
        console.error(`❌ ${name} wallet connection error:`, error);
        alert(`Wallet connection failed: ${error.message}`);
    }
}

async function saveWalletAddress(address) {
    try {
        const response = await fetch("/api/save-wallet/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCSRFToken()
            },
            body: JSON.stringify({ wallet_address: address })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to save wallet address');
        }

        const data = await response.json();
        console.log("✅ Wallet address saved:", data);
    } catch (err) {
        console.error("Failed to save wallet:", err);
    }
}

export async function handleTransaction(event) {
    event.preventDefault();

    if (!walletApi) {
        alert("Please connect your wallet first!");
        return;
    }

    const address = document.getElementById("recipient").value.trim();
    const amount = document.getElementById("amount").value.trim();

    if (!address || !amount) {
        alert("Recipient and amount are required");
        return;
    }

    const submitBtn = event.target.querySelector('button[type="submit"]');
    const originalText = submitBtn ? submitBtn.textContent : 'Submit';

    try {
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.textContent = 'Processing...';
        }

        const txHash = await sendAda(address, parseInt(amount));

        // Log to Django backend
        await fetch("/api/log-transaction/", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCSRFToken()
            },
            body: JSON.stringify({
                tx_hash: txHash,
                recipient_address: address,
                amount_lovelace: parseInt(amount)
            })
        });

        // Display success
        const txHashDisplay = document.getElementById("tx-hash-display");
        if (txHashDisplay) {
            txHashDisplay.style.display = 'block';
            txHashDisplay.className = 'success-message';
            txHashDisplay.innerHTML = `
                <strong>Transaction Submitted Successfully! 🎉</strong><br>
                <strong>Transaction Hash:</strong><br>
                <a href="https://preview.cardanoscan.io/transaction/${txHash}" target="_blank" rel="noopener">
                    ${txHash}
                </a><br>
                <small>Click the hash to view on CardanoScan</small>
            `;
        }

        alert("TX Submitted: " + txHash);
    } catch (err) {
        console.error("Transaction error:", err);
        alert("Transaction failed:\n" + err.message);

        const txHashDisplay = document.getElementById("tx-hash-display");
        if (txHashDisplay) {
            txHashDisplay.style.display = 'block';
            txHashDisplay.className = 'error-message';
            txHashDisplay.innerHTML = `
                <strong>Transaction Failed ❌</strong><br>
                ${err.message}
            `;
        }
    } finally {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    }
}

function getCSRFToken() {
    return document.cookie
        .split("; ")
        .find(row => row.startsWith("csrftoken="))
        ?.split("=")[1] || "";
}

document.addEventListener("DOMContentLoaded", () => {
    console.log("🔥 Wallet Connection DOM loaded, initializing...");

    updateWalletUI();

    const connectBtn = document.getElementById("connectWalletBtn");
    if (connectBtn) {
        console.log("🔥 Found connect button, adding event listener");
        connectBtn.addEventListener("click", () => {
            const select = document.getElementById("wallet-select");
            const walletName = select ? select.value : null;
            console.log("🔥 Connect button clicked, wallet:", walletName);
            connectWallet(walletName);
        });
    } else {
        console.warn("❌ Connect button not found");
    }

    const walletSelect = document.getElementById("wallet-select");
    if (walletSelect) {
        walletSelect.addEventListener("change", (e) => {
            if (e.target.value) {
                connectWallet(e.target.value);
            }
        });
    }

    const sendTxForm = document.getElementById("sendTxForm");
    if (sendTxForm) {
        sendTxForm.addEventListener("submit", handleTransaction);
    }
});

