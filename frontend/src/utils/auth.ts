export type StoredUser = {
  id: number;
  email: string;
  firstName: string;
  lastName: string;
};

const TOKEN_KEY = "token";
const USER_KEY = "user";

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function isAuthenticated() {
  return Boolean(getToken());
}

export function getStoredUser(): StoredUser | null {
  const rawUser = localStorage.getItem(USER_KEY);
  if (!rawUser) return null;

  try {
    return JSON.parse(rawUser) as StoredUser;
  } catch {
    return null;
  }
}

export function setStoredAuth(token: string, user?: StoredUser) {
  localStorage.setItem(TOKEN_KEY, token);
  if (user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  }
}

export function setStoredUser(user: StoredUser) {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearStoredAuth() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export async function apiFetch(input: RequestInfo | URL, init: RequestInit = {}) {
  const headers = new Headers(init.headers ?? undefined);
  const token = getToken();
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(input, { ...init, headers });
  if (response.status === 401) {
    clearStoredAuth();
    window.location.assign("/signin");
  }

  return response;
}

export function getRecordingUrl(baseUrl: string, filename: string) {
  const token = getToken();
  const normalizedBaseUrl = baseUrl.endsWith("/") ? baseUrl.slice(0, -1) : baseUrl;
  const url = new URL(`${normalizedBaseUrl}/recordings/${filename}`);
  if (token) {
    url.searchParams.set("token", token);
  }
  return url.toString();
}
