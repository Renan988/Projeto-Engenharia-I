import Link from 'next/link'
import { redirect } from 'next/navigation'
import { createClient } from '@/lib/supabase/server'
import { fetchCurrentProfile } from '@/api/client'
import { logoutAction } from '@/app/actions/auth'
import { Button } from '@/components/common/Button'
import { FuncionariosManager } from '@/components/funcionarios/FuncionariosManager'
import type { FuncionarioProfile } from '@/types/auth'

export default async function DashboardPage() {
  const supabase = await createClient()

  const {
    data: { user },
  } = await supabase.auth.getUser()

  if (!user) {
    redirect('/login')
  }

  // Obter a sessão com o JWT do Supabase
  const {
    data: { session },
  } = await supabase.auth.getSession()

  let profile: FuncionarioProfile | null = null
  let profileError: string | null = null

  if (session?.access_token) {
    try {
      profile = await fetchCurrentProfile(session.access_token)
    } catch (err: unknown) {
      profileError =
        err instanceof Error
          ? err.message
          : 'Não foi possível carregar os dados funcionais vinculados no backend.'
    }
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

          {profile?.isAdmin && (
            <nav
              aria-label="Navegação principal"
              style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}
            >
              <Link
                href="/dashboard"
                style={{
                  fontSize: '0.875rem',
                  fontWeight: 600,
                  color: '#2563eb',
                  textDecoration: 'none',
                }}
              >
                Dashboard
              </Link>
              <Link
                href="/funcionarios"
                style={{
                  fontSize: '0.875rem',
                  fontWeight: 500,
                  color: '#4b5563',
                  textDecoration: 'none',
                }}
              >
                Funcionários
              </Link>
            </nav>
          )}
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

        {/* Card do Perfil Conectado */}
        <section
          style={{
            backgroundColor: '#ffffff',
            borderRadius: '8px',
            border: '1px solid #e5e7eb',
            padding: '1.5rem',
            marginBottom: '1.5rem',
          }}
        >
          <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.125rem', color: '#111827' }}>
            Sessão Ativa via Supabase SSR & Server Actions
          </h3>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
              gap: '1rem',
              fontSize: '0.875rem',
            }}
          >
            <div>
              <strong style={{ color: '#4b5563' }}>E-mail:</strong>
              <div>{user.email}</div>
            </div>
            <div>
              <strong style={{ color: '#4b5563' }}>Identificador Supabase (`sub`):</strong>
              <div style={{ fontFamily: 'monospace', fontSize: '0.8125rem', wordBreak: 'break-all' }}>
                {user.id}
              </div>
            </div>
            <div>
              <strong style={{ color: '#4b5563' }}>Nível de Acesso (Backend):</strong>
              <div>
                <span
                  style={{
                    display: 'inline-block',
                    padding: '0.2rem 0.5rem',
                    borderRadius: '4px',
                    backgroundColor: profile?.isAdmin ? '#dbeafe' : '#f3f4f6',
                    color: profile?.isAdmin ? '#1e40af' : '#374151',
                    fontWeight: 600,
                  }}
                >
                  {profile ? profile.perfil : 'Não vinculado'}
                </span>
              </div>
            </div>
          </div>
        </section>

        {/* Seção Administrativa Condicional */}
        {profile?.isAdmin ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <section
              style={{
                backgroundColor: '#eff6ff',
                borderRadius: '8px',
                border: '1px solid #bfdbfe',
                padding: '1.5rem',
              }}
            >
              <h3 style={{ margin: '0 0 0.5rem 0', color: '#1e3a8a', fontSize: '1.125rem' }}>
                Painel do Administrador
              </h3>
              <p style={{ margin: '0 0 1rem 0', fontSize: '0.875rem', color: '#1e40af' }}>
                Você tem permissão de Administrador. Os endpoints de gerenciamento de usuários
                (`GET/POST/PUT/DELETE /api/funcionarios/`) estão disponíveis para sua credencial.
              </p>
              <div
                style={{
                  backgroundColor: '#ffffff',
                  border: '1px solid #dbeafe',
                  borderRadius: '6px',
                  padding: '1rem',
                  fontSize: '0.8125rem',
                  color: '#3b82f6',
                }}
              >
                ✓ Autorização garantida pelo backend via token JWT validado (`SupabaseJWTAuthentication`).
              </div>
            </section>

            <FuncionariosManager
              token={session?.access_token ?? null}
              currentUser={profile}
            />
          </div>
        ) : (
          <section
            style={{
              backgroundColor: '#ffffff',
              borderRadius: '8px',
              border: '1px solid #e5e7eb',
              padding: '1.5rem',
            }}
          >
            <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.125rem', color: '#374151' }}>
              Área do Colaborador
            </h3>
            <p style={{ margin: 0, fontSize: '0.875rem', color: '#6b7280' }}>
              Você está autenticado como <strong>Funcionário</strong>. Seu acesso permite visualizar
              e gerenciar a esteira de SPEDs e clientes.
            </p>
          </section>
        )}
      </main>
    </div>
  )
}
