import { randomUUID } from 'node:crypto';
import type { Env } from '../../config/env.js';
import type { Db } from '../../db/pool.js';
import { withTransaction } from '../../db/pool.js';
import { AppError } from '../../lib/errors.js';
import { generateOtpCode, hmac, randomToken, safeEqual, sha256 } from '../../lib/crypto.js';
import { normalizeIranianMobile } from '../../lib/phone.js';
import { logger } from '../../lib/logger.js';
import type { SmsSender } from '../../lib/sms.js';
import { signAccessToken } from './tokens.js';
import { toPublicUser, type PublicUser, type UserRow } from '../users/user.mapper.js';

export interface TokenPair {
  accessToken: string;
  accessTokenExpiresIn: number;
  refreshToken: string;
  refreshTokenExpiresIn: number;
}

export interface AuthDeps {
  db: Db;
  env: Pick<
    Env,
    | 'JWT_ACCESS_SECRET'
    | 'OTP_HMAC_SECRET'
    | 'ACCESS_TOKEN_TTL_SECONDS'
    | 'REFRESH_TOKEN_TTL_DAYS'
    | 'OTP_TTL_SECONDS'
    | 'OTP_MAX_ATTEMPTS'
    | 'OTP_DEV_ECHO'
  >;
  sms: SmsSender;
  now?: () => Date;
}

const OTP_RESEND_COOLDOWN_SECONDS = 60;
const OTP_MAX_REQUESTS_PER_HOUR = 5;

export class AuthService {
  constructor(private readonly deps: AuthDeps) {}

  private now(): Date {
    return this.deps.now ? this.deps.now() : new Date();
  }

  /** Step 1: send a one-time code to the phone number. */
  async requestOtp(rawPhone: string): Promise<{ expiresIn: number; devCode?: string }> {
    const phone = normalizeIranianMobile(rawPhone);
    if (!phone) throw AppError.badRequest('INVALID_PHONE', 'Phone number is not a valid Iranian mobile number');

    const { db, env } = this.deps;

    const recent = await db.query<{ created_at: Date; cnt: string }>(
      `SELECT max(created_at) AS created_at,
              count(*) FILTER (WHERE created_at > now() - interval '1 hour') AS cnt
         FROM otp_codes WHERE phone = $1`,
      [phone],
    );
    const last = recent.rows[0]?.created_at;
    if (last && this.now().getTime() - new Date(last).getTime() < OTP_RESEND_COOLDOWN_SECONDS * 1000) {
      throw AppError.tooMany('OTP_COOLDOWN', 'Please wait a minute before requesting a new code');
    }
    if (Number(recent.rows[0]?.cnt ?? 0) >= OTP_MAX_REQUESTS_PER_HOUR) {
      throw AppError.tooMany('OTP_HOURLY_LIMIT', 'Too many verification codes requested for this number');
    }

    const code = generateOtpCode();
    const expiresAt = new Date(this.now().getTime() + env.OTP_TTL_SECONDS * 1000);
    await db.query(
      `INSERT INTO otp_codes (phone, code_hash, expires_at) VALUES ($1, $2, $3)`,
      [phone, hmac(env.OTP_HMAC_SECRET, `${phone}:${code}`), expiresAt],
    );

    await this.deps.sms.sendOtp(phone, code);
    return {
      expiresIn: env.OTP_TTL_SECONDS,
      // Only exposed in development; never in production (validated at boot).
      ...(env.OTP_DEV_ECHO ? { devCode: code } : {}),
    };
  }

  /** Step 2: verify the code, create the user on first login, issue tokens. */
  async verifyOtp(
    rawPhone: string,
    code: string,
    meta: { userAgent?: string },
  ): Promise<{ user: PublicUser; isNewUser: boolean; tokens: TokenPair }> {
    const phone = normalizeIranianMobile(rawPhone);
    if (!phone) throw AppError.badRequest('INVALID_PHONE', 'Phone number is not a valid Iranian mobile number');

    const { db, env } = this.deps;
    const otp = await db.query<{ id: string; code_hash: string; attempts: number; expires_at: Date }>(
      `SELECT id, code_hash, attempts, expires_at FROM otp_codes
        WHERE phone = $1 AND consumed_at IS NULL
        ORDER BY created_at DESC LIMIT 1`,
      [phone],
    );
    const row = otp.rows[0];
    if (!row || new Date(row.expires_at).getTime() < this.now().getTime()) {
      throw AppError.badRequest('OTP_EXPIRED', 'Verification code has expired. Request a new one.');
    }
    if (row.attempts >= env.OTP_MAX_ATTEMPTS) {
      throw AppError.tooMany('OTP_TOO_MANY_ATTEMPTS', 'Too many wrong attempts. Request a new code.');
    }

    const expected = hmac(env.OTP_HMAC_SECRET, `${phone}:${code}`);
    if (!safeEqual(expected, row.code_hash)) {
      await db.query('UPDATE otp_codes SET attempts = attempts + 1 WHERE id = $1', [row.id]);
      throw AppError.badRequest('OTP_INVALID', 'The verification code is incorrect');
    }

    return withTransaction(db, async (client) => {
      await client.query('UPDATE otp_codes SET consumed_at = now() WHERE id = $1', [row.id]);

      const inserted = await client.query<UserRow & { inserted: boolean }>(
        `INSERT INTO users (phone, last_login_at) VALUES ($1, now())
         ON CONFLICT (phone) DO UPDATE SET last_login_at = now()
         RETURNING *, (xmax = 0) AS inserted`,
        [phone],
      );
      const userRow = inserted.rows[0];
      if (!userRow.is_active) throw AppError.forbidden('ACCOUNT_DISABLED', 'This account is disabled');

      const tokens = await this.issueTokens(client, userRow, meta.userAgent, randomUUID());
      logger.info('user logged in', { userId: userRow.id, isNewUser: userRow.inserted });
      return { user: toPublicUser(userRow), isNewUser: userRow.inserted, tokens };
    });
  }

