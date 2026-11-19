import type {
  CreateFuncionarioPayload,
  DeleteFuncionarioResponse,
  FuncionarioFilters,
  FuncionarioProfile,
  UpdateFuncionarioPayload,
} from '../types/auth'

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

function extractErrorMessage(data: unknown, fallback: string): string {
  if (!data || typeof data !== 'object') {
    return fallback
  }

  const record = data as Record<string, unknown>
  if (typeof record.detail === 'string' && record.detail.trim()) {
    return record.detail
  }
  if (typeof record.message === 'string' && record.message.trim()) {
    return record.message
  }

  const fieldMessages: string[] = []
  for (const [key, value] of Object.entries(record)) {
    if (Array.isArray(value) && value.length > 0) {
      fieldMessages.push(`${key}: ${value.map(String).join(' ')}`)
    } else if (typeof value === 'string' && value.trim()) {
      fieldMessages.push(`${key}: ${value}`)
    }
  }

  if (fieldMessages.length > 0) {
    return fieldMessages.join(' | ')
  }

  return JSON.stringify(data)
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
      errorDetail = extractErrorMessage(data, errorDetail)
    } catch {
      // Ignora erro caso corpo não seja JSON
    }
    throw new ApiError(errorDetail, response.status)
  }

  if (response.status === 204) {
    return {} as T
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

/**
 * Lista funcionários com filtros opcionais de nome e e-mail (RF01.02).
 * GET /api/funcionarios/?nome=...&email=...
 */
export async function fetchFuncionarios(
  token: string,
  filters?: FuncionarioFilters
): Promise<FuncionarioProfile[]> {
  const params = new URLSearchParams()
  if (filters?.nome?.trim()) {
    params.set('nome', filters.nome.trim())
  }
  if (filters?.email?.trim()) {
    params.set('email', filters.email.trim())
  }
  const queryString = params.toString()
  const endpoint = queryString ? `funcionarios/?${queryString}` : 'funcionarios/'

  return apiRequest<FuncionarioProfile[]>(endpoint, { method: 'GET' }, token)
}

/**
 * Cadastra um novo funcionário vinculando identidade no Supabase Auth (RF01.01).
 * POST /api/funcionarios/
 */
export async function createFuncionario(
  payload: CreateFuncionarioPayload,
  token: string
): Promise<FuncionarioProfile> {
  return apiRequest<FuncionarioProfile>(
    'funcionarios/',
    {
      method: 'POST',
      body: JSON.stringify(payload),
    },
    token
  )
}

/**
 * Atualiza os dados funcionais de um funcionário (nome, email, isAdmin) sem expor ou alterar senha (RF01.03).
 * PATCH /api/funcionarios/{idFuncionario}/
 */
export async function updateFuncionario(
  idFuncionario: number,
  payload: UpdateFuncionarioPayload,
  token: string
): Promise<FuncionarioProfile> {
  return apiRequest<FuncionarioProfile>(
    `funcionarios/${idFuncionario}/`,
    {
      method: 'PATCH',
      body: JSON.stringify(payload),
    },
    token
  )
}

/**
 * Remove um funcionário pelo seu identificador (RF01.04).
 * DELETE /api/funcionarios/{idFuncionario}/
 */
export async function deleteFuncionario(
  idFuncionario: number,
  token: string
): Promise<DeleteFuncionarioResponse> {
  return apiRequest<DeleteFuncionarioResponse>(
    `funcionarios/${idFuncionario}/`,
    {
      method: 'DELETE',
    },
    token
  )
}

/**
 * Remove um funcionário pelo seu endereço de e-mail (RF01.04).
 * DELETE /api/funcionarios/deletar-por-email/?email=...
 */
export async function deleteFuncionarioByEmail(
  email: string,
  token: string
): Promise<DeleteFuncionarioResponse> {
  const params = new URLSearchParams({ email: email.trim() })
  return apiRequest<DeleteFuncionarioResponse>(
    `funcionarios/deletar-por-email/?${params.toString()}`,
    {
      method: 'DELETE',
    },
    token
  )
}
