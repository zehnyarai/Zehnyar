import { randomUUID } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { AppError } from './errors.js';

export type ImageMime = 'image/jpeg' | 'image/png' | 'image/webp';

/** Detects the real image type from magic bytes. Client-supplied MIME types are ignored. */
export function detectImageMime(buf: Buffer): ImageMime | null {
  if (buf.length >= 3 && buf[0] === 0xff && buf[1] === 0xd8 && buf[2] === 0xff) return 'image/jpeg';
  if (buf.length >= 8 && buf.subarray(0, 8).equals(Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]))) {
    return 'image/png';
  }
  if (buf.length >= 12 && buf.subarray(0, 4).toString('ascii') === 'RIFF' && buf.subarray(8, 12).toString('ascii') === 'WEBP') {
    return 'image/webp';
  }
  return null;
}

const EXT: Record<ImageMime, string> = { 'image/jpeg': 'jpg', 'image/png': 'png', 'image/webp': 'webp' };

/**
 * Private file storage on the local disk (not served statically).
 * Production deployments can swap this for S3-compatible object storage with
 * the same interface (see docs/DEPLOYMENT.md).
 */
export class LocalImageStorage {
  constructor(private readonly root: string) {}

  async save(userId: string, buf: Buffer, mime: ImageMime): Promise<string> {
    const key = `${userId}/${randomUUID()}.${EXT[mime]}`;
    const full = this.resolve(key);
    await mkdir(path.dirname(full), { recursive: true });
    await writeFile(full, buf, { mode: 0o600 });
    return key;
  }

  async read(key: string): Promise<Buffer> {
    try {
      return await readFile(this.resolve(key));
    } catch {
      throw AppError.notFound('IMAGE_MISSING', 'Image file is missing');
    }
  }

  /** Prevents path traversal: the resolved path must stay inside the storage root. */
  private resolve(key: string): string {
    const full = path.resolve(this.root, key);
    if (!full.startsWith(path.resolve(this.root) + path.sep)) {
      throw new Error('Invalid storage key');
    }
    return full;
  }
}
