import Link from 'next/link'
import { redirect } from 'next/navigation'
import { createClient } from '@/lib/supabase/server'
import { fetchCurrentProfile } from '@/api/client'
import { logoutAction } from '@/app/actions/auth'
import { Button } from '@/components/common/Button'
import { FuncionariosManager } from '@/components/funcionarios/FuncionariosManager'
import type { FuncionarioProfile } from '@/types/auth'

export default async function FuncionariosPage() {
  const supabase = await createClient()

  const {
    data: { user },
  } = await supabase.auth.getUser()

  if (!user) {
    redirect('/login')
  }

  const {
    data: { session },
  } = await supabase.auth.getSession()

  let profile: FuncionarioProfile | null = null
  let profileError: string | null = null

  if (session?.access_token) {
    try {
      profile = await fetchCurrentProfile(session.access_token)
      if (!profile || profile.is_active === false) {
        await supabase.auth.signOut()
        redirect('/login')
      }
      if (!profile.isAdmin) {
        redirect('/dashboard')
      }
    } catch {
      await supabase.auth.signOut()
      redirect('/login')
    }
  } else {
    redirect('/login')
  }

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f9fafb', color: '#111827' }}>
      {/* Topbar */}
      <header
        style={{
          backgroundColor: '#ffffff',
          borderBottom: '1px solid #e5e7eb',
          padding: '1rem 2rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0, color: '#1f2937' }}>
              Intech Sistemas
            </h2>
            <span style={{ fontSize: '0.8125rem', color: '#6b7280' }}>
              Controle de Fluxo de SPEDs
            </span>
          </div>

          <nav
            aria-label="Navegação principal"
            style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}
          >
            <Link
              href="/dashboard"
              style={{
                fontSize: '0.875rem',
                fontWeight: 500,
                color: '#4b5563',
                textDecoration: 'none',
              }}
            >
              Dashboard
            </Link>
            {profile?.isAdmin && (
              <Link
                href="/funcionarios"
                style={{
                  fontSize: '0.875rem',
                  fontWeight: 600,
                  color: '#2563eb',
                  textDecoration: 'none',
                }}
              >
                Funcionários
              </Link>
            )}
          </nav>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.875rem', fontWeight: 600 }}>
              {profile?.nome || user.email}
            </div>
            <div style={{ fontSize: '0.75rem', color: '#6b7280' }}>
              {profile ? profile.perfil : 'Perfil não sincronizado'}
            </div>
          </div>
          <form action={logoutAction}>
            <Button
              variant="secondary"
              type="submit"
              style={{ fontSize: '0.8125rem', padding: '0.4rem 0.8rem' }}
            >
              Sair
            </Button>
          </form>
        </div>
      </header>

      {/* Main Content */}
      <main style={{ maxWidth: '1000px', margin: '2rem auto', padding: '0 1rem' }}>
        {profileError && (
          <div
            role="alert"
            style={{
              backgroundColor: '#fffbeb',
              border: '1px solid #fcd34d',
              color: '#92400e',
              padding: '0.75rem 1rem',
              borderRadius: '6px',
              marginBottom: '1rem',
              fontSize: '0.875rem',
            }}
          >
            <strong>Aviso de Perfil:</strong> {profileError}
          </div>
        )}

        <FuncionariosManager
          token={session?.access_token ?? null}
          currentUser={profile}
        />
      </main>
    </div>
  )
}
