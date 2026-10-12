import { createCipheriv, createDecipheriv, hkdfSync, randomBytes } from 'node:crypto';

/**
 * Authenticated encryption for secrets stored in the database (e.g. the Gemini API key).
 * AES-256-GCM with a key derived from a high-entropy master secret via HKDF-SHA256.
 * Format: `v1:<iv>:<authTag>:<ciphertext>` (base64url segments).
 */

const VERSION = 'v1';

function deriveKey(masterSecret: string): Buffer {
  return Buffer.from(hkdfSync('sha256', masterSecret, 'pestino-secretbox', 'aes-256-gcm-key', 32));
}

export function encryptSecret(plaintext: string, masterSecret: string): string {
  const key = deriveKey(masterSecret);
  const iv = randomBytes(12);
  const cipher = createCipheriv('aes-256-gcm', key, iv);
  const ciphertext = Buffer.concat([cipher.update(plaintext, 'utf8'), cipher.final()]);
  const tag = cipher.getAuthTag();
  return [VERSION, iv.toString('base64url'), tag.toString('base64url'), ciphertext.toString('base64url')].join(':');
}

/** Throws if the master secret is wrong or the payload was tampered with. */
export function decryptSecret(payload: string, masterSecret: string): string {
  const [version, ivB64, tagB64, dataB64] = payload.split(':');
  if (version !== VERSION || !ivB64 || !tagB64 || !dataB64) {
    throw new Error('Unsupported secret format');
  }
  const decipher = createDecipheriv('aes-256-gcm', deriveKey(masterSecret), Buffer.from(ivB64, 'base64url'));
  decipher.setAuthTag(Buffer.from(tagB64, 'base64url'));
  const plain = Buffer.concat([decipher.update(Buffer.from(dataB64, 'base64url')), decipher.final()]);
  return plain.toString('utf8');
}
