import { existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

/**
 * Returns the backend root (the directory containing package.json), regardless of
 * whether code runs from src/ (tsx) or dist/src/ (compiled).
 */
export function backendRoot(): string {
  let dir = path.dirname(fileURLToPath(import.meta.url));
  for (let i = 0; i < 6; i++) {
    if (existsSync(path.join(dir, 'package.json'))) return dir;
    dir = path.dirname(dir);
  }
  throw new Error('Could not locate backend root (package.json)');
}
