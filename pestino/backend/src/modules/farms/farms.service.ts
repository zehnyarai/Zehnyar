import type { Env } from '../../config/env.js';
import type { Db } from '../../db/pool.js';
import { AppError } from '../../lib/errors.js';
import { resolvePlan } from '../subscriptions/plans.js';
import type { FarmInput, IrrigationMethod } from './farms.schemas.js';

export interface FarmRow {
  id: string;
  user_id: string;
  name: string;
  province: string;
  city: string;
  latitude: string | null;
  longitude: string | null;
  area_hectares: string | null;
  pistachio_variety: string | null;
  average_tree_age: number | null;
  irrigation_method: IrrigationMethod | null;
  soil_type: string | null;
  soil_notes: string | null;
  created_at: Date;
  updated_at: Date;
}

export interface TreeRow {
  id: string;
  farm_id: string;
  label: string;
  planted_year: number | null;
  variety: string | null;
  created_at: Date;
}

export const toFarmDto = (r: FarmRow) => ({
  id: r.id,
  name: r.name,
  province: r.province,
  city: r.city,
  latitude: r.latitude === null ? null : Number(r.latitude),
  longitude: r.longitude === null ? null : Number(r.longitude),
  areaHectares: r.area_hectares === null ? null : Number(r.area_hectares),
  pistachioVariety: r.pistachio_variety,
  averageTreeAge: r.average_tree_age,
  irrigationMethod: r.irrigation_method,
  soilType: r.soil_type,
  soilNotes: r.soil_notes,
  createdAt: new Date(r.created_at).toISOString(),
  updatedAt: new Date(r.updated_at).toISOString(),
});

export const toTreeDto = (r: TreeRow) => ({
  id: r.id,
  farmId: r.farm_id,
  label: r.label,
  plantedYear: r.planted_year,
  variety: r.variety,
  createdAt: new Date(r.created_at).toISOString(),
});

export class FarmsService {
  constructor(
    private readonly db: Db,
    private readonly env: Pick<Env, 'FREE_MONTHLY_ANALYSES' | 'FREE_MAX_FARMS'>,
  ) {}

  async list(userId: string) {
    const res = await this.db.query<FarmRow>(
      `SELECT * FROM farms WHERE user_id = $1 AND deleted_at IS NULL ORDER BY created_at DESC`,
      [userId],
    );
    return res.rows.map(toFarmDto);
  }

  /** Loads a farm owned by the user. Other users' farms are reported as not found. */
  async getOwned(userId: string, farmId: string): Promise<FarmRow> {
    const res = await this.db.query<FarmRow>(
      `SELECT * FROM farms WHERE id = $1 AND user_id = $2 AND deleted_at IS NULL`,
      [farmId, userId],
    );
    if (!res.rows[0]) throw AppError.notFound('FARM_NOT_FOUND', 'Farm not found');
    return res.rows[0];
  }

  async create(userId: string, input: FarmInput) {
    const plan = await resolvePlan(this.db, userId, this.env);
    if (plan.maxFarms !== null) {
      const count = await this.db.query<{ c: string }>(
        'SELECT count(*) AS c FROM farms WHERE user_id = $1 AND deleted_at IS NULL',
        [userId],
      );
      if (Number(count.rows[0].c) >= plan.maxFarms) {
        throw new AppError(
          402,
          'FARM_LIMIT_REACHED',
          `Your ${plan.nameFa} plan allows up to ${plan.maxFarms} farm(s). Upgrade to add more.`,
        );
      }
    }

    const res = await this.db.query<FarmRow>(
      `INSERT INTO farms (user_id, name, province, city, latitude, longitude, area_hectares,
         pistachio_variety, average_tree_age, irrigation_method, soil_type, soil_notes)
       VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12) RETURNING *`,
      [
        userId,
        input.name,
        input.province,
        input.city,
        input.latitude,
        input.longitude,
        input.areaHectares,
        input.pistachioVariety,
        input.averageTreeAge,
        input.irrigationMethod,
        input.soilType,
        input.soilNotes,
      ],
    );
    return toFarmDto(res.rows[0]);
  }

  async get(userId: string, farmId: string) {
    return toFarmDto(await this.getOwned(userId, farmId));
  }

  async update(userId: string, farmId: string, patch: Partial<FarmInput>) {
    await this.getOwned(userId, farmId);
    const map: Array<[keyof FarmInput, string]> = [
      ['name', 'name'],
      ['province', 'province'],
      ['city', 'city'],
      ['latitude', 'latitude'],
      ['longitude', 'longitude'],
      ['areaHectares', 'area_hectares'],
      ['pistachioVariety', 'pistachio_variety'],
      ['averageTreeAge', 'average_tree_age'],
      ['irrigationMethod', 'irrigation_method'],
      ['soilType', 'soil_type'],
      ['soilNotes', 'soil_notes'],
    ];
    const sets: string[] = [];
    const values: unknown[] = [];
    for (const [key, column] of map) {
      if (patch[key] !== undefined) {
        values.push(patch[key]);
        sets.push(`${column} = $${values.length}`);
      }
    }
    if (sets.length === 0) return this.get(userId, farmId);
    values.push(farmId, userId);
    const res = await this.db.query<FarmRow>(
      `UPDATE farms SET ${sets.join(', ')} WHERE id = $${values.length - 1} AND user_id = $${values.length} RETURNING *`,
      values,
    );
    return toFarmDto(res.rows[0]);
  }

  /** Soft delete – analyses remain available for the user's history. */
  async remove(userId: string, farmId: string): Promise<void> {
    await this.getOwned(userId, farmId);
    await this.db.query('UPDATE farms SET deleted_at = now() WHERE id = $1 AND user_id = $2', [farmId, userId]);
  }

  async listTrees(userId: string, farmId: string) {
    await this.getOwned(userId, farmId);
    const res = await this.db.query<TreeRow>('SELECT * FROM trees WHERE farm_id = $1 ORDER BY created_at', [farmId]);
    return res.rows.map(toTreeDto);
  }

  async addTree(
    userId: string,
    farmId: string,
    input: { label: string; plantedYear: number | null; variety: string | null },
  ) {
    await this.getOwned(userId, farmId);
    const res = await this.db.query<TreeRow>(
      `INSERT INTO trees (farm_id, label, planted_year, variety) VALUES ($1,$2,$3,$4) RETURNING *`,
      [farmId, input.label, input.plantedYear, input.variety],
    );
    return toTreeDto(res.rows[0]);
  }

  async removeTree(userId: string, farmId: string, treeId: string): Promise<void> {
    await this.getOwned(userId, farmId);
    const res = await this.db.query('DELETE FROM trees WHERE id = $1 AND farm_id = $2', [treeId, farmId]);
    if (res.rowCount === 0) throw AppError.notFound('TREE_NOT_FOUND', 'Tree not found');
  }
}
