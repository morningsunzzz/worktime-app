import type { WorkRecord } from '../api/client'
import { formatTime, formatHours } from '../utils/time'

interface Props {
  record: WorkRecord
  onEdit: (record: WorkRecord) => void
}

export default function RecordCard({ record, onEdit }: Props) {
  const isComplete = !!record.clock_out
  const dayOfWeek = new Date(record.date).toLocaleDateString('zh-CN', { weekday: 'short' })

  return (
    <div
      className="flex items-center justify-between px-4 py-3 border-b border-gray-100 active:bg-gray-50"
      onClick={() => onEdit(record)}
    >
      <div className="flex items-center gap-3">
        <div className="text-center w-10">
          <div className="text-lg font-bold leading-tight">{record.date.slice(8)}</div>
          <div className="text-xs text-gray-400">{dayOfWeek}</div>
        </div>
        <div>
          <div className="text-sm">
            {formatTime(record.clock_in)} ~ {formatTime(record.clock_out)}
          </div>
          {record.note && <div className="text-xs text-gray-400 mt-0.5">{record.note}</div>}
        </div>
      </div>
      <div className="text-right">
        {isComplete ? (
          <>
            <div className="text-sm font-medium">{formatHours(record.total_hours)}</div>
            {record.overtime_hours && record.overtime_hours > 0 && (
              <div className="text-xs text-orange-500">+{formatHours(record.overtime_hours)}</div>
            )}
          </>
        ) : (
          <span className="text-xs text-blue-500 bg-blue-50 px-2 py-0.5 rounded">进行中</span>
        )}
      </div>
    </div>
  )
}
