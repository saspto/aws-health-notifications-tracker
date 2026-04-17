import { useNavigate } from 'react-router-dom'
import { formatDistanceToNow, parseISO, isBefore } from 'date-fns'
import { ChevronUp, ChevronDown } from 'lucide-react'
import { UrgencyBadge, FollowUpBadge } from './StatusBadge'
import type { HealthEvent } from '../types'

interface NotificationTableProps {
  events: HealthEvent[]
  isLoading?: boolean
}

function DeadlineCell({ deadline }: { deadline?: string }) {
  if (!deadline) return <span className="text-gray-400 text-sm">No deadline</span>
  try {
    const date = parseISO(deadline)
    const overdue = isBefore(date, new Date())
    const relative = formatDistanceToNow(date, { addSuffix: true })
    return (
      <span className={`text-sm ${overdue ? 'text-red-600 font-semibold' : 'text-gray-700'}`}>
        {overdue ? `Overdue ${relative}` : `Due ${relative}`}
      </span>
    )
  } catch {
    return <span className="text-gray-400 text-sm">{deadline}</span>
  }
}

export function NotificationTable({ events, isLoading }: NotificationTableProps) {
  const navigate = useNavigate()

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              {['Event Type', 'Service', 'Account', 'Deadline', 'Urgency', 'Follow-up'].map(h => (
                <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: 5 }).map((_, i) => (
              <tr key={i} className="border-b animate-pulse">
                {Array.from({ length: 6 }).map((_, j) => (
                  <td key={j} className="px-4 py-3"><div className="h-4 bg-gray-200 rounded" /></td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )
  }

  if (!events.length) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-12 text-center">
        <p className="text-gray-400 text-lg">No events found</p>
        <p className="text-gray-300 text-sm mt-1">Try adjusting your filters</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-sm overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 border-b">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Event Type</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Service</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Account</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Deadline</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Urgency</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase">Follow-up</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {events.map(event => (
            <tr
              key={`${event.eventArn}-${event.accountId}`}
              className="hover:bg-gray-50 cursor-pointer"
              onClick={() => {
                navigate(`/notifications/${encodeURIComponent(event.eventArn)}/${encodeURIComponent(event.accountId)}`)
              }}
            >
              <td className="px-4 py-3">
                <p className="font-medium text-gray-800 truncate max-w-xs">{event.eventTypeCode}</p>
                {event.summary && (
                  <p className="text-gray-500 text-xs truncate max-w-xs mt-0.5">{event.summary}</p>
                )}
              </td>
              <td className="px-4 py-3 text-gray-700">{event.service}</td>
              <td className="px-4 py-3">
                <p className="text-gray-700">{event.accountAlias || event.accountId}</p>
                <p className="text-gray-400 text-xs">{event.accountId}</p>
              </td>
              <td className="px-4 py-3"><DeadlineCell deadline={event.deadline} /></td>
              <td className="px-4 py-3"><UrgencyBadge urgency={event.urgency} /></td>
              <td className="px-4 py-3"><FollowUpBadge status={event.followUpStatus} /></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
