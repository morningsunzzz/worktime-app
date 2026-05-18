import { useState, useEffect } from 'react'
import { api, type Settings, type WorkRecord } from '../api/client'
import { exportCSV } from '../utils/export'

export default function SettingsPage() {
  const [settings, setSettings] = useState<Settings>({ standard_hours: 8, lunch_break_minutes: 60, pre_hours: 1 })
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    api.getSettings().then((s) => {
      setSettings(s as Settings)
      setLoaded(true)
    })
  }, [])

  const handleSave = (s: Settings) => {
    setSettings(s)
    api.saveSettings(s)
  }

  const handleExport = async () => {
    const all = await api.getAllRecords()
    exportCSV(all as WorkRecord[])
  }

  if (!loaded) return null

  return (
    <div className="px-4 py-6 space-y-6">
      <h2 className="text-lg font-semibold">设置</h2>

      {/* 标准工时 */}
      <div className="bg-gray-50 rounded-xl p-4">
        <label className="text-sm text-gray-500">标准日工时（小时）</label>
        <div className="flex items-center gap-2 mt-2">
          <input
            type="range"
            min={4}
            max={12}
            step={0.5}
            value={settings.standard_hours}
            onChange={(e) => handleSave({ ...settings, standard_hours: +e.target.value })}
            className="flex-1"
          />
          <span className="text-lg font-bold w-10 text-right">{settings.standard_hours}h</span>
        </div>
        <p className="text-xs text-gray-400 mt-1">超出部分计入加班</p>
      </div>

      {/* 午休时长 */}
      <div className="bg-gray-50 rounded-xl p-4">
        <label className="text-sm text-gray-500">午休时长（分钟，0=不扣除）</label>
        <div className="flex items-center gap-2 mt-2">
          <input
            type="range"
            min={0}
            max={120}
            step={15}
            value={settings.lunch_break_minutes}
            onChange={(e) => handleSave({ ...settings, lunch_break_minutes: +e.target.value })}
            className="flex-1"
          />
          <span className="text-lg font-bold w-14 text-right">{settings.lunch_break_minutes}min</span>
        </div>
      </div>

      {/* 导出 */}
      <button
        onClick={handleExport}
        className="w-full py-3 bg-blue-500 text-white rounded-xl font-medium active:bg-blue-600"
      >
        导出 CSV
      </button>

      <p className="text-xs text-gray-400 text-center">
        所有数据仅存储在您的设备上，不会上传到任何服务器。
      </p>
    </div>
  )
}
