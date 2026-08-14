import { create } from 'zustand';
import { orgsAPI } from '../api';
import type { Organization, OrgCreate, OrgUpdate, OrgMemberAdd, Project } from '../types';

interface OrgState {
  orgs: Organization[];
  currentOrg: Organization | null;
  orgProjects: Project[];
  loading: boolean;
  error: string | null;

  // Actions
  fetchOrgs: () => Promise<void>;
  fetchOrg: (id: string) => Promise<void>;
  createOrg: (data: OrgCreate) => Promise<Organization>;
  updateOrg: (id: string, data: OrgUpdate) => Promise<void>;
  deleteOrg: (id: string) => Promise<void>;
  addMember: (id: string, data: OrgMemberAdd) => Promise<void>;
  removeMember: (id: string, userId: string) => Promise<void>;
  fetchOrgProjects: (id: string) => Promise<void>;
  setCurrentOrg: (org: Organization | null) => void;
}

export const useOrgStore = create<OrgState>((set) => ({
  orgs: [],
  currentOrg: null,
  orgProjects: [],
  loading: false,
  error: null,

  fetchOrgs: async () => {
    set({ loading: true, error: null });
    try {
      const { data } = await orgsAPI.list();
      set({ orgs: data, loading: false });
    } catch (err: any) {
      set({ error: err.response?.data?.message || 'Failed to fetch organizations', loading: false });
    }
  },

  fetchOrg: async (id: string) => {
    set({ loading: true, error: null });
    try {
      const { data } = await orgsAPI.get(id);
      set({ currentOrg: data, loading: false });
    } catch (err: any) {
      set({ error: err.response?.data?.message || 'Failed to fetch organization details', loading: false });
    }
  },

  createOrg: async (data: OrgCreate) => {
    set({ loading: true, error: null });
    try {
      const response = await orgsAPI.create(data);
      set(state => ({ orgs: [response.data, ...state.orgs], loading: false }));
      return response.data;
    } catch (err: any) {
      const msg = err.response?.data?.message || 'Failed to create organization';
      set({ error: msg, loading: false });
      throw new Error(msg);
    }
  },

  updateOrg: async (id: string, data: OrgUpdate) => {
    set({ loading: true, error: null });
    try {
      const response = await orgsAPI.update(id, data);
      set(state => ({
        orgs: state.orgs.map(o => (o.id === id ? response.data : o)),
        currentOrg: state.currentOrg?.id === id ? response.data : state.currentOrg,
        loading: false
      }));
    } catch (err: any) {
      const msg = err.response?.data?.message || 'Failed to update organization';
      set({ error: msg, loading: false });
      throw new Error(msg);
    }
  },

  deleteOrg: async (id: string) => {
    set({ loading: true, error: null });
    try {
      await orgsAPI.delete(id);
      set(state => ({
        orgs: state.orgs.filter(o => o.id !== id),
        currentOrg: state.currentOrg?.id === id ? null : state.currentOrg,
        loading: false
      }));
    } catch (err: any) {
      const msg = err.response?.data?.message || 'Failed to delete organization';
      set({ error: msg, loading: false });
      throw new Error(msg);
    }
  },

  addMember: async (id: string, data: OrgMemberAdd) => {
    set({ loading: true, error: null });
    try {
      const response = await orgsAPI.addMember(id, data);
      set(state => ({
        currentOrg: state.currentOrg?.id === id ? response.data : state.currentOrg,
        orgs: state.orgs.map(o => (o.id === id ? response.data : o)),
        loading: false
      }));
    } catch (err: any) {
      const msg = err.response?.data?.message || 'Failed to add member';
      set({ error: msg, loading: false });
      throw new Error(msg);
    }
  },

  removeMember: async (id: string, userId: string) => {
    set({ loading: true, error: null });
    try {
      const response = await orgsAPI.removeMember(id, userId);
      set(state => ({
        currentOrg: state.currentOrg?.id === id ? response.data : state.currentOrg,
        orgs: state.orgs.map(o => (o.id === id ? response.data : o)),
        loading: false
      }));
    } catch (err: any) {
      const msg = err.response?.data?.message || 'Failed to remove member';
      set({ error: msg, loading: false });
      throw new Error(msg);
    }
  },

  fetchOrgProjects: async (id: string) => {
    set({ loading: true, error: null });
    try {
      const { data } = await orgsAPI.listProjects(id);
      set({ orgProjects: data, loading: false });
    } catch (err: any) {
      set({ error: err.response?.data?.message || 'Failed to fetch organization projects', loading: false });
    }
  },

  setCurrentOrg: (org) => set({ currentOrg: org }),
}));
