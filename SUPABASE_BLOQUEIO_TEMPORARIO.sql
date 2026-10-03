-- Bloqueia o acesso da API publica às tabelas do esquema public.
-- Nao apaga registos. A aplicacao online e a sincronizacao deixam de funcionar
-- ate serem configuradas e testadas politicas de acesso adequadas.
-- Executar no SQL Editor do projecto Supabase como administrador.

BEGIN;

DO $$
DECLARE
    tabela RECORD;
BEGIN
    FOR tabela IN
        SELECT schemaname, tablename
        FROM pg_tables
        WHERE schemaname = 'public'
    LOOP
        EXECUTE format(
            'ALTER TABLE %I.%I ENABLE ROW LEVEL SECURITY',
            tabela.schemaname,
            tabela.tablename
        );
    END LOOP;
END
$$;

REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public
    FROM PUBLIC, anon, authenticated;
REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public
    FROM PUBLIC, anon, authenticated;
REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA public
    FROM PUBLIC, anon, authenticated;
REVOKE USAGE ON SCHEMA public FROM anon, authenticated;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
    REVOKE ALL ON TABLES FROM PUBLIC, anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    REVOKE ALL ON SEQUENCES FROM PUBLIC, anon, authenticated;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC, anon, authenticated;

COMMIT;
