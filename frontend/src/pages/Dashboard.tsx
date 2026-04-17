import { Link } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts'
import { StatsCards } from '../components/StatsCards'
import { NotificationTable } from '../components/NotificationTable'
import { UrgencyBadge } from '../components/StatusBadge'
import { useStats, useNotifications } from '../hooks/useNotifications'

export function Dashboard() {
  const { data: stats, isLoading: statsLoading } = useStats()
  const { data: eventsData, isLoading: eventsLoading } = useNotifications({ urgency: 'Critical' }, undefined)

  const serviceChartData = Object.entries(stats?.byService || {})
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 10)

  const urgencyChartData = Object.entries(stats?.byUrgency || {}).map(([name, value]) => ({ name, value }))

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">Dashboard</h1>
        <Link
          to="/notifications"
          className="px-4 py-2 bg-[#FF9900] text-white text-sm rounded hover:bg-orange-600"
        >
          View All Events
        </Link>
      </div>

      <StatsCards stats={stats} isLoading={statsLoading} />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow-sm p-4">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Events by Service (Top 10)</h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={serviceChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="value" fill="#FF9900" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-4">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Events by Urgency</h2>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={urgencyChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="value" fill="#232F3E" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div>
        <h2 className="text-sm font-semibold text-gray-700 mb-3">Most Urgent Events</h2>
        <NotificationTable
          events={(eventsData?.items || []).slice(0, 10)}
          isLoading={eventsLoading}
        />
      </div>
    </div>
  )
}
