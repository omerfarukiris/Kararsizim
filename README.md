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
2. Projede **Connect → Direct** menüsünden iki bağlantı dizesini al ve `.env`'e yaz. `[YOUR-PASSWORD]` dahil köşeli parantezli yer tutucuların parantezlerini de sil. Sunucu adını (`aws-0-…` / `aws-1-…`) tahmin etme, Connect'te yazanı kullan; yanlışsa pooler `tenant/user not found` hatası verir:
   - **Transaction pooler** (port 6543) → `DATABASE_URL`
   - **Session pooler** (port 5432) → `DATABASE_URL_DIRECT`

   > Ağın 5432/6543 portlarını engelliyorsa (bağlantı zaman aşımına uğrar) 3. ve 5. adımları lokalden yapamazsın. Bu durumda migration SQL'i lokalde üretilip Supabase **SQL Editor**'de çalıştırılabilir; yönetici için de canlı sitede normal kayıt olup o hesabı SQL ile yetkilendir: `UPDATE accounts_user SET is_staff = true, is_superuser = true WHERE username = '...';`
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
   | `DJANGO_ALLOWED_HOSTS` | Projenin adresi, örn. `kararsizim.vercel.app` (özel alan adın varsa virgülle ekle). Joker (`.vercel.app`) yalnızca ilk deploy'da adres henüz belli değilken kullanılır. |
   | `DATABASE_URL` | Transaction pooler bağlantı dizesi (port 6543) |
   | `DJANGO_HSTS_SECONDS` | İsteğe bağlı; varsayılan `3600`. Site sorunsuz çalışıyorsa `31536000`. |

   `CSRF_TRUSTED_ORIGINS` gerekmez; formlar aynı adresten gönderildiği için Django bunu kendisi doğrular. `https://*.vercel.app` gibi bir joker **girme**: Vercel'deki herkesin sitesini güvenilir sayar.

3. Deploy et. `STATIC_ROOT` tanımlı olduğu için `collectstatic` build sırasında çalışır; statik dosyaları WhiteNoise sunar. Bağımlılıklar `pyproject.toml`'dan kurulur.

### Güvenlik notları

- `DEBUG=False` iken: HTTP → HTTPS yönlendirme, HSTS, yalnızca HTTPS çerezleri, `X-Frame-Options: DENY`, `nosniff` açık.
- Supabase'de tüm tablolarda RLS açık ve policy yok; Supabase REST API'si tablolara erişemez, Django `postgres` rolüyle (tablo sahibi) etkilenmez.
- Hız sınırı (giriş, kayıt, oy) yok. Yayına almadan önce Vercel **Firewall → Rate Limiting** ile `/giris/`, `/kayit/` ve `/anket/*/oy/` için kural eklenmesi önerilir.

### Canlı kontrol listesi

- Kayıt, giriş, anket oluşturma ve oy verme çalışıyor.
- `/static/css/style.css` ve `/static/js/vote.js` 200 dönüyor.
- Olmayan bir adres (`/yok/`) özel 404 sayfasını gösteriyor, hata ayrıntısı sızmıyor.

## Bilinen sınırlamalar (prototip)

- Üye olmayan biri çerezlerini silerse aynı ankete tekrar oy verebilir.
- Misafirken oy veren biri sonradan üye olup giriş yaparsa aynı ankete bir kez daha oy verebilir (misafir ve üye oyları farklı `voter_key` ile tutulur).
