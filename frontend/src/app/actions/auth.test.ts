import { describe, it, expect, vi, beforeEach } from 'vitest'
import { loginAction } from './auth'
import { createClient } from '@/lib/supabase/server'
import { fetchCurrentProfile } from '@/api/client'
import { redirect } from 'next/navigation'

vi.mock('@/lib/supabase/server', () => ({
  createClient: vi.fn(),
}))

vi.mock('@/api/client', () => ({
  fetchCurrentProfile: vi.fn(),
}))

vi.mock('next/navigation', () => ({
  redirect: vi.fn(),
}))

describe('loginAction (Server Action)', () => {
  const mockSignInWithPassword = vi.fn()
  const mockSignOut = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(createClient).mockResolvedValue({
      auth: {
        signInWithPassword: mockSignInWithPassword,
        signOut: mockSignOut,
      },
    } as unknown as Awaited<ReturnType<typeof createClient>>)
  })

  it('retorna erro se o e-mail não for informado', async () => {
    const formData = new FormData()
    formData.append('email', '')
    formData.append('password', '123456')

    const result = await loginAction(null, formData)
    expect(result).toEqual({ error: 'Por favor, informe seu e-mail.' })
    expect(mockSignInWithPassword).not.toHaveBeenCalled()
  })

  it('retorna erro se a senha não for informada', async () => {
    const formData = new FormData()
    formData.append('email', 'admin@intech.com.br')
    formData.append('password', '')

    const result = await loginAction(null, formData)
    expect(result).toEqual({ error: 'Por favor, informe sua senha.' })
    expect(mockSignInWithPassword).not.toHaveBeenCalled()
  })

  it('retorna mensagem amigável quando credenciais forem inválidas no Supabase', async () => {
    mockSignInWithPassword.mockResolvedValueOnce({
      data: { session: null },
      error: { message: 'Invalid login credentials' },
    })

    const formData = new FormData()
    formData.append('email', 'errado@intech.com.br')
    formData.append('password', 'senhaerrada')

    const result = await loginAction(null, formData)
    expect(result).toEqual({ error: 'E-mail ou senha incorretos.' })
  })

  it('rejeita login e faz signOut se o perfil do funcionário estiver inativo no Django', async () => {
    mockSignInWithPassword.mockResolvedValueOnce({
      data: { session: { access_token: 'fake-token-123' } },
      error: null,
    })
    vi.mocked(fetchCurrentProfile).mockResolvedValueOnce({
      idFuncionario: 5,
      nome: 'Excluído',
      email: 'excluido@intech.com.br',
      isAdmin: false,
      perfil: 'Funcionário',
      is_active: false,
    })

    const formData = new FormData()
    formData.append('email', 'excluido@intech.com.br')
    formData.append('password', 'senha123')

    const result = await loginAction(null, formData)

    expect(mockSignOut).toHaveBeenCalled()
    expect(result.error).toContain('inativado')
    expect(redirect).not.toHaveBeenCalled()
  })

  it('rejeita login e faz signOut se o backend Django retornar erro de perfil inativo', async () => {
    mockSignInWithPassword.mockResolvedValueOnce({
      data: { session: { access_token: 'fake-token-123' } },
      error: null,
    })
    vi.mocked(fetchCurrentProfile).mockRejectedValueOnce(
      new Error('Perfil de funcionário inativo.')
    )

    const formData = new FormData()
    formData.append('email', 'inativo@intech.com.br')
    formData.append('password', 'senha123')

    const result = await loginAction(null, formData)

    expect(mockSignOut).toHaveBeenCalled()
    expect(result.error).toContain('inativo')
    expect(redirect).not.toHaveBeenCalled()
  })

  it('redireciona para /dashboard se o login e perfil estiverem ativos e válidos', async () => {
    mockSignInWithPassword.mockResolvedValueOnce({
      data: { session: { access_token: 'valid-token-admin' } },
      error: null,
    })
    vi.mocked(fetchCurrentProfile).mockResolvedValueOnce({
      idFuncionario: 1,
      nome: 'Admin',
      email: 'admin@intech.com.br',
      isAdmin: true,
      perfil: 'Administrador',
      is_active: true,
    })

    const formData = new FormData()
    formData.append('email', 'admin@intech.com.br')
    formData.append('password', 'senha123')

    await loginAction(null, formData)

    expect(mockSignOut).not.toHaveBeenCalled()
    expect(redirect).toHaveBeenCalledWith('/dashboard')
  })
})
