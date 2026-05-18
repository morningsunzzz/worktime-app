import type { WorkRecord } from '../api/client'
import { formatTime, formatHours } from './time'

function escapeCsv(v: string): string {
  return `"${v.replace(/"/g, '""')}"`
}

export function exportCSV(records: WorkRecord[]): void {
  const header = '日期,上班时间,下班时间,工时,加班,备注'
  const rows = records.map((r) =>
    [
      r.date,
      formatTime(r.clock_in),
      formatTime(r.clock_out),
      formatHours(r.total_hours),
      formatHours(r.overtime_hours),
      r.note ?? '',
    ]
      .map(escapeCsv)
      .join(','),
  )
  const csv = [header, ...rows].join('\n')
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `考勤记录_${new Date().toISOString().slice(0, 10)}.csv`
  a.click()
  URL.revokeObjectURL(url)
}
