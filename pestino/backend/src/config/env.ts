import { z } from 'zod';

/**
 * Typed, validated environment configuration.
 * The process refuses to start if a required secret is missing or weak.
 */
const envSchema = z
  .object({
    NODE_ENV: z.enum(['development', 'test', 'production']).default('development'),
    PORT: z.coerce.number().int().positive().default(8080),
    HOST: z.string().default('0.0.0.0'),

    DATABASE_URL: z.string().url(),
    DATABASE_SSL: z
      .enum(['true', 'false'])
      .default('false')
      .transform((v) => v === 'true'),

    JWT_ACCESS_SECRET: z.string().min(32, 'JWT_ACCESS_SECRET must be at least 32 chars'),
    OTP_HMAC_SECRET: z.string().min(32, 'OTP_HMAC_SECRET must be at least 32 chars'),
    ACCESS_TOKEN_TTL_SECONDS: z.coerce.number().int().positive().default(900),
    REFRESH_TOKEN_TTL_DAYS: z.coerce.number().int().positive().default(60),
    OTP_TTL_SECONDS: z.coerce.number().int().positive().default(120),
    OTP_MAX_ATTEMPTS: z.coerce.number().int().positive().default(5),
    /** Per-IP limit for /auth endpoints per 15 minutes. Generous because carriers share IPs (CGNAT). */
    AUTH_RATE_LIMIT_PER_15MIN: z.coerce.number().int().positive().default(100),
    /** Per-IP global limit per 15 minutes. */
    GLOBAL_RATE_LIMIT_PER_15MIN: z.coerce.number().int().positive().default(600),
    /** Only for development / staging. In production the OTP is sent by an SMS provider. */
    OTP_DEV_ECHO: z
      .enum(['true', 'false'])
      .default('false')
      .transform((v) => v === 'true'),

    GEMINI_API_KEY: z.string().min(10, 'GEMINI_API_KEY is required'),
    GEMINI_MODEL: z.string().default('gemini-2.5-flash'),
    GEMINI_TIMEOUT_MS: z.coerce.number().int().positive().default(45000),

    UPLOAD_DIR: z.string().default('./storage/uploads'),
    MAX_UPLOAD_MB: z.coerce.number().positive().default(8),

    FREE_MONTHLY_ANALYSES: z.coerce.number().int().nonnegative().default(5),
    FREE_MAX_FARMS: z.coerce.number().int().positive().default(1),

    CORS_ORIGINS: z
      .string()
      .default('')
      .transform((v) =>
        v
          .split(',')
          .map((s) => s.trim())
          .filter(Boolean),
      ),
    TRUST_PROXY: z.coerce.number().int().nonnegative().default(1),
  })
  .superRefine((env, ctx) => {
    if (env.NODE_ENV === 'production') {
      if (env.OTP_DEV_ECHO) {
        ctx.addIssue({ code: 'custom', path: ['OTP_DEV_ECHO'], message: 'Must be false in production' });
      }
      if (env.JWT_ACCESS_SECRET === env.OTP_HMAC_SECRET) {
        ctx.addIssue({ code: 'custom', path: ['OTP_HMAC_SECRET'], message: 'Must differ from JWT secret' });
      }
    }
  });

export type Env = z.infer<typeof envSchema>;

export function loadEnv(source: NodeJS.ProcessEnv = process.env): Env {
  const parsed = envSchema.safeParse(source);
  if (!parsed.success) {
    const details = parsed.error.issues.map((i) => `  - ${i.path.join('.')}: ${i.message}`).join('\n');
    throw new Error(`Invalid environment configuration:\n${details}`);
  }
  return parsed.data;
}
