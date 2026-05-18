import dayjs from 'dayjs'

interface Props {
  hasClockedIn: boolean
  hasClockedOut: boolean
  onClockIn: () => void
  onClockOut: () => void
}

export default function ClockButton({ hasClockedIn, hasClockedOut, onClockIn, onClockOut }: Props) {
  if (hasClockedOut) {
    return (
      <div className="flex flex-col items-center gap-2">
        <div className="w-36 h-36 rounded-full bg-gray-200 flex items-center justify-center">
          <span className="text-gray-400 text-lg font-medium">已完成</span>
        </div>
        <span className="text-gray-400 text-sm">今天的打卡已完成</span>
      </div>
    )
  }

  if (hasClockedIn) {
    const hour = dayjs().hour()
    const isOvertime = hour >= 18
    return (
      <div className="flex flex-col items-center gap-2">
        <button
          onClick={onClockOut}
          className={`w-36 h-36 rounded-full active:scale-95 transition-all flex items-center justify-center shadow-lg ${
            isOvertime
              ? 'bg-orange-500 hover:bg-orange-600 shadow-orange-200'
              : 'bg-red-500 hover:bg-red-600 shadow-red-200'
          }`}
        >
          <span className="text-white text-xl font-bold">
            {isOvertime ? '加班下班' : '下班打卡'}
          </span>
        </button>
        {isOvertime && <span className="text-orange-500 text-sm">已超 18:00，记得下班</span>}
      </div>
    )
  }

  // 未打卡：根据当前时间智能判断
  const hour = dayjs().hour()
  if (hour < 10) {
    return (
      <button
        onClick={onClockIn}
        className="w-36 h-36 rounded-full bg-blue-500 hover:bg-blue-600 active:scale-95 transition-all flex items-center justify-center shadow-lg shadow-blue-200"
      >
        <span className="text-white text-xl font-bold">上班打卡</span>
      </button>
    )
  }

  if (hour < 14) {
    return (
      <div className="flex flex-col items-center gap-2">
        <button
          onClick={onClockIn}
          className="w-36 h-36 rounded-full bg-amber-400 hover:bg-amber-500 active:scale-95 transition-all flex items-center justify-center shadow-lg shadow-amber-200"
        >
          <span className="text-white text-lg font-bold leading-tight text-center">
            上班打卡
          </span>
        </button>
        <span className="text-amber-500 text-xs">已过 10:00，是忘记打卡了吗？</span>
      </div>
    )
  }

  return (
    <div className="flex flex-col items-center gap-2">
      <button
        onClick={onClockIn}
        className="w-36 h-36 rounded-full bg-orange-500 hover:bg-orange-600 active:scale-95 transition-all flex items-center justify-center shadow-lg shadow-orange-200"
      >
        <span className="text-white text-lg font-bold leading-tight text-center">
          补上班打卡
        </span>
      </button>
      <span className="text-orange-500 text-xs">已过 14:00，补卡将标记为迟到</span>
    </div>
  )
}
