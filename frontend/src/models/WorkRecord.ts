export interface WorkRecord {
  id: string
  date: string // "2026-05-15"
  clockIn: string // ISO datetime
  clockOut: string | null
  totalHours: number | null
  overtimeHours: number | null
  note: string | null
  createdAt: string
  updatedAt: string
}

export interface AppSettings {
  id?: number
  standardHours: number // 标准日工时，默认8
  lunchBreakMinutes: number // 午休时长(分钟)，默认60
  preHours: number // 9点前上班时，自动计入加班的时段(小时)，默认1
}
