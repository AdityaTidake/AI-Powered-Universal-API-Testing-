/**
 * TanStack Query hooks for Analytics data.
 */
import { useQuery } from '@tanstack/react-query';
import { analyticsAPI } from '../api';

export const DASHBOARD_STATS_KEY = ['analytics', 'dashboard'] as const;
export const TRENDS_KEY          = ['analytics', 'trends']    as const;
export const COVERAGE_KEY        = ['analytics', 'coverage']  as const;

export function useDashboardStats() {
  return useQuery({
    queryKey: DASHBOARD_STATS_KEY,
    queryFn: () => analyticsAPI.dashboard().then(r => r.data),
    staleTime: 60_000, // 1 min
  });
}

export function useTrends() {
  return useQuery({
    queryKey: TRENDS_KEY,
    queryFn: () => analyticsAPI.trends().then(r => r.data),
    staleTime: 60_000,
  });
}

export function useCoverage() {
  return useQuery({
    queryKey: COVERAGE_KEY,
    queryFn: () => analyticsAPI.coverage().then(r => r.data),
    staleTime: 60_000,
  });
}
