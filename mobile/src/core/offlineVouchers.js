import nacl from 'tweetnacl';

// Public half of the owner-held Ed25519 signing key. The private half is never
// bundled; it is kept in the owner's offline voucher-issuing tool.
export const OFFLINE_VOUCHER_PUBLIC_KEY = 'ZBvGernwDX5VRYQMXZGyZjzxgQhlXGn_RO8dRLvr5HY=';

const BASE64_ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/';

function decodeBase64Url(value) {
  const input = String(value).replace(/-/g, '+').replace(/_/g, '/').replace(/=+$/g, '');
  const output = [];
  let buffer = 0;
  let bits = 0;
  for (const character of input) {
    const digit = BASE64_ALPHABET.indexOf(character);
    if (digit < 0) throw new Error('INVALID_VOUCHER');
    buffer = (buffer << 6) | digit;
    bits += 6;
    if (bits >= 8) {
      bits -= 8;
      output.push((buffer >> bits) & 0xff);
    }
  }
  return new Uint8Array(output);
}

function decodeUtf8(bytes) {
  const encoded = Array.from(bytes, (byte) => `%${byte.toString(16).padStart(2, '0')}`).join('');
  return decodeURIComponent(encoded);
}

export function verifyOfflineVoucher(code, expectedInstallId, publicKey = OFFLINE_VOUCHER_PUBLIC_KEY) {
  const parts = String(code || '').trim().split('.');
  if (parts.length !== 2) throw new Error('INVALID_VOUCHER');
  let message;
  let signature;
  let publicKeyBytes;
  let payload;
  try {
    message = decodeBase64Url(parts[0]);
    signature = decodeBase64Url(parts[1]);
    publicKeyBytes = decodeBase64Url(publicKey);
    if (publicKeyBytes.length !== nacl.sign.publicKeyLength || signature.length !== nacl.sign.signatureLength) {
      throw new Error('INVALID_VOUCHER');
    }
    if (!nacl.sign.detached.verify(message, signature, publicKeyBytes)) throw new Error('INVALID_VOUCHER');
    payload = JSON.parse(decodeUtf8(message));
  } catch (error) {
    if (error?.message === 'INVALID_VOUCHER') throw error;
    throw new Error('INVALID_VOUCHER');
  }
  if (payload?.v !== 1 || !payload.id || !payload.installId || !Number.isInteger(payload.credits)) {
    throw new Error('INVALID_VOUCHER');
  }
  if (payload.installId.toLowerCase() !== String(expectedInstallId).toLowerCase()) {
    throw new Error('VOUCHER_FOR_ANOTHER_INSTALL');
  }
  if (![1, 3, 6, 12].includes(payload.credits)) throw new Error('INVALID_VOUCHER');
  return payload;
}
