import type { Db } from '../../db/pool.js';
import { AppError } from '../../lib/errors.js';

export const KNOWLEDGE_KINDS = ['pest', 'disease', 'nutrient', 'environmental'] as const;
export type KnowledgeKind = (typeof KNOWLEDGE_KINDS)[number];

interface ArticleRow {
  id: string;
  slug: string;
  kind: KnowledgeKind;
  title_fa: string;
  title_en: string;
  summary_fa: string;
  symptoms: string[];
  causes: string[];
  management: string[];
  image_urls: string[];
  scientific_name: string | null;
  damage_type: string | null;
  monitoring_method: string | null;
  pathogen: string | null;
  pathogen_type: string | null;
}

export interface ArticleSummary {
  slug: string;
  kind: KnowledgeKind;
  titleFa: string;
  titleEn: string;
  summaryFa: string;
}

const summaryOf = (r: ArticleRow): ArticleSummary => ({
  slug: r.slug,
  kind: r.kind,
  titleFa: r.title_fa,
  titleEn: r.title_en,
  summaryFa: r.summary_fa,
});

export class KnowledgeService {
  constructor(private readonly db: Db) {}

  async list(filter: { kind?: KnowledgeKind; q?: string }): Promise<ArticleSummary[]> {
    const where: string[] = ['is_published'];
    const params: unknown[] = [];
    if (filter.kind) {
      params.push(filter.kind);
      where.push(`kind = $${params.length}`);
    }
    if (filter.q) {
      params.push(`%${filter.q.replace(/[%_]/g, '\\$&')}%`);
      where.push(`(title_fa ILIKE $${params.length} OR title_en ILIKE $${params.length} OR summary_fa ILIKE $${params.length})`);
    }
    const res = await this.db.query<ArticleRow>(
      `SELECT a.*, NULL::text AS scientific_name, NULL::text AS damage_type, NULL::text AS monitoring_method,
              NULL::text AS pathogen, NULL::text AS pathogen_type
         FROM knowledge_articles a WHERE ${where.join(' AND ')}
        ORDER BY kind, title_fa`,
      params,
    );
    return res.rows.map(summaryOf);
  }

  /** Full article with attributes and references. */
  async get(slug: string) {
    const res = await this.db.query<ArticleRow>(
      `SELECT a.*, p.scientific_name, p.damage_type, p.monitoring_method, d.pathogen, d.pathogen_type
         FROM knowledge_articles a
         LEFT JOIN pests p ON p.article_id = a.id
         LEFT JOIN diseases d ON d.article_id = a.id
        WHERE a.slug = $1 AND a.is_published`,
      [slug],
    );
    const row = res.rows[0];
    if (!row) throw AppError.notFound('ARTICLE_NOT_FOUND', 'Knowledge article not found');

    const refs = await this.db.query<{ citation: string; url: string | null; doi: string | null; year: number | null; verified: boolean }>(
      `SELECT r.citation, r.url, r.doi, r.year, r.verified
         FROM article_references ar JOIN knowledge_references r ON r.id = ar.reference_id
        WHERE ar.article_id = $1 ORDER BY r.year NULLS LAST`,
      [row.id],
    );

    return {
      ...summaryOf(row),
      symptoms: row.symptoms,
      causes: row.causes,
      management: row.management,
      images: row.image_urls,
      attributes:
        row.kind === 'pest'
          ? { scientificName: row.scientific_name, damageType: row.damage_type, monitoringMethod: row.monitoring_method }
          : row.kind === 'disease'
            ? { pathogen: row.pathogen, pathogenType: row.pathogen_type }
            : null,
      references: refs.rows.map((r) => ({
        citation: r.citation,
        url: r.url,
        doi: r.doi,
        year: r.year,
        verified: r.verified,
      })),
    };
  }

  /** Compact catalogue used to ground the AI prompt (slug → name, kind). */
  async catalogForPrompt(): Promise<Array<{ slug: string; kind: KnowledgeKind; titleFa: string; symptoms: string[] }>> {
    const res = await this.db.query<{ slug: string; kind: KnowledgeKind; title_fa: string; symptoms: string[] }>(
      `SELECT slug, kind, title_fa, symptoms FROM knowledge_articles WHERE is_published ORDER BY kind, slug`,
    );
    return res.rows.map((r) => ({ slug: r.slug, kind: r.kind, titleFa: r.title_fa, symptoms: r.symptoms.slice(0, 3) }));
  }
}
