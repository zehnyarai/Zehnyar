/**
 * Grants or revokes the admin role for an existing user (bootstrap for the first admin).
 * Usage: npm run admin:promote -- 09123456789 [--revoke]
 */
import { loadEnv } from '../src/config/env.js';
import { createPool } from '../src/db/pool.js';
import { migrate } from '../src/db/migrate.js';
import { normalizeIranianMobile } from '../src/lib/phone.js';

const args = process.argv.slice(2);
const revoke = args.includes('--revoke');
const rawPhone = args.find((a) => !a.startsWith('--'));
if (!rawPhone) {
  console.error('Usage: npm run admin:promote -- <phone> [--revoke]');
  process.exit(1);
}

const env = loadEnv();
const db = createPool(env);
try {
  await migrate(db);
  const phone = normalizeIranianMobile(rawPhone);
  if (!phone) {
    console.error('Invalid phone number.');
    process.exit(1);
  }
  const res = await db.query<{ id: string; role: string }>(
    'UPDATE users SET role = $2, updated_at = now() WHERE phone = $1 RETURNING id, role',
    [phone, revoke ? 'farmer' : 'admin'],
  );
  if (!res.rows[0]) {
    console.error('No user with this phone. The user must log in once first.');
    process.exitCode = 1;
  } else {
    await db.query(
      'INSERT INTO admin_audit_logs (actor_id, action, target, details) VALUES (NULL, $1, $2, $3)',
      [revoke ? 'role.revoke_admin' : 'role.grant_admin', `user:${res.rows[0].id}`, JSON.stringify({ via: 'cli' })],
    );
    console.log(`Role updated: ${res.rows[0].role}`);
  }
} finally {
  await db.end();
}
