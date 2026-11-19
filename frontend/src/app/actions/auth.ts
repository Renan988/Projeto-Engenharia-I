'use server'

import { redirect } from 'next/navigation'
import { createClient } from '@/lib/supabase/server'

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

  const { error } = await supabase.auth.signInWithPassword({
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
