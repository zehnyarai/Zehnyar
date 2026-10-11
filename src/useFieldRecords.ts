import { useCallback, useEffect, useState } from 'react'
import { api, errorMessage } from './api'
import type { FieldKind, FieldPayloads, FieldRecord } from './fieldwork'

export function useFieldRecords<K extends FieldKind>(kind: K) {
  const [records, setRecords] = useState<FieldRecord<K>[]>([]),
    [error, setError] = useState(''),
    [loading, setLoading] = useState(true)
  const reload = useCallback(async () => {
    setRecords(await api<FieldRecord<K>[]>(`/field-records/${kind}`))
    setError('')
  }, [kind])
  useEffect(() => {
    let active = true
    setLoading(true)
    void api<FieldRecord<K>[]>(`/field-records/${kind}`)
      .then((r) => {
        if (active) {
          setRecords(r)
          setError('')
        }
      })
      .catch((e) => {
        if (active) setError(errorMessage(e))
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [kind])
  async function save(data: FieldPayloads[K]) {
    const record = await api<FieldRecord<K>>(`/field-records/${kind}`, {
      method: 'POST',
      body: JSON.stringify(data),
    })
    await reload()
    return record
  }
  async function remove(id: string) {
    await api(`/field-records/${kind}/${id}`, { method: 'DELETE' })
    await reload()
  }
  return { records, loading, error, reload, save, remove }
}
