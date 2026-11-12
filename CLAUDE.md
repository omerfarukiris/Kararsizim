# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Proje ve çalışma şekli

Kararsızım: kullanıcıların anket açıp herkesin (misafirler dahil) oy verdiği bir Django prototipi. **Tek referans kaynağı [docs/KARARSIZIM_PLAN.md](docs/KARARSIZIM_PLAN.md)'dir.** Veri modeli, URL'ler, iş kuralları, tasarım sistemi ve 6 geliştirme aşaması orada tanımlı.

- İş aşama aşama yapılır. Yalnızca istenen aşamayı uygula, sonunda o aşamanın kabul kriterlerini tek tek doğrula, özet ver ve dur. Bir sonraki aşamaya kendiliğinden geçme.
- Prototip kuralı: frontend framework, npm, build adımı, CSS framework yok. `requirements.txt` dışında paket eklemeden önce gerekçesini kullanıcıya söyle.
- Arayüz dili tamamen Türkçe; kullanıcıya görünen hata mesajları da Türkçe (planda birebir metinler verilmiş, örn. "Bu ankete zaten oy verdin.").
- Aşama 6'da (yayına alma) Supabase projesi, RLS ve Vercel projesi bağlı MCP araçlarıyla doğrudan kurulacak (kullanıcı bu seçeneği onayladı). Yalnızca README rehberi yazılmayacak.

## Komutlar

Sanal ortam `.venv` (Python 3.12; 3.14 değil). Aktive etmeden `.venv/bin/python` ile çalıştır.

```bash
.venv/bin/pip install -r requirements.txt
.venv/bin/python manage.py runserver
.venv/bin/python manage.py makemigrations && .venv/bin/python manage.py migrate
.venv/bin/python manage.py makemigrations --check --dry-run   # model/migration uyumu
.venv/bin/python manage.py check
.venv/bin/python manage.py test                               # tüm testler
.venv/bin/python manage.py test polls.tests.VoteTests.test_duplicate_vote   # tek test
```

