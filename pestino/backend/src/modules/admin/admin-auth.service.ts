import type { Db } from '../../db/pool.js';
import { AppError } from '../../lib/errors.js';
import { logger } from '../../lib/logger.js';
import { normalizeIranianMobile } from '../../lib/phone.js';
import { verifyPassword } from '../../lib/password.js';
import type { AuthService } from '../auth/auth.service.js';

export const ADMIN_MAX_FAILED_LOGINS = 5;
export const ADMIN_LOCK_MINUTES = 15;

/**
 * Password login for admin accounts only (separate from the farmer OTP flow).
 * - One generic error for every failure, so the response does not reveal which phone numbers are admins.
 * - Account lockout after repeated wrong passwords; the counter resets on success.
 * - Every attempt is written to the admin audit log (never the password).
 */
export class AdminAuthService {
  constructor(private readonly deps: { db: Db; auth: AuthService }) {}

  async login(rawPhone: string, password: string, meta: { userAgent?: string; ip?: string }) {
    const { db, auth } = this.deps;
    const invalid = () => AppError.unauthorized('INVALID_CREDENTIALS', 'Phone number or password is incorrect');

    const phone = normalizeIranianMobile(rawPhone);
    const res = phone
      ? await db.query<{
          id: string;
          role: string;
          is_active: boolean;
          password_hash: string | null;
          password_failed_count: number;
          password_locked_until: Date | null;
        }>(
          `SELECT id, role, is_active, password_hash, password_failed_count, password_locked_until
             FROM users WHERE phone = $1`,
          [phone],
        )
      : { rows: [] };
    const user = res.rows[0];

    if (!user || user.role !== 'admin' || !user.is_active || !user.password_hash) {
      // Spend the same time as a real check, then return the same error.
      await verifyPassword(password, null);
      throw invalid();
    }

    if (user.password_locked_until && user.password_locked_until.getTime() > Date.now()) {
      await this.audit(user.id, 'admin.login_locked', meta);
      throw AppError.tooMany('ACCOUNT_LOCKED', 'Too many failed attempts. Try again later.');
    }

    const ok = await verifyPassword(password, user.password_hash);
    if (!ok) {
      const failures = user.password_failed_count + 1;
      const lock = failures >= ADMIN_MAX_FAILED_LOGINS;
      await db.query(
        `UPDATE users SET password_failed_count = $2,
                password_locked_until = CASE WHEN $3::boolean THEN now() + ($4 || ' minutes')::interval ELSE NULL END,
                updated_at = now()
          WHERE id = $1`,
        [user.id, lock ? 0 : failures, lock, String(ADMIN_LOCK_MINUTES)],
      );
      await this.audit(user.id, lock ? 'admin.login_locked' : 'admin.login_failed', meta);
      throw invalid();
    }

    await db.query(
      `UPDATE users SET password_failed_count = 0, password_locked_until = NULL, last_login_at = now(), updated_at = now()
        WHERE id = $1`,
      [user.id],
    );
    const session = await auth.createSession(user.id, meta);
    await this.audit(user.id, 'admin.login', meta);
    logger.info('admin logged in', { adminId: user.id });
    return session;
  }

  private async audit(actorId: string, action: string, meta: { ip?: string; userAgent?: string }) {
    await this.deps.db.query(
      'INSERT INTO admin_audit_logs (actor_id, action, target, details) VALUES ($1,$2,$3,$4)',
      [actorId, action, `user:${actorId}`, JSON.stringify({ ip: meta.ip ?? null, userAgent: meta.userAgent?.slice(0, 120) ?? null })],
    );
  }
}
