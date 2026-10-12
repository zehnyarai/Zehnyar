/**
 * Grants or revokes the admin role for an existing user (bootstrap for the first admin).
 *
 * Grant (the admin password comes from the environment, never from the command line):
 *   ADMIN_PASSWORD='...' npm run admin:promote -- 09XXXXXXXXX
 * Revoke:
 *   npm run admin:promote -- 09XXXXXXXXX --revoke
 *
 * The user must have logged in with OTP at least once. Admins sign in with a password only,
 * so granting admin without a valid password is refused.
 */
import { loadEnv } from '../src/config/env.js';
import { createPool } from '../src/db/pool.js';
import { migrate } from '../src/db/migrate.js';
import { normalizeIranianMobile } from '../src/lib/phone.js';
import { hashPassword } from '../src/lib/password.js';
import { adminPasswordProblem } from '../src/lib/password-policy.js';

const args = process.argv.slice(2);
const revoke = args.includes('--revoke');
const rawPhone = args.find((a) => !a.startsWith('--'));
if (!rawPhone) {
  console.error('Usage: npm run admin:promote -- <phone> [--revoke]   (set ADMIN_PASSWORD when granting)');
  process.exit(1);
}
const phone = normalizeIranianMobile(rawPhone);
if (!phone) {
  console.error('Invalid phone number.');
  process.exit(1);
}

const password = process.env.ADMIN_PASSWORD ?? '';
if (!revoke) {
  const problem = adminPasswordProblem(password);
  if (problem) {
    console.error(`ADMIN_PASSWORD is required and must have ${problem}.`);
    process.exit(1);
  }
}

const env = loadEnv();
const db = createPool(env);
try {
  await migrate(db);
  const hash = revoke ? null : await hashPassword(password);
  const res = await db.query<{ id: string; role: string }>(
    `UPDATE users
        SET role = $2::varchar,
            password_hash = CASE WHEN $2::varchar = 'admin' THEN $3::varchar ELSE password_hash END,
            password_changed_at = CASE WHEN $2::varchar = 'admin' THEN now() ELSE password_changed_at END,
            password_failed_count = 0,
            password_locked_until = NULL,
            updated_at = now()
      WHERE phone = $1
      RETURNING id, role`,
    [phone, revoke ? 'farmer' : 'admin', hash],
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
