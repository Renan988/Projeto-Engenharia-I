'use client'

import type { FuncionarioProfile } from '@/types/auth'
import { Button } from '../common/Button'
import { Alert } from '../common/Alert'

interface DeleteConfirmModalProps {
  isOpen: boolean
  funcionario: FuncionarioProfile | null
  isDeleting: boolean
  apiError?: string | null
  onCancel: () => void
  onConfirm: (funcionario: FuncionarioProfile) => Promise<void>
}

export function DeleteConfirmModal({
  isOpen,
  funcionario,
  isDeleting,
  apiError,
  onCancel,
  onConfirm,
}: DeleteConfirmModalProps) {
  if (!isOpen || !funcionario) {
    return null
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="delete-modal-title"
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
          maxWidth: '440px',
          padding: '1.5rem',
          boxShadow:
            '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
          color: '#111827',
        }}
      >
        <h3
          id="delete-modal-title"
          style={{
            margin: '0 0 0.75rem 0',
            fontSize: '1.125rem',
            fontWeight: 700,
            color: '#991b1b',
          }}
        >
          Confirmar Exclusão de Funcionário
        </h3>

        {apiError && <Alert type="error" message={apiError} />}

        <p
          style={{
            margin: '0 0 1.25rem 0',
            fontSize: '0.9375rem',
            color: '#374151',
            lineHeight: 1.5,
          }}
        >
          Tem certeza que deseja remover o funcionário{' '}
          <strong>{funcionario.nome}</strong> (<code>{funcionario.email}</code>)? Esta
          ação removerá o acesso funcional ao sistema.
        </p>

        <div
          style={{
            display: 'flex',
            justifyContent: 'flex-end',
            gap: '0.75rem',
          }}
        >
          <Button
            type="button"
            variant="secondary"
            onClick={onCancel}
            disabled={isDeleting}
          >
            Cancelar
          </Button>
          <Button
            type="button"
            variant="danger"
            isLoading={isDeleting}
            onClick={() => onConfirm(funcionario)}
          >
            Confirmar Exclusão
          </Button>
        </div>
      </div>
    </div>
  )
}
