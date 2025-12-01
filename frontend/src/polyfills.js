// Polyfills for Node.js globals required by Blaze SDK
import { Buffer } from 'buffer';

// Make Buffer available globally (required by Cardano libraries)
if (typeof window !== 'undefined') {
  window.Buffer = Buffer;
}

if (typeof globalThis !== 'undefined') {
  globalThis.Buffer = Buffer;
}

// Ensure global is available
if (typeof global === 'undefined') {
  window.global = window;
}
