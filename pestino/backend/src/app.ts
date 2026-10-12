import express, { type Express } from 'express';
import helmet from 'helmet';
import cors from 'cors';
import rateLimit from 'express-rate-limit';
import type { Env } from './config/env.js';
import type { Db } from './db/pool.js';
import { AuthService } from './modules/auth/auth.service.js';
import { authRoutes, meRoutes } from './modules/auth/auth.routes.js';
import { FarmsService } from './modules/farms/farms.service.js';
import { farmsRoutes } from './modules/farms/farms.routes.js';
import { AnalysesService } from './modules/analyses/analyses.service.js';
import { analysesRoutes } from './modules/analyses/analyses.routes.js';
import { KnowledgeService } from './modules/knowledge/knowledge.service.js';
import { knowledgeRoutes } from './modules/knowledge/knowledge.routes.js';
import { subscriptionsRoutes } from './modules/subscriptions/subscriptions.routes.js';
import { GeminiVisionClient } from './modules/ai/gemini.client.js';
import { LocalImageStorage } from './lib/storage.js';
import type { SmsSender } from './lib/sms.js';
import { errorHandler, notFoundHandler } from './middleware/error.js';
import { AppError } from './lib/errors.js';

export interface AppDeps {
  env: Env;
  db: Db;
  sms: SmsSender;
  ai: GeminiVisionClient;
  storage: LocalImageStorage;
}

/** Builds the Express application. Dependencies are injected so tests can run without network. */
export function createApp(deps: AppDeps): Express {
  const { env, db } = deps;
  const app = express();

  app.disable('x-powered-by');
  app.set('trust proxy', env.TRUST_PROXY);
  app.use(helmet({ contentSecurityPolicy: false }));
  app.use(
    cors({
      origin: env.CORS_ORIGINS.length ? env.CORS_ORIGINS : false,
      methods: ['GET', 'POST', 'PATCH', 'DELETE'],
      allowedHeaders: ['Authorization', 'Content-Type'],
      maxAge: 600,
    }),
  );
  app.use(express.json({ limit: '100kb' }));

  // Global abuse protection (per IP, 15 min window).
  app.use(
    rateLimit({
      windowMs: 15 * 60 * 1000,
      limit: env.GLOBAL_RATE_LIMIT_PER_15MIN,
      standardHeaders: 'draft-7',
      legacyHeaders: false,
      handler: (_req, _res, next) => next(AppError.tooMany()),
    }),
  );

  app.get('/health', async (_req, res) => {
    try {
      await db.query('SELECT 1');
      res.json({ status: 'ok', db: 'ok', time: new Date().toISOString() });
    } catch {
      res.status(503).json({ status: 'degraded', db: 'down' });
    }
  });

  const auth = new AuthService({ db, env, sms: deps.sms });
  const farms = new FarmsService(db, env);
  const knowledge = new KnowledgeService(db);
  const analyses = new AnalysesService({ db, env, storage: deps.storage, knowledge, farms, ai: deps.ai });

  const api = express.Router();
  // Strict limiter for authentication (brute-force & SMS-pumping protection).
  const authLimiter = rateLimit({
    windowMs: 15 * 60 * 1000,
    limit: env.AUTH_RATE_LIMIT_PER_15MIN,
    standardHeaders: 'draft-7',
    legacyHeaders: false,
    handler: (_req, _res, next) => next(AppError.tooMany()),
  });
  api.use('/auth', authLimiter, authRoutes({ auth, db, jwtSecret: env.JWT_ACCESS_SECRET }));
  api.use('/me', meRoutes({ db, jwtSecret: env.JWT_ACCESS_SECRET }));
  api.use('/farms', farmsRoutes({ farms, jwtSecret: env.JWT_ACCESS_SECRET }));
  api.use('/analyses', analysesRoutes({ analyses, jwtSecret: env.JWT_ACCESS_SECRET, env }));
  api.use('/knowledge', knowledgeRoutes({ knowledge, jwtSecret: env.JWT_ACCESS_SECRET }));
  api.use('/subscriptions', subscriptionsRoutes({ db, env }));

  app.use('/api/v1', api);
  app.use(notFoundHandler);
  app.use(errorHandler);
  return app;
}
