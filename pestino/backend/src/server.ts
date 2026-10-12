import { loadEnv } from './config/env.js';
import { createPool } from './db/pool.js';
import { migrate } from './db/migrate.js';
import { createApp } from './app.js';
import { GeminiVisionClient } from './modules/ai/gemini.client.js';
import { AiSettingsService } from './modules/ai/ai-settings.service.js';
import { DevLogSmsSender, UnconfiguredSmsSender, type SmsSender } from './lib/sms.js';
import { LocalImageStorage } from './lib/storage.js';
import { logger } from './lib/logger.js';

async function main() {
  const env = loadEnv();
  const db = createPool(env);

  if (process.env.RUN_MIGRATIONS_ON_BOOT !== 'false') {
    const applied = await migrate(db);
    if (applied.length) logger.info('migrations applied', { applied });
  }

  // Production must use a real SMS adapter; the dev sender only logs codes.
  const sms: SmsSender = env.NODE_ENV === 'production' ? new UnconfiguredSmsSender() : new DevLogSmsSender();

  // Gemini settings are read from the database on every call (admin panel), with environment fallbacks.
  const aiSettings = new AiSettingsService(db, env);
  const app = createApp({
    env,
    db,
    sms,
    ai: new GeminiVisionClient({
      apiKey: env.GEMINI_API_KEY,
      model: env.GEMINI_MODEL,
      timeoutMs: env.GEMINI_TIMEOUT_MS,
      runtime: () => aiSettings.resolveRuntime(),
    }),
    storage: new LocalImageStorage(env.UPLOAD_DIR),
    aiSettings,
  });

  const server = app.listen(env.PORT, env.HOST, () => {
    logger.info('Pestino API listening', { port: env.PORT, host: env.HOST, env: env.NODE_ENV });
  });

  const shutdown = (signal: string) => {
    logger.info('shutting down', { signal });
    server.close(() => {
      db.end().finally(() => process.exit(0));
    });
    setTimeout(() => process.exit(1), 10_000).unref();
  };
  process.on('SIGINT', () => shutdown('SIGINT'));
  process.on('SIGTERM', () => shutdown('SIGTERM'));
}

main().catch((err) => {
  logger.error('fatal startup error', { error: err instanceof Error ? err.message : String(err) });
  process.exit(1);
});
