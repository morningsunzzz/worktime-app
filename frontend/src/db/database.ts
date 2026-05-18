import Dexie, { Table } from 'dexie'
import type { WorkRecord, AppSettings } from '../models/WorkRecord'

class WorkTimeDB extends Dexie {
  records!: Table<WorkRecord, string>
  settings!: Table<AppSettings, number>

  constructor() {
    super('WorkTimeDB')
    this.version(1).stores({
      records: 'id, date',
      settings: 'id',
    })
    this.version(2).upgrade(async (tx) => {
      const s = await tx.table('settings').get(1)
      if (s) {
        await tx.table('settings').put({
          ...s,
          lunchBreakMinutes: s.lunchBreakMinutes === 0 ? 60 : s.lunchBreakMinutes,
          preHours: s.preHours ?? 1,
        })
      }
    })
  }
}

export const db = new WorkTimeDB()

export async function getSettings(): Promise<AppSettings> {
  const s = await db.settings.get(1)
  if (!s) return { standardHours: 8, lunchBreakMinutes: 60, preHours: 1 }
  return {
    standardHours: s.standardHours ?? 8,
    lunchBreakMinutes: s.lunchBreakMinutes === 0 ? 60 : (s.lunchBreakMinutes ?? 60),
    preHours: s.preHours ?? 1,
  }
}

export async function saveSettings(s: AppSettings): Promise<void> {
  await db.settings.put({
    standardHours: s.standardHours,
    lunchBreakMinutes: s.lunchBreakMinutes,
    preHours: s.preHours,
    id: 1,
  })
}
