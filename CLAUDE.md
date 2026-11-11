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

Henüz test dosyası yok. Test eklenecekse Django'nun test runner'ı (`django.test.TestCase`) kullanılır; ek test paketi yok. Linter/formatter tanımlı değil.

## Mimari

- `config/`: proje ayarları. `settings.py` her şeyi ortam değişkeninden okur (`python-dotenv` ile lokal `.env`). `DATABASE_URL` boşsa SQLite (`db.sqlite3`), doluysa `dj_database_url` ile Supabase Postgres kullanılır (transaction pooler için `conn_max_age=0`, `DISABLE_SERVER_SIDE_CURSORS=True`, SSL zorunlu). `DEBUG=False` iken `DJANGO_SECRET_KEY` yoksa başlatma hata verir. Statikler WhiteNoise + `CompressedManifestStaticFilesStorage` ile sunulur; production'da `collectstatic` gerekir.
- `accounts/`: özel `User` modeli (`AUTH_USER_MODEL = "accounts.User"`). Giriş **e-posta** ile yapılır (`USERNAME_FIELD = "email"`). Manager'ın `get_by_natural_key` metodu e-postayı `iexact` ile arar. E-posta `save()`/`clean()` içinde küçük harfe çevrilir. Kullanıcı adı ve e-posta benzersizliği hem alan seviyesinde hem `Lower()` fonksiyonel `UniqueConstraint` ile veritabanında büyük/küçük harf duyarsızdır. Kullanıcı adı yalnızca ASCII harf, rakam, `_` ve `.` kabul eder (3–30). Django'nun hazır `UserCreationForm`'u auth.User'a bağlı olduğu için admin, `accounts/forms.py` içindeki özel formları kullanır.
- `polls/`: `Poll` → `Choice` (en az 2, en fazla 5, `order` 0–4 ve `(poll, order)` benzersiz; `order` seçenek rengini belirler) → `Vote`. Tek oy kuralı veritabanındaki `UniqueConstraint(poll, voter_key)` (`one_vote_per_voter`) ile sağlanır. `voter_key` üyeler için `u:<user.id>`, misafirler için imzalı `kz_voter` çerezindeki UUID'den `a:<uuid>` (mantık `polls/utils.py` içinde toplanacak). Mükerrer oy `IntegrityError` olarak yakalanıp Türkçe mesaja çevrilir. `choice.poll == poll` kontrolü view'da da yapılmalı. `Poll.total_votes`, queryset `annotate(vote_count=Count("votes"))` içeriyorsa ek sorgu yapmaz.
- `templates/` ve `static/` proje kökündedir (uygulama içinde değil). JS dosyaları (`vote.js`, `create-poll.js`) yalnızca progressive enhancement içindir: tüm form ve oy akışları JS kapalıyken de çalışmalı ve doğrulama sunucu tarafında yapılmalı.

## Değişmez kurallar

- `email` hiçbir template'te, JSON cevabında veya admin dışı bir yerde gösterilmez. Yazar bilgisi her zaman `poll.author.username` ile yazılır.
- Oy vermemiş kişi sonuçları görmez; anket sahibi her zaman görür; toplam oy sayısı herkese görünür. Bu kural ana sayfa kartlarında da geçerlidir.
- Silme ve çıkış yalnızca POST ile yapılır. Anketi yalnızca sahibi silebilir. `|safe` kullanılmaz.
- Bilinen ve kabul edilmiş sınırlamalar (README'de yazılı): çerez silen misafir ve misafirken oy verip sonra giriş yapan kullanıcı tekrar oy verebilir.
