import type { Session, User } from '@supabase/supabase-js'

export interface FuncionarioProfile {
  idFuncionario: number
  supabaseUserId?: string | null
  supabase_user_id?: string | null
  nome: string
  email: string
  isAdmin: boolean
  is_active: boolean
  perfil: 'Administrador' | 'Funcionário'
}

export interface FuncionarioFilters {
  nome?: string
  email?: string
}

export interface CreateFuncionarioPayload {
  nome: string
  email: string
  senha: string
  isAdmin: boolean
}

export interface UpdateFuncionarioPayload {
  nome: string
  email: string
  isAdmin: boolean
}

export interface DeleteFuncionarioResponse {
  detail?: string
}

export interface AuthContextType {
  user: User | null
  session: Session | null
  profile: FuncionarioProfile | null
  isLoading: boolean
  error: string | null
  signIn: (email: string, password: string) => Promise<void>
  signOut: () => Promise<void>
  refreshProfile: () => Promise<void>
  clearError: () => void
}
