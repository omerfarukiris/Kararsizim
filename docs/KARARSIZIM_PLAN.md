# Kararsızım — Proje Planı (Claude Code için)

> Bu dosya projenin tek referans kaynağıdır. Claude Code her aşamaya başlamadan önce bu dosyanın tamamını okumalı, **yalnızca istenen aşamayı** yapmalı ve aşama sonundaki kabul kriterlerini kontrol etmelidir. Bir sonraki aşamaya kendiliğinden geçme.

---

## 1. Proje Özeti

**Kararsızım**, kullanıcıların kararsız kaldıkları konularda diğer kullanıcılara danışmak için anket açtığı bir web uygulamasıdır.

Örnek: *"Bu akşam sinemaya mı gitsem, restorana mı?"* → 2 ila 5 seçenek → platformdaki herkes oy verir.

### Temel kurallar
| Kural | Detay |
|---|---|
| Takip sistemi | **Yok.** Takipçi/takip edilen kavramı yok. Herkes tüm anketleri görür. |
| Anket görüntüleme | Üye olmayanlar dahil **herkes** |
| Oy verme | Üye olmayanlar dahil **herkes** (anket başına 1 oy) |
| Anket oluşturma | **Sadece üyeler** |
| Seçenek sayısı | En az **2**, en fazla **5** |
| Kayıt bilgileri | E-posta + kullanıcı adı + parola |
| Görünürlük | Anketlerde **kullanıcı adı görünür**, e-posta **asla** görünmez |

### Bu bir prototip
- Amaç hızlıca çalışan bir sürüm çıkarmak. Gereksiz karmaşıklık, ekstra kütüphane, build aracı, frontend framework **eklenmez**.
- Basit ve okunabilir kod tercih edilir. Sonraki adımlarda geliştirilecek.

---

## 2. Teknoloji Yığını

| Katman | Teknoloji | Not |
|---|---|---|
| Backend | Python 3.12 + Django 5.x | Django template sistemi ile sunucu taraflı render |
| Veritabanı | Supabase (PostgreSQL) | Django ORM ile doğrudan Postgres bağlantısı. Supabase Auth / JS SDK **kullanılmaz** |
| Kimlik doğrulama | Django'nun kendi auth sistemi | Özel (custom) kullanıcı modeli |
| Frontend | Saf HTML + CSS + JavaScript | Framework yok, npm yok, build adımı yok. Aynı repo içinde `templates/` ve `static/` |
| Statik dosyalar | WhiteNoise | |
| Deployment | Vercel | Vercel, `manage.py` dosyasını görünce Django'yu otomatik algılar (zero-config) |

### Python bağımlılıkları (`requirements.txt`)
```
Django>=5.0,<6.0
psycopg[binary]>=3.1
dj-database-url>=2.1
whitenoise>=6.6
python-dotenv>=1.0
```
Başka paket eklemeden önce gerekçesini belirt.

---

## 3. Klasör Yapısı

```
kararsizim/
├── manage.py
├── requirements.txt
├── pyproject.toml            # Python sürümü (3.12) ve gerekirse Vercel ayarları
├── .env.example
├── .gitignore
├── README.md
├── config/                   # Django proje ayarları
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── accounts/                 # Kullanıcı, kayıt, giriş
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   └── admin.py
├── polls/                    # Anket, seçenek, oy
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   ├── admin.py
│   └── utils.py              # voter_key üretimi vb.
├── templates/
│   ├── base.html
│   ├── partials/
│   │   ├── navbar.html
│   │   └── poll_card.html
│   ├── accounts/
│   │   ├── register.html
│   │   └── login.html
│   └── polls/
│       ├── home.html
│       ├── detail.html
│       ├── create.html
│       └── my_polls.html
└── static/
    ├── css/
    │   └── style.css
    ├── js/
    │   ├── vote.js
    │   └── create-poll.js
    └── img/
        └── logo.svg
```

---

## 4. Veri Modeli

### 4.1 `accounts.User` (özel kullanıcı modeli)
`AbstractUser`'dan türetilir. **Projenin en başında** tanımlanmalı ve `AUTH_USER_MODEL = "accounts.User"` olarak ayarlanmalı (ilk migration'dan önce).

