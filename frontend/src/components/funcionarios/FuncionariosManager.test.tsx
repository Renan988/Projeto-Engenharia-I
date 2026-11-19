import { describe, it, expect, vi, beforeEach } from 'vitest'
import '@testing-library/jest-dom/vitest'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import { FuncionariosManager } from './FuncionariosManager'
import * as apiClient from '@/api/client'
import type { FuncionarioProfile } from '@/types/auth'

const adminUser: FuncionarioProfile = {
  idFuncionario: 1,
  supabase_user_id: '11111111-1111-4111-8111-111111111111',
  nome: 'Admin Intech',
  email: 'admin@intech.com.br',
  isAdmin: true,
  is_active: true,
  perfil: 'Administrador',
}

const commonUser: FuncionarioProfile = {
  idFuncionario: 2,
  supabase_user_id: '22222222-2222-4222-8222-222222222222',
  nome: 'Colaborador Intech',
  email: 'colab@intech.com.br',
  isAdmin: false,
  is_active: true,
  perfil: 'Funcionário',
}

const mockFuncionarios: FuncionarioProfile[] = [
  adminUser,
  commonUser,
  {
    idFuncionario: 3,
    supabase_user_id: '33333333-3333-4333-8333-333333333333',
    nome: 'Mariana Costa',
    email: 'mariana@intech.com.br',
    isAdmin: false,
    is_active: true,
    perfil: 'Funcionário',
  },
]

