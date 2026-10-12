import type { NextFunction, Request, Response } from 'express';
import { AppError } from '../lib/errors.js';
import { verifyAccessToken } from '../modules/auth/tokens.js';

export interface AuthContext {
  userId: string;
  role: 'farmer' | 'expert' | 'admin';
}

declare module 'express-serve-static-core' {
  interface Request {
    auth?: AuthContext;
  }
}

/** Requires `Authorization: Bearer <access token>` and attaches `req.auth`. */
export function requireAuth(jwtSecret: string) {
  return (req: Request, _res: Response, next: NextFunction) => {
    const header = req.headers.authorization ?? '';
    const match = /^Bearer\s+(.+)$/i.exec(header);
    if (!match) return next(AppError.unauthorized());
    try {
      const payload = verifyAccessToken(match[1], jwtSecret);
      req.auth = { userId: payload.sub, role: payload.role };
      next();
    } catch (err) {
      next(err);
    }
  };
}