| Alan | Tip | Kural |
|---|---|---|
| `email` | EmailField | `unique=True`, zorunlu. Giriş bu alanla yapılır |
| `username` | CharField(30) | `unique=True`, zorunlu. 3–30 karakter; harf, rakam, `_` ve `.` |
| `password` | (Django) | Django'nun hash'leme sistemi |
| `date_joined` | (Django) | |

- `USERNAME_FIELD = "email"`, `REQUIRED_FIELDS = ["username"]`
- Kullanıcı adı karşılaştırması **büyük/küçük harf duyarsız** benzersiz olmalı (`Ali` ve `ali` aynı kabul edilir).
- E-posta kaydedilirken küçük harfe çevrilir.

### 4.2 `polls.Poll`
| Alan | Tip | Kural |
|---|---|---|
| `author` | FK → User | `on_delete=CASCADE`, `related_name="polls"` |
| `question` | CharField(200) | Zorunlu, en az 5 karakter |
| `description` | TextField | Opsiyonel, en fazla 500 karakter |
| `created_at` | DateTimeField | `auto_now_add=True` |

- Varsayılan sıralama: `-created_at`
- Yardımcı: `total_votes` (property veya annotate ile)

### 4.3 `polls.Choice`
| Alan | Tip | Kural |
|---|---|---|
| `poll` | FK → Poll | `CASCADE`, `related_name="choices"` |
| `text` | CharField(100) | Zorunlu |
| `order` | PositiveSmallIntegerField | 0–4, seçeneklerin sırası ve renk eşlemesi için |

- Sıralama: `order`

### 4.4 `polls.Vote`
| Alan | Tip | Kural |
|---|---|---|
| `poll` | FK → Poll | `CASCADE`, `related_name="votes"` |
| `choice` | FK → Choice | `CASCADE`, `related_name="votes"` |
| `user` | FK → User | `null=True, blank=True`, `SET_NULL` |
| `voter_key` | CharField(64) | Oy verenin kimliği (aşağıya bak) |
| `created_at` | DateTimeField | `auto_now_add=True` |

- **Kısıt:** `UniqueConstraint(fields=["poll", "voter_key"], name="one_vote_per_voter")`
- `choice.poll == poll` kontrolü view/serviste yapılır.

### 4.5 Tek oy kuralı — `voter_key` mantığı
- **Üye ise:** `voter_key = f"u:{user.id}"`
- **Üye değilse:** Tarayıcıda `kz_voter` adlı bir çerez aranır. Yoksa rastgele bir UUID üretilip **imzalı çerez** (`set_signed_cookie`) olarak 1 yıllığına yazılır. `voter_key = f"a:{uuid}"`
- Bu mantık `polls/utils.py` içinde `get_or_create_voter_key(request, response=None)` gibi tek bir fonksiyonda toplanır.
- **Bilinen sınırlama (prototip için kabul edilebilir):** Üye olmayan biri çerezlerini silerse tekrar oy verebilir. İleride IP/rate limit ile güçlendirilecek.
- Oy **değiştirilemez** ve **geri alınamaz** (prototip).
- Anket sahibi kendi anketine oy verebilir.

---

## 5. Sayfalar ve URL'ler

| URL | View | Erişim | Açıklama |
|---|---|---|---|
| `/` | `home` | Herkes | Tüm anketler, en yeni üstte, sayfa başına 20 (Django Paginator) |
| `/anket/<id>/` | `poll_detail` | Herkes | Soru, açıklama, sahibi (kullanıcı adı), seçenekler, oy/sonuç |
| `/anket/<id>/oy/` | `vote` (POST) | Herkes | Oy kaydeder, JSON veya redirect döner |
| `/anket/yeni/` | `poll_create` | Sadece üye | Anket oluşturma formu |
| `/anket/<id>/sil/` | `poll_delete` (POST) | Sadece anket sahibi | Onay sonrası siler |
| `/anketlerim/` | `my_polls` | Sadece üye | Kullanıcının kendi anketleri |
| `/kayit/` | `register` | Misafir | Kayıt formu, başarılıysa otomatik giriş |
| `/giris/` | `login` | Misafir | E-posta + parola |
| `/cikis/` | `logout` (POST) | Üye | |
| `/admin/` | Django admin | Superuser | |