Supabase'e migration (session pooler, `.env`'deki `DATABASE_URL_DIRECT`): `DJANGO_DB_DIRECT=1 .venv/bin/python manage.py migrate`; ardından `scripts/enable_rls.sql` çalıştırılır (RLS + `anon`/`authenticated` için `api_erisimi_yok` deny policy'si; yeni tablo eklenince tekrar çalıştır). Not: kullanıcının ağı ve bu ortam 5432/6543 portlarına çıkamıyor; migration gerekirse SQL üretilip Supabase MCP ile uygulanır. `.env`'de `DATABASE_URL` doluyken testler de Supabase'e gider; lokal SQLite için komutun başına `DATABASE_URL=` ekle. Production `vercel.json` ile Frankfurt (`fra1`) bölgesinde çalışır.

Testler `accounts/tests.py` ve `polls/tests.py` içinde, Django'nun test runner'ı (`django.test.TestCase`) ile; ek test paketi yok. Linter/formatter tanımlı değil.

## Mimari

- `config/`: proje ayarları. `settings.py` her şeyi ortam değişkeninden okur (`python-dotenv` ile lokal `.env`). `DATABASE_URL` boşsa SQLite (`db.sqlite3`), doluysa `dj_database_url` ile Supabase Postgres kullanılır (transaction pooler için `conn_max_age=0`, `DISABLE_SERVER_SIDE_CURSORS=True`, SSL zorunlu). `DEBUG=False` iken `DJANGO_SECRET_KEY` yoksa başlatma hata verir. Statikler WhiteNoise ile sunulur. `CompressedManifestStaticFilesStorage` yalnızca `DEBUG=False` iken seçilir ve `collectstatic` gerektirir; `.env` içinde `DJANGO_DEBUG=True` değilse testler `Missing staticfiles manifest entry` hatası verir.
- `accounts/`: özel `User` modeli (`AUTH_USER_MODEL = "accounts.User"`). Giriş **e-posta** ile yapılır (`USERNAME_FIELD = "email"`). Manager'ın `get_by_natural_key` metodu e-postayı `iexact` ile arar. E-posta `save()`/`clean()` içinde küçük harfe çevrilir. Kullanıcı adı ve e-posta benzersizliği hem alan seviyesinde hem `Lower()` fonksiyonel `UniqueConstraint` ile veritabanında büyük/küçük harf duyarsızdır. Kullanıcı adı yalnızca ASCII harf, rakam, `_` ve `.` kabul eder (3–30). Django'nun hazır `UserCreationForm`'u auth.User'a bağlı olduğu için admin, `accounts/forms.py` içindeki özel formları kullanır.
- `polls/`: `Poll` → `Choice` (en az 2, en fazla 5, `order` 0–4 ve `(poll, order)` benzersiz; `order` seçenek rengini belirler) → `Vote`. Tek oy kuralı veritabanındaki `UniqueConstraint(poll, voter_key)` (`one_vote_per_voter`) ile sağlanır. `voter_key` üyeler için `u:<user.id>`, misafirler için imzalı `kz_voter` çerezindeki UUID'den `a:<uuid>` (mantık `polls/utils.py` içinde toplanacak). Mükerrer oy `IntegrityError` olarak yakalanıp Türkçe mesaja çevrilir. `choice.poll == poll` kontrolü view'da da yapılmalı. `Poll.total_votes`, queryset `annotate(vote_count=Count("votes"))` içeriyorsa ek sorgu yapmaz.
- Anket formu (`polls/forms.py`): seçenekler aynı isimli tekrarlanan `choices` input'ları olarak gönderilir ve `ChoiceListField` ile liste halinde okunur (kırpma, boşları atma, 2–5 adet, harf büyüklüğünden bağımsız tekrar kontrolü). Sunucu her zaman 5 kutu çizer (`form.choice_inputs`); `create-poll.js` boş fazlalıkları kaldırır. Misafiri uyarı mesajıyla girişe yönlendiren `member_required` decorator'ı `polls/views.py` içindedir. Zaman gösterimi için `{% load poll_tags %}` ve `time_ago` filtresi kullanılır (`timesince` yerine; bir dakikadan yeniyse "az önce").
- Oylama: `polls/utils.py` içinde `get_voter_key` (salt okuma, çerez üretmez), `get_or_create_voter_key` + `set_voter_cookie` (oy anında) ve `attach_vote_state` vardır. Listeleyen her view anketlere `attach_vote_state` uygulamalıdır; şablonlar `poll.can_vote`, `poll.show_results`, `poll.results` alanlarına dayanır ve `poll_queryset()` seçenekleri `vote_count` annotate ederek prefetch eder. `vote` view'ı `Accept: application/json` gelirse JSON (200 / 400 geçersiz seçenek / 409 zaten oy verdin, sonuçlarla birlikte), gelmezse mesaj + güvenli `next` redirect döner. Sonuç çubuğu HTML'i iki yerde üretilir: `templates/partials/poll_results.html` ve `static/js/vote.js` içindeki `renderResults` — birini değiştirirsen diğerini de güncelle.
- Bağımlılıklar hem `requirements.txt` hem `pyproject.toml` (`[project].dependencies`) içinde, sabit sürümlerle (`==`). Vercel `pyproject.toml`'dan kurar; ikisini aynı tut.
- Production güvenliği (`DEBUG=False`): `SECURE_SSL_REDIRECT`, HSTS (`DJANGO_HSTS_SECONDS`, varsayılan 3600; includeSubDomains/preload bilerek kapalı), güvenli çerezler, `WHITENOISE_MANIFEST_STRICT=False`. `CSRF_TRUSTED_ORIGINS` boş kalmalı; `*.vercel.app` jokeri kullanılmaz. `DJANGO_ALLOWED_HOSTS` gerçek adresle sınırlanır.
- `templates/` ve `static/` proje kökündedir (uygulama içinde değil). JS dosyaları (`vote.js`, `create-poll.js`) yalnızca progressive enhancement içindir: tüm form ve oy akışları JS kapalıyken de çalışmalı ve doğrulama sunucu tarafında yapılmalı.

## Tasarım

Tüm stil `static/css/style.css` içinde, `:root` değişkenleriyle (plan Bölüm 7). Seçenek rengi `order` ile `.choice-pill--N` / `.result--N` sınıflarından gelir (0–4: pembe, mor, sarı, mint, turuncu). Beyaz yazı taşıyan mor zeminler kontrast için `--purple-strong` kullanır; `--purple` yalnızca dekor ve sonuç çubuklarında. 600px altında navbar sabit değildir ve iki satıra düşer. `templates/500.html` bilerek `base.html`'i kullanmaz (hata anında bağlam olmayabilir).

## Değişmez kurallar

- `email` hiçbir template'te, JSON cevabında veya admin dışı bir yerde gösterilmez. Yazar bilgisi her zaman `poll.author.username` ile yazılır.
- Oy vermemiş kişi sonuçları görmez; anket sahibi her zaman görür; toplam oy sayısı herkese görünür. Bu kural ana sayfa kartlarında da geçerlidir.
- Silme ve çıkış yalnızca POST ile yapılır. Anketi yalnızca sahibi silebilir. `|safe` kullanılmaz.
- Bilinen ve kabul edilmiş sınırlamalar (README'de yazılı): çerez silen misafir ve misafirken oy verip sonra giriş yapan kullanıcı tekrar oy verebilir.
