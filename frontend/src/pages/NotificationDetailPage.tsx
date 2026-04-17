import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, ExternalLink, ChevronDown, ChevronUp, Save } from 'lucide-react'
import { formatDistanceToNow, parseISO } from 'date-fns'
import { UrgencyBadge, FollowUpBadge } from '../components/StatusBadge'
import { useNotification, usePatchEvent } from '../hooks/useNotifications'

export function NotificationDetailPage() {
  const { eventArn, accountId } = useParams<{ eventArn: string; accountId: string }>()
  const navigate = useNavigate()
  const decodedArn = decodeURIComponent(eventArn || '')
  const decodedAccount = decodeURIComponent(accountId || '')

  const { data: event, isLoading } = useNotification(decodedArn, decodedAccount)
  const patchMutation = usePatchEvent()

  const [followUpStatus, setFollowUpStatus] = useState('')
  const [followUpOwner, setFollowUpOwner] = useState('')
  const [followUpNotes, setFollowUpNotes] = useState('')
  const [resourcesExpanded, setResourcesExpanded] = useState(false)
  const [saveMessage, setSaveMessage] = useState('')

  if (!isLoading && event && !followUpStatus) {
    setFollowUpStatus(event.followUpStatus || 'Pending')
    setFollowUpOwner(event.followUpOwner || '')
    setFollowUpNotes(event.followUpNotes || '')
  }

  async function handleSave() {
    if (!event) return
    try {
      await patchMutation.mutateAsync({
        eventArn: decodedArn,
        accountId: decodedAccount,
        data: { followUpStatus, followUpOwner, followUpNotes },
      })
      setSaveMessage('Saved successfully')
      setTimeout(() => setSaveMessage(''), 3000)
    } catch {
      setSaveMessage('Error saving')
      setTimeout(() => setSaveMessage(''), 3000)
    }
  }

  if (isLoading) {
    return (
      <div className="p-6 space-y-4 animate-pulse">
        <div className="h-6 bg-gray-200 rounded w-1/3" />
        <div className="h-32 bg-gray-200 rounded" />
      </div>
    )
  }

  if (!event) {
    return (
      <div className="p-6 text-center">
        <p className="text-gray-500">Event not found</p>
        <button onClick={() => navigate(-1)} className="mt-4 text-[#FF9900] hover:underline">Go back</button>
      </div>
    )
  }

  const deadline = event.deadline ? parseISO(event.deadline) : null

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate(-1)} className="text-gray-500 hover:text-gray-700">
          <ArrowLeft size={20} />
        </button>
        <div className="flex items-center gap-3">
          <h1 className="text-xl font-bold text-gray-800">{event.eventTypeCode}</h1>
          <UrgencyBadge urgency={event.urgency} />
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: 'Account', value: event.accountAlias || event.accountId },
          { label: 'Service', value: event.service },
          { label: 'Region', value: event.region || 'us-east-1' },
          { label: 'Status', value: event.status || 'Open' },
        ].map(({ label, value }) => (
          <div key={label} className="bg-white rounded-lg p-3 shadow-sm">
            <p className="text-xs text-gray-500">{label}</p>
            <p className="text-sm font-semibold text-gray-800 mt-0.5">{value}</p>
          </div>
        ))}
      </div>

      {deadline && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 flex items-center justify-between">
          <span className="text-sm font-medium text-yellow-800">
            Deadline: {event.deadline?.split('T')[0]}
          </span>
          <span className="text-sm text-yellow-700">
            {formatDistanceToNow(deadline, { addSuffix: true })}
          </span>
        </div>
      )}

      {event.summary && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <p className="text-xs font-semibold text-blue-700 uppercase mb-2">AI-Generated Summary</p>
          <p className="text-sm text-blue-900">{event.summary}</p>
        </div>
      )}

      {event.recommendedActions && event.recommendedActions.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm p-4">
          <p className="text-sm font-semibold text-gray-700 mb-3">Recommended Actions</p>
          <ul className="space-y-2">
            {event.recommendedActions.map((action, i) => (
              <li key={i} className="flex items-start gap-2">
                <input type="checkbox" className="mt-0.5 rounded" />
                <span className="text-sm text-gray-700">{action}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="bg-white rounded-lg shadow-sm p-4">
        <a
          href="https://health.aws.amazon.com/health/home#/account/dashboard/open-issues"
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 px-4 py-2 bg-[#FF9900] text-white rounded text-sm hover:bg-orange-600"
        >
          <ExternalLink size={14} />
          View in AWS Health Console
        </a>
      </div>

      {event.affectedResources && event.affectedResources.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm p-4">
          <button
            onClick={() => setResourcesExpanded(!resourcesExpanded)}
            className="flex items-center gap-2 text-sm font-semibold text-gray-700 w-full"
          >
            {resourcesExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            Affected Resources ({event.affectedResources.length})
          </button>
          {resourcesExpanded && (
            <ul className="mt-3 space-y-1">
              {event.affectedResources.map((arn, i) => (
                <li key={i} className="text-xs font-mono text-gray-600 bg-gray-50 px-2 py-1 rounded">{arn}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      <div className="bg-white rounded-lg shadow-sm p-4 space-y-4">
        <p className="text-sm font-semibold text-gray-700">Follow-up Tracker</p>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Status</label>
            <select
              value={followUpStatus}
              onChange={e => setFollowUpStatus(e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded text-sm focus:outline-none focus:ring-2 focus:ring-[#FF9900]"
            >
              <option>Pending</option>
              <option>In Progress</option>
              <option>Resolved</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Owner</label>
            <input
              type="text"
              value={followUpOwner}
              onChange={e => setFollowUpOwner(e.target.value)}
              placeholder="email or name"
              className="w-full px-3 py-2 border border-gray-200 rounded text-sm focus:outline-none focus:ring-2 focus:ring-[#FF9900]"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs text-gray-500 mb-1">Notes</label>
          <textarea
            value={followUpNotes}
            onChange={e => setFollowUpNotes(e.target.value)}
            rows={3}
            className="w-full px-3 py-2 border border-gray-200 rounded text-sm focus:outline-none focus:ring-2 focus:ring-[#FF9900]"
          />
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => void handleSave()}
            disabled={patchMutation.isPending}
            className="flex items-center gap-2 px-4 py-2 bg-[#FF9900] text-white rounded text-sm hover:bg-orange-600 disabled:opacity-50"
          >
            <Save size={14} />
            {patchMutation.isPending ? 'Saving...' : 'Save'}
          </button>
          {saveMessage && (
            <span className={`text-sm ${saveMessage.includes('Error') ? 'text-red-600' : 'text-green-600'}`}>
              {saveMessage}
            </span>
          )}
          {event.lastUpdated && (
            <span className="text-xs text-gray-400 ml-auto">Last updated: {event.lastUpdated.split('T')[0]}</span>
          )}
        </div>
      </div>
    </div>
  )
}
