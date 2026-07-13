const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1'

export class ApiError extends Error {
  constructor(public status: number, public details: { code?: string; message?: string; fields?: Record<string, string> }) { super(details.message ?? 'Something went wrong') }
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('access_token')
  const response = await fetch(`${API_URL}${path}`, { ...options, headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}), ...options.headers } })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    const details = body.error ?? body.detail ?? { message: 'Request failed' }
    throw new ApiError(response.status, details)
  }
  return response.json()
}
