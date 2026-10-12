import { randomBytes, scrypt as scryptCb, timingSafeEqual, type ScryptOptions } from 'node:crypto';

/**
 * Password hashing with scrypt (memory-hard, built into Node; no native dependency).
 * Stored format: `scrypt$N$r$p$<saltB64url>$<hashB64url>`.
 */

const PARAMS = { N: 2 ** 15, r: 8, p: 1, keylen: 32, maxmem: 64 * 1024 * 1024 };
export const ADMIN_MIN_PASSWORD_LENGTH = 12;

function deriveKey(password: string, salt: Buffer, N: number, r: number, p: number, keylen: number): Promise<Buffer> {
  const options: ScryptOptions = { N, r, p, maxmem: PARAMS.maxmem };
  return new Promise((resolve, reject) => {
    scryptCb(password, salt, keylen, options, (err, key) => (err ? reject(err) : resolve(key)));
  });
}

export async function hashPassword(password: string): Promise<string> {
  const salt = randomBytes(16);
  const key = await deriveKey(password, salt, PARAMS.N, PARAMS.r, PARAMS.p, PARAMS.keylen);
  return ['scrypt', PARAMS.N, PARAMS.r, PARAMS.p, salt.toString('base64url'), key.toString('base64url')].join('$');
}

export async function verifyPassword(password: string, stored: string | null | undefined): Promise<boolean> {
  const parts = (stored ?? '').split('$');
  if (parts.length !== 6 || parts[0] !== 'scrypt') {
    // Still spend the same time so the response does not reveal whether an account exists.
    await deriveKey(password, Buffer.alloc(16), PARAMS.N, PARAMS.r, PARAMS.p, PARAMS.keylen);
    return false;
  }
  const [, n, r, p, saltB64, hashB64] = parts;
  const expected = Buffer.from(hashB64, 'base64url');
  const actual = await deriveKey(password, Buffer.from(saltB64, 'base64url'), Number(n), Number(r), Number(p), expected.length);
  return actual.length === expected.length && timingSafeEqual(actual, expected);
}
