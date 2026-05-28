import { useState, useEffect } from 'react'
import dayjs from 'dayjs'
import { api, type Stats } from '../api/client'

interface DailyHour { date: string; hours: number }
interface SaturdayStats { count: number; hours: number }

export function useStats(year: number, month: number) {
  const [monthly, setMonthly] = useState<Stats>({ work_days: 0, total_hours: 0, overtime_hours: 0 })
  const [dailyHours, setDailyHours] = useState<DailyHour[]>([])
  const [saturday, setSaturday] = useState<SaturdayStats>({ count: 0, hours: 0 })

  useEffect(() => {
    ;(async () => {
      try {
        const stats = await api.getStats(year, month)
        setMonthly(stats as Stats)
      } catch {}

      const records = await api.getRecords(year, month) as { date: string; total_hours: number | null }[]

      const hoursByDate = new Map(
        records.map((record) => [
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

      // Saturday stats: day 6 in JS Date (0=Sun, 6=Sat)
      let satCount = 0
      let satHours = 0
      for (const r of records) {
        if (new Date(r.date).getDay() === 6 && r.total_hours) {
          satCount++
          satHours += r.total_hours
        }
      }
      setSaturday({ count: satCount, hours: Math.round(satHours * 100) / 100 })
    })()
  }, [year, month])

  return { monthly, dailyHours, saturday }
}
