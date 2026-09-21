const TOKEN_KEY = 'recyclesort.token'
const USER_KEY = 'recyclesort.user'

export type User = { id: number; email: string; points: number }

export type ScanResult = {
  predicted_class: string
  confidence: number
  is_recyclable: boolean
  bin_message: string
  fun_fact: string
  points_awarded: number
  total_points: number
  model_loaded: boolean
}

export type ScanLog = {
  id: number
  user_id: number
  user_email?: string | null
  predicted_class: string
  confidence: number
  is_recyclable: boolean
  points_awarded: number
  created_at: string
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem(TOKEN_KEY)
  const headers = new Headers(init.headers)
  if (token) headers.set('Authorization', `Bearer ${token}`)
  const response = await fetch(path, { ...init, headers })
  const text = await response.text()
  let data: unknown = null
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = { detail: text }
    }
  }
  if (!response.ok) {
    const detail =
      typeof data === 'object' && data && 'detail' in data
        ? String((data as { detail: unknown }).detail)
        : `Request failed (${response.status})`
    throw new Error(detail)
  }
  return data as T
}

export function saveSession(token: string, user: User) {
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

export function loadUser(): User | null {
  const raw = localStorage.getItem(USER_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as User
  } catch {
    return null
  }
}

export function isAuthed() {
  return Boolean(localStorage.getItem(TOKEN_KEY))
}

export const api = {
  register: (email: string, password: string) =>
    request<{ access_token: string; user: User }>('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    }),
  login: (email: string, password: string) =>
    request<{ access_token: string; user: User }>('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    }),
  me: () => request<User>('/api/auth/me'),
  profile: () => request<User>('/api/profile'),
  myLogs: () => request<ScanLog[]>('/api/logs/me'),
  upload: async (file: File) => {
    const body = new FormData()
    body.append('file', file)
    return request<ScanResult>('/api/upload', { method: 'POST', body })
  },
  adminLogs: (adminKey: string) =>
    request<ScanLog[]>('/api/admin/logs', { headers: { 'X-Admin-Key': adminKey } }),
  adminBoard: (adminKey: string) =>
    request<{ email: string; points: number }[]>('/api/admin/leaderboard', {
      headers: { 'X-Admin-Key': adminKey },
    }),
  health: () => request<{ status: string }>('/health'),
}
