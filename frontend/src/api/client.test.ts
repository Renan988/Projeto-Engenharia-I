import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  apiRequest,
  fetchCurrentProfile,
  fetchFuncionarios,
  createFuncionario,
  updateFuncionario,
  deleteFuncionario,
  ApiError,
} from './client'

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
      status: 200,
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

  it('lista funcionários com filtros de nome e e-mail (GET /api/funcionarios/)', async () => {
    const mockList = [
      {
        idFuncionario: 1,
        nome: 'Ana Silva',
        email: 'ana@intech.com.br',
        isAdmin: true,
        is_active: true,
        perfil: 'Administrador',
      },
    ]
    const fetchSpy = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => mockList,
    })
    globalThis.fetch = fetchSpy

    const result = await fetchFuncionarios('token-admin', {
      nome: 'Ana',
      email: 'ana@intech',
    })

    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining('/api/funcionarios/?nome=Ana&email=ana%40intech'),
      expect.objectContaining({ method: 'GET' })
    )
    expect(result).toEqual(mockList)
  })

  it('cadastra, atualiza e exclui funcionário enviando os payloads corretos', async () => {
    const fetchSpy = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        status: 201,
        json: async () => ({
          idFuncionario: 10,
          nome: 'Carlos',
          email: 'carlos@intech.com.br',
          isAdmin: false,
          is_active: true,
          perfil: 'Funcionário',
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          idFuncionario: 10,
          nome: 'Carlos Editado',
          email: 'carlos@intech.com.br',
          isAdmin: true,
          is_active: true,
          perfil: 'Administrador',
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({ detail: 'Usuário "carlos@intech.com.br" deletado com sucesso.' }),
      })

    globalThis.fetch = fetchSpy

    const created = await createFuncionario(
      {
        nome: 'Carlos',
        email: 'carlos@intech.com.br',
        senha: 'senhaInicial123',
        isAdmin: false,
      },
      'token-admin'
    )
    expect(created.idFuncionario).toBe(10)
    expect(JSON.parse(fetchSpy.mock.calls[0][1].body as string)).toEqual({
      nome: 'Carlos',
      email: 'carlos@intech.com.br',
      senha: 'senhaInicial123',
      isAdmin: false,
    })

    const updated = await updateFuncionario(
      10,
      {
        nome: 'Carlos Editado',
        email: 'carlos@intech.com.br',
        isAdmin: true,
      },
      'token-admin'
    )
    expect(updated.isAdmin).toBe(true)
    const updateBody = JSON.parse(fetchSpy.mock.calls[1][1].body as string)
    expect(updateBody).toEqual({
      nome: 'Carlos Editado',
      email: 'carlos@intech.com.br',
      isAdmin: true,
    })
    expect(updateBody).not.toHaveProperty('senha')

    const deleted = await deleteFuncionario(10, 'token-admin')
    expect(deleted.detail).toContain('deletado com sucesso')
  })
})
