-- ============================================================================
-- SCRIPT SQL PARA CRIAÇÃO DAS TABELAS NO SUPABASE (SQL EDITOR)
-- Baseado no Documento de Modelos (docs/doc-modelos.md) e Visão (docs/doc-visao.md)
--
-- Issue #19: a tabela FUNCIONARIO guarda apenas o perfil funcional. Identidade,
-- e-mail de login e senha são gerenciados pelo Supabase Auth (auth.users).
-- ============================================================================

-- 1. Tabela FUNCIONARIO (US01 - Manter Usuário)
-- "supabaseUserId" referencia logicamente auth.users(id) e é único por identidade.
-- A senha/hash NÃO é armazenada nesta tabela (pertence ao Supabase Auth).
CREATE TABLE IF NOT EXISTS "FUNCIONARIO" (
    "idFuncionario" SERIAL PRIMARY KEY,
    "supabaseUserId" UUID NULL,
    "nome" VARCHAR(150) NOT NULL,
    "email" VARCHAR(150) UNIQUE NOT NULL,
    "isAdmin" BOOLEAN NOT NULL DEFAULT FALSE,
    "is_active" BOOLEAN NOT NULL DEFAULT TRUE,
    "is_staff" BOOLEAN NOT NULL DEFAULT FALSE,
    "is_superuser" BOOLEAN NOT NULL DEFAULT FALSE,
    "last_login" TIMESTAMPTZ NULL,
    CONSTRAINT unique_funcionario_supabase_user_id UNIQUE ("supabaseUserId")
);

-- Migração idempotente para bancos criados antes da Issue #19:
-- remove a coluna de senha e adiciona o vínculo com o Supabase Auth.
ALTER TABLE "FUNCIONARIO" DROP COLUMN IF EXISTS "senha";
ALTER TABLE "FUNCIONARIO" ADD COLUMN IF NOT EXISTS "supabaseUserId" UUID;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint c
        JOIN pg_attribute a
          ON a.attrelid = c.conrelid
         AND a.attnum = ANY (c.conkey)
        WHERE c.conrelid = 'public."FUNCIONARIO"'::regclass
          AND c.contype = 'u'
          AND a.attname = 'supabaseUserId'
    ) THEN
        ALTER TABLE "FUNCIONARIO"
            ADD CONSTRAINT unique_funcionario_supabase_user_id
            UNIQUE ("supabaseUserId");
    END IF;
END
$$;

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
-- diretamente na tabela FUNCIONARIO do sistema, sem copiar a senha!
-- ============================================================================
CREATE OR REPLACE FUNCTION public.sincronizar_usuario_supabase_auth()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public."FUNCIONARIO" ("supabaseUserId", "nome", "email", "isAdmin", "is_active", "is_staff", "is_superuser")
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data->>'nome', split_part(NEW.email, '@', 1)),
        NEW.email,
        COALESCE((NEW.raw_user_meta_data->>'isAdmin')::boolean, FALSE),
        TRUE,
        COALESCE((NEW.raw_user_meta_data->>'isAdmin')::boolean, FALSE),
        COALESCE((NEW.raw_user_meta_data->>'isAdmin')::boolean, FALSE)
    )
    ON CONFLICT ("email") DO UPDATE
        SET "supabaseUserId" = COALESCE("FUNCIONARIO"."supabaseUserId", EXCLUDED."supabaseUserId");
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.sincronizar_usuario_supabase_auth();
