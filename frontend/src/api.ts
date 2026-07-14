const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1'

export class ApiError extends Error {
  constructor(public status: number, public details: { code?: string; message?: string; fields?: Record<string, string> }) {
    super(details.message ?? 'The request could not be completed')
  }
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('access_token')
  let response: Response
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...options.headers,
      },
    })
  } catch {
    throw new ApiError(0, { code: 'network_error', message: 'The service is unavailable. Your entries remain on this page; check your connection and try again.' })
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    const details = body.error ?? body.detail ?? { message: 'The request could not be completed. Please try again.' }
    if (response.status === 401 && token) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      window.dispatchEvent(new CustomEvent('session-expired'))
    }
    throw new ApiError(response.status, details)
  }
  return response.json()
}
