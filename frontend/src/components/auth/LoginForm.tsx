'use client'

import { useActionState, useState } from 'react'
import { loginAction, type ActionState } from '@/app/actions/auth'
import { Input } from '../common/Input'
import { Button } from '../common/Button'
import { Alert } from '../common/Alert'

interface LoginFormProps {
  onCustomSubmit?: (email: string, pass: string) => Promise<void>
  initialError?: string | null
}

export function LoginForm({ onCustomSubmit, initialError = null }: LoginFormProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [clientError, setClientError] = useState<string | null>(null)

  const [state, formAction, isPending] = useActionState<ActionState | null, FormData>(
    async (prevState, formData) => {
      if (onCustomSubmit) {
        try {
          await onCustomSubmit(email, password)
          return { success: true }
        } catch (err: unknown) {
          return { error: err instanceof Error ? err.message : 'Erro ao realizar login.' }
        }
      }
      return await loginAction(prevState, formData)
    },
    initialError ? { error: initialError } : null
  )

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    if (!email.trim()) {
      e.preventDefault()
      setClientError('Por favor, informe seu e-mail.')
      return
    }
    if (!password) {
      e.preventDefault()
      setClientError('Por favor, informe sua senha.')
      return
    }
    setClientError(null)
  }

  const activeError = clientError || state?.error

  return (
    <form
      action={formAction}
      onSubmit={handleSubmit}
      noValidate
      style={{
        display: 'flex',
        flexDirection: 'column',
        width: '100%',
        maxWidth: '380px',
      }}
    >
      {activeError && (
        <Alert
          type="error"
          message={activeError}
          onClose={() => setClientError(null)}
        />
      )}

      <Input
        label="E-mail"
        id="email"
        name="email"
        type="email"
        autoComplete="email"
        placeholder="seu.email@empresa.com"
        value={email}
        onChange={(e) => {
          setEmail(e.target.value)
          if (clientError) setClientError(null)
        }}
        disabled={isPending}
        required
      />

      <Input
        label="Senha"
        id="password"
        name="password"
        type="password"
        autoComplete="current-password"
        placeholder="••••••••"
        value={password}
        onChange={(e) => {
          setPassword(e.target.value)
          if (clientError) setClientError(null)
        }}
        disabled={isPending}
        required
      />

      <Button
        type="submit"
        variant="primary"
        isLoading={isPending}
        style={{ marginTop: '0.5rem', width: '100%' }}
      >
        Entrar
      </Button>
    </form>
  )
}
