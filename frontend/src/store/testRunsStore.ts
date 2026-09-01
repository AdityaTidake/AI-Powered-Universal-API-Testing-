/**
 * TanStack Query hooks for Test Runs.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { testRunsAPI } from '../api';
import type { TestRunCreate } from '../types';
import { PROJECTS_KEY } from './projectsStore';

export const runsKey = (projectId: string) => ['test-runs', projectId] as const;
export const runKey  = (runId: string)     => ['test-run',  runId]     as const;

// ── List Runs for a Project ───────────────────────────────────────────────────
export function useTestRuns(projectId: string | undefined) {
  return useQuery({
    queryKey: runsKey(projectId!),
    queryFn: () => testRunsAPI.list(projectId!).then(r => r.data),
    enabled: !!projectId,
  });
}

// ── Get Single Run ────────────────────────────────────────────────────────────
export function useTestRun(runId: string | undefined) {
  return useQuery({
    queryKey: runKey(runId!),
    queryFn: () => testRunsAPI.get(runId!).then(r => r.data),
    enabled: !!runId,
  });
}

// ── Poll Run (for RUNNING/PENDING status) ─────────────────────────────────────
export function usePollTestRun(runId: string | undefined, active: boolean) {
  return useQuery({
    queryKey: runKey(runId!),
    queryFn: () => testRunsAPI.get(runId!).then(r => r.data),
    enabled: !!runId && active,
    refetchInterval: active ? 3_000 : false,
  });
}

// ── Create Run ────────────────────────────────────────────────────────────────
export function useCreateTestRun(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: TestRunCreate) =>
      testRunsAPI.create(projectId, data).then(r => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: runsKey(projectId) });
      qc.invalidateQueries({ queryKey: PROJECTS_KEY });
      toast.success('Test run launched!');
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.detail ?? 'Failed to launch test run.';
      toast.error(typeof msg === 'string' ? msg : JSON.stringify(msg));
    },
  });
}

// ── Delete Run ────────────────────────────────────────────────────────────────
export function useDeleteTestRun(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (runId: string) => testRunsAPI.delete(runId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: runsKey(projectId) });
      toast.success('Test run deleted.');
    },
    onError: () => {
      toast.error('Failed to delete test run.');
    },
  });
}

// ── Cancel Run ────────────────────────────────────────────────────────────────
export function useCancelTestRun(projectId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (runId: string) => testRunsAPI.cancel(runId),
    onSuccess: (_data, runId) => {
      qc.invalidateQueries({ queryKey: runsKey(projectId) });
      qc.invalidateQueries({ queryKey: runKey(runId) });
      toast.success('Test run cancelled.');
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.detail ?? 'Failed to cancel test run.';
      toast.error(typeof msg === 'string' ? msg : JSON.stringify(msg));
    },
  });
}

