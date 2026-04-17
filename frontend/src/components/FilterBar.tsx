import { Search, X } from 'lucide-react'
import type { EventFilters } from '../types'
import type { AccountItem } from '../types'

interface FilterBarProps {
  filters: EventFilters
  onChange: (filters: EventFilters) => void
  accounts?: AccountItem[]
}

const SERVICES = ['EC2', 'ECS', 'RDS', 'Lambda', 'S3', 'IAM', 'CloudFront', 'DynamoDB', 'OpenSearch', 'ELB']
const URGENCY_LEVELS = ['Critical', 'High', 'Medium', 'Low']
const STATUSES = ['Open', 'Closed', 'Upcoming']
const FOLLOW_UP_STATUSES = ['Pending', 'In Progress', 'Resolved']

export function FilterBar({ filters, onChange, accounts = [] }: FilterBarProps) {
  function update(key: keyof EventFilters, value: string) {
    onChange({ ...filters, [key]: value || undefined })
  }

  function clearAll() {
    onChange({})
  }

  const hasFilters = Object.values(filters).some(Boolean)

  return (
    <div className="bg-white rounded-lg shadow-sm p-4 space-y-3">
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-48">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Search events..."
            value={filters.search || ''}
            onChange={e => update('search', e.target.value)}
            className="w-full pl-9 pr-3 py-2 border border-gray-200 rounded text-sm focus:outline-none focus:ring-2 focus:ring-[#FF9900]"
          />
        </div>

        <select
          value={filters.service || ''}
          onChange={e => update('service', e.target.value)}
          className="px-3 py-2 border border-gray-200 rounded text-sm focus:outline-none focus:ring-2 focus:ring-[#FF9900]"
        >
          <option value="">All Services</option>
          {SERVICES.map(s => <option key={s} value={s}>{s}</option>)}
        </select>

        <select
          value={filters.urgency || ''}
          onChange={e => update('urgency', e.target.value)}
          className="px-3 py-2 border border-gray-200 rounded text-sm focus:outline-none focus:ring-2 focus:ring-[#FF9900]"
        >
          <option value="">All Urgency</option>
          {URGENCY_LEVELS.map(u => <option key={u} value={u}>{u}</option>)}
        </select>

        <select
          value={filters.status || ''}
          onChange={e => update('status', e.target.value)}
          className="px-3 py-2 border border-gray-200 rounded text-sm focus:outline-none focus:ring-2 focus:ring-[#FF9900]"
        >
          <option value="">All Status</option>
          {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
        </select>

        <select
          value={filters.followUpStatus || ''}
          onChange={e => update('followUpStatus', e.target.value)}
          className="px-3 py-2 border border-gray-200 rounded text-sm focus:outline-none focus:ring-2 focus:ring-[#FF9900]"
        >
          <option value="">All Follow-up</option>
          {FOLLOW_UP_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
        </select>

        {accounts.length > 0 && (
          <select
            value={filters.accountId || ''}
            onChange={e => update('accountId', e.target.value)}
            className="px-3 py-2 border border-gray-200 rounded text-sm focus:outline-none focus:ring-2 focus:ring-[#FF9900]"
          >
            <option value="">All Accounts</option>
            {accounts.map(a => (
              <option key={a.accountId} value={a.accountId}>
                {a.accountAlias || a.accountId}
              </option>
            ))}
          </select>
        )}

        {hasFilters && (
          <button
            onClick={clearAll}
            className="flex items-center gap-1 px-3 py-2 text-sm text-red-600 hover:bg-red-50 rounded"
          >
            <X size={14} />
            Clear
          </button>
        )}
      </div>
    </div>
  )
}