- Üye olmayan biri `/anket/yeni/` adresine giderse giriş sayfasına yönlendirilir ve üst kısımda şu mesaj görünür: **"Anket oluşturmak için üye olmalısın."** Giriş sonrası `next` ile forma geri döner.
- Ana sayfadaki "Anket Oluştur" butonu misafirlere de görünür; tıklayınca yukarıdaki akış çalışır.

---

## 6. İş Kuralları ve Davranışlar

### Anket oluşturma
- Form: soru (zorunlu), açıklama (opsiyonel), seçenekler.
- Varsayılan olarak **2 seçenek alanı** gösterilir. "+ Seçenek ekle" butonu ile en fazla 5'e çıkar; her ek alanın yanında "×" ile silinebilir (min 2'nin altına inemez). Bu işlem `create-poll.js` ile yapılır.
- **Sunucu tarafı doğrulama zorunlu** (JS'e güvenilmez):
  - Boş olanlar atıldıktan sonra seçenek sayısı 2–5 arası olmalı.
  - Aynı metne sahip iki seçenek olamaz (büyük/küçük harf duyarsız, baştaki/sondaki boşluklar kırpılarak).
- Anket ve seçenekler tek bir `transaction.atomic()` içinde kaydedilir.
- Başarılı olunca anket detay sayfasına yönlendirilir.

### Oy verme
- Detay sayfasında ve ana sayfadaki kartta oy verilebilir.
- Oy, `vote.js` ile `fetch` POST (CSRF token header'ı ile) gönderilir. JS kapalıysa normal form POST'u da çalışmalıdır (progressive enhancement).
- Başarılı oy sonrası sayfa yenilenmeden sonuçlar gösterilir: her seçenek için yüzde çubuğu + oy sayısı, kullanıcının seçtiği seçenek işaretlenir.
- Daha önce oy verilmişse butonlar yerine doğrudan sonuçlar gösterilir.
- Mükerrer oy denemesinde (`IntegrityError`) kullanıcıya nazik bir mesaj döner: **"Bu ankete zaten oy verdin."**
- **Sonuç görünürlüğü:** Oy vermemiş kişi sonuçları görmez (oyları etkilememek için). Anket sahibi her zaman görür. Toplam oy sayısı herkese görünür.

### Vote endpoint JSON cevabı (örnek)
```json
{
  "ok": true,
  "total": 42,
  "voted_choice_id": 7,
  "results": [
    {"id": 7, "text": "Sinema", "votes": 25, "percent": 59.5},
    {"id": 8, "text": "Restoran", "votes": 17, "percent": 40.5}
  ]
}
```

### Kayıt / Giriş
- Kayıt formu: e-posta, kullanıcı adı, parola, parola tekrar. Django'nun parola doğrulayıcıları açık.
- Hata mesajları Türkçe: "Bu e-posta zaten kayıtlı.", "Bu kullanıcı adı alınmış." vb.
- Giriş e-posta + parola ile yapılır.

### Gizlilik
- Hiçbir template'te, JSON cevabında veya admin dışı yerde `email` gösterilmez. Template'lerde yazar bilgisi her zaman `poll.author.username` ile yazılır.

---

## 7. Arayüz ve Tasarım

### Hedef kitle ve his
Genç, enerjik, eğlenceli. **Açık (beyaza yakın) arka plan** üzerinde **canlı, doygun renk vurguları**. Sosyal medya uygulaması hissi, kurumsal değil.

### Renk paleti (CSS değişkenleri, `:root` içinde)
```css
:root {
  --bg: #FFF8F0;          /* krem, ana arka plan */
  --surface: #FFFFFF;     /* kartlar */
  --ink: #1A1530;         /* ana metin, kenarlıklar */
  --muted: #6B6580;       /* ikincil metin */

  --pink:   #FF4D8D;
  --purple: #7B5CFF;
  --yellow: #FFD23F;
  --mint:   #2EE6A8;
  --orange: #FF8A3D;

  --radius: 18px;
  --shadow: 4px 4px 0 var(--ink);   /* hafif "neo-brutalist" sert gölge */
}
```
- Seçenekler sırasıyla (order 0–4) **pembe, mor, sarı, mint, turuncu** renklerini alır. Sonuç çubukları da aynı renkte olur.
- Ana buton (Anket Oluştur, Oy Ver): `--purple` veya `--pink` zemin, beyaz yazı, sert gölge, hover'da hafif yukarı kalkma.
- Arka planda çok hafif, büyük, bulanık renk lekeleri (blob) olabilir; içeriğin okunabilirliğini bozmamalı.

### Tipografi
- Google Fonts: Başlıklar için **Bricolage Grotesque** (700–800), gövde için **DM Sans** (400–600). İkisi de Türkçe karakterleri destekler.
- Soru metinleri büyük ve kalın; kartta 20–22px, detayda 28–36px.

### Bileşenler
- **Navbar:** Solda logo + "Kararsızım" yazısı, sağda: misafir → "Giriş" / "Kayıt Ol"; üye → "@kullaniciadi", "Anketlerim", "Çıkış". Her durumda belirgin bir "+ Anket Oluştur" butonu.
- **Hero (ana sayfa üstü):** Kısa slogan, örn. *"Karar veremedin mi? Herkese sor."*
- **Anket kartı:** Beyaz kart, kalın koyu kenarlık, sert gölge, yuvarlatılmış köşeler. İçinde: `@kullaniciadi · 2 saat önce`, soru, seçenek butonları (renkli, hap şeklinde), alt kısımda "🗳️ 42 oy".
- **Sonuç görünümü:** Her seçenek için yatay çubuk; genişlik CSS transition ile 0'dan yüzdeye animasyonlu dolar. Kazanan seçeneğin yanında küçük bir 👑 veya "önde" etiketi.
- **Boş durum:** Hiç anket yoksa sevimli bir mesaj + "İlk anketi sen oluştur" butonu.
- **Flash mesajları:** Django messages framework; renkli, kapatılabilir kutular.

### Genel kurallar
- **Mobil öncelikli** ve responsive. 360px genişlikte yatay kaydırma olmamalı.
- Erişilebilirlik: yeterli kontrast, butonlarda görünür `:focus` stili, form alanlarında `<label>`.
- Arayüz dili tamamen **Türkçe**. `LANGUAGE_CODE = "tr"`, `TIME_ZONE = "Europe/Istanbul"`, zamanlar "2 saat önce" gibi gösterilir (`timesince` filtresi yeterli).
- Tek bir `style.css` dosyası; CSS framework (Bootstrap/Tailwind) kullanılmaz.

---

## 8. Ayarlar ve Ortam Değişkenleri

### `.env.example`
```
DJANGO_SECRET_KEY=degistir-beni
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,.vercel.app
CSRF_TRUSTED_ORIGINS=https://*.vercel.app
DATABASE_URL=
```

### `settings.py` kuralları
- Tüm gizli bilgiler ortam değişkeninden okunur; `python-dotenv` ile lokal `.env` yüklenir.
- `DATABASE_URL` **boşsa** lokal geliştirme için SQLite kullanılır; doluysa `dj_database_url` ile Postgres (Supabase).
- Postgres bağlantısında (Supabase pooler için):
  - `CONN_MAX_AGE = 0`
  - `DISABLE_SERVER_SIDE_CURSORS = True` (transaction pooler, port 6543 ile uyum için)
  - `sslmode=require`
- `STATIC_URL = "/static/"`, `STATIC_ROOT = BASE_DIR / "staticfiles"`, `STATICFILES_DIRS = [BASE_DIR / "static"]`
- WhiteNoise middleware `SecurityMiddleware`'den hemen sonra eklenir.
- `DEBUG=False` iken: `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")`.
- `LOGIN_URL = "/giris/"`, `LOGIN_REDIRECT_URL = "/"`, `LOGOUT_REDIRECT_URL = "/"`.

---

## 9. Güvenlik Kontrol Listesi (prototip seviyesi)
- [ ] CSRF koruması tüm POST'larda aktif (fetch isteklerinde `X-CSRFToken` header'ı).
- [ ] Silme ve çıkış işlemleri sadece POST ile.
- [ ] Anket silme yalnızca sahibine açık (başkası denerse 404/403).
- [ ] Template'lerde otomatik HTML escape açık (`|safe` kullanılmaz).
- [ ] E-posta hiçbir public yerde görünmüyor.
- [ ] Supabase'de Django tablolarında **Row Level Security (RLS) açık ve policy yok** — böylece Supabase'in otomatik REST API'si üzerinden dışarıdan erişilemez. Django `postgres` rolüyle bağlandığı için etkilenmez.
- [ ] `.env` dosyası `.gitignore` içinde.

---

## 10. Geliştirme Aşamaları

> Her aşama ayrı bir Claude Code oturumunda/isteğinde yapılır. Aşama bitince kabul kriterlerini kontrol et, kısa bir özet ver ve dur.

### Aşama 1 — Proje iskeleti ve veri modeli
**Yapılacaklar**
- Klasör yapısını (Bölüm 3) oluştur; `config`, `accounts`, `polls` uygulamaları.
- `requirements.txt`, `.gitignore`, `.env.example`, `pyproject.toml` (Python 3.12), kısa `README.md`.
- `settings.py`'yi Bölüm 8'e göre yaz (SQLite fallback dahil).
- Bölüm 4'teki tüm modelleri yaz; custom User modeli ilk migration'dan **önce**.
- Admin kayıtları: Poll (Choice inline), Vote, User.
- Migration'ları oluştur ve çalıştır.

**Kabul kriterleri**
- `python manage.py runserver` hatasız açılıyor.
- `/admin/` üzerinden kullanıcı, anket ve seçenek eklenebiliyor.
- Aynı `voter_key` ile aynı ankete ikinci oy veritabanı seviyesinde engelleniyor.

### Aşama 2 — Kayıt, giriş, çıkış
**Yapılacaklar**
- Kayıt formu (e-posta, kullanıcı adı, parola x2), e-posta ile giriş, POST ile çıkış.
- `base.html` + `navbar.html` iskeleti (tasarım henüz sade olabilir).
- Türkçe hata mesajları, büyük/küçük harf duyarsız kullanıcı adı/e-posta benzersizliği.

**Kabul kriterleri**
- Yeni kullanıcı kayıt olup otomatik giriş yapıyor.
- Aynı e-posta / aynı kullanıcı adı (farklı harf büyüklüğüyle bile) ikinci kez alınamıyor.
- Navbar'da e-posta değil `@kullaniciadi` görünüyor.

### Aşama 3 — Anket oluşturma, listeleme, detay, silme
**Yapılacaklar**
- `/anket/yeni/` (login_required), dinamik seçenek alanları (`create-poll.js`), sunucu tarafı 2–5 ve tekrar kontrolü.
- Ana sayfa listesi + sayfalama, `poll_card.html` partial'ı.
- Detay sayfası, `/anketlerim/`, sahibe özel silme.
- Misafir yönlendirmesi ve "Anket oluşturmak için üye olmalısın." mesajı.

**Kabul kriterleri**
- 1 veya 6 seçenekli anket oluşturulamıyor (JS kapalıyken bile).
- Misafir ana sayfayı ve detayları görebiliyor ama form sayfasına girince girişe yönleniyor.
- Başkasının anketini silme denemesi başarısız.

### Aşama 4 — Oylama ve sonuçlar
**Yapılacaklar**
- `polls/utils.py` içinde `voter_key` mantığı (Bölüm 4.5).
- `/anket/<id>/oy/` endpoint'i: JSON (fetch) ve normal form POST desteği.
- `vote.js`: CSRF'li fetch, sonuç çubuklarını animasyonla gösterme.
- Sonuç görünürlüğü kuralları (Bölüm 6).

**Kabul kriterleri**
- Misafir ve üye oy verebiliyor; ikinci deneme "Bu ankete zaten oy verdin." döndürüyor.
- Sayfa yenilendiğinde oy verilmiş anketlerde sonuçlar doğrudan görünüyor.
- Yüzdeler toplamı ~%100, seçilen seçenek işaretli.
- Başka bir anketin seçenek id'si ile oy gönderilirse reddediliyor.

### Aşama 5 — Arayüz ve tasarım
**Yapılacaklar**
- Bölüm 7'deki tasarım sistemini `style.css` içinde uygula: renk değişkenleri, fontlar, kartlar, butonlar, sonuç çubukları, hero, boş durum, flash mesajları.
- Basit bir SVG logo (konuşma balonu içinde soru işareti gibi, palet renklerinde).
- Mobil uyumluluk ve focus stilleri.

**Kabul kriterleri**
- 360px, 768px ve 1280px genişlikte düzgün görünüm, yatay kaydırma yok.
- Seçenek renkleri sırayla pembe/mor/sarı/mint/turuncu.
- Tüm sayfalar aynı tasarım dilini kullanıyor.

### Aşama 6 — Supabase ve Vercel'e taşıma
**Yapılacaklar**
- README'ye adım adım kurulum yaz:
  1. Supabase'de proje oluştur → **Connect** menüsünden **Transaction pooler** bağlantı dizesini (port 6543) al → `DATABASE_URL` olarak kullan.
  2. Lokalde `DATABASE_URL` ayarlıyken `python manage.py migrate` çalıştır (migration'lar deploy sırasında değil, lokalden yapılır). Gerekirse migration için **Session pooler** (port 5432) bağlantı dizesi kullanılabilir.
  3. Django tablolarında RLS'i aç (her tablo için `ALTER TABLE ... ENABLE ROW LEVEL SECURITY;`) — bunu bir SQL dosyası olarak `scripts/enable_rls.sql` içinde hazırla.
  4. `createsuperuser` ile admin oluştur.
  5. GitHub'a push → Vercel'de repo'yu import et. Vercel `manage.py`'yi görüp Django'yu otomatik algılar; `STATIC_ROOT` tanımlı olduğu için `collectstatic` build sırasında otomatik çalışır.
  6. Vercel ortam değişkenlerini gir: `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=False`, `DJANGO_ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `DATABASE_URL`.
- Vercel'in Django algılamasıyla ilgili güncel gereksinimleri (entrypoint, `pyproject.toml` ayarları) Vercel'in resmi Django dokümanından kontrol et: https://vercel.com/docs/frameworks/full-stack/django

**Kabul kriterleri**
- Canlı adreste kayıt, giriş, anket oluşturma ve oy verme çalışıyor.
- CSS/JS dosyaları yükleniyor (404 yok).
- `DEBUG=False` ve hata sayfaları detay sızdırmıyor.

---

## 11. Sonraki Adımlar (şimdilik YAPMA)
Prototip bittikten sonra değerlendirilecek fikirler:
- Anket süresi / otomatik kapanma
- Kategoriler ve arama
- Paylaşılabilir anket linki + Open Graph önizlemesi
- Oy değiştirme hakkı
- Yorumlar
- "Popüler" / "Yeni" sekmeleri
- Rate limiting ve daha güçlü anonim oy koruması
- Uygunsuz içerik bildirme
- E-posta doğrulama ve parola sıfırlama
- Profil sayfası (`/u/<kullaniciadi>/`)

---

## 12. Claude Code'a Verilecek Hazır Promptlar

Bu dosyayı repo köküne `PLAN.md` olarak koy. Sonra sırasıyla:

**Aşama 1:**
> PLAN.md dosyasını baştan sona oku. Sadece "Aşama 1 — Proje iskeleti ve veri modeli" bölümünü uygula. Bitince kabul kriterlerini tek tek kontrol et, ne yaptığını kısaca özetle ve dur.

**Aşama 2:**
> PLAN.md'yi tekrar oku. Aşama 1 tamamlandı. Şimdi sadece "Aşama 2 — Kayıt, giriş, çıkış" bölümünü uygula. Kabul kriterlerini kontrol et ve dur.

**Aşama 3:**
> PLAN.md'yi oku. Aşama 1–2 tamamlandı. Şimdi sadece "Aşama 3 — Anket oluşturma, listeleme, detay, silme" bölümünü uygula. Kabul kriterlerini kontrol et ve dur.

**Aşama 4:**
> PLAN.md'yi oku. Aşama 1–3 tamamlandı. Şimdi sadece "Aşama 4 — Oylama ve sonuçlar" bölümünü uygula. Kabul kriterlerini kontrol et ve dur.

**Aşama 5:**
> PLAN.md'yi oku, özellikle Bölüm 7'yi. Aşama 1–4 tamamlandı. Şimdi sadece "Aşama 5 — Arayüz ve tasarım" bölümünü uygula. Mevcut işlevselliği bozma. Kabul kriterlerini kontrol et ve dur.

**Aşama 6:**
> PLAN.md'yi oku. Aşama 1–5 tamamlandı. Şimdi "Aşama 6 — Supabase ve Vercel'e taşıma" bölümünü uygula: ayarları production'a hazırla, scripts/enable_rls.sql dosyasını oluştur ve README'ye adım adım deployment rehberi yaz. Kabul kriterlerini kontrol et ve dur.
