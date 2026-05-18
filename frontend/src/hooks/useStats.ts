import { useState, useEffect } from 'react'
import dayjs from 'dayjs'
import { api, type Stats } from '../api/client'

interface DailyHour { date: string; hours: number }

export function useStats(year: number, month: number) {
  const [monthly, setMonthly] = useState<Stats>({ work_days: 0, total_hours: 0, overtime_hours: 0 })
  const [dailyHours, setDailyHours] = useState<DailyHour[]>([])

  useEffect(() => {
    ;(async () => {
      try {
        const stats = await api.getStats(year, month)
        setMonthly(stats as Stats)
      } catch {}

      const records = await api.getRecords(year, month)
      const hoursByDate = new Map(
        (records as { date: string; total_hours: number | null }[]).map((record) => [
          dayjs(record.date).format('MM-DD'),
          record.total_hours ?? 0,
        ]),
      )
      const days: DailyHour[] = []
      for (let i = 29; i >= 0; i--) {
        const date = dayjs().subtract(i, 'day').format('MM-DD')
        days.push({ date, hours: hoursByDate.get(date) ?? 0 })
      }
      setDailyHours(days)
    })()
  }, [year, month])

  return { monthly, dailyHours }
}