describe('FuncionariosManager Component (CRUD de Funcionários)', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('bloqueia visualização de controles de CRUD para usuários não administradores', () => {
    const fetchSpy = vi.spyOn(apiClient, 'fetchFuncionarios')

    render(
      <FuncionariosManager token="token-colab" currentUser={commonUser} />
    )

    expect(
      screen.getByText(/Apenas usuários com perfil de Administrador/i)
    ).toBeInTheDocument()
    expect(
      screen.queryByRole('button', { name: /Novo Funcionário/i })
    ).not.toBeInTheDocument()
    expect(
      screen.queryByRole('button', { name: /Editar/i })
    ).not.toBeInTheDocument()
    expect(
      screen.queryByRole('button', { name: /Excluir/i })
    ).not.toBeInTheDocument()
    expect(fetchSpy).not.toHaveBeenCalled()
  })

  it('exibe estado de carregamento e depois lista funcionários sem expor senhas', async () => {
    vi.spyOn(apiClient, 'fetchFuncionarios').mockResolvedValueOnce(
      mockFuncionarios
    )

    render(<FuncionariosManager token="token-admin" currentUser={adminUser} />)

    expect(screen.getByText(/Carregando funcionários.../i)).toBeInTheDocument()

    expect(await screen.findByText('Mariana Costa')).toBeInTheDocument()
    expect(screen.getByText('mariana@intech.com.br')).toBeInTheDocument()
    expect(screen.getByText('Colaborador Intech')).toBeInTheDocument()

    // Garante que não há coluna ou texto de senha na listagem
    const table = screen.getByRole('table')
    expect(within(table).queryByText(/senha/i)).not.toBeInTheDocument()
  })

  it('exibe estado de lista vazia quando não há funcionários retornados', async () => {
    vi.spyOn(apiClient, 'fetchFuncionarios').mockResolvedValueOnce([])

    render(<FuncionariosManager token="token-admin" currentUser={adminUser} />)

    expect(
      await screen.findByText('Nenhum funcionário encontrado.')
    ).toBeInTheDocument()
  })

  it('exibe estado de erro quando a requisição inicial falha', async () => {
    vi.spyOn(apiClient, 'fetchFuncionarios').mockRejectedValueOnce(
      new Error('Falha de comunicação com o servidor Django.')
    )

    render(<FuncionariosManager token="token-admin" currentUser={adminUser} />)

    expect(
      await screen.findByText('Falha de comunicação com o servidor Django.')
    ).toBeInTheDocument()
  })

  it('permite filtrar funcionários por nome e e-mail', async () => {
    const fetchSpy = vi
      .spyOn(apiClient, 'fetchFuncionarios')
      .mockResolvedValueOnce(mockFuncionarios)
      .mockResolvedValueOnce([mockFuncionarios[2]])

    render(<FuncionariosManager token="token-admin" currentUser={adminUser} />)

    expect(await screen.findByText('Mariana Costa')).toBeInTheDocument()

    const nomeInput = screen.getByLabelText(/Filtrar por nome/i)
    const emailInput = screen.getByLabelText(/Filtrar por e-mail/i)

    fireEvent.change(nomeInput, { target: { value: 'Mariana' } })
    fireEvent.change(emailInput, { target: { value: 'mariana@intech' } })

    // Filtro reativo já oculta os demais itens na tabela
    expect(screen.getByText('Mariana Costa')).toBeInTheDocument()
    expect(screen.queryByText('Colaborador Intech')).not.toBeInTheDocument()

    // Submeter formulário dispara busca filtrada na API
    fireEvent.click(screen.getByRole('button', { name: /^Filtrar$/i }))

    await waitFor(() => {
      expect(fetchSpy).toHaveBeenCalledWith('token-admin', {
        nome: 'Mariana',
        email: 'mariana@intech',
      })
    })
  })

  it('cadastra um novo funcionário informando nome, e-mail, senha inicial e perfil', async () => {
    vi.spyOn(apiClient, 'fetchFuncionarios').mockResolvedValueOnce(
      mockFuncionarios
    )
    const createSpy = vi
      .spyOn(apiClient, 'createFuncionario')
      .mockResolvedValueOnce({
        idFuncionario: 4,
        supabase_user_id: '44444444-4444-4444-8444-444444444444',
        nome: 'Pedro Santos',
        email: 'pedro@intech.com.br',
        isAdmin: true,
        is_active: true,
        perfil: 'Administrador',
      })

    render(<FuncionariosManager token="token-admin" currentUser={adminUser} />)
    await screen.findByText('Mariana Costa')

    fireEvent.click(screen.getByRole('button', { name: /\+ Novo Funcionário/i }))

    const dialog = screen.getByRole('dialog')
    expect(within(dialog).getByLabelText(/Nome Completo/i)).toBeInTheDocument()
    expect(within(dialog).getByLabelText(/E-mail/i)).toBeInTheDocument()
    expect(within(dialog).getByLabelText(/Senha Inicial/i)).toBeInTheDocument()
    expect(within(dialog).getByLabelText(/Perfil/i)).toBeInTheDocument()

    fireEvent.change(within(dialog).getByLabelText(/Nome Completo/i), {
      target: { value: 'Pedro Santos' },
    })
    fireEvent.change(within(dialog).getByLabelText(/E-mail/i), {
      target: { value: 'pedro@intech.com.br' },
    })
    fireEvent.change(within(dialog).getByLabelText(/Senha Inicial/i), {
      target: { value: 'senhaSegura123' },
    })
    fireEvent.change(within(dialog).getByLabelText(/Perfil/i), {
      target: { value: 'Administrador' },
    })

    fireEvent.click(
      within(dialog).getByRole('button', { name: /Cadastrar Funcionário/i })
    )

    await waitFor(() => {
      expect(createSpy).toHaveBeenCalledWith(
        {
          nome: 'Pedro Santos',
          email: 'pedro@intech.com.br',
          senha: 'senhaSegura123',
          isAdmin: true,
        },
        'token-admin'
      )
    })

    expect(
      await screen.findByText('Usuário cadastrado com sucesso.')
    ).toBeInTheDocument()
    expect(screen.getByText('Pedro Santos')).toBeInTheDocument()
  })

  it('edita nome, e-mail e perfil de funcionário sem exibir campo de senha', async () => {
    vi.spyOn(apiClient, 'fetchFuncionarios').mockResolvedValueOnce(
      mockFuncionarios
    )
    const updateSpy = vi
      .spyOn(apiClient, 'updateFuncionario')
      .mockResolvedValueOnce({
        ...mockFuncionarios[2],
        nome: 'Mariana Costa Atualizada',
        email: 'mariana.costa@intech.com.br',
        isAdmin: true,
        perfil: 'Administrador',
      })

    render(<FuncionariosManager token="token-admin" currentUser={adminUser} />)
    await screen.findByText('Mariana Costa')

    fireEvent.click(
      screen.getByRole('button', { name: /Editar Mariana Costa/i })
    )

    const dialog = screen.getByRole('dialog')
    // Garante que o campo de senha NUNCA é exibido no modal de edição
    expect(within(dialog).queryByLabelText(/Senha/i)).not.toBeInTheDocument()

    const nomeInput = within(dialog).getByLabelText(/Nome Completo/i)
    const emailInput = within(dialog).getByLabelText(/E-mail/i)
    const perfilSelect = within(dialog).getByLabelText(/Perfil/i)

    fireEvent.change(nomeInput, {
      target: { value: 'Mariana Costa Atualizada' },
    })
    fireEvent.change(emailInput, {
      target: { value: 'mariana.costa@intech.com.br' },
    })
    fireEvent.change(perfilSelect, {
      target: { value: 'Administrador' },
    })

    fireEvent.click(
      within(dialog).getByRole('button', { name: /Salvar Alterações/i })
    )

    await waitFor(() => {
      expect(updateSpy).toHaveBeenCalledWith(
        3,
        {
          nome: 'Mariana Costa Atualizada',
          email: 'mariana.costa@intech.com.br',
          isAdmin: true,
        },
        'token-admin'
      )
    })

    expect(
      await screen.findByText(
        'Funcionário "Mariana Costa Atualizada" atualizado com sucesso.'
      )
    ).toBeInTheDocument()
    expect(screen.getByText('Mariana Costa Atualizada')).toBeInTheDocument()
  })

  it('exibe modal de confirmação ao excluir e apresenta feedback de sucesso ou erro da API', async () => {
    vi.spyOn(apiClient, 'fetchFuncionarios').mockResolvedValueOnce(
      mockFuncionarios
    )
    const deleteSpy = vi
      .spyOn(apiClient, 'deleteFuncionario')
      .mockRejectedValueOnce(
        new Error('Não é permitido excluir o próprio usuário autenticado.')
      )
      .mockResolvedValueOnce({
        detail: 'Usuário "mariana@intech.com.br" deletado com sucesso.',
      })

    render(<FuncionariosManager token="token-admin" currentUser={adminUser} />)
    await screen.findByText('Mariana Costa')

    // 1. Tenta excluir o próprio admin -> exibe erro da API
    fireEvent.click(screen.getByRole('button', { name: /Excluir Admin Intech/i }))
    const confirmDialog1 = screen.getByRole('dialog')
    expect(
      within(confirmDialog1).getByText(/Confirmar Exclusão de Funcionário/i)
    ).toBeInTheDocument()

    fireEvent.click(
      within(confirmDialog1).getByRole('button', { name: /Confirmar Exclusão/i })
    )

    expect(
      await within(confirmDialog1).findByText(
        'Não é permitido excluir o próprio usuário autenticado.'
      )
    ).toBeInTheDocument()

    fireEvent.click(
      within(confirmDialog1).getByRole('button', { name: /Cancelar/i })
    )

    // 2. Exclui Mariana Costa -> confirma no modal e exibe feedback de sucesso
    fireEvent.click(
      screen.getByRole('button', { name: /Excluir Mariana Costa/i })
    )
    const confirmDialog2 = screen.getByRole('dialog')
    fireEvent.click(
      within(confirmDialog2).getByRole('button', { name: /Confirmar Exclusão/i })
    )

    await waitFor(() => {
      expect(deleteSpy).toHaveBeenCalledWith(3, 'token-admin')
    })

    expect(
      await screen.findByText(
        'Usuário "mariana@intech.com.br" deletado com sucesso.'
      )
    ).toBeInTheDocument()
    expect(screen.queryByText('Mariana Costa')).not.toBeInTheDocument()
  })
})
