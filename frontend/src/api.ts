import { appConfig } from './env'

const API_URL = appConfig.apiUrl

export class ApiError extends Error {
  constructor(public status: number, public details: { code?: string; message?: string; fields?: Record<string, string>; current_revision?: number }) {
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
    const isPublicAuthRequest = path === '/auth/login' || path.startsWith('/auth/register')
    if (response.status === 401 && !isPublicAuthRequest) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      window.dispatchEvent(new CustomEvent('session-expired'))
    }
    throw new ApiError(response.status, details)
  }
  if (response.status === 204) return undefined as T
  return response.json()
}

// Binary sibling of `api` for authorized image delivery. Avatar routes require the
// bearer token, so a bare `<img src>` cannot load them; callers fetch the blob here
// and render it through an object URL instead. A 404 (no photo / not related) is a
// normal outcome the caller turns into an initials fallback.
export async function apiBlob(path: string): Promise<Blob> {
  const token = localStorage.getItem('access_token')
  let response: Response
  try {
    response = await fetch(`${API_URL}${path}`, {
      headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    })
  } catch {
    throw new ApiError(0, { code: 'network_error', message: 'The service is unavailable.' })
  }
  if (!response.ok) {
    if (response.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      window.dispatchEvent(new CustomEvent('session-expired'))
    }
    throw new ApiError(response.status, { code: 'media_unavailable', message: 'Image unavailable' })
  }
  return response.blob()
}

// Multipart-aware sibling of `api`. It shares authentication, session-expiry, and
// error handling but never sets `Content-Type`, so the browser can attach the
// multipart boundary itself. Pass a `FormData`; do not stringify.
export async function apiUpload<T>(path: string, form: FormData, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('access_token')
  let response: Response
  try {
    response = await fetch(`${API_URL}${path}`, {
      method: 'POST',
      ...options,
      body: form,
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...options.headers,
      },
    })
  } catch {
    throw new ApiError(0, { code: 'network_error', message: 'The service is unavailable. Your entries remain on this page; check your connection and try again.' })
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    const details = body.error ?? body.detail ?? { message: 'The upload could not be completed. Please try again.' }
    if (response.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
      window.dispatchEvent(new CustomEvent('session-expired'))
    }
    throw new ApiError(response.status, details)
  }
  if (response.status === 204) return undefined as T
  return response.json()
}
