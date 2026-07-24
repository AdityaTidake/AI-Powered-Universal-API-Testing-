/**
 * Zustand auth store.
 * Manages current user, tokens, and authentication state.
 */
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User } from '../types';
import { authAPI } from '../api';

interface AuthState {
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  // Actions
  init:     () => Promise<void>;
  login:    (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, full_name: string, org_name?: string) => Promise<void>;
  logout:   () => Promise<void>;
  fetchMe:  () => Promise<void>;
  setTokens: (access: string, refresh: string) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      isAuthenticated: false,
      isLoading: false,

      setTokens: (access, refresh) => {
        localStorage.setItem('access_token', access);
        localStorage.setItem('refresh_token', refresh);
        set({ accessToken: access, isAuthenticated: true });
      },

      // Called once on app mount — restores session from persisted token
      init: async () => {
        const token = localStorage.getItem('access_token');
        if (!token) return;
        set({ accessToken: token, isAuthenticated: true });
        await get().fetchMe();
      },

      login: async (email, password) => {
        set({ isLoading: true });
        try {
          const { data } = await authAPI.login({ email, password });
          get().setTokens(data.access_token, data.refresh_token);
          await get().fetchMe();
        } finally {
          set({ isLoading: false });
        }
      },

      register: async (email, password, full_name, org_name) => {
        set({ isLoading: true });
        try {
          const { data } = await authAPI.register({ email, password, full_name, org_name });
          get().setTokens(data.access_token, data.refresh_token);
          await get().fetchMe();
        } finally {
          set({ isLoading: false });
        }
      },

      logout: async () => {
        try { await authAPI.logout(); } catch { /* ignore */ }
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        set({ user: null, accessToken: null, isAuthenticated: false });
      },

      fetchMe: async () => {
        try {
          const { data } = await authAPI.me();
          set({ user: data, isAuthenticated: true });
        } catch {
          set({ user: null, isAuthenticated: false });
        }
      },
    }),
    {
      name: 'specguard-auth',
      partialize: state => ({
        accessToken: state.accessToken,
        isAuthenticated: state.isAuthenticated,
        user: state.user,
      }),
    },
  ),
);
