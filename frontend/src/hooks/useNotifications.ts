import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../services/api'
import type { EventFilters } from '../types'

export function useNotifications(filters: EventFilters = {}, lastKey?: string) {
  return useQuery({
    queryKey: ['notifications', filters, lastKey],
    queryFn: () => api.listEvents({ ...filters, lastKey }),
    staleTime: 30_000,
  })
}

export function useNotification(eventArn: string, accountId: string) {
  return useQuery({
    queryKey: ['notification', eventArn, accountId],
    queryFn: () => api.getEvent(eventArn, accountId),
    enabled: Boolean(eventArn && accountId),
  })
}

export function useStats() {
  return useQuery({
    queryKey: ['stats'],
    queryFn: api.getStats,
    staleTime: 60_000,
  })
}

export function useAccounts() {
  return useQuery({
    queryKey: ['accounts'],
    queryFn: api.getAccounts,
    staleTime: 300_000,
  })
}

export function usePatchEvent() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      eventArn,
      accountId,
      data,
    }: {
      eventArn: string
      accountId: string
      data: { followUpStatus?: string; followUpNotes?: string; followUpOwner?: string }
    }) => api.patchEvent(eventArn, accountId, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['notifications'] })
      void queryClient.invalidateQueries({ queryKey: ['notification'] })
      void queryClient.invalidateQueries({ queryKey: ['stats'] })
    },
  })
}
