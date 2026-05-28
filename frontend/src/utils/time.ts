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
 * Calculate overtime: morning bonus (before 9am) + evening overtime (after overtime_start).
 * @param clockIn - ISO datetime of clock-in
 * @param clockOut - ISO datetime of clock-out (null if still working)
 * @param preHours - overtime bonus hours for arriving before 9am (default 1)
 * @param overtimeStart - time string like "18:00", "18:30", "19:00"
 */
export function calcOvertimeHours(
  clockIn: string,
  clockOut: string | null,
  preHours: number,
  overtimeStart: string,
): number {
  if (!clockOut) return 0

  const inTime = dayjs(clockIn)

  // Morning bonus: clocked in before 9am
  const morningBonus = inTime.hour() < 9 ? preHours : 0

  // Evening overtime: time after overtime_start (anchored to clock_in date)
  const [ostH, ostM] = overtimeStart.split(':').map(Number)
  const ostTime = inTime.hour(ostH).minute(ostM).second(0).millisecond(0)
  const diffMinutes = dayjs(clockOut).diff(ostTime, 'minute')
  const eveningOvertime = Math.max(0, roundToHalfHour(diffMinutes))

  return morningBonus + eveningOvertime
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
