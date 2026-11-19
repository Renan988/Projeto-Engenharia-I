import { describe, it, expect, vi, beforeEach } from 'vitest'
import '@testing-library/jest-dom/vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { LoginForm } from './LoginForm'

describe('LoginForm Component (Next.js)', () => {
  const mockCustomSubmit = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renderiza os campos de e-mail, senha e botão de login', () => {
    render(<LoginForm />)

    expect(screen.getByLabelText(/E-mail/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Senha/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Entrar/i })).toBeInTheDocument()
  })

  it('exibe erro de validação caso os campos estejam vazios ao submeter', async () => {
    render(<LoginForm />)

    const submitBtn = screen.getByRole('button', { name: /Entrar/i })
    fireEvent.click(submitBtn)

    expect(await screen.findByText('Por favor, informe seu e-mail.')).toBeInTheDocument()
  })

  it('exibe erro de validação se apenas o e-mail for preenchido', async () => {
    render(<LoginForm />)

    const emailInput = screen.getByLabelText(/E-mail/i)
    fireEvent.change(emailInput, { target: { value: 'teste@intech.com' } })

    const submitBtn = screen.getByRole('button', { name: /Entrar/i })
    fireEvent.click(submitBtn)

    expect(await screen.findByText('Por favor, informe sua senha.')).toBeInTheDocument()
  })

  it('chama onCustomSubmit quando submetido com credenciais válidas', async () => {
    mockCustomSubmit.mockResolvedValueOnce(undefined)

    render(<LoginForm onCustomSubmit={mockCustomSubmit} />)

    fireEvent.change(screen.getByLabelText(/E-mail/i), {
      target: { value: 'admin@intech.com' },
    })
    fireEvent.change(screen.getByLabelText(/Senha/i), {
      target: { value: 'senhaForte123' },
    })

    fireEvent.click(screen.getByRole('button', { name: /Entrar/i }))

    await waitFor(() => {
      expect(mockCustomSubmit).toHaveBeenCalledWith('admin@intech.com', 'senhaForte123')
    })
  })

  it('exibe a mensagem de erro inicial passada por prop', () => {
    render(<LoginForm initialError="Credenciais inválidas no servidor." />)

    expect(screen.getByText('Credenciais inválidas no servidor.')).toBeInTheDocument()
  })
})
