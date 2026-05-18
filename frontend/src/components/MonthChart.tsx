import { BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Tooltip } from 'recharts'

interface DailyHour {
  date: string
  hours: number
}

export default function MonthChart({ data }: { data: DailyHour[] }) {
  return (
    <div className="h-48">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 5, right: 5, left: -25, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="date" tick={{ fontSize: 10 }} interval={4} />
          <YAxis tick={{ fontSize: 10 }} domain={[0, 12]} />
          <Tooltip
            formatter={(value: number) => [`${value}h`, '工时']}
            labelStyle={{ fontSize: 12 }}
            contentStyle={{ fontSize: 12 }}
          />
          <Bar dataKey="hours" fill="#3b82f6" radius={[4, 4, 0, 0]} maxBarSize={20} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
