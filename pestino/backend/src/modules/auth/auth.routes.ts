import { Router } from 'express';
import { z } from 'zod';
import { validateBody } from '../../middleware/validate.js';
import { requireAuth } from '../../middleware/auth.js';
import type { AuthService } from './auth.service.js';
import type { Db } from '../../db/pool.js';
import { AppError } from '../../lib/errors.js';
import { toPublicUser, type UserRow } from '../users/user.mapper.js';

const phoneSchema = z.object({ phone: z.string().min(9).max(20) });
const verifySchema = z.object({
  phone: z.string().min(9).max(20),
  code: z.string().regex(/^\d{6}$/, 'Code must be 6 digits'),
});
const refreshSchema = z.object({ refreshToken: z.string().min(20).max(200) });

export function authRoutes(deps: { auth: AuthService; db: Db; jwtSecret: string }): Router {
  const r = Router();

  r.post('/otp/request', validateBody(phoneSchema), async (req, res) => {
    const result = await deps.auth.requestOtp(req.body.phone);
    res.status(202).json(result);
  });

  r.post('/otp/verify', validateBody(verifySchema), async (req, res) => {
    const result = await deps.auth.verifyOtp(req.body.phone, req.body.code, {
      userAgent: req.get('user-agent') ?? undefined,
    });
    res.json({
      user: result.user,
      isNewUser: result.isNewUser,
      tokens: result.tokens,
    });
  });

  r.post('/refresh', validateBody(refreshSchema), async (req, res) => {
    const tokens = await deps.auth.refresh(req.body.refreshToken, {
      userAgent: req.get('user-agent') ?? undefined,
    });
    res.json({ tokens });
  });

  r.post('/logout', validateBody(refreshSchema), async (req, res) => {
    await deps.auth.logout(req.body.refreshToken);
    res.status(204).end();
  });

  return r;
}

/** Profile endpoints under /me (authenticated). */
export function meRoutes(deps: { db: Db; jwtSecret: string }): Router {
  const r = Router();
  r.use(requireAuth(deps.jwtSecret));

  const updateSchema = z
    .object({
      fullName: z.string().trim().min(2).max(120).nullable().optional(),
      province: z.string().trim().min(2).max(80).nullable().optional(),
      city: z.string().trim().min(2).max(80).nullable().optional(),
    })
    .strict();

  r.get('/', async (req, res) => {
    const row = await loadUser(deps.db, req.auth!.userId);
    res.json({ user: toPublicUser(row) });
  });

  r.patch('/', validateBody(updateSchema), async (req, res) => {
    const b = req.body as z.infer<typeof updateSchema>;
    const result = await deps.db.query<UserRow>(
      `UPDATE users SET
         full_name = CASE WHEN $2::boolean THEN $3 ELSE full_name END,
         province  = CASE WHEN $4::boolean THEN $5 ELSE province END,
         city      = CASE WHEN $6::boolean THEN $7 ELSE city END
       WHERE id = $1 RETURNING *`,
      [
        req.auth!.userId,
        b.fullName !== undefined,
        b.fullName ?? null,
        b.province !== undefined,
        b.province ?? null,
        b.city !== undefined,
        b.city ?? null,
      ],
    );
    if (!result.rows[0]) throw AppError.notFound('USER_NOT_FOUND', 'User not found');
    res.json({ user: toPublicUser(result.rows[0]) });
  });

  return r;
}

export async function loadUser(db: Db, userId: string): Promise<UserRow> {
  const res = await db.query<UserRow>('SELECT * FROM users WHERE id = $1 AND is_active', [userId]);
  if (!res.rows[0]) throw AppError.notFound('USER_NOT_FOUND', 'User not found');
  return res.rows[0];
}
