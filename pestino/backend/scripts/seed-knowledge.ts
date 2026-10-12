import { loadEnv } from '../src/config/env.js';
import { createPool } from '../src/db/pool.js';
import { migrate } from '../src/db/migrate.js';
import { seedKnowledge } from '../src/modules/knowledge/knowledge.seed.js';

const env = loadEnv({ ...process.env, GEMINI_API_KEY: process.env.GEMINI_API_KEY ?? 'seed-placeholder-key' });
const db = createPool(env);
try {
  await migrate(db);
  const result = await seedKnowledge(db);
  console.log(`Knowledge base seeded: ${result.articles} articles, ${result.references} references`);
} finally {
  await db.end();
}
