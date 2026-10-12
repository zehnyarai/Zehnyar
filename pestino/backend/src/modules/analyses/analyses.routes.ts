import { Router } from 'express';
import multer from 'multer';
import rateLimit from 'express-rate-limit';
import type { Env } from '../../config/env.js';
import { requireAuth } from '../../middleware/auth.js';
import { validateQuery } from '../../middleware/validate.js';
import { AppError } from '../../lib/errors.js';
import { AnalysesService } from './analyses.service.js';
import { analysisFieldsSchema, listQuerySchema } from './analyses.schemas.js';

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export function analysesRoutes(deps: { analyses: AnalysesService; jwtSecret: string; env: Pick<Env, 'MAX_UPLOAD_MB'> }): Router {
  const r = Router();
  r.use(requireAuth(deps.jwtSecret));
  r.param('analysisId', (_req, _res, next, value: string) => {
    if (!UUID_RE.test(value)) return next(AppError.badRequest('INVALID_ID', 'Invalid analysis id'));
    next();
  });

  // Heavy AI endpoint: at most 10 analyses per user per 10 minutes (on top of the plan quota).
  const analyzeLimiter = rateLimit({
    windowMs: 10 * 60 * 1000,
    limit: 10,
    standardHeaders: 'draft-7',
    legacyHeaders: false,
    keyGenerator: (req) => req.auth?.userId ?? req.ip ?? 'anon',
    handler: (_req, _res, next) => next(AppError.tooMany('ANALYZE_RATE_LIMIT', 'Too many analyses in a short time. Please wait a few minutes.')),
  });

  const upload = multer({
    storage: multer.memoryStorage(),
    limits: { fileSize: deps.env.MAX_UPLOAD_MB * 1024 * 1024, files: 1, fields: 10 },
    fileFilter: (_req, file, cb) => {
      if (!/^image\/(jpeg|png|webp)$/.test(file.mimetype)) {
        return cb(AppError.badRequest('UNSUPPORTED_IMAGE', 'Only JPEG, PNG or WEBP images are accepted'));
      }
      cb(null, true);
    },
  });

  r.get('/usage', async (req, res) => {
    res.json({ usage: await deps.analyses.usage(req.auth!.userId) });
  });

  r.get('/', validateQuery(listQuerySchema), async (req, res) => {
    const q = res.locals.query as { limit: number; cursor?: string; farmId?: string };
    res.json(await deps.analyses.list(req.auth!.userId, q));
  });

  r.post('/', analyzeLimiter, upload.single('image'), async (req, res) => {
    if (!req.file) throw AppError.badRequest('IMAGE_REQUIRED', 'An image file is required in the "image" field');
    const fields = analysisFieldsSchema.parse(req.body ?? {});
    const analysis = await deps.analyses.create({
      userId: req.auth!.userId,
      file: req.file.buffer,
      category: fields.category,
      season: fields.season,
      farmId: fields.farmId ?? null,
      treeAgeYears: fields.treeAgeYears ?? null,
      location: fields.location ?? null,
      userNotes: fields.userNotes ?? null,
    });
    res.status(201).json({ analysis });
  });

  r.get('/:analysisId', async (req, res) => {
    res.json({ analysis: await deps.analyses.get(req.auth!.userId, req.params.analysisId) });
  });

  r.get('/:analysisId/image', async (req, res) => {
    const { data, mime } = await deps.analyses.imageFor(req.auth!.userId, req.params.analysisId);
    res.set({
      'Content-Type': mime,
      'Cache-Control': 'private, no-store',
      'X-Content-Type-Options': 'nosniff',
    });
    res.send(data);
  });

  r.delete('/:analysisId', async (req, res) => {
    await deps.analyses.remove(req.auth!.userId, req.params.analysisId);
    res.status(204).end();
  });

  return r;
}