  /** Starts a session for an already-authenticated account (used by the admin password login). */
  async createSession(
    userId: string,
    meta: { userAgent?: string },
  ): Promise<{ user: PublicUser; tokens: TokenPair }> {
    return withTransaction(this.deps.db, async (client) => {
      const res = await client.query<UserRow>('SELECT * FROM users WHERE id = $1', [userId]);
      const userRow = res.rows[0];
      if (!userRow || !userRow.is_active) throw AppError.forbidden('ACCOUNT_DISABLED', 'This account is disabled');
      const tokens = await this.issueTokens(client, userRow, meta.userAgent, randomUUID());
      return { user: toPublicUser(userRow), tokens };
    });
  }

  /** Refresh-token rotation with reuse detection. */
  async refresh(refreshToken: string, meta: { userAgent?: string }): Promise<TokenPair> {
    const hash = sha256(refreshToken);
    const outcome = await withTransaction(this.deps.db, async (client) => {
      const found = await client.query<{
        id: string;
        user_id: string;
        family_id: string;
        revoked_at: Date | null;
        expires_at: Date;
      }>(`SELECT id, user_id, family_id, revoked_at, expires_at FROM refresh_tokens WHERE token_hash = $1 FOR UPDATE`, [
        hash,
      ]);
      const token = found.rows[0];
      if (!token) return { kind: 'invalid' as const };

      if (token.revoked_at) {
        // Token reuse detected: revoke the entire family. Committed, then rejected below.
        await client.query(
          `UPDATE refresh_tokens SET revoked_at = now()
            WHERE family_id = $1 AND revoked_at IS NULL`,
          [token.family_id],
        );
        logger.warn('refresh token reuse detected; family revoked', { userId: token.user_id });
        return { kind: 'reused' as const };
      }
      if (new Date(token.expires_at).getTime() < this.now().getTime()) {
        return { kind: 'expired' as const };
      }

      const userRes = await client.query<UserRow>('SELECT * FROM users WHERE id = $1', [token.user_id]);
      const user = userRes.rows[0];
      if (!user || !user.is_active) return { kind: 'invalid' as const };

      const newId = randomUUID();
      const tokens = await this.issueTokens(client, user, meta.userAgent, token.family_id, newId);
      await client.query('UPDATE refresh_tokens SET revoked_at = now(), replaced_by = $2 WHERE id = $1', [
        token.id,
        newId,
      ]);
      return { kind: 'ok' as const, tokens };
    });

    switch (outcome.kind) {
      case 'ok':
        return outcome.tokens;
      case 'reused':
        throw AppError.unauthorized('REFRESH_REUSED', 'Session has been revoked. Please sign in again.');
      case 'expired':
        throw AppError.unauthorized('REFRESH_EXPIRED', 'Session expired. Please sign in again.');
      default:
        throw AppError.unauthorized('REFRESH_INVALID', 'Refresh token is invalid');
    }
  }

  /** Revokes the whole session family of the given refresh token. Idempotent. */
  async logout(refreshToken: string): Promise<void> {
    const hash = sha256(refreshToken);
    await this.deps.db.query(
      `UPDATE refresh_tokens SET revoked_at = now()
        WHERE family_id = (SELECT family_id FROM refresh_tokens WHERE token_hash = $1)
          AND revoked_at IS NULL`,
      [hash],
    );
  }

  private async issueTokens(
    client: { query: Db['query'] },
    user: Pick<UserRow, 'id' | 'role'>,
    userAgent: string | undefined,
    familyId: string,
    rowId: string = randomUUID(),
  ): Promise<TokenPair> {
    const refreshToken = randomToken();
    const refreshTtlMs = this.deps.env.REFRESH_TOKEN_TTL_DAYS * 24 * 3600 * 1000;
    await client.query(
      `INSERT INTO refresh_tokens (id, user_id, family_id, token_hash, user_agent, expires_at)
       VALUES ($1, $2, $3, $4, $5, $6)`,
      [
        rowId,
        user.id,
        familyId,
        sha256(refreshToken),
        userAgent?.slice(0, 255) ?? null,
        new Date(this.now().getTime() + refreshTtlMs),
      ],
    );
    return {
      accessToken: signAccessToken(user, {
        secret: this.deps.env.JWT_ACCESS_SECRET,
        ttlSeconds: this.deps.env.ACCESS_TOKEN_TTL_SECONDS,
      }),
      accessTokenExpiresIn: this.deps.env.ACCESS_TOKEN_TTL_SECONDS,
      refreshToken,
      refreshTokenExpiresIn: Math.floor(refreshTtlMs / 1000),
    };
  }
}
