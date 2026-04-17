export interface HealthEvent {
  eventArn: string
  accountId: string
  accountAlias?: string
  service: string
  eventTypeCode: string
  eventTypeCategory?: string
  region?: string
  startTime: string
  endTime?: string
  deadline?: string
  lastUpdated?: string
  statusCode?: string
  status?: string
  affectedResources?: string[]
  rawEventUrl?: string
  awsHealthUrl?: string
  summary?: string
  recommendedActions?: string[]
  urgency: 'Critical' | 'High' | 'Medium' | 'Low'
  followUpStatus: 'Pending' | 'In Progress' | 'Resolved'
  followUpNotes?: string
  followUpOwner?: string
  llmProcessed?: boolean
}

export interface EventsResponse {
  items: HealthEvent[]
  nextKey?: string
  count: number
}

export interface StatsResponse {
  total: number
  byUrgency: Record<string, number>
  byStatus: Record<string, number>
  byService: Record<string, number>
  upcomingDeadlines: number
  pendingFollowUps: number
}

export interface AccountItem {
  accountId: string
  accountAlias?: string
}

export interface EventFilters {
  search?: string
  service?: string
  urgency?: string
  status?: string
  followUpStatus?: string
  accountId?: string
  dateFrom?: string
  dateTo?: string
}
