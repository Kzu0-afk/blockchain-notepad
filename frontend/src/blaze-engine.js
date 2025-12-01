import { Blaze, Core, WebWallet, Blockfrost } from "@blaze-cardano/sdk";
import { U5C } from "@utxorpc/blaze-provider";

let blaze = null;
let provider = null;

/**
 * Initialize the provider.
 * Defaults to Blockfrost for reliability.
 * Can optionally use U5C if configured.
 */
export async function initProvider() {
    if (provider) return provider;

    const apiKey = window.BLOCKFROST_API_KEY;
    // You can switch this via env var or config if needed
    const useU5C = false; // Set to true only if you have a robust U5C endpoint

    if (useU5C) {
        console.log("🔥 Initializing U5C Provider (Advanced Mode)...");
        // Note: U5C provider must fully implement protocol parameters
        provider = new U5C({
            url: "https://rpc.demeter.run/preview",
            headers: { project_id: apiKey },
        });
    } else {
        console.log("🔥 Initializing Blockfrost Provider (Standard Mode)...");
        if (!apiKey) throw new Error("Missing Blockfrost API Key");
        
        provider = new Blockfrost({
            network: "cardano-preview",
            projectId: apiKey,
        });
    }

    return provider;
}

export async function setWallet(walletApi) {
    try {
        if (!provider) await initProvider();

        console.log("🔥 Setting wallet...");

        // Use the standard WebWallet wrapper from Blaze SDK
        // This avoids manual shims and ensures better compatibility
        const wallet = new WebWallet(walletApi);

        // Initialize Blaze with the selected provider and wallet
        blaze = await Blaze.from(provider, wallet);

        console.log("🔥 Blaze initialized successfully");
        return blaze;
    } catch (error) {
        console.error("❌ Failed to initialize Blaze:", error);
        throw error;
    }
}

export async function sendAda(recipient, lovelace) {
    if (!blaze) throw new Error("Wallet not initialized");

    console.log(`🔥 Preparing transaction: ${lovelace} lovelace to ${recipient}`);

    try {
        const tx = await blaze
            .newTransaction()
            .payLovelace(Core.Address.fromBech32(recipient), BigInt(lovelace))
            .complete();

        const signed = await blaze.signTransaction(tx);
        const txId = await blaze.provider.postTransactionToChain(signed);

        console.log("🔥 Transaction submitted:", txId);
        return txId;
    } catch (error) {
        console.error("❌ Transaction failed:", error);
        // Known limitation: Blockfrost propogation might be slightly delayed
        throw error;
    }
}