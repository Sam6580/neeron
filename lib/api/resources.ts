// Typed endpoint wrappers around the API client.

import { apiFetch } from "./client";
import type {
  AlertResponse,
  LoginResponse,
  TankHealthResponse,
  TankResponse,
  UserProfile,
} from "./types";

export const authApi = {
  login: (email: string, password: string) =>
    apiFetch<LoginResponse>("/auth/login", {
      method: "POST",
      auth: false,
      body: { email, password },
    }),
  me: () => apiFetch<UserProfile>("/auth/me"),
  logout: () => apiFetch<{ success: boolean; message: string }>("/auth/logout", { method: "POST" }),
  refresh: (refreshToken: string) =>
    apiFetch<LoginResponse>("/auth/refresh", {
      method: "POST",
      auth: false,
      body: { refresh_token: refreshToken },
    }),
};

// The list endpoints return the full paginated envelope (data + pagination),
// so we request the raw envelope by reading `.data` ourselves.
export const tanksApi = {
  list: async (): Promise<TankResponse[]> => {
    // apiFetch unwraps `.data`; for paginated responses that is the array.
    return apiFetch<TankResponse[]>("/tanks");
  },
  get: (id: string) => apiFetch<TankResponse>(`/tanks/${id}`),
  health: (id: string) => apiFetch<TankHealthResponse>(`/tanks/${id}/health`),
};

export const alertsApi = {
  list: async (): Promise<AlertResponse[]> => apiFetch<AlertResponse[]>("/alerts"),
};

import type {
  Tank,
  Zone,
  Alert as AlertDTO,
  Recommendation,
  BiosecurityRecord,
  AnalyticsMetric,
} from "@/types";
import type { DashboardData } from "./types";

// View-shaped UI endpoints — each returns data exactly as the frontend types.
export const uiApi = {
  zones: () => apiFetch<Zone[]>("/ui/zones"),
  tanks: () => apiFetch<Tank[]>("/ui/tanks"),
  tank: (id: string) => apiFetch<Tank>(`/ui/tanks/${id}`),
  alerts: () => apiFetch<AlertDTO[]>("/ui/alerts"),
  recommendations: () => apiFetch<Recommendation[]>("/ui/recommendations"),
  biosecurity: () => apiFetch<BiosecurityRecord[]>("/ui/biosecurity"),
  analytics: () => apiFetch<AnalyticsMetric[]>("/ui/analytics"),
  dashboard: () => apiFetch<DashboardData>("/ui/dashboard"),
};
