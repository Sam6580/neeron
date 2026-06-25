// Centralized API client for the NEERON backend.
// Handles base URL, JWT bearer auth, response-envelope unwrapping and errors.

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

const ACCESS_TOKEN_KEY = "neeron_auth_token";
const REFRESH_TOKEN_KEY = "neeron_refresh_token";

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setTokens(accessToken: string, refreshToken?: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  if (refreshToken) {
    window.localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  }
}

export function clearTokens(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
  window.localStorage.removeItem(REFRESH_TOKEN_KEY);
}

export class ApiError extends Error {
  status: number;
  code?: string;

  constructor(message: string, status: number, code?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
  }
}

interface ApiEnvelope<T> {
  success: boolean;
  timestamp?: string;
  data: T;
  error?: { code?: string; message?: string };
}

interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  auth?: boolean;
  _isRetry?: boolean;
}

let isRefreshingPromise: Promise<string | null> | null = null;

async function performTokenRefresh(): Promise<string | null> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return null;

  try {
    const finalHeaders = new Headers();
    finalHeaders.set("Content-Type", "application/json");

    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: "POST",
      headers: finalHeaders,
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) {
      clearTokens();
      return null;
    }

    const payload = (await response.json()) as ApiEnvelope<{ access_token: string; refresh_token: string }>;
    if (payload?.data?.access_token) {
      setTokens(payload.data.access_token, payload.data.refresh_token);
      return payload.data.access_token;
    }
    clearTokens();
    return null;
  } catch {
    clearTokens();
    return null;
  } finally {
    isRefreshingPromise = null;
  }
}

/**
 * Perform a request against the API and return the unwrapped `data` payload.
 * Throws {@link ApiError} on non-2xx responses.
 */
export async function apiFetch<T>(
  endpoint: string,
  options: RequestOptions = {},
): Promise<T> {
  const { body, auth = true, headers, _isRetry, ...rest } = options;

  const finalHeaders = new Headers(headers);
  finalHeaders.set("Content-Type", "application/json");

  if (auth) {
    const token = getAccessToken();
    if (token) finalHeaders.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...rest,
    headers: finalHeaders,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  let payload: ApiEnvelope<T> | null = null;
  try {
    payload = (await response.json()) as ApiEnvelope<T>;
  } catch {
    payload = null;
  }

  if (!response.ok) {
    if (response.status === 401 && auth && getRefreshToken() && !_isRetry) {
      if (!isRefreshingPromise) {
        isRefreshingPromise = performTokenRefresh();
      }
      const newAccessToken = await isRefreshingPromise;
      if (newAccessToken) {
        return apiFetch<T>(endpoint, {
          ...options,
          _isRetry: true,
        });
      }
    }

    const message =
      payload?.error?.message || response.statusText || "Request failed";
    if (response.status === 401) clearTokens();
    throw new ApiError(message, response.status, payload?.error?.code);
  }

  // Unwrap the standard { success, data } envelope when present.
  if (payload && typeof payload === "object" && "data" in payload) {
    return payload.data;
  }
  return payload as unknown as T;
}
