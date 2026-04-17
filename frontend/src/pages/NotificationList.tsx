import { useState, useEffect } from 'react'
import { Download } from 'lucide-react'
import { FilterBar } from '../components/FilterBar'
import { NotificationTable } from '../components/NotificationTable'
import { useNotifications, useAccounts } from '../hooks/useNotifications'
import type { EventFilters } from '../types'

function exportToCsv(items: object[]) {
  if (!items.length) return
  const keys = Object.keys(items[0])
  const rows = [keys.join(','), ...items.map(item =>
    keys.map(k => JSON.stringify((item as Record<string, unknown>)[k] ?? '')).join(',')
  )]
  const blob = new Blob([rows.join('\n')], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'health-events.csv'
  a.click()
  URL.revokeObjectURL(url)
}

export function NotificationList() {
  const [filters, setFilters] = useState<EventFilters>(() => {
    try {
      const saved = sessionStorage.getItem('notif-filters')
      return saved ? (JSON.parse(saved) as EventFilters) : {}
    } catch {
      return {}
    }
  })
  const [lastKey, setLastKey] = useState<string | undefined>()

  useEffect(() => {
    sessionStorage.setItem('notif-filters', JSON.stringify(filters))
    setLastKey(undefined)
  }, [filters])

  const { data, isLoading } = useNotifications(filters, lastKey)
  const { data: accounts } = useAccounts()

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">Notifications</h1>
        <button
          onClick={() => exportToCsv(data?.items || [])}
          className="flex items-center gap-2 px-3 py-2 border border-gray-200 rounded text-sm hover:bg-gray-50"
        >
          <Download size={14} />
          Export CSV
        </button>
      </div>

      <FilterBar filters={filters} onChange={setFilters} accounts={accounts} />

      <NotificationTable events={data?.items || []} isLoading={isLoading} />

      {(data?.nextKey || lastKey) && (
        <div className="flex justify-center gap-3">
          {lastKey && (
            <button
              onClick={() => setLastKey(undefined)}
              className="px-4 py-2 border border-gray-200 rounded text-sm hover:bg-gray-50"
            >
              First Page
            </button>
          )}
          {data?.nextKey && (
            <button
              onClick={() => setLastKey(data.nextKey)}
              className="px-4 py-2 bg-[#FF9900] text-white rounded text-sm hover:bg-orange-600"
            >
              Next Page
            </button>
          )}
        </div>
      )}
    </div>
  )
}
