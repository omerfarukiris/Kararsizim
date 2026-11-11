-- Kararsızım — Supabase'de Django tablolarında Row Level Security'yi açar.
--
-- Amaç: Supabase'in otomatik REST/GraphQL API'si (anon / authenticated rolleri)
-- üzerinden bu tablolara dışarıdan erişilememesi. Policy tanımlanmadığı için
-- bu roller hiçbir satırı okuyamaz/yazamaz. Django `postgres` rolüyle bağlandığı
-- (tablo sahibi + BYPASSRLS) için etkilenmez.
--
-- `python manage.py migrate` sonrasında çalıştırılır. Tekrar çalıştırmak
-- güvenlidir. Yeni bir app/model eklendiğinde de tekrar çalıştır: public
-- şemasındaki RLS'i kapalı tüm tabloları bulup açar.

DO $$
DECLARE
    t record;
BEGIN
    FOR t IN
        SELECT c.relname
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public'
          AND c.relkind = 'r'
          AND NOT c.relrowsecurity
    LOOP
        EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY;', t.relname);
        RAISE NOTICE 'RLS açıldı: %', t.relname;
    END LOOP;
END
$$;

-- Kontrol: RLS'i kapalı tablo kalmamalı (boş sonuç beklenir).
SELECT c.relname AS rls_kapali_tablo
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public' AND c.relkind = 'r' AND NOT c.relrowsecurity;
