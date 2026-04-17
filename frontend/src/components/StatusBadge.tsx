import clsx from 'clsx'

interface UrgencyBadgeProps {
  urgency: string
}

export function UrgencyBadge({ urgency }: UrgencyBadgeProps) {
  const colors: Record<string, string> = {
    Critical: 'bg-red-100 text-red-800 border-red-200',
    High: 'bg-orange-100 text-orange-800 border-orange-200',
    Medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    Low: 'bg-green-100 text-green-800 border-green-200',
  }
  return (
    <span className={clsx('px-2 py-0.5 rounded-full text-xs font-semibold border', colors[urgency] || 'bg-gray-100 text-gray-800')}>
      {urgency}
    </span>
  )
}

interface FollowUpBadgeProps {
  status: string
}

export function FollowUpBadge({ status }: FollowUpBadgeProps) {
  const colors: Record<string, string> = {
    Pending: 'bg-gray-100 text-gray-700 border-gray-200',
    'In Progress': 'bg-blue-100 text-blue-800 border-blue-200',
    Resolved: 'bg-green-100 text-green-800 border-green-200',
  }
  return (
    <span className={clsx('px-2 py-0.5 rounded-full text-xs font-semibold border', colors[status] || 'bg-gray-100 text-gray-700')}>
      {status}
    </span>
  )
}
