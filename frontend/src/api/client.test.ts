import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { apiRequest, fetchCurrentProfile, ApiError } from './client'

describe('API Client', () => {
  const originalFetch = globalThis.fetch

  beforeEach(() => {
    vi.restoreAllMocks()
  })

  afterEach(() => {
    globalThis.fetch = originalFetch
  })

  it('anexa o header Authorization: Bearer quando fornecido token', async () => {
    const mockData = { idFuncionario: 1, nome: 'Admin' }
    const fetchSpy = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockData,
    })
    globalThis.fetch = fetchSpy

    const result = await apiRequest('test-endpoint/', {}, 'token-teste-123')

    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining('/api/test-endpoint/'),
      expect.objectContaining({
        headers: expect.any(Headers),
      })
    )

    const callArgs = fetchSpy.mock.calls[0]
    const headers = callArgs[1].headers as Headers
    expect(headers.get('Authorization')).toBe('Bearer token-teste-123')
    expect(headers.get('Accept')).toBe('application/json')
    expect(result).toEqual(mockData)
  })

  it('lança ApiError com a mensagem detalhada em caso de erro 401', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      statusText: 'Unauthorized',
      json: async () => ({ detail: 'Token expirado ou inválido.' }),
    })

    await expect(fetchCurrentProfile('token-invalido')).rejects.toThrow(ApiError)
    await expect(fetchCurrentProfile('token-invalido')).rejects.toThrow(
      'Token expirado ou inválido.'
    )
  })
})
