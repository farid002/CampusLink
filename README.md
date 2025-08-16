
# CampusLink — Kampus Birliyi Platforması


> **Dərs istifadəsi üçün:** İstədiyiniz faylların içini boşaldıb (kod hissələrini silib) *yalnız şərhləri saxlaya bilərsiniz*.
Şərhlər hər funksiyanın **məqsədini, giriş/çıxışlarını, addım-addım nə etməli olduğunu** izah edir.

## 🔧 Quraşdırma

```bash
git clone https://github.com/farid002/CampusLink.git
cd CampusLink
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
python app.py
# http://127.0.0.1:5000
```

## 📦 Əsas texnologiyalar
- Backend: **Flask**
- Şablonlar: **Jinja2**
- Verilənlər bazası: **SQLite** (`campusconnect.db`)
- Stil: **Bootstrap (CDN)**

## 📂 Layihə quruluşu (qısa)
```
CampusLink/
 ├─ app.py
 ├─ database.py
 ├─ blog.py          # 📝 Blog + (axtarış, teq filtr, düzəliş/silmə, səhifələmə)
 ├─ events.py        # 🎟 Tədbirlər + (kapasite, təkrar qeydiyyatın qarşısı, CSV ixrac)
 ├─ forum.py         # 💬 Forum + (axtarış, bəyənmə, pin, səhifələmə)
 ├─ gallery.py       # 📸 Qalereya + (detal səhifəsi, filtr, admin silmə, ölçü limiti)
 ├─ polls.py         # 🗳 Sorğular + (yeni sorğu yarat, bağla, sessiya ilə təkrar səslərin qarşısı)
 ├─ feedback.py      # 📬 Əlaqə + (status dəyiş, filtr, CSV ixrac)
 ├─ templates/...
 └─ static/...
```

## 🗄 Verilənlər bazası (yeniləmələr)
- `blog_posts`: `is_published INTEGER DEFAULT 1`, `slug TEXT UNIQUE`
- `events`: `capacity INTEGER DEFAULT 100`
- `forum_topics`: `is_pinned INTEGER DEFAULT 0`, `likes INTEGER DEFAULT 0`
- `gallery_images`: dəyişiklik yoxdur
- `polls`: `is_closed INTEGER DEFAULT 0`
- `feedback`: `status TEXT DEFAULT 'pending'` (mövcuddur)

## 👩‍💻 Tapşırıqlar və öyrənmə məqsədləri
Hər modul faylında **docstring** və funksiyaların başında **maddələnmiş izahlar** var. Bunlar tələbənin:
- HTTP metodlarını (GET/POST) düzgün ayırmağı,
- Forma məlumatlarını yoxlamağı (validation),
- SQL sorğuları ilə CRUD əməliyyatlarını,
- Jinja2 ilə şablon miraslandırma və bloklardan istifadəni,
- Səhifələmə (pagination), axtarış, filter kimi real funksiya dizaynlarını
öyrənməsinə kömək edir.

## 🔐 Admin (demo)
Bəzi funksiyalar (məs., silmək, yaratmaq) üçün *sadə demo parol* istifadə olunur.
Bunu dərsdə **environment variable**-a keçirmək təklif olunur.
