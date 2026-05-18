import { useState, useEffect, useCallback } from 'react'
import { api, type WorkRecord, type Settings } from '../api/client'
import dayjs from 'dayjs'

export function useTodayRecord() {
  const [record, setRecord] = useState<WorkRecord | null>(null)
  const [settings, setSettings] = useState<Settings>({ standard_hours: 8, lunch_break_minutes: 60, pre_hours: 1 })
  const [elapsed, setElapsed] = useState(0)

  const refresh = useCallback(async () => {
    try {
      const r = await api.getToday()
      setRecord(r as WorkRecord | null)
    } catch { setRecord(null) }
    try {
      const s = await api.getSettings()
      setSettings(s as Settings)
    } catch {}
  }, [])

  useEffect(() => { refresh() }, [refresh])

  useEffect(() => {
    if (!record || record.clock_out) { setElapsed(0); return }
    const tick = () => {
      const diff = dayjs().diff(dayjs(record.clock_in), 'minute') - (settings.lunch_break_minutes || 0)
      setElapsed(Math.max(0, diff))
    }
    tick()
    const h = setInterval(tick, 1000)
    return () => clearInterval(h)
  }, [record?.id, record?.clock_out, settings.lunch_break_minutes])

  const clockIn = async () => {
    const r = await api.clockIn()
    setRecord(r as WorkRecord)
  }

  const clockOut = async () => {
    const r = await api.clockOut()
    setRecord(r as WorkRecord)
  }

  return { record, settings, elapsed, clockIn, clockOut }
}
