# -*- coding: utf-8 -*-
"""
forum.py — Forum modulu (SKELETON + TƏLİMAT)

Bu faylda funksiyalar qəsdən “boş” saxlanılıb ki, tələbələr özləri
implement etsinlər. Hər funksiyanın docstring-i addım-addım nə etməli
olduqlarını təsvir edir.

Şablonlar (tövsiyə):
- templates/forum/list.html
- templates/forum/new.html
- templates/forum/detail.html
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import get_db, paginate_query
import datetime

bp = Blueprint("forum", __name__, url_prefix="/forum")
ADMIN_PASS = "admin123"  # demo parol (yalnız dərs məqsədi üçün)


@bp.route("/")
def list_topics():
    """
    Mövzuların siyahısı + axtarış + səhifələmə.

    Bu funksiya **tələbə tərəfindən implement olunmalıdır**:

      1) Query parametrləri:
         - `q` (opsional): başlıq və məzmun üzrə axtarış (LIKE).
         - `page` (opsional, default 1): səhifə nömrəsi. Hər səhifədə məsələn 8 mövzu.

      2) WHERE qurulması:
         - `where = ["1=1"]`, `params = []`.
         - Əgər `q` varsa: `where.append("(title LIKE ? OR content LIKE ?)")`
           və `params.extend([f"%{q}%", f"%{q}%"])`.

      3) Sıralama:
         - `ORDER BY is_pinned DESC, created_at DESC`
           (əvvəl pinned olanlar, sonra ən yenilər).

      4) Səhifələmə:
         - `base = f"SELECT * FROM forum_topics WHERE {' AND '.join(where)} ORDER BY ..."`
         - `sql, limit, offset = paginate_query(base, page, per_page=8)`
         - `db.execute(sql, (*params, limit, offset))`

      5) Şablon render:
         - `forum/list.html`-ə göndərin:
           - `topics` (siyahı),
           - `q`, `page` (formda geri göstərmək üçün).

      6) UX ipucları:
         - Axtarış üçün input + “Axtar” düyməsi.
         - Pinned mövzular üçün badge (`PINNED`) göstərin.
         - Səhifələmə linkləri: əvvəlki/sonrakı səhifə.

    Qeyd: Skeleton olaraq hazırda yalnız şablonu qaytarır.
    """
    return render_template("forum/list.html")


@bp.route("/new", methods=["GET", "POST"])
def new_topic():
    """
    Yeni mövzu yaratmaq (GET: formu göstər, POST: DB-yə yaz).

    Bu funksiya **tələbə tərəfindən implement olunmalıdır**:

      1) GET:
         - `forum/new.html` şablonunu render edin.
         - Form sahələri: `title` (mütləq), `author` (mütləq), `content` (mütləq).

      2) POST:
         - `request.form` ilə dəyərləri al, `.strip()` et.
         - Validasiya: `title`, `author`, `content` boş ola bilməz.
           - Boşdursa eyni şablonu `error="Bütün sahələr mütləqdir."` ilə render et
             (və istifadəçinin yazdıqlarını input-lara geri qoy).
         - DB INSERT:
           `INSERT INTO forum_topics (title, author, content, created_at, likes, is_pinned)
            VALUES (?, ?, ?, ?, 0, 0)`
           - `created_at` üçün `datetime.datetime.now().strftime("%Y-%m-%d %H:%M")`.
         - `commit()` et.
         - Uğurdan sonra `redirect(url_for("forum.list_topics"))`.

      3) UX ipucları:
         - Uğurlu əlavə üçün `flash()` mesajı.
         - `Cancel` → siyahıya qayıt linki.

    Qeyd: Skeleton olaraq hazırda yalnız şablonu qaytarır.
    """
    return render_template("forum/new.html")


@bp.route("/<int:topic_id>", methods=["GET", "POST"])
def detail(topic_id: int):
    """
    Mövzu detalları + cavabı (reply) əlavə etmək.

    Bu funksiya **tələbə tərəfindən implement olunmalıdır**:

      1) Mövzunu DB-dən gətir:
         - `SELECT * FROM forum_topics WHERE id=?`.
         - Tapılmasa: `render_template("404.html"), 404`.

      2) GET:
         - Bu mövzuya aid cavabları gətir:
           `SELECT * FROM forum_replies WHERE topic_id=? ORDER BY id ASC`.
         - `forum/detail.html`-ə `topic` və `replies` ötür.

      3) POST (reply əlavə etmək):
         - Form sahələri: `author` (mütləq), `content` (mütləq).
         - Boşdursa eyni səhifəyə redirect (və ya `flash()`).
         - DB INSERT:
           `INSERT INTO forum_replies (topic_id, author, content, created_at) VALUES (?, ?, ?, ?)`
           - `created_at` üçün `datetime.datetime.now().strftime("%Y-%m-%d %H:%M")`.
         - `commit()` və `redirect(url_for("forum.detail", topic_id=topic_id))`.

      4) UX ipucları:
         - Reply formu səhifənin aşağısında.
         - Mövzunun üstündə `likes` sayı və `PINNED` badge (əgər `is_pinned=1`).

    Qeyd: Skeleton olaraq hazırda yalnız şablonu qaytarır.
    """
    return render_template("forum/detail.html")


@bp.route("/<int:topic_id>/like", methods=["POST"])
def like(topic_id: int):
    """
    Mövzunu “bəyənmək” (likes sayını 1 artırmaq).

    Bu funksiya **tələbə tərəfindən implement olunmalıdır**:

      1) HTTP method:
         - Təhlükəsizlik baxımından **POST** istifadə edin (GET deyil).
         - `form` və ya `fetch`/AJAX ilə çağırıla bilər.

      2) DB UPDATE:
         - `UPDATE forum_topics SET likes = likes + 1 WHERE id = ?`.
         - `commit()`.

      3) Nəticə:
         - `redirect(url_for("forum.detail", topic_id=topic_id))`
           və ya JSON cavab (əgər AJAX).

      4) Anti-abuse (opsional):
         - Sessiya və ya IP ilə eyni istifadəçinin tez-tez bəyənməsinin qarşısını alın.

    Qeyd: Skeleton olaraq hazırda yalnız şablonu qaytarır.
    """
    return render_template("forum/detail.html")


@bp.route("/<int:topic_id>/pin", methods=["POST"])
def pin(topic_id: int):
    """
    Mövzunu “pin” etmək (üstə qaldırmaq) — admin demo parolla.

    Bu funksiya **tələbə tərəfindən implement olunmalıdır**:

      1) Admin yoxlaması:
         - `request.form.get("password")` `ADMIN_PASS` ilə eyni olmalıdır.
         - Yanlışdırsa, 403 qaytar (və ya `flash()` + redirect).

      2) DB UPDATE:
         - `UPDATE forum_topics SET is_pinned = 1 WHERE id = ?`.
         - `commit()`.

      3) Nəticə:
         - Siyahıya yönləndir:
           `redirect(url_for("forum.list_topics"))`.

      4) UX ipucları:
         - Admin list və ya detail səhifəsində “Pin” düyməsi.
         - Pinned mövzuları siyahıda badge ilə fərqləndir.

    Qeyd: Skeleton olaraq hazırda yalnız siyahı şablonunu qaytarır.
    """
    return render_template("forum/list.html")