import type { FuncionarioProfile } from '../types/auth'

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

/**
 * Utilitário para realizar requisições autenticadas à API do backend Django.
 * Injeta o cabeçalho Authorization: Bearer <token>.
 */
export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {},
  token?: string | null
): Promise<T> {
  const url = `${API_BASE_URL.replace(/\/$/, '')}/${endpoint.replace(/^\//, '')}`
  const headers = new Headers(options.headers || {})

  headers.set('Accept', 'application/json')
  if (!(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }

  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  const response = await fetch(url, {
    ...options,
    headers,
  })

  if (!response.ok) {
    let errorDetail = `Erro HTTP ${response.status}: ${response.statusText}`
    try {
      const data = await response.json()
      if (data && typeof data === 'object') {
        errorDetail = data.detail || data.message || JSON.stringify(data)
      }
    } catch {
      // Ignora erro caso corpo não seja JSON
    }
    throw new ApiError(errorDetail, response.status)
  }

  return response.json() as Promise<T>
}

/**
 * Consulta o perfil do funcionário autenticado via Supabase token.
 * GET /api/funcionarios/me/
 */
export async function fetchCurrentProfile(token: string): Promise<FuncionarioProfile> {
  return apiRequest<FuncionarioProfile>('funcionarios/me/', { method: 'GET' }, token)
}
