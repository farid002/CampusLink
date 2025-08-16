# -*- coding: utf-8 -*-
"""
events.py — Tədbirlər modulu (SKELETON + TƏLİMAT)

Bu faylda bütün funksiyalar şüurlu şəkildə “boş” saxlanılıb ki, tələbələr
özləri implement etsinlər. Hər funksiyanın docstring-i addım-addım nə etməli
olduqlarını, hansı SQL sorğularını yazacaqlarını və UX/ipucu detalları göstərir.

Texnologiyalar: Flask (routes, request/response, render_template), SQLite (sqlite3), Jinja2 (templates)
Şablonlar: templates/events/ qovluğunda (list.html, create.html, detail.html, my_registrations.html, export_info.html)
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, Response
from database import get_db
import datetime, csv, io

bp = Blueprint("events", __name__, url_prefix="/events")
ADMIN_PASS = "admin123"  # demo üçün sadə parol (yalnız dərs məqsədli)

@bp.route("/")
def list_events():
    """
    Bütün tədbirləri tarixə görə **artan** sırada göstərən siyahı səhifəsi.

    Bu funksiya **tələbə tərəfindən implement olunmalıdır**. Görüləcək işlər:
      1) **DB sorğusu:**
         - `events` cədvəlindən bütün sətrləri tarixə görə artan qaydada seçin:
           `SELECT * FROM events ORDER BY date ASC`
         - `sqlite3.Row` ilə işləyirsinizsə, nəticələri dict kimi istifadə edə biləcəksiniz.

      2) **Qalan yer (capacity remaining) hesabı:**
         - Hər tədbir üçün qeydiyyatların sayını tapın:
           `SELECT COUNT(*) AS c FROM event_registrations WHERE event_id=?`
         - `remaining = max(0, capacity - count)` hesablayın.
         - Şablona ötürəcəyiniz obyektə `remaining` sahəsini əlavə edin (məs., `dict(e)` üzərində).

      3) **Şablon render:**
         - `events/list.html` şablonunu render edin.
         - Şablona `events` (içində `remaining` sahəsi olan) siyahısını verin.

      4) **UX ipucları:**
         - Qalan yer 0 olduqda “Full” etiketi göstərin və “Register” düyməsini deaktiv edin.
         - Tarixi insan-oxunaqlı göstərmək üçün Jinja2-də formatlama edə bilərsiniz.

    Qeyd: Hal-hazırda funksiya yalnız boş şablonu qaytarır.
    """
    return render_template("events/list.html")


@bp.route("/create", methods=["GET","POST"])
def create_event():
    """
    Yeni tədbir yaratmaq üçün səhifə (GET formu göstərir, POST məlumatı qəbul edir) — **admin parolu** ilə sadə demo.

    Bu funksiya **tələbə tərəfindən implement olunmalıdır**. Görüləcək işlər:
      1) **GET (formun göstərilməsi):**
         - `events/create.html` şablonunu render edin.
         - Forma sahələri: `title` (mütləq), `date` (mütləq, ISO `YYYY-MM-DD`), `location` (mütləq),
           `description` (mütləq), `capacity` (default 100), `password` (admin yoxlaması üçün).
         - Forma Bootstrap ilə tərtib oluna bilər.

      2) **POST (formun emalı):**
         - `request.form` vasitəsilə dəyərləri oxuyun və `.strip()` tətbiq edin.
         - **Admin parolu**: `password` dəyəri `ADMIN_PASS` ilə eyni olmalıdır. Yanlışdırsa:
           - eyni şablonu `error="Admin parolu səhvdir."` ilə render edin.
         - **Validasiya**: `title`, `date`, `location`, `description` boş ola bilməz.
           - Boşdursa `error="Bütün sahələr doldurulmalıdır."` mesajı ilə render edin.
         - `capacity` rəqəmə çevrilməlidir (int). Boşdursa 100 götürün (və ya formda `min="1"` təyin edin).
         - DB-yə INSERT:
           `INSERT INTO events (title, date, location, description, capacity) VALUES (?, ?, ?, ?, ?)`
         - `commit()` edin.
         - Uğurdan sonra `redirect(url_for("events.list_events"))`.

      3) **Təhlükəsizlik qeydi:**
         - Bu parol yoxlaması yalnız **dərs məqsədi** üçündür. Real layihədə proper auth lazımdır.

    Qeyd: Hal-hazırda funksiya yalnız boş şablonu qaytarır.
    """
    return render_template("events/create.html", error=None)


@bp.route("/<int:event_id>", methods=["GET", "POST"])
def detail(event_id: int):
    """
    Tədbir detalı + qeydiyyat formu (GET: göstər, POST: qeydiyyat et).

    Bu funksiya **tələbə tərəfindən implement olunmalıdır**. Görüləcək işlər:

      1) **Tədbiri DB-dən gətirin:**
         - `SELECT * FROM events WHERE id = ?` ilə tədbiri tapın.
         - Tapılmasa → `render_template("404.html"), 404`.

      2) **Qalan yerin hesablanması:**
         - `reg_count = SELECT COUNT(*) FROM event_registrations WHERE event_id=?`
         - `remaining = max(0, event["capacity"] - reg_count)`

      3) **POST (qeydiyyat):**
         - Form sahələri: `name` (mütləq), `email` (mütləq).
         - Boşdursa `flash("Ad və e-poçt mütləqdir.")` və `redirect(url_for("events.detail", event_id=event_id))`.
         - `remaining <= 0` isə `flash("Kapasite dolub.")` və redirect eyni səhifəyə.
         - INSERT:
           `INSERT INTO event_registrations (event_id, name, email, created_at) VALUES (?, ?, ?, ?)`
           `created_at` üçün `datetime.datetime.now().strftime("%Y-%m-%d %H:%M")`.
         - **Eyni e-poçtun təkrarı**: DB-də `UNIQUE(event_id, email)` constraint əlavə olunduqda,
           təkrar cəhd `IntegrityError` verəcək. `try/except` ilə `flash("Bu e-poçt ilə artıq qeydiyyatdan keçmisiniz.")`.

      4) **GET (səhifənin göstərilməsi):**
         - Bu tədbirə aid qeydiyyatları da göstərin:
           `SELECT * FROM event_registrations WHERE event_id = ? ORDER BY id DESC`
         - `events/detail.html` şablonunu render edin və ötürün:
           `event`, `regs` (qeydiyyatlar), `remaining`.

      5) **UX ipucları:**
         - Qalan yer 0 olduqda qeydiyyat formunu deaktiv edin.
         - Qeydiyyat uğurlu olduqda flash mesajı göstərin.
         - E-poçt inputunda `type="email"` istifadə edin.

    Qeyd: Hal-hazırda funksiya yalnız boş şablonu qaytarır.
    """
    return render_template("events/detail.html")


@bp.route("/<int:event_id>/export.csv")
def export_csv(event_id: int):
    """
    Bu route **tədbir qeydiyyatlarını CSV faylı kimi ixrac** edir.

    Bu funksiya **tələbə tərəfindən implement olunmalıdır**. Görüləcək işlər:
      1) **Tədbirin mövcudluğunu yoxlayın:**
         - `SELECT * FROM events WHERE id = ?`
         - Tapılmasa → `render_template("404.html"), 404`.

      2) **Qeydiyyatları seçin və CSV hazırlayın:**
         - `SELECT name, email, created_at FROM event_registrations WHERE event_id=? ORDER BY id ASC`
         - `io.StringIO()` buffer yaradın, `csv.writer(buf)` istifadə edin.
         - Başlıq sətri yazın: `["name","email","created_at"]`
         - Sətirləri dövrə salıb `writer.writerow([...])` ilə əlavə edin.

      3) **Cavab olaraq CSV qaytarın:**
         - `Response(buf.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=event_<ID>_regs.csv"})`

      4) **UX ipucları:**
         - `events/detail.html` daxilində “Export CSV” düyməsi verin.
         - Boş qeydiyyat olduqda fayl ancaq header-larla yüklənəcək.

    Qeyd: Skeleton olaraq biz burada yalnız məlumat səhifəsi/şablonu göstəririk.
    """
    # Birbaşa CSV qaytara bilərsiniz


@bp.route("/my-registrations")
def my_regs():
    """
    İstifadəçinin e-poçtuna görə **bütün iştirak etdiyi tədbirləri** göstərən səhifə.

    Bu funksiya **tələbə tərəfindən implement olunmalıdır**. Görüləcək işlər:
      1) **Query parametri:**
         - `email` dəyərini `request.args.get("email")` ilə alın və `.strip()` edin.
         - Boşdursa, sadəcə formu göstərin və `items=[]` qaytarın.

      2) **DB sorğusu (email varsa):**
         - Join sorğusu yazın ki, tədbirin başlıq/tarix/məkanını da görək:
           ```
           SELECT e.title, e.date, e.location, r.created_at
           FROM event_registrations r
           JOIN events e ON e.id = r.event_id
           WHERE r.email = ?
           ORDER BY r.created_at DESC
           ```
         - Nəticəni `items` kimi şablona ötürün.

      3) **Şablon render:**
         - `events/my_registrations.html` şablonunu render edin.
         - Şablona `email` və `items` verin.

      4) **UX ipucları:**
         - Üstdə sadə bir forma (email input + “Bax” düyməsi).
         - Nəticə cədvəlində başlıq, tarix, məkan, qeydiyyat vaxtı sütünları.

    Qeyd: Hal-hazırda funksiya yalnız boş şablonu qaytarır.
    """
    return render_template("events/my_registrations.html")