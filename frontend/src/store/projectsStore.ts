/**
 * TanStack Query hooks for the Projects resource.
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { projectsAPI } from '../api';
import type { ProjectCreate } from '../types';

export const PROJECTS_KEY = ['projects'] as const;
export const projectKey = (id: string) => ['projects', id] as const;

// ── List ──────────────────────────────────────────────────────────────────────
export function useProjects() {
  return useQuery({
    queryKey: PROJECTS_KEY,
    queryFn: () => projectsAPI.list().then(r => r.data),
  });
}

// ── Single ────────────────────────────────────────────────────────────────────
export function useProject(id: string | undefined) {
  return useQuery({
    queryKey: projectKey(id!),
    queryFn: () => projectsAPI.get(id!).then(r => r.data),
    enabled: !!id,
  });
}

// ── Create ────────────────────────────────────────────────────────────────────
export function useCreateProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: ProjectCreate) => projectsAPI.create(data).then(r => r.data),
    onSuccess: (project) => {
      qc.invalidateQueries({ queryKey: PROJECTS_KEY });
      toast.success(`Project "${project.name}" created!`);
    },
    onError: () => {
      toast.error('Failed to create project.');
    },
  });
}

// ── Delete ────────────────────────────────────────────────────────────────────
export function useDeleteProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => projectsAPI.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: PROJECTS_KEY });
      toast.success('Project deleted.');
    },
    onError: () => {
      toast.error('Failed to delete project.');
    },
  });
}

// ── Upload Spec ───────────────────────────────────────────────────────────────
export function useUploadSpec() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, file }: { id: string; file: File }) =>
      projectsAPI.uploadSpec(id, file).then(r => r.data),
    onSuccess: (project) => {
      qc.invalidateQueries({ queryKey: PROJECTS_KEY });
      qc.invalidateQueries({ queryKey: projectKey(project.id) });
      toast.success('OpenAPI spec uploaded successfully!');
    },
    onError: () => {
      toast.error('Failed to upload spec. Ensure it is a valid OpenAPI YAML/JSON file.');
    },
  });
}
