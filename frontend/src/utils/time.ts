import dayjs from 'dayjs'

export function todayStr(): string {
  return dayjs().format('YYYY-MM-DD')
}

export function nowISO(): string {
  return dayjs().toISOString()
}

export function roundToHalfHour(minutes: number): number {
  return Math.round(minutes / 30) * 0.5
}

export function calcWorkMinutes(clockIn: string, clockOut: string, lunchMinutes: number): number {
  const start = dayjs(clockIn)
  const end = dayjs(clockOut)
  const diff = end.diff(start, 'minute')
  return Math.max(0, diff - lunchMinutes)
}

export function calcTotalHours(workMinutes: number): number {
  return roundToHalfHour(workMinutes)
}

/**
 * @param clockIn - ISO datetime of clock-in
 * @param totalHours - total worked hours (after lunch deduction)
 * @param standardHours - standard hours (default 8)
 * @param preHours - hours before 9am that auto-count as overtime
 */
export function calcOvertimeHours(
  clockIn: string,
  totalHours: number,
  standardHours: number,
  preHours: number,
): number {
  const hour = dayjs(clockIn).hour()
  const preOvertime = hour < 9 ? preHours : 0
  return Math.max(0, totalHours - standardHours + preOvertime)
}

export function formatTime(iso: string | null): string {
  if (!iso) return '--:--'
  return dayjs(iso).format('HH:mm')
}

export function formatHours(hours: number | null): string {
  if (hours == null || Number.isNaN(hours)) return '--'
  return `${hours}h`
}

export function formatMinutesToHM(minutes: number): string {
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return `${h}h ${m}m`
}
