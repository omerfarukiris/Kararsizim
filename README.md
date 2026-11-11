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

## Bilinen sınırlamalar (prototip)

- Üye olmayan biri çerezlerini silerse aynı ankete tekrar oy verebilir.
- Misafirken oy veren biri sonradan üye olup giriş yaparsa aynı ankete bir kez daha oy verebilir (misafir ve üye oyları farklı `voter_key` ile tutulur).
