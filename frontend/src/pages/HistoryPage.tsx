import { useState } from 'react'
import dayjs from 'dayjs'
import { ChevronLeft, ChevronRight, Plus } from 'lucide-react'
import { useRecords, updateRecord } from '../hooks/useRecords'
import RecordCard from '../components/RecordCard'
import { api, type WorkRecord } from '../api/client'
import { calcWorkMinutes, calcTotalHours, calcOvertimeHours } from '../utils/time'

export default function HistoryPage() {
  const now = dayjs()
  const [year, setYear] = useState(now.year())
  const [month, setMonth] = useState(now.month() + 1)
  const [editing, setEditing] = useState<WorkRecord | null>(null)
  const [adding, setAdding] = useState(false)
  const [addDate, setAddDate] = useState(dayjs().format('YYYY-MM-DD'))
  const [addClockIn, setAddClockIn] = useState('08:00')
  const [addClockOut, setAddClockOut] = useState('18:00')
  const { records, reload } = useRecords(year, month)

  const prevMonth = () => {
    if (month === 1) { setYear(year - 1); setMonth(12) }
    else setMonth(month - 1)
  }
  const nextMonth = () => {
    if (month === 12) { setYear(year + 1); setMonth(1) }
    else setMonth(month + 1)
  }

  const handleEdit = (r: WorkRecord) => setEditing(r)

  const handleSave = async () => {
    if (!editing) return
    await updateRecord(editing.id, editing)
    setEditing(null)
    reload()
  }

  const handleDelete = async () => {
    if (!editing) return
    await api.deleteRecord(editing.id)
    setEditing(null)
    reload()
  }

  const handleAdd = async () => {
    const clockInISO = dayjs(`${addDate}T${addClockIn}:00`).toISOString()
    const clockOutISO = dayjs(`${addDate}T${addClockOut}:00`).toISOString()
    await api.addRecord({
      date: addDate,
      clock_in: clockInISO,
      clock_out: clockOutISO,
      total_hours: null,
      overtime_hours: null,
      note: null,
    })
    setAdding(false)
    reload()
  }

  return (
    <div className="flex flex-col h-full">
      {/* 月份切换 */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
        <button onClick={prevMonth} className="p-1"><ChevronLeft size={20} /></button>
        <span className="font-medium">{year}年{month}月</span>
        <div className="flex items-center gap-2">
          <button onClick={() => setAdding(true)} className="p-1"><Plus size={20} /></button>
          <button onClick={nextMonth} className="p-1"><ChevronRight size={20} /></button>
        </div>
      </div>

      {/* 记录列表 */}
      <div className="flex-1 overflow-y-auto">
        {records.length === 0 ? (
          <div className="text-center text-gray-400 mt-20">暂无打卡记录</div>
        ) : (
          records.map((r) => (
            <RecordCard key={r.id} record={r} onEdit={handleEdit} />
          ))
        )}
      </div>

      {/* 编辑弹窗 */}
      {editing && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={() => setEditing(null)}>
          <div className="bg-white rounded-xl p-6 w-80 shadow-xl" onClick={(e) => e.stopPropagation()}>
            <h3 className="font-medium text-lg mb-4">编辑记录</h3>
            <div className="text-sm text-gray-500 mb-4">{editing.date}</div>

            <div className="space-y-3">
              <div>
                <label className="text-xs text-gray-500">上班时间</label>
                <input
                  type="time"
                  value={dayjs(editing.clock_in).format('HH:mm')}
                  onChange={(e) => {
                    const t = e.target.value
                    const newIso = dayjs(`${editing.date}T${t}:00`).toISOString()
                    setEditing({ ...editing, clock_in: newIso })
                  }}
                  className="w-full border rounded px-3 py-2 mt-1"
                />
              </div>
              <div>
                <label className="text-xs text-gray-500">下班时间</label>
                <input
                  type="time"
                  value={editing.clock_out ? dayjs(editing.clock_out).format('HH:mm') : ''}
                  onChange={(e) => {
                    const t = e.target.value
                    const newIso = dayjs(`${editing.date}T${t}:00`).toISOString()
                    const workMin = calcWorkMinutes(editing.clock_in, newIso, 0)
                    const totalH = calcTotalHours(workMin)
                    const overtimeH = calcOvertimeHours(editing.clock_in, totalH, 8, 1)
                    setEditing({
                      ...editing,
                      clock_out: newIso,
                      total_hours: totalH,
                      overtime_hours: overtimeH,
                    })
                  }}
                  className="w-full border rounded px-3 py-2 mt-1"
                />
              </div>
              <div>
                <label className="text-xs text-gray-500">备注</label>
                <input
                  type="text"
                  value={editing.note ?? ''}
                  onChange={(e) => setEditing({ ...editing, note: e.target.value || null })}
                  className="w-full border rounded px-3 py-2 mt-1"
                  placeholder="选填"
                />
              </div>
            </div>

            <div className="flex justify-between mt-6">
              <button onClick={handleDelete} className="text-red-500 text-sm">删除</button>
              <div className="flex gap-3">
                <button onClick={() => setEditing(null)} className="text-gray-500 text-sm">取消</button>
                <button onClick={handleSave} className="text-blue-500 text-sm font-medium">保存</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 新增记录弹窗 */}
      {adding && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" onClick={() => setAdding(false)}>
          <div className="bg-white rounded-xl p-6 w-80 shadow-xl" onClick={(e) => e.stopPropagation()}>
            <h3 className="font-medium text-lg mb-4">新增记录</h3>

            <div className="space-y-3">
              <div>
                <label className="text-xs text-gray-500">日期</label>
                <input
                  type="date"
                  value={addDate}
                  onChange={(e) => setAddDate(e.target.value)}
                  className="w-full border rounded px-3 py-2 mt-1"
                />
              </div>
              <div>
                <label className="text-xs text-gray-500">上班时间</label>
                <input
                  type="time"
                  value={addClockIn}
                  onChange={(e) => setAddClockIn(e.target.value)}
                  className="w-full border rounded px-3 py-2 mt-1"
                />
              </div>
              <div>
                <label className="text-xs text-gray-500">下班时间</label>
                <input
                  type="time"
                  value={addClockOut}
                  onChange={(e) => setAddClockOut(e.target.value)}
                  className="w-full border rounded px-3 py-2 mt-1"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 mt-6">
              <button onClick={() => setAdding(false)} className="text-gray-500 text-sm">取消</button>
              <button onClick={handleAdd} className="text-blue-500 text-sm font-medium">添加</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
