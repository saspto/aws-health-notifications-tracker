import { AlertTriangle, Clock, CheckSquare, Activity } from 'lucide-react'
import type { StatsResponse } from '../types'

interface StatsCardsProps {
  stats?: StatsResponse
  isLoading?: boolean
}

export function StatsCards({ stats, isLoading }: StatsCardsProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="bg-white rounded-lg p-4 shadow-sm animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-2" />
            <div className="h-8 bg-gray-200 rounded w-1/2" />
          </div>
        ))}
      </div>
    )
  }

  const cards = [
    { label: 'Total Events', value: stats?.total ?? 0, icon: Activity, color: 'text-blue-600' },
    { label: 'Critical', value: stats?.byUrgency?.Critical ?? 0, icon: AlertTriangle, color: 'text-red-600' },
    { label: 'High', value: stats?.byUrgency?.High ?? 0, icon: AlertTriangle, color: 'text-orange-500' },
    { label: 'Due This Week', value: stats?.upcomingDeadlines ?? 0, icon: Clock, color: 'text-yellow-600' },
    { label: 'Pending Follow-ups', value: stats?.pendingFollowUps ?? 0, icon: CheckSquare, color: 'text-purple-600' },
  ]

  return (
    <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
      {cards.map(({ label, value, icon: Icon, color }) => (
        <div key={label} className="bg-white rounded-lg p-4 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-gray-500">{label}</p>
            <Icon size={18} className={color} />
          </div>
          <p className="text-2xl font-bold text-gray-800">{value}</p>
        </div>
      ))}
    </div>
  )
}
