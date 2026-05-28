const BASE = '/api'

async function req(path: string, opts?: RequestInit) {
  const r = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  })
  if (!r.ok) throw new Error(await r.text())
  return r.json()
}

export interface WorkRecord {
  id: string
  date: string
  clock_in: string
  clock_out: string | null
  total_hours: number | null
  overtime_hours: number | null
  note: string | null
  created_at: string
  updated_at: string
}

export interface Settings {
  standard_hours: number
  lunch_break_minutes: number
  pre_hours: number
  overtime_start: string
}

export interface Stats {
  work_days: number
  total_hours: number
  overtime_hours: number
}

export const api = {
  getToday: () => req('/records/today'),
  clockIn: () => req('/records/clock-in', { method: 'POST' }),
  clockOut: () => req('/records/clock-out', { method: 'POST' }),
  getRecords: (year: number, month: number) => req(`/records?year=${year}&month=${month}`),
  getAllRecords: () => req('/records/all'),
  getStats: (year: number, month: number) => req(`/records/stats?year=${year}&month=${month}`),
  getSettings: () => req('/settings'),
  saveSettings: (s: Settings) => req('/settings', { method: 'PUT', body: JSON.stringify(s) }),
  recalculateOvertime: () => req('/settings/recalculate', { method: 'POST' }),
  addRecord: (r: Omit<WorkRecord, 'id' | 'created_at' | 'updated_at'>) =>
    req('/records/add', { method: 'POST', body: JSON.stringify(r) }),
  updateRecord: (id: string, r: Partial<WorkRecord>) =>
    req(`/records/${id}`, { method: 'PUT', body: JSON.stringify(r) }),
  deleteRecord: (id: string) => req(`/records/${id}`, { method: 'DELETE' }),
}
