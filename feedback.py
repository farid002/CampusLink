# -*- coding: utf-8 -*-
"""
feedback.py — Əlaqə/Geri bildiriş modulu (SKELETON + TƏLİMAT)

Bu faylda funksiyalar qəsdən “boş” saxlanılıb ki, tələbələr özləri
implement etsinlər. Hər funksiya üçün docstring-də addım-addım nə etmək
lazım olduğu göstərilib.

Şablonlar (tövsiyə):
- templates/feedback/contact.html
- templates/feedback/admin_list.html
- templates/feedback/status_result.html  (opsional təsdiq səhifəsi)
"""

from flask import Blueprint, render_template, request, redirect, url_for, Response, flash
from database import get_db
import datetime, csv, io

bp = Blueprint("feedback", __name__)
ADMIN_PASS = "admin123"  # demo parol (yalnız dərs məqsədi üçün)


@bp.route("/contact", methods=["GET", "POST"])
def contact():
    """
    İstifadəçi geri-bildiriş (əlaqə) formu.

    Bu funksiya **tələbə tərəfindən implement olunmalıdır**:

      1) GET → formu göstər:
         - `feedback/contact.html` şablonunu render et.
         - Forma sahələri: `name` (mütləq), `email` (mütləq), `category` (opsional; default "general"),
           `message` (mütləq).
         - Bootstrap ilə sadə, səliqəli form düzəni.

      2) POST → form məlumatını qəbul et və DB-yə yaz:
         - `request.form` ilə dəyərləri al, `.strip()` et.
         - **Validasiya**: `name`, `email`, `message` boş ola bilməz.
           - Boşdursa, eyni şablonu (contact.html) xəta mesajı ilə render et (məs., `error="..."`).
         - DB INSERT:
           `INSERT INTO feedback (name, email, category, message, status, created_at)
            VALUES (?, ?, ?, ?, 'pending', ?)`
           - `created_at` üçün `datetime.datetime.now().strftime("%Y-%m-%d %H:%M")`.
           - İlk status `pending` olsun (default iş axını).
         - `commit()` et.
         - Uğurdan sonra yenidən form səhifəsinə yönləndir (və ya flash mesaj göstər).

      3) UX ipucları:
         - Xəta zamanı istifadəçinin yazdıqlarını input-lara geri qoy.
         - `category` üçün `select` istifadə edə bilərsən (məs. "general", "bug", "idea").

    Qeyd: Skeleton olaraq hazırda yalnız şablonu qaytarır.
    """
    return render_template("feedback/contact.html")


@bp.route("/admin/feedback")
def admin_feedback():
    """
    Admin baxışı (demo): sadə parol ilə (query: `?password=admin123`) təsdiq.

    Bu funksiya **tələbə tərəfindən implement olunmalıdır**:

      1) Admin yoxlaması:
         - `password = request.args.get("password")` qiymətini yoxla.
         - Düzgün deyilsə:
           - `feedback/admin_list.html`-i `items=[]` və `error="Görüntü üçün ?password=admin123 əlavə edin."` ilə render et.
           - **Qeyd:** Bu yalnız dərs üçün sadə yoxlamadır; real auth sistemi ayrıca mövzudur.

      2) Axtarış və filtrlər:
         - Query parametrləri:
           - `q` — axtarış sözü (name/email/message LIKE)
           - `status` — (`pending`, `open`, `handled`) filtr
           - `category` — kateqoriya filtr (tam və ya LIKE)
         - Dinamik WHERE qur:
           ```
           where = ["1=1"]; params = []
           if q: where.append("(name LIKE ? OR email LIKE ? OR message LIKE ?)"); params.extend(["%q%","%q%","%q%"])
           if status: where.append("status = ?"); params.append(status)
           if category: where.append("category LIKE ?"); params.append("%category%")
           ```
         - SQL:
           `SELECT * FROM feedback WHERE ... ORDER BY id DESC`

      3) Şablon render:
         - `feedback/admin_list.html`-ə:
           - `items`: nəticələr
           - `error`: varsa xəta mətni (yoxdursa `None`)
           - `q`, `status`, `category` dəyərləri (formda geri göstərmək üçün)

      4) UX ipucları:
         - Üst hissədə filtr formu (q, status, category).
         - Nəticələri cədvəl (name, email, category, status, created_at, qısa message).

    Qeyd: Skeleton olaraq hazırda yalnız şablonu qaytarır.
    """
    return render_template("feedback/admin_list.html", items=[], error=None)


@bp.route("/admin/feedback/<int:fb_id>/status", methods=["POST"])
def set_status(fb_id: int):
    """
    Statusu dəyişmək üçün route (admin demo).

    Bu funksiya **tələbə tərəfindən implement olunmalıdır**:

      1) Admin yoxlaması:
         - `request.form.get("password")` `ADMIN_PASS`-ə bərabər olmalıdır.
         - Yanlışdırsa, 403 qaytar:
           - ya `return "İcazə yoxdur.", 403`
           - ya `feedback/status_result.html` şablonunu xəta ilə göstər.

      2) `status` dəyərini al və validate et:
         - İcazəli dəyərlər: `pending`, `open`, `handled`
         - Yalnışdırsa 400 qaytar (və ya xəta mesajı ilə şablon göstər).

      3) DB UPDATE:
         - `UPDATE feedback SET status=? WHERE id=?`
         - `commit()` etməyi unutma.

      4) Nəticə:
         - `redirect(url_for("feedback.admin_feedback", password=ADMIN_PASS))`
           və “uğurla dəyişdirildi” mesajı.

    """


@bp.route("/admin/feedback/export.csv")
def export_csv():
    """
    Filtrə uyğun nəticələri **CSV** kimi ixrac edən route (admin demo).

    Bu funksiya **tələbə tərəfindən implement olunmalıdır**:

      1) Admin yoxlaması:
         - `request.args.get("password")` `ADMIN_PASS` ilə eyni olmalıdır.
         - Yanlışdırsa 403.

      2) Filtrləri oxu və WHERE qur:
         - Parametrlər: `q`, `status`, `category`
         - Eyni `admin_feedback()`-dəki kimi WHERE + params hazırla.
         - Seçim: `SELECT name,email,category,message,status,created_at FROM feedback WHERE ... ORDER BY id DESC`

      3) CSV hazırlığı:
         - `buf = io.StringIO()`, `writer = csv.writer(buf)`
         - Başlıq sətri: `["name","email","category","message","status","created_at"]`
         - Dövrə ilə sətrləri yaz: `writer.writerow([...])`

      4) CSV cavabını qaytar:
         - `Response(buf.getvalue(), mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=feedback_export.csv"})`

      5) UX ipucları:
         - `admin_list.html` daxilində “Export CSV” düyməsi qoy.
         - Filtrlərlə istifadəçi CSV-ni dəqiqləşdirə bilsin (məs., yalnız `status=handled`).
    """
