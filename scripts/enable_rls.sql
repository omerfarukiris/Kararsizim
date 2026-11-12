-- Kararsızım — Supabase'de Django tablolarını Supabase API'sine kapatır.
--
-- 1) public şemasındaki her tabloda Row Level Security'yi açar.
-- 2) Her tabloya Supabase API rolleri (anon, authenticated) için açık bir
--    "hiçbir satıra erişim yok" policy'si ekler. Policy olmadan da erişim
--    kapalıdır; açık policy hem niyeti belgeler hem de Supabase Security
--    Advisor'daki "RLS Enabled No Policy" notunu kaldırır.
--
-- Django `postgres` rolüyle (tablo sahibi) bağlandığı için etkilenmez:
-- PostgreSQL'de tablo sahibi, FORCE ROW LEVEL SECURITY açık olmadıkça RLS'e takılmaz.
--
-- `python manage.py migrate` sonrasında çalıştırılır. Tekrar çalıştırmak güvenlidir;
-- yeni bir app/model eklendiğinde de çalıştır.

DO $$
DECLARE
    t record;
BEGIN
    FOR t IN
        SELECT c.relname, c.relrowsecurity
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public'
          AND c.relkind = 'r'
    LOOP
        IF NOT t.relrowsecurity THEN
            EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY;', t.relname);
            RAISE NOTICE 'RLS açıldı: %', t.relname;
        END IF;

        EXECUTE format('DROP POLICY IF EXISTS api_erisimi_yok ON public.%I;', t.relname);
        EXECUTE format(
            'CREATE POLICY api_erisimi_yok ON public.%I AS PERMISSIVE FOR ALL '
            'TO anon, authenticated USING (false) WITH CHECK (false);',
            t.relname
        );
    END LOOP;
END
$$;

-- Kontrol: boş sonuç beklenir (RLS'i kapalı ya da policy'si olmayan tablo kalmamalı).
SELECT c.relname AS eksik_tablo, c.relrowsecurity AS rls
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public'
  AND c.relkind = 'r'
  AND (
      NOT c.relrowsecurity
      OR NOT EXISTS (
          SELECT 1 FROM pg_policies p
          WHERE p.schemaname = 'public' AND p.tablename = c.relname AND p.policyname = 'api_erisimi_yok'
      )
  );
