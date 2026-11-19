'use client'

import { useState } from 'react'
import type {
  CreateFuncionarioPayload,
  FuncionarioProfile,
  UpdateFuncionarioPayload,
} from '@/types/auth'
import { Input } from '../common/Input'
import { Button } from '../common/Button'
import { Alert } from '../common/Alert'

interface FuncionarioFormModalProps {
  isOpen: boolean
  mode: 'create' | 'edit'
  funcionario?: FuncionarioProfile | null
  isSubmitting: boolean
  apiError?: string | null
  onClose: () => void
  onSubmitCreate: (payload: CreateFuncionarioPayload) => Promise<void>
  onSubmitEdit: (
    idFuncionario: number,
    payload: UpdateFuncionarioPayload
  ) => Promise<void>
}

export function FuncionarioFormModal({
  isOpen,
  mode,
  funcionario,
  isSubmitting,
  apiError,
  onClose,
  onSubmitCreate,
  onSubmitEdit,
}: FuncionarioFormModalProps) {
  const isEdit = mode === 'edit' && Boolean(funcionario)
  const [nome, setNome] = useState(isEdit && funcionario ? funcionario.nome : '')
  const [email, setEmail] = useState(isEdit && funcionario ? funcionario.email : '')
  const [senha, setSenha] = useState('')
  const [perfil, setPerfil] = useState<'Funcionário' | 'Administrador'>(
    isEdit && funcionario?.isAdmin ? 'Administrador' : 'Funcionário'
  )
  const [validationError, setValidationError] = useState<string | null>(null)

  if (!isOpen) {
    return null
  }

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()

    const trimmedNome = nome.trim()
    const trimmedEmail = email.trim()

    if (!trimmedNome) {
      setValidationError('Por favor, informe o nome do funcionário.')
      return
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!trimmedEmail || !emailRegex.test(trimmedEmail)) {
      setValidationError('Por favor, informe um e-mail válido.')
      return
    }

    const isAdmin = perfil === 'Administrador'

    if (mode === 'create') {
      if (!senha || senha.length < 6) {
        setValidationError('A senha inicial deve ter pelo menos 6 caracteres.')
        return
      }
      setValidationError(null)
      await onSubmitCreate({
        nome: trimmedNome,
        email: trimmedEmail,
        senha,
        isAdmin,
      })
    } else if (mode === 'edit' && funcionario) {
      setValidationError(null)
      await onSubmitEdit(funcionario.idFuncionario, {
        nome: trimmedNome,
        email: trimmedEmail,
        isAdmin,
      })
    }
  }

  const activeError = validationError || apiError

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="funcionario-modal-title"
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(17, 24, 39, 0.55)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '1rem',
        zIndex: 50,
      }}
    >
      <div
        style={{
          backgroundColor: '#ffffff',
          borderRadius: '10px',
          width: '100%',
          maxWidth: '480px',
          padding: '1.5rem',
          boxShadow:
            '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
          color: '#111827',
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '1rem',
          }}
        >
          <h3
            id="funcionario-modal-title"
            style={{ margin: 0, fontSize: '1.125rem', fontWeight: 700, color: '#111827' }}
          >
            {mode === 'create' ? 'Novo Funcionário' : 'Editar Funcionário'}
          </h3>
          <button
            type="button"
            onClick={onClose}
            disabled={isSubmitting}
            aria-label="Fechar modal"
            style={{
              background: 'none',
              border: 'none',
              fontSize: '1.25rem',
              color: '#6b7280',
              cursor: isSubmitting ? 'not-allowed' : 'pointer',
              padding: '0.25rem 0.5rem',
            }}
          >
            ×
          </button>
        </div>

        {activeError && (
          <Alert
            type="error"
            message={activeError}
            onClose={() => setValidationError(null)}
          />
        )}

        <form onSubmit={handleSubmit} noValidate>
          <Input
            label="Nome Completo"
            id="funcionario-nome"
            name="nome"
            type="text"
            placeholder="Ex.: Maria Oliveira"
            value={nome}
            onChange={(e) => {
              setNome(e.target.value)
              if (validationError) setValidationError(null)
            }}
            disabled={isSubmitting}
            maxLength={150}
            required
          />

          <Input
            label="E-mail"
            id="funcionario-email"
            name="email"
            type="email"
            placeholder="maria.oliveira@intech.com.br"
            value={email}
            onChange={(e) => {
              setEmail(e.target.value)
              if (validationError) setValidationError(null)
            }}
            disabled={isSubmitting}
            maxLength={150}
            required
          />

          {mode === 'create' && (
            <Input
              label="Senha Inicial"
              id="funcionario-senha"
              name="senha"
              type="password"
              autoComplete="new-password"
              placeholder="Mínimo de 6 caracteres"
              value={senha}
              onChange={(e) => {
                setSenha(e.target.value)
                if (validationError) setValidationError(null)
              }}
              disabled={isSubmitting}
              minLength={6}
              required
            />
          )}

          <div
            style={{
              marginBottom: '1rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.375rem',
            }}
          >
            <label
              htmlFor="funcionario-perfil"
              style={{
                fontSize: '0.875rem',
                fontWeight: 600,
                color: '#1f2937',
                textAlign: 'left',
              }}
            >
              Perfil
            </label>
            <select
              id="funcionario-perfil"
              name="perfil"
              value={perfil}
              onChange={(e) =>
                setPerfil(e.target.value as 'Funcionário' | 'Administrador')
              }
              disabled={isSubmitting}
              style={{
                padding: '0.625rem 0.75rem',
                borderRadius: '6px',
                border: '1px solid #d1d5db',
                fontSize: '1rem',
                backgroundColor: '#ffffff',
                color: '#111827',
              }}
            >
              <option value="Funcionário">Funcionário</option>
              <option value="Administrador">Administrador</option>
            </select>
          </div>

          {mode === 'edit' && (
            <p
              style={{
                margin: '0 0 1rem 0',
                padding: '0.625rem 0.75rem',
                backgroundColor: '#f3f4f6',
                borderRadius: '6px',
                fontSize: '0.75rem',
                color: '#4b5563',
              }}
            >
              As credenciais de autenticação (senha) são gerenciadas exclusivamente pelo
              Supabase Auth e não são exibidas nem alteradas neste formulário.
            </p>
          )}

          <div
            style={{
              display: 'flex',
              justifyContent: 'flex-end',
              gap: '0.75rem',
              marginTop: '1.25rem',
            }}
          >
            <Button
              type="button"
              variant="secondary"
              onClick={onClose}
              disabled={isSubmitting}
            >
              Cancelar
            </Button>
            <Button type="submit" variant="primary" isLoading={isSubmitting}>
              {mode === 'create' ? 'Cadastrar Funcionário' : 'Salvar Alterações'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
