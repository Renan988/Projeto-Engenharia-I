'use client'

import { useCallback, useEffect, useMemo, useState } from 'react'
import {
  createFuncionario,
  deleteFuncionario,
  fetchFuncionarios,
  updateFuncionario,
} from '@/api/client'
import type {
  CreateFuncionarioPayload,
  FuncionarioProfile,
  UpdateFuncionarioPayload,
} from '@/types/auth'
import { Button } from '../common/Button'
import { Input } from '../common/Input'
import { Alert } from '../common/Alert'
import { Spinner } from '../common/Spinner'
import { FuncionarioFormModal } from './FuncionarioFormModal'
import { DeleteConfirmModal } from './DeleteConfirmModal'

interface FuncionariosManagerProps {
  token: string | null
  currentUser: FuncionarioProfile | null
  initialFuncionarios?: FuncionarioProfile[]
}

export function FuncionariosManager({
  token,
  currentUser,
  initialFuncionarios,
}: FuncionariosManagerProps) {
  const isAdmin = Boolean(currentUser?.isAdmin)

  const [funcionarios, setFuncionarios] = useState<FuncionarioProfile[]>(
    initialFuncionarios ?? []
  )
  const [isLoading, setIsLoading] = useState<boolean>(
    isAdmin && initialFuncionarios === undefined
  )
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  // Filtros
  const [filterNome, setFilterNome] = useState('')
  const [filterEmail, setFilterEmail] = useState('')

  // Estado do Modal de Criação / Edição
  const [isFormOpen, setIsFormOpen] = useState(false)
  const [formMode, setFormMode] = useState<'create' | 'edit'>('create')
  const [editingFuncionario, setEditingFuncionario] =
    useState<FuncionarioProfile | null>(null)
  const [isSubmittingForm, setIsSubmittingForm] = useState(false)
  const [formApiError, setFormApiError] = useState<string | null>(null)

  // Estado do Modal de Exclusão
  const [deletingFuncionario, setDeletingFuncionario] =
    useState<FuncionarioProfile | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)
  const [deleteApiError, setDeleteApiError] = useState<string | null>(null)

  const loadFuncionarios = useCallback(
    async (nome?: string, email?: string) => {
      if (!isAdmin) return
      if (!token) {
        setError('Sessão de autenticação ausente. Faça login novamente.')
        setIsLoading(false)
        return
      }

      setIsLoading(true)
      setError(null)
      try {
        const data = await fetchFuncionarios(token, { nome, email })
        setFuncionarios(Array.isArray(data) ? data : [])
      } catch (err: unknown) {
        setError(
          err instanceof Error
            ? err.message
            : 'Não foi possível carregar a lista de funcionários.'
        )
      } finally {
        setIsLoading(false)
      }
    },
    [isAdmin, token]
  )

  useEffect(() => {
    if (!isAdmin || initialFuncionarios !== undefined) {
      return
    }

    let cancelled = false

    async function fetchInitial() {
      if (!token) {
        if (!cancelled) {
          setError('Sessão de autenticação ausente. Faça login novamente.')
          setIsLoading(false)
        }
        return
      }

      try {
        const data = await fetchFuncionarios(token)
        if (!cancelled) {
          setFuncionarios(Array.isArray(data) ? data : [])
        }
      } catch (err: unknown) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : 'Não foi possível carregar a lista de funcionários.'
          )
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false)
        }
      }
    }

    void fetchInitial()

    return () => {
      cancelled = true
    }
  }, [isAdmin, initialFuncionarios, token])

  const filteredFuncionarios = useMemo(() => {
    const nomeTerm = filterNome.trim().toLowerCase()
    const emailTerm = filterEmail.trim().toLowerCase()

    return funcionarios.filter((item) => {
      const matchNome = !nomeTerm || item.nome.toLowerCase().includes(nomeTerm)
      const matchEmail = !emailTerm || item.email.toLowerCase().includes(emailTerm)
      return matchNome && matchEmail
    })
  }, [funcionarios, filterNome, filterEmail])

  // Bloqueio de interface para usuários não administradores
  if (!isAdmin) {
    return (
      <section
        aria-label="Acesso restrito"
        style={{
          backgroundColor: '#ffffff',
          borderRadius: '8px',
          border: '1px solid #e5e7eb',
          padding: '1.5rem',
        }}
      >
        <Alert
          type="warning"
          message="Acesso Restrito: Apenas usuários com perfil de Administrador podem visualizar e gerenciar funcionários."
        />
      </section>
    )
  }

  const handleFilterSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    await loadFuncionarios(filterNome, filterEmail)
  }

  const handleClearFilters = async () => {
    setFilterNome('')
    setFilterEmail('')
    await loadFuncionarios('', '')
  }

  const openCreateModal = () => {
    setFormMode('create')
    setEditingFuncionario(null)
    setFormApiError(null)
    setIsFormOpen(true)
  }

  const openEditModal = (func: FuncionarioProfile) => {
    setFormMode('edit')
    setEditingFuncionario(func)
    setFormApiError(null)
    setIsFormOpen(true)
  }

  const closeFormModal = () => {
    if (isSubmittingForm) return
    setIsFormOpen(false)
    setEditingFuncionario(null)
    setFormApiError(null)
  }

  const handleCreate = async (payload: CreateFuncionarioPayload) => {
    if (!token) {
      setFormApiError('Token de autenticação não disponível.')
      return
    }

    setIsSubmittingForm(true)
    setFormApiError(null)
    setSuccessMessage(null)
    try {
      const created = await createFuncionario(payload, token)
      setFuncionarios((prev) =>
        [...prev, created].sort((a, b) => a.nome.localeCompare(b.nome))
      )
      setIsFormOpen(false)
      setSuccessMessage('Usuário cadastrado com sucesso.')
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : 'Erro ao cadastrar funcionário.'
      setFormApiError(msg)
    } finally {
      setIsSubmittingForm(false)
    }
  }

  const handleEdit = async (
    idFuncionario: number,
    payload: UpdateFuncionarioPayload
  ) => {
    if (!token) {
      setFormApiError('Token de autenticação não disponível.')
      return
    }

    setIsSubmittingForm(true)
    setFormApiError(null)
    setSuccessMessage(null)
    try {
      const updated = await updateFuncionario(idFuncionario, payload, token)
      setFuncionarios((prev) =>
        prev
          .map((item) =>
            item.idFuncionario === idFuncionario ? updated : item
          )
          .sort((a, b) => a.nome.localeCompare(b.nome))
      )
      setIsFormOpen(false)
      setEditingFuncionario(null)
      setSuccessMessage(`Funcionário "${updated.nome}" atualizado com sucesso.`)
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : 'Erro ao atualizar funcionário.'
      setFormApiError(msg)
    } finally {
      setIsSubmittingForm(false)
    }
  }

  const openDeleteModal = (func: FuncionarioProfile) => {
    setDeletingFuncionario(func)
    setDeleteApiError(null)
  }

  const closeDeleteModal = () => {
    if (isDeleting) return
    setDeletingFuncionario(null)
    setDeleteApiError(null)
  }

  const handleConfirmDelete = async (func: FuncionarioProfile) => {
    if (!token) {
      setDeleteApiError('Token de autenticação não disponível.')
      return
    }

    setIsDeleting(true)
    setDeleteApiError(null)
    setSuccessMessage(null)
    setError(null)
    try {
      const response = await deleteFuncionario(func.idFuncionario, token)
      setFuncionarios((prev) =>
        prev.filter((item) => item.idFuncionario !== func.idFuncionario)
      )
      setDeletingFuncionario(null)
      setSuccessMessage(
        response?.detail || `Funcionário "${func.nome}" removido com sucesso.`
      )
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : 'Erro ao excluir funcionário.'
      setDeleteApiError(msg)
      setError(msg)
    } finally {
      setIsDeleting(false)
    }
  }

  return (
    <section
      aria-label="Gerenciamento de Funcionários"
      style={{
        backgroundColor: '#ffffff',
        borderRadius: '8px',
        border: '1px solid #e5e7eb',
        padding: '1.5rem',
      }}
    >
      {/* Cabeçalho da seção */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '1rem',
          marginBottom: '1.25rem',
        }}
      >
        <div>
          <h3 style={{ margin: '0 0 0.25rem 0', fontSize: '1.125rem', color: '#111827' }}>
            Gerenciamento de Funcionários
          </h3>
          <p style={{ margin: 0, fontSize: '0.875rem', color: '#6b7280' }}>
            Cadastre, consulte, atualize perfis de acesso e remova colaboradores do sistema.
          </p>
        </div>

        <Button type="button" variant="primary" onClick={openCreateModal}>
          + Novo Funcionário
        </Button>
      </div>

      {/* Feedback de sucesso e erro */}
      {successMessage && (
        <Alert
          type="success"
          message={successMessage}
          onClose={() => setSuccessMessage(null)}
        />
      )}

      {error && (
        <Alert
          type="error"
          message={error}
          onClose={() => setError(null)}
        />
      )}

      {/* Formulário de filtro por nome e e-mail */}
      <form
        onSubmit={handleFilterSubmit}
        aria-label="Filtros de funcionários"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '0.75rem',
          alignItems: 'end',
          backgroundColor: '#f9fafb',
          padding: '1rem',
          borderRadius: '8px',
          border: '1px solid #e5e7eb',
          marginBottom: '1.25rem',
        }}
      >
        <div style={{ marginBottom: '-1rem' }}>
          <Input
            label="Filtrar por nome"
            id="filtro-nome"
            name="filtroNome"
            type="text"
            placeholder="Buscar por nome..."
            value={filterNome}
            onChange={(e) => setFilterNome(e.target.value)}
          />
        </div>

        <div style={{ marginBottom: '-1rem' }}>
          <Input
            label="Filtrar por e-mail"
            id="filtro-email"
            name="filtroEmail"
            type="text"
            placeholder="Buscar por e-mail..."
            value={filterEmail}
            onChange={(e) => setFilterEmail(e.target.value)}
          />
        </div>

        <div style={{ display: 'flex', gap: '0.5rem', paddingTop: '0.5rem' }}>
          <Button
            type="submit"
            variant="primary"
            disabled={isLoading}
            style={{ flex: 1 }}
          >
            Filtrar
          </Button>
          {(filterNome || filterEmail) && (
            <Button
              type="button"
              variant="secondary"
              disabled={isLoading}
              onClick={handleClearFilters}
            >
              Limpar
            </Button>
          )}
        </div>
      </form>

      {/* Estado de Carregamento */}
      {isLoading ? (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '2.5rem 1rem',
            color: '#6b7280',
          }}
        >
          <Spinner size={32} />
          <span style={{ fontSize: '0.875rem', marginTop: '0.5rem' }}>
            Carregando funcionários...
          </span>
        </div>
      ) : filteredFuncionarios.length === 0 ? (
        /* Estado de Lista Vazia */
        <div
          style={{
            textAlign: 'center',
            padding: '2.5rem 1rem',
            backgroundColor: '#f9fafb',
            borderRadius: '8px',
            border: '1px dashed #d1d5db',
            color: '#6b7280',
          }}
        >
          <p style={{ margin: '0 0 0.5rem 0', fontWeight: 600, color: '#374151' }}>
            Nenhum funcionário encontrado.
          </p>
          <p style={{ margin: 0, fontSize: '0.875rem' }}>
            {filterNome || filterEmail
              ? 'Tente ajustar ou limpar os filtros de nome e e-mail.'
              : 'Clique em "+ Novo Funcionário" para cadastrar o primeiro colaborador.'}
          </p>
        </div>
      ) : (
        /* Tabela de Funcionários (Sem exposição de senha) */
        <div style={{ overflowX: 'auto' }}>
          <table
            style={{
              width: '100%',
              borderCollapse: 'collapse',
              fontSize: '0.875rem',
              textAlign: 'left',
            }}
          >
            <thead>
              <tr
                style={{
                  borderBottom: '2px solid #e5e7eb',
                  backgroundColor: '#f9fafb',
                  color: '#374151',
                }}
              >
                <th style={{ padding: '0.75rem 1rem', fontWeight: 600 }}>Nome</th>
                <th style={{ padding: '0.75rem 1rem', fontWeight: 600 }}>E-mail</th>
                <th style={{ padding: '0.75rem 1rem', fontWeight: 600 }}>Perfil</th>
                <th
                  style={{
                    padding: '0.75rem 1rem',
                    fontWeight: 600,
                    textAlign: 'right',
                  }}
                >
                  Ações
                </th>
              </tr>
            </thead>
            <tbody>
              {filteredFuncionarios.map((func) => {
                const isSelf =
                  currentUser?.idFuncionario === func.idFuncionario
                const perfilLabel =
                  func.perfil || (func.isAdmin ? 'Administrador' : 'Funcionário')

                return (
                  <tr
                    key={func.idFuncionario}
                    style={{
                      borderBottom: '1px solid #e5e7eb',
                    }}
                  >
                    <td
                      style={{
                        padding: '0.875rem 1rem',
                        fontWeight: 500,
                        color: '#111827',
                      }}
                    >
                      {func.nome}
                      {isSelf && (
                        <span
                          style={{
                            marginLeft: '0.5rem',
                            fontSize: '0.75rem',
                            color: '#6b7280',
                            fontWeight: 400,
                          }}
                        >
                          (Você)
                        </span>
                      )}
                    </td>
                    <td style={{ padding: '0.875rem 1rem', color: '#4b5563' }}>
                      {func.email}
                    </td>
                    <td style={{ padding: '0.875rem 1rem' }}>
                      <span
                        style={{
                          display: 'inline-block',
                          padding: '0.2rem 0.6rem',
                          borderRadius: '9999px',
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          backgroundColor: func.isAdmin ? '#dbeafe' : '#f3f4f6',
                          color: func.isAdmin ? '#1e40af' : '#374151',
                        }}
                      >
                        {perfilLabel}
                      </span>
                    </td>
                    <td
                      style={{
                        padding: '0.875rem 1rem',
                        textAlign: 'right',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      <div
                        style={{
                          display: 'inline-flex',
                          gap: '0.5rem',
                          justifyContent: 'flex-end',
                        }}
                      >
                        <Button
                          type="button"
                          variant="secondary"
                          aria-label={`Editar ${func.nome}`}
                          onClick={() => openEditModal(func)}
                          style={{
                            padding: '0.35rem 0.75rem',
                            fontSize: '0.8125rem',
                          }}
                        >
                          Editar
                        </Button>
                        <Button
                          type="button"
                          variant="danger"
                          aria-label={`Excluir ${func.nome}`}
                          onClick={() => openDeleteModal(func)}
                          style={{
                            padding: '0.35rem 0.75rem',
                            fontSize: '0.8125rem',
                          }}
                        >
                          Excluir
                        </Button>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal de Cadastro e Edição */}
      {isFormOpen && (
        <FuncionarioFormModal
          key={
            formMode === 'edit' && editingFuncionario
              ? `edit-${editingFuncionario.idFuncionario}`
              : 'create'
          }
          isOpen={isFormOpen}
          mode={formMode}
          funcionario={editingFuncionario}
          isSubmitting={isSubmittingForm}
          apiError={formApiError}
          onClose={closeFormModal}
          onSubmitCreate={handleCreate}
          onSubmitEdit={handleEdit}
        />
      )}

      {/* Modal de Confirmação de Exclusão */}
      <DeleteConfirmModal
        isOpen={Boolean(deletingFuncionario)}
        funcionario={deletingFuncionario}
        isDeleting={isDeleting}
        apiError={deleteApiError}
        onCancel={closeDeleteModal}
        onConfirm={handleConfirmDelete}
      />
    </section>
  )
}
