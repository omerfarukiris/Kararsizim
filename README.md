# Kararsızım

Kararsız kaldığın konularda anket aç, herkes oy versin. Django 5 + saf HTML/CSS/JS ile yazılmış bir prototip.

Projenin ayrıntılı planı: [docs/KARARSIZIM_PLAN.md](docs/KARARSIZIM_PLAN.md)

## Lokal kurulum

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # DATABASE_URL boş kalırsa SQLite kullanılır
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Uygulama http://127.0.0.1:8000 adresinde, yönetim paneli `/admin/` altında açılır (giriş e-posta ile yapılır).

Testler: `python manage.py test` (lokalde `DATABASE_URL` boşken SQLite ile çalışır).

## Yayına alma: Supabase + Vercel

### 1. Supabase

1. Supabase'de **Frankfurt (`eu-central-1`)** bölgesinde bir proje oluştur. Veritabanı parolasını kaydet; yalnızca harf, rakam ve `-` kullanmak URL kodlama derdini önler.
2. Projede **Connect** menüsünden iki bağlantı dizesini al ve `.env`'e yaz. `[YOUR-PASSWORD]` dahil köşeli parantezli yer tutucuların parantezlerini de sil:
   - **Transaction pooler** (port 6543) → `DATABASE_URL`
   - **Session pooler** (port 5432) → `DATABASE_URL_DIRECT`
3. Migration'ları lokalden, session pooler üzerinden çalıştır (deploy sırasında migration yapılmaz):
   ```bash
   DJANGO_DB_DIRECT=1 python manage.py migrate
   ```
4. Supabase'in otomatik REST API'sinden erişimi kapatmak için tüm tablolarda RLS'i aç: [scripts/enable_rls.sql](scripts/enable_rls.sql) dosyasını Supabase **SQL Editor**'de çalıştır. Yeni migration'lardan sonra da tekrar çalıştır. Son sorgu boş dönmeli.
5. Yönetici hesabı oluştur:
   ```bash
   DJANGO_DB_DIRECT=1 python manage.py createsuperuser
   ```

### 2. Vercel

1. Repoyu GitHub'a push et, Vercel'de **Add New → Project** ile import et. Vercel `manage.py`'yi görüp Django'yu otomatik algılar (`config.wsgi.application`). Python sürümü `pyproject.toml`'daki `requires-python` ile 3.12'dir. `vercel.json` fonksiyonları veritabanına yakın olsun diye Frankfurt'ta (`fra1`) çalıştırır.
2. **Settings → Environment Variables** (Production ve Preview):

   | Değişken | Değer |
   |---|---|
   | `DJANGO_SECRET_KEY` | Uzun, rastgele bir değer: `python -c "import secrets; print(secrets.token_urlsafe(50))"` |
   | `DJANGO_DEBUG` | `False` |
   | `DJANGO_ALLOWED_HOSTS` | `.vercel.app` (özel alan adın varsa virgülle ekle) |
   | `CSRF_TRUSTED_ORIGINS` | `https://*.vercel.app` (özel alan adın varsa `https://alanadin.com` ekle) |
   | `DATABASE_URL` | Transaction pooler bağlantı dizesi (port 6543) |

3. Deploy et. `STATIC_ROOT` tanımlı olduğu için `collectstatic` build sırasında çalışır; statik dosyaları WhiteNoise sunar.

### Canlı kontrol listesi

- Kayıt, giriş, anket oluşturma ve oy verme çalışıyor.
- `/static/css/style.css` ve `/static/js/vote.js` 200 dönüyor.
- Olmayan bir adres (`/yok/`) özel 404 sayfasını gösteriyor, hata ayrıntısı sızmıyor.

## Bilinen sınırlamalar (prototip)

- Üye olmayan biri çerezlerini silerse aynı ankete tekrar oy verebilir.
- Misafirken oy veren biri sonradan üye olup giriş yaparsa aynı ankete bir kez daha oy verebilir (misafir ve üye oyları farklı `voter_key` ile tutulur).
