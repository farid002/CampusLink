# -*- coding: utf-8 -*-
"""
blog.py — Blog modulu.

Yeni imkanlar:
 - Axtarış (başlıq + məzmun)
 - Teq üzrə filtr
 - Səhifələmə (pagination)
 - Yazını düzəltmək / silmək
 - Draft (is_published=0) və dərc edilmiş yazılar üçün filtr
 - Slug ilə hər bir blog yazısına giriş

**Qeyd** Hər funksiyanın docstring-i addım-addım nə edilməli olduğunu təsvir edir.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import get_db
import datetime, re

bp = Blueprint("blog", __name__, url_prefix="/blog")

ADMIN_PASS = "admin123"  # demo parol


def slugify(text: str) -> str:
    """
    Verilən başlıqdan sadə slug yaradır.
    - Kiçik hərfləşdirir, boşluqları tire edir, latın olmayan simvolları silir.
    """
    s = text.strip().lower()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    return s[:80]

@bp.route("/")
def list_posts():
    """
    Bütün postları listləyir.
    - q parametri ilə axtarış (title və content)
    - tag parametri ilə filtr
    - published (0 və ya 1) ilə filtr
    - səhifələmə (page=?)
    """
    db = get_db()
    q = request.args.get("q", "").strip()
    tag = request.args.get("tag", "").strip()
    published = request.args.get("published", "").strip()
    page = int(request.args.get("page", 1))

    where = ["1=1"]
    params = []

    # Axtarış
    if q:
        where.append("(title LIKE ? OR content LIKE ?)")
        params.extend([f"%{q}%", f"%{q}%"])

    # Teq filtr
    if tag:
        where.append("tags LIKE ?")
        params.append(f"%{tag}%")

    # Published filtr
    if published in ("0", "1"):
        where.append("is_published=?")
        params.append(published)

    # Pagination parametrləri
    per_page = 5
    offset = (page - 1) * per_page

    # Ümumi say
    count_sql = f"SELECT COUNT(*) as c FROM blog_posts WHERE {' AND '.join(where)}"
    total = db.execute(count_sql, params).fetchone()["c"]

    # Postları gətir
    sql = f"""
        SELECT * FROM blog_posts
        WHERE {" AND ".join(where)}
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    """
    posts = db.execute(sql, params + [per_page, offset]).fetchall()

    total_pages = (total + per_page - 1) // per_page

    return render_template("blog/list.html",
                           posts=posts,
                           q=q, tag=tag, published=published,
                           page=page, total_pages=total_pages)


@bp.route("/<slug>")
def show_post(slug: str):
    db = get_db()

    # Fetch post first
    post = db.execute("SELECT * FROM blog_posts WHERE slug=?", (slug,)).fetchone()
    if post is None:
        return render_template("404.html"), 404

    # Increment views
    db.execute("UPDATE blog_posts SET views = views + 1 WHERE slug=?", (slug,))
    db.commit()

    post_dict = dict(post)
    post_dict["views"] += 1

    return render_template("blog/detail.html", post=post_dict)


@bp.route("/id/<int:post_id>")
def show_post_by_id(post_id: int):
    """
    ID əsasında post göstər.
    """
    db = get_db()
    post = db.execute("SELECT * FROM blog_posts WHERE id=?", (post_id,)).fetchone()
    if post is None:
        return render_template("404.html"), 404
    return render_template("blog/detail.html", post=post)


@bp.route("/new", methods=["GET", "POST"])
def new_post():
    """
    Yeni post yaratmaq.
    - Formadan title, content, tags, is_published götürür.
    - Slug unikallığını yoxlayır.
    """
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        tags = request.form.get("tags", "").strip()
        is_published = 1 if request.form.get("is_published") else 0

        if not title or not content:
            flash("Title və Content boş ola bilməz!", "danger")
            return redirect(url_for("blog.new_post"))

        db = get_db()
        slug = slugify(title)

        # slug unikallığını yoxla
        exists = db.execute("SELECT id FROM blog_posts WHERE slug=?", (slug,)).fetchone()
        i = 2
        while exists:
            slug = f"{slugify(title)}-{i}"
            exists = db.execute("SELECT id FROM blog_posts WHERE slug=?", (slug,)).fetchone()
            i += 1

        created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        db.execute(
            "INSERT INTO blog_posts (title, content, tags, created_at, is_published, slug) VALUES (?, ?, ?, ?, ?, ?)",
            (title, content, tags, created_at, is_published, slug)
        )
        db.commit()

        flash("Yeni yazı əlavə olundu!", "success")
        return redirect(url_for("blog.list_posts"))

    return render_template("blog/new.html")



@bp.route("/<int:post_id>/edit", methods=["GET", "POST"])
def edit(post_id: int):
    """
    Mövcud postu redaktə etmək.
    - Parol yoxlanılır.
    - Form POST ilə yeni məlumatları DB-də yeniləyir.
    """
    password = request.args.get("password", "")
    if password != ADMIN_PASS:
        return render_template("blog/edit.html", error="İcazə yoxdur (parol səhvdir)")

    db = get_db()
    post = db.execute("SELECT * FROM blog_posts WHERE id=?", (post_id,)).fetchone()
    if post is None:
        return render_template("404.html"), 404

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("content", "").strip()
        tags = request.form.get("tags", "").strip()
        is_published = 1 if request.form.get("is_published") else 0

        if not title or not content:
            error = "Title və Content boş ola bilməz!"
            return render_template("blog/edit.html", post=request.form, error=error)

        db.execute(
            "UPDATE blog_posts SET title=?, content=?, tags=?, is_published=? WHERE id=?",
            (title, content, tags, is_published, post_id)
        )
        db.commit()
        flash("Yazı yeniləndi!", "success")
        return redirect(url_for("blog.show_post_by_id", post_id=post_id))

    return render_template("blog/edit.html", post=post, error=None)


@bp.route("/<int:post_id>/delete")
def delete(post_id: int):
    """
    Postu silmək.
    - Parol yoxlanılır.
    """
    password = request.args.get("password", "")
    if password != ADMIN_PASS:
        return "İcazə yoxdur", 403

    db = get_db()
    db.execute("DELETE FROM blog_posts WHERE id=?", (post_id,))
    db.commit()

    flash("Yazı silindi!", "info")
    return redirect(url_for("blog.list_posts"))


@bp.route("/<int:post_id>", methods=["GET"])
def detail(post_id):
    db = get_db()

    # Increment views
    db.execute("UPDATE blog_posts SET views = views + 1 WHERE id = ?", (post_id,))
    db.commit()

    # Fetch post
    post = db.execute("SELECT * FROM blog_posts WHERE id = ?", (post_id,)).fetchone()

    if post is None:
        return render_template("404.html"), 404

    # Convert to dict to update views for display
    post_dict = dict(post)
    post_dict["views"] += 1

    return render_template("blog/detail.html", post=post_dict)