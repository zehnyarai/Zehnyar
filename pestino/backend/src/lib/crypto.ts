import { createHash, createHmac, randomBytes, randomInt, timingSafeEqual } from 'node:crypto';

/** Random opaque token (URL-safe), used for refresh tokens. */
export function randomToken(bytes = 48): string {
  return randomBytes(bytes).toString('base64url');
}

/** SHA-256 hex digest – used for storing refresh tokens & file checksums. */
export function sha256(input: string | Buffer): string {
  return createHash('sha256').update(input).digest('hex');
}

/** Keyed hash (HMAC-SHA256). Protects low-entropy values such as OTP codes. */
export function hmac(secret: string, value: string): string {
  return createHmac('sha256', secret).update(value).digest('hex');
}

/** Constant-time comparison of two hex/base64 strings of any length. */
export function safeEqual(a: string, b: string): boolean {
  const ba = Buffer.from(a);
  const bb = Buffer.from(b);
  if (ba.length !== bb.length) return false;
  return timingSafeEqual(ba, bb);
}

/** Cryptographically secure 6-digit numeric OTP. */
export function generateOtpCode(): string {
  return randomInt(0, 1_000_000).toString().padStart(6, '0');
}
