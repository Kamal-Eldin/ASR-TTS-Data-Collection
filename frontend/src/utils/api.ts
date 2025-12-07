export const API_BASE = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8500';
const LOCAL_TOKEN_KEY = 'auth_token';

export type JsonValue = Record<string, any> | string | number | boolean | null | undefined;

export function authHeaders(token?: string, extra: HeadersInit = {}): HeadersInit {
  const activeToken = token || (typeof localStorage !== 'undefined' ? localStorage.getItem(LOCAL_TOKEN_KEY) || undefined : undefined);
  if (!activeToken) return extra;
  return { ...extra, Authorization: `Bearer ${activeToken}` };
}

export async function fetchJson<T = any>(
  path: string,
  token?: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = authHeaders(token, options.headers || {});
  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const isJson = (res.headers.get('content-type') || '').includes('application/json');
  const body = isJson ? await res.json() : await res.text();

  if (!res.ok) {
    const detail = typeof body === 'string' ? body : body?.detail;
    throw new Error(detail || `Request failed with status ${res.status}`);
  }

  return body as T;
}
