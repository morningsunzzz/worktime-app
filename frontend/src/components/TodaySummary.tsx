import { useMemo } from 'react'
import type { WorkRecord } from '../api/client'
import { formatTime, formatMinutesToHM } from '../utils/time'

interface Props {
  record: WorkRecord | null
  elapsedMinutes: number
}

export default function TodaySummary({ record, elapsedMinutes }: Props) {
  const timeDisplay = useMemo(() => {
    if (!record) return null
    if (record.clock_out) {
      return (
        <div className="text-center space-y-1">
          <div className="flex justify-center gap-6 text-sm">
            <span className="text-gray-500">上班 {formatTime(record.clock_in)}</span>
            <span className="text-gray-500">下班 {formatTime(record.clock_out)}</span>
          </div>
          <div className="text-lg font-semibold">
            今日工时 <span className="text-blue-600">{record.total_hours}h</span>
            {record.overtime_hours && record.overtime_hours > 0 && (
              <span className="text-orange-500 ml-2">加班 {record.overtime_hours}h</span>
            )}
          </div>
        </div>
      )
    }
    return (
      <div className="text-center space-y-1">
        <div className="text-sm text-gray-500">上班 {formatTime(record.clock_in)}</div>
        <div className="text-lg font-semibold text-blue-600">
          已工作 {formatMinutesToHM(elapsedMinutes)}
        </div>
      </div>
    )
  }, [record, elapsedMinutes])

  if (!timeDisplay) {
    return <div className="text-gray-400 text-sm">今天还没有打卡记录</div>
  }

  return timeDisplay
}
