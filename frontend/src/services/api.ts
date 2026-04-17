import { fetchAuthSession } from 'aws-amplify/auth'
import type { HealthEvent, EventsResponse, StatsResponse, AccountItem, EventFilters } from '../types'
import awsConfig from '../aws-exports'

const API_BASE = awsConfig.apiEndpoint?.replace(/\/$/, '') || ''

async function getAuthToken(): Promise<string> {
  try {
    const session = await fetchAuthSession()
    return session.tokens?.idToken?.toString() || ''
  } catch {
    return ''
  }
}

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = await getAuthToken()
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: token } : {}),
      ...options.headers,
    },
  })
  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`)
  }
  return response.json() as Promise<T>
}

function buildQuery(filters: EventFilters & { lastKey?: string; limit?: number }): string {
  const params = new URLSearchParams()
  if (filters.search) params.set('search', filters.search)
  if (filters.service) params.set('service', filters.service)
  if (filters.urgency) params.set('urgency', filters.urgency)
  if (filters.status) params.set('status', filters.status)
  if (filters.followUpStatus) params.set('followUpStatus', filters.followUpStatus)
  if (filters.accountId) params.set('accountId', filters.accountId)
  if (filters.lastKey) params.set('lastKey', filters.lastKey)
  if (filters.limit) params.set('limit', String(filters.limit))
  return params.toString() ? `?${params.toString()}` : ''
}

export const api = {
  listEvents: (filters: EventFilters & { lastKey?: string } = {}) =>
    apiFetch<EventsResponse>(`/events${buildQuery(filters)}`),

  getEvent: (eventArn: string, accountId: string) =>
    apiFetch<HealthEvent>(`/events/${encodeURIComponent(eventArn)}/${encodeURIComponent(accountId)}`),

  patchEvent: (
    eventArn: string,
    accountId: string,
    data: { followUpStatus?: string; followUpNotes?: string; followUpOwner?: string }
  ) =>
    apiFetch<{ updated: boolean }>(
      `/events/${encodeURIComponent(eventArn)}/${encodeURIComponent(accountId)}`,
      { method: 'PATCH', body: JSON.stringify(data) }
    ),

  getStats: () => apiFetch<StatsResponse>('/stats'),

  getAccounts: () => apiFetch<AccountItem[]>('/accounts'),
}
