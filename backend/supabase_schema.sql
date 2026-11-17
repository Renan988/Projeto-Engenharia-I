-- ============================================================================
-- SCRIPT SQL PARA CRIAÇÃO DAS TABELAS NO SUPABASE (SQL EDITOR)
-- Baseado no Documento de Modelos (docs/doc-modelos.md) e Visão (docs/doc-visao.md)
-- ============================================================================

-- 1. Tabela FUNCIONARIO (US01 - Manter Usuário)
CREATE TABLE IF NOT EXISTS "FUNCIONARIO" (
    "idFuncionario" SERIAL PRIMARY KEY,
    "nome" VARCHAR(150) NOT NULL,
    "email" VARCHAR(150) UNIQUE NOT NULL,
    "senha" VARCHAR(255) NOT NULL,
    "isAdmin" BOOLEAN NOT NULL DEFAULT FALSE,
    "is_active" BOOLEAN NOT NULL DEFAULT TRUE,
    "is_staff" BOOLEAN NOT NULL DEFAULT FALSE,
    "is_superuser" BOOLEAN NOT NULL DEFAULT FALSE,
    "last_login" TIMESTAMPTZ NULL
);

-- 2. Tabela CLIENTE (US02 - Manter Cliente)
CREATE TABLE IF NOT EXISTS "CLIENTE" (
    "idCli" SERIAL PRIMARY KEY,
    "cnpj" VARCHAR(18) UNIQUE NOT NULL,
    "nomeEmpresa" VARCHAR(150) NOT NULL,
    "razaoSocial" VARCHAR(150) NOT NULL,
    "telefoneWhatsApp" VARCHAR(20) DEFAULT '',
    "emailContador" VARCHAR(150) NOT NULL,
    "regimeTributario" VARCHAR(50) NOT NULL
);

-- 3. Tabela SPED (US03 - Manter SPED e US04 - Enviar SPED)
CREATE TABLE IF NOT EXISTS "SPED" (
    "idSped" SERIAL PRIMARY KEY,
    "mesReferencia" VARCHAR(7) NOT NULL,
    "status" VARCHAR(15) NOT NULL DEFAULT 'PENDENTE'
        CHECK ("status" IN ('PENDENTE', 'GERADO', 'ENVIADO')),
    "arquivoRar" VARCHAR(255) NULL,
    "idCli" INTEGER NOT NULL REFERENCES "CLIENTE" ("idCli") ON DELETE CASCADE,
    "ordemPrioridade" SMALLINT NOT NULL DEFAULT 3,
    "criadoEm" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    "atualizadoEm" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT "unique_sped_cliente_mes_referencia" UNIQUE ("idCli", "mesReferencia")
);

-- 4. Tabela LOG_RASTREABILIDADE (US05 - Rastreabilidade Automática)
CREATE TABLE IF NOT EXISTS "LOG_RASTREABILIDADE" (
    "idLog" SERIAL PRIMARY KEY,
    "dataHora" TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    "acaoRealizada" VARCHAR(250) NOT NULL,
    "idFuncionario" INTEGER NOT NULL REFERENCES "FUNCIONARIO" ("idFuncionario") ON DELETE CASCADE,
    "idSped" INTEGER NULL REFERENCES "SPED" ("idSped") ON DELETE SET NULL
);

-- ============================================================================
-- GATILHO AUTOMÁTICO: Sincroniza novos usuários do Supabase Auth (auth.users)
-- diretamente na tabela FUNCIONARIO do sistema!
-- ============================================================================
CREATE OR REPLACE FUNCTION public.sincronizar_usuario_supabase_auth()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public."FUNCIONARIO" ("nome", "email", "senha", "isAdmin", "is_active", "is_staff", "is_superuser")
    VALUES (
        COALESCE(NEW.raw_user_meta_data->>'nome', split_part(NEW.email, '@', 1)),
        NEW.email,
        COALESCE(NEW.encrypted_password, 'supabase_auth_managed'),
        COALESCE((NEW.raw_user_meta_data->>'isAdmin')::boolean, FALSE),
        TRUE,
        COALESCE((NEW.raw_user_meta_data->>'isAdmin')::boolean, FALSE),
        COALESCE((NEW.raw_user_meta_data->>'isAdmin')::boolean, FALSE)
    )
    ON CONFLICT ("email") DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.sincronizar_usuario_supabase_auth();
