import { useState, useEffect, useCallback } from 'react'
import { api, type WorkRecord } from '../api/client'

export function useRecords(year: number, month: number) {
  const [records, setRecords] = useState<WorkRecord[]>([])

  const load = useCallback(async () => {
    const rows = await api.getRecords(year, month)
    setRecords((rows as WorkRecord[]).reverse())
  }, [year, month])

  useEffect(() => { load() }, [load])

  return { records, reload: load }
}

export async function updateRecord(id: string, updates: Partial<WorkRecord>) {
  await api.updateRecord(id, updates)
}