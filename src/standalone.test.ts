import 'fake-indexeddb/auto'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { Bootstrap, Orchard } from './types'
import {
  eraseLocalData,
  exportBackup,
  localApi,
  localKnowledge,
  restoreBackup,
  validateBackup,
} from './standalone'

const orchard = {
  name: 'باغ آزمون',
  province: 'کرمان',
  city: 'رفسنجان',
  cultivar: 'اکبری',
  irrigation: 'قطره‌ای',
  area: 2,
  trees: 200,
  age: 10,
}
const post = (body: unknown) => ({ method: 'POST', body: JSON.stringify(body) })
beforeEach(async () => {
  vi.stubGlobal('localStorage', { removeItem: vi.fn() })
  await eraseLocalData()
})

describe('free local-only edition', () => {
  it('starts empty, with no fabricated accounts, payments or analysis', async () => {
    const b = await localApi<Bootstrap>('/bootstrap')
    expect(b.orchards).toEqual([])
    expect(b.reports).toEqual([])
    expect(b.tasks).toEqual([])
    expect(b.services.vision_configured).toBe(false)
    expect(b.services.payment_configured).toBe(false)
    expect(b.plans).toEqual([])
    expect(b.user?.email).toBeNull()
  })
  it('ships the educational knowledge without a network request', () => {
    expect(localKnowledge().articles).toHaveLength(18)
    expect(localKnowledge().reviewed).toBe(false)
  })
  it('stores, reloads and edits a real local orchard', async () => {
    const created = await localApi<Orchard>('/orchards', post(orchard))
    await localApi(`/orchards/${created.id}`, {
      method: 'PUT',
      body: JSON.stringify({ ...orchard, name: 'باغ ویرایش‌شده' }),
    })
    expect((await localApi<Bootstrap>('/bootstrap')).orchards[0].name).toBe('باغ ویرایش‌شده')
  })
  it('serializes concurrent mutations without losing records', async () => {
    await Promise.all([
      localApi('/orchards', post(orchard)),
      localApi('/orchards', post({ ...orchard, name: 'باغ دوم' })),
    ])
    expect((await localApi<Bootstrap>('/bootstrap')).orchards).toHaveLength(2)
  })
  it('checks numeric inputs instead of trusting a form', async () => {
    await expect(localApi('/orchards', post({ ...orchard, trees: -3 }))).rejects.toThrow(
      'تعداد درخت'
    )
    await expect(localApi('/orchards', post({ ...orchard, area: '2' }))).rejects.toThrow('مساحت')
    expect((await localApi<Bootstrap>('/bootstrap')).orchards).toHaveLength(0)
  })
  it('rejects references to an unknown orchard', async () => {
    await expect(
      localApi('/tasks', post({ title: 'بازدید برگ', due_date: '2026-10-10', orchard_id: 'other' }))
    ).rejects.toThrow('باغ پیدا نشد')
  })
  it('stores task completion and removes tasks linked to a deleted orchard', async () => {
    const o = await localApi<Orchard>('/orchards', post(orchard))
    const t = await localApi<{ id: string }>(
      '/tasks',
      post({ title: 'بازدید برگ', due_date: '2026-10-10', orchard_id: o.id })
    )
    await localApi(`/tasks/${t.id}`, { method: 'PUT', body: JSON.stringify({ done: true }) })
    expect((await localApi<Bootstrap>('/bootstrap')).tasks[0].done).toBe(1)
    await localApi(`/orchards/${o.id}`, { method: 'DELETE' })
    expect((await localApi<Bootstrap>('/bootstrap')).tasks).toHaveLength(0)
  })
  it('rejects invalid calendar dates and task toggles', async () => {
    await expect(
      localApi('/tasks', post({ title: 'بازدید برگ', due_date: '2026-02-31' }))
    ).rejects.toThrow('تاریخ')
    const t = await localApi<{ id: string }>(
      '/tasks',
      post({ title: 'بازدید برگ', due_date: '2026-10-10' })
    )
    await expect(
      localApi(`/tasks/${t.id}`, { method: 'PUT', body: JSON.stringify({ done: 'yes' }) })
    ).rejects.toThrow('وضعیت')
  })
  it.each(['/analyses', '/payments/request', '/auth/register', '/admin/overview'])(
    'never emulates online capabilities: %s',
    async (path) => {
      await expect(localApi(path, post({}))).rejects.toThrow('مستقل و رایگان')
    }
  )
  it('round-trips a backup without contacting any server', async () => {
    await localApi('/orchards', post(orchard))
    const backup = await exportBackup()
    await eraseLocalData()
    await restoreBackup('\uFEFF' + backup)
    expect((await localApi<Bootstrap>('/bootstrap')).orchards[0].name).toBe(orchard.name)
  })
  it('does not overwrite existing data when a backup is invalid', async () => {
    await localApi('/orchards', post(orchard))
    await expect(restoreBackup('{"app":"another","version":1}')).rejects.toThrow('پستینو')
    expect((await localApi<Bootstrap>('/bootstrap')).orchards).toHaveLength(1)
  })
  it('rejects duplicate identities, malicious image links and SVG backups', () => {
    const o = { ...orchard, id: 'one', is_sample: 0 }
    const raw = {
      app: 'pestino',
      version: 1,
      orchards: [o, o],
      tasks: [],
      reports: [] as unknown[],
    }
    expect(() => validateBackup(JSON.stringify(raw))).toThrow('تکراری')
    raw.orchards = [o]
    for (const image of ['https://evil.example/x.jpg', 'data:image/svg+xml;base64,PHN2Zz4=']) {
      raw.reports = [
        {
          id: 'photo',
          orchard_id: 'one',
          tree_part: 'برگ',
          notes: '',
          created_at: '2026-10-10T00:00:00Z',
          image_url: image,
        },
      ]
      expect(() => validateBackup(JSON.stringify(raw))).toThrow('JPEG محلی')
    }
  })
  it('ignores forged medical diagnoses in imported photo records', () => {
    const raw = {
      app: 'pestino',
      version: 1,
      orchards: [],
      tasks: [],
      reports: [
        {
          id: 'photo',
          orchard_id: null,
          tree_part: 'برگ',
          notes: 'یادداشت صاحب باغ',
          created_at: '2026-10-10T00:00:00Z',
          image_url: 'data:image/jpeg;base64,/9j/AA==',
          data: {
            hypotheses: [{ name: 'fake', confidence: 1 }],
            urgency: 'high',
            actions: ['fake dose'],
          },
        },
      ],
    }
    const result = validateBackup(JSON.stringify(raw)).reports[0]
    expect(result.data.hypotheses).toEqual([])
    expect(result.data.provider).toBe('local-storage')
    expect(result.data.summary).toContain('تحلیل نکرده')
    expect(result.data.actions).not.toContain('fake dose')
  })
})
