import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { z } from 'zod';
import type { Db } from '../../db/pool.js';
import { withTransaction } from '../../db/pool.js';
import { backendRoot } from '../../lib/paths.js';

/** backend/knowledge */
export const KNOWLEDGE_DIR = path.join(backendRoot(), 'knowledge');

const strList = z.array(z.string().min(1)).default([]);

export const referenceSeedSchema = z.object({
  key: z.string().regex(/^[a-z0-9_]+$/),
  citation: z.string().min(10),
  doi: z.string().nullable(),
  url: z.string().url().nullable(),
  year: z.number().int().nullable(),
  verified: z.boolean(),
});

export const articleSeedSchema = z.object({
  slug: z.string().regex(/^[a-z0-9-]+$/),
  kind: z.enum(['pest', 'disease', 'nutrient', 'environmental']),
  titleFa: z.string().min(2),
  titleEn: z.string().min(2),
  summaryFa: z.string().min(10),
  symptoms: strList,
  causes: strList,
  management: strList,
  imageUrls: strList.optional(),
  referenceKeys: z.array(z.string()).min(1, 'Every article needs at least one reference'),
  pest: z
    .object({ scientificName: z.string().nullable(), damageType: z.string().nullable(), monitoringMethod: z.string().nullable() })
    .optional(),
  disease: z.object({ pathogen: z.string().nullable(), pathogenType: z.string().nullable() }).optional(),
});

export type ArticleSeed = z.infer<typeof articleSeedSchema>;
export type ReferenceSeed = z.infer<typeof referenceSeedSchema>;

export async function loadKnowledgeFiles(dir = KNOWLEDGE_DIR) {
  const refs = referenceSeedSchema.array().parse(JSON.parse(await readFile(path.join(dir, 'references.json'), 'utf8')));
  const articles = articleSeedSchema.array().parse(JSON.parse(await readFile(path.join(dir, 'articles.json'), 'utf8')));

  const refKeys = new Set(refs.map((r) => r.key));
  for (const a of articles) {
    if (a.kind === 'pest' && !a.pest) throw new Error(`${a.slug}: pest attributes missing`);
    if (a.kind === 'disease' && !a.disease) throw new Error(`${a.slug}: disease attributes missing`);
    for (const key of a.referenceKeys) {
      if (!refKeys.has(key)) throw new Error(`${a.slug}: unknown reference key "${key}"`);
    }
  }
  return { refs, articles };
}

/**
 * Idempotently upserts the knowledge base. Re-running updates content in place
 * (matched by slug / reference key) and replaces article-reference links.
 */
export async function seedKnowledge(db: Db, dir = KNOWLEDGE_DIR): Promise<{ articles: number; references: number }> {
  const { refs, articles } = await loadKnowledgeFiles(dir);

  return withTransaction(db, async (client) => {
    const refIds = new Map<string, string>();
    for (const r of refs) {
      const res = await client.query<{ id: string }>(
        `INSERT INTO knowledge_references (citation, doi, url, year, verified)
         VALUES ($1,$2,$3,$4,$5)
         ON CONFLICT (citation) DO UPDATE SET doi = EXCLUDED.doi, url = EXCLUDED.url,
           year = EXCLUDED.year, verified = EXCLUDED.verified
         RETURNING id`,
        [r.citation, r.doi, r.url, r.year, r.verified],
      );
      refIds.set(r.key, res.rows[0].id);
    }

    for (const a of articles) {
      const res = await client.query<{ id: string }>(
        `INSERT INTO knowledge_articles (slug, kind, title_fa, title_en, summary_fa, symptoms, causes, management, image_urls)
         VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
         ON CONFLICT (slug) DO UPDATE SET kind = EXCLUDED.kind, title_fa = EXCLUDED.title_fa,
           title_en = EXCLUDED.title_en, summary_fa = EXCLUDED.summary_fa, symptoms = EXCLUDED.symptoms,
           causes = EXCLUDED.causes, management = EXCLUDED.management, image_urls = EXCLUDED.image_urls
         RETURNING id`,
        [
          a.slug,
          a.kind,
          a.titleFa,
          a.titleEn,
          a.summaryFa,
          JSON.stringify(a.symptoms),
          JSON.stringify(a.causes),
          JSON.stringify(a.management),
          JSON.stringify(a.imageUrls ?? []),
        ],
      );
      const articleId = res.rows[0].id;

      if (a.pest) {
        await client.query(
          `INSERT INTO pests (article_id, scientific_name, damage_type, monitoring_method) VALUES ($1,$2,$3,$4)
           ON CONFLICT (article_id) DO UPDATE SET scientific_name = EXCLUDED.scientific_name,
             damage_type = EXCLUDED.damage_type, monitoring_method = EXCLUDED.monitoring_method`,
          [articleId, a.pest.scientificName, a.pest.damageType, a.pest.monitoringMethod],
        );
      }
      if (a.disease) {
        await client.query(
          `INSERT INTO diseases (article_id, pathogen, pathogen_type) VALUES ($1,$2,$3)
           ON CONFLICT (article_id) DO UPDATE SET pathogen = EXCLUDED.pathogen, pathogen_type = EXCLUDED.pathogen_type`,
          [articleId, a.disease.pathogen, a.disease.pathogenType],
        );
      }

      await client.query('DELETE FROM article_references WHERE article_id = $1', [articleId]);
      for (const key of a.referenceKeys) {
        await client.query('INSERT INTO article_references (article_id, reference_id) VALUES ($1,$2)', [
          articleId,
          refIds.get(key),
        ]);
      }
    }
    return { articles: articles.length, references: refs.length };
  });
}
