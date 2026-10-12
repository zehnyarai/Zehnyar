import jwt from 'jsonwebtoken';
import { AppError } from '../../lib/errors.js';

export const JWT_ISSUER = 'pestino-api';
export const JWT_AUDIENCE = 'pestino-app';

export interface AccessTokenPayload {
  sub: string;
  role: 'farmer' | 'expert' | 'admin';
  typ: 'access';
}

export function signAccessToken(
  user: { id: string; role: AccessTokenPayload['role'] },
  opts: { secret: string; ttlSeconds: number },
): string {
  return jwt.sign({ sub: user.id, role: user.role, typ: 'access' } satisfies AccessTokenPayload, opts.secret, {
    algorithm: 'HS256',
    expiresIn: opts.ttlSeconds,
    issuer: JWT_ISSUER,
    audience: JWT_AUDIENCE,
  });
}

export function verifyAccessToken(token: string, secret: string): AccessTokenPayload {
  try {
    const payload = jwt.verify(token, secret, {
      algorithms: ['HS256'],
      issuer: JWT_ISSUER,
      audience: JWT_AUDIENCE,
    }) as jwt.JwtPayload & AccessTokenPayload;
    if (payload.typ !== 'access' || typeof payload.sub !== 'string') {
      throw new Error('wrong token type');
    }
    return { sub: payload.sub, role: payload.role, typ: 'access' };
  } catch {
    throw AppError.unauthorized('TOKEN_INVALID', 'Access token is invalid or expired');
  }
}
