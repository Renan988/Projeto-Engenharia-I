'use server'

import { redirect } from 'next/navigation'
import { createClient } from '@/lib/supabase/server'
import { fetchCurrentProfile } from '@/api/client'

export interface ActionState {
  error?: string | null
  success?: boolean
}

/**
 * Server Action para realizar login via Supabase Auth
 */
export async function loginAction(
  _prevState: ActionState | null,
  formData: FormData
): Promise<ActionState> {
  const email = (formData.get('email') as string)?.trim()
  const password = formData.get('password') as string

  if (!email) {
    return { error: 'Por favor, informe seu e-mail.' }
  }

  if (!password) {
    return { error: 'Por favor, informe sua senha.' }
  }

  const supabase = await createClient()

  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  })

  if (error) {
    return {
      error:
        error.message === 'Invalid login credentials'
          ? 'E-mail ou senha incorretos.'
          : error.message,
    }
  }

  // Validação de sincronização: perfil precisa existir e estar ativo no backend Django
  const token = data.session?.access_token
  if (token) {
    try {
      const profile = await fetchCurrentProfile(token)
      if (!profile || profile.is_active === false) {
        await supabase.auth.signOut()
        return {
          error: 'Este usuário foi inativado ou não possui permissão de acesso ao sistema.',
        }
      }
    } catch (err: unknown) {
      await supabase.auth.signOut()
      const message =
        err instanceof Error ? err.message : 'Falha na validação do perfil.'
      return {
        error: message.toLowerCase().includes('inativo')
          ? 'Este perfil de funcionário está inativo. Acesso negado.'
          : 'Usuário não possui perfil ativo vinculado no sistema.',
      }
    }
  }

  redirect('/dashboard')
}

/**
 * Server Action para realizar logout
 */
export async function logoutAction(): Promise<void> {
  const supabase = await createClient()
  await supabase.auth.signOut()
  redirect('/login')
}
