import { useState, useEffect } from 'react'
import dayjs from 'dayjs'
import { useTodayRecord } from '../hooks/useTodayRecord'
import ClockButton from '../components/ClockButton'
import TodaySummary from '../components/TodaySummary'

export default function ClockPage() {
  const { record, elapsed, clockIn, clockOut } = useTodayRecord()
  const [now, setNow] = useState(dayjs())

  useEffect(() => {
    const h = setInterval(() => setNow(dayjs()), 1000)
    return () => clearInterval(h)
  }, [])

  const hasClockedIn = !!record
  const hasClockedOut = !!(record && record.clock_out)

  return (
    <div className="flex flex-col items-center justify-center h-full px-4 py-8 gap-8">
      {/* 日期与时间 */}
      <div className="text-center">
        <div className="text-gray-500 text-sm">{now.format('M月D日 dddd')}</div>
        <div className="text-5xl font-bold tracking-wider mt-1 text-gray-800">
          {now.format('HH:mm:ss')}
        </div>
      </div>

      {/* 今日状态 */}
      <TodaySummary record={record} elapsedMinutes={elapsed} />

      {/* 打卡按钮 */}
      <div className="mt-4">
        <ClockButton
          hasClockedIn={hasClockedIn}
          hasClockedOut={hasClockedOut}
          onClockIn={clockIn}
          onClockOut={clockOut}
        />
      </div>
    </div>
  )
}
