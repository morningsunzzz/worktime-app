import { useState } from 'react'
import dayjs from 'dayjs'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { useStats } from '../hooks/useStats'
import MonthChart from '../components/MonthChart'

export default function StatsPage() {
  const now = dayjs()
  const [year, setYear] = useState(now.year())
  const [month, setMonth] = useState(now.month() + 1)
  const { monthly, dailyHours } = useStats(year, month)

  const prevMonth = () => {
    if (month === 1) { setYear(year - 1); setMonth(12) }
    else setMonth(month - 1)
  }
  const nextMonth = () => {
    if (month === 12) { setYear(year + 1); setMonth(1) }
    else setMonth(month + 1)
  }

  return (
    <div className="flex flex-col h-full">
      {/* 月份切换 */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
        <button onClick={prevMonth} className="p-1"><ChevronLeft size={20} /></button>
        <span className="font-medium">{year}年{month}月</span>
        <button onClick={nextMonth} className="p-1"><ChevronRight size={20} /></button>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-6">
        {/* 概览卡片 */}
        <div className="grid grid-cols-3 gap-3">
          <StatCard label="出勤天数" value={`${monthly.work_days}天`} color="text-blue-600" />
          <StatCard label="总工时" value={`${monthly.total_hours}h`} color="text-green-600" />
          <StatCard label="加班" value={`${monthly.overtime_hours}h`} color="text-orange-500" />
        </div>

        {/* 近30天工时图表 */}
        <div>
          <h3 className="text-sm font-medium text-gray-500 mb-3">近30天工时趋势</h3>
          <MonthChart data={dailyHours} />
        </div>
      </div>
    </div>
  )
}

function StatCard({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="bg-gray-50 rounded-xl p-3 text-center">
      <div className="text-xs text-gray-400">{label}</div>
      <div className={`text-xl font-bold mt-1 ${color}`}>{value}</div>
    </div>
  )
}
