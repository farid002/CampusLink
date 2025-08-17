# -*- coding: utf-8 -*-
"""
gallery.py — Qalereya modulu

Bu modul Flask blueprint istifadə edir və şəkillərin yüklənməsi,
göstərilməsi, filtrlənməsi və admin tərəfindən silinməsi funksiyalarını təmin edir.
"""

from flask import Blueprint, render_template, request, redirect, url_for, current_app, flash, abort
from database import get_db
import os, datetime, secrets

bp = Blueprint("gallery", __name__, url_prefix="/gallery")

ALLOWED = {"png", "jpg", "jpeg", "gif", "webp"}
MAX_SIZE = 3 * 1024 * 1024  # 3 MB
ADMIN_PASS = "admin123"     # demo parol (yalnız dərs məqsədi üçün)


def allowed(filename: str) -> bool:
    """Faylın genişlənməsini yoxlayır."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED


@bp.route("/")
def grid():
    """
    Şəkillərin siyahısı (grid) + uploader-a görə filtr.
    """
    uploader = (request.args.get("uploader") or "").strip()
    db = get_db()
    if uploader:
        query = "SELECT * FROM gallery_images WHERE uploader LIKE ? ORDER BY id DESC"
        images = db.execute(query, (f"%{uploader}%",)).fetchall()
    else:
        query = "SELECT * FROM gallery_images ORDER BY id DESC"
        images = db.execute(query).fetchall()
    images = [dict(img) for img in images]
    return render_template("gallery/list.html", images=images, uploader=uploader)


@bp.route("/<int:image_id>")
def detail(image_id: int):
    """
    Tək şəklin detal səhifəsi.
    """
    db = get_db()
    img = db.execute("SELECT * FROM gallery_images WHERE id=?", (image_id,)).fetchone()
    if img is None:
        return render_template("404.html"), 404
    img = dict(img)
    return render_template("gallery/detail.html", img=img)


@bp.route("/<int:image_id>/delete", methods=["GET", "POST"])
def delete(image_id: int):
    """
    Şəkli silmək üçün admin route.
    """
    password = request.args.get("password") if request.method == "GET" else request.form.get("password")
    if password != ADMIN_PASS:
        abort(403)

    db = get_db()
    img = db.execute("SELECT filename FROM gallery_images WHERE id=?", (image_id,)).fetchone()
    if img is None:
        flash("Şəkil tapılmadı.")
        return redirect(url_for("gallery.grid"))

    if request.method == "POST":
        filename = img["filename"]
        path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception as e:
            flash(f"Fayl silinərkən xəta baş verdi: {e}")
        db.execute("DELETE FROM gallery_images WHERE id=?", (image_id,))
        db.commit()
        flash("Şəkil uğurla silindi.")
        return redirect(url_for("gallery.grid"))

    # GET: təsdiq səhifəsi
    return render_template("gallery/delete.html", image_id=image_id)


@bp.route("/upload", methods=["GET", "POST"])
def upload():
    """
    Şəkil yükləmə formu.
    """
    if request.method == "POST":
        file = request.files.get("file")
        title = (request.form.get("title") or "Başlıqsız").strip()
        uploader = (request.form.get("uploader") or "Anonim").strip()

        if not file or not file.filename:
            flash("Zəhmət olmasa şəkil faylı seçin.")
            return redirect(url_for("gallery.upload"))

        if not allowed(file.filename):
            flash("Zəhmət olmasa şəkil faylı yükləyin (png, jpg, jpeg, gif, webp).")
            return redirect(url_for("gallery.upload"))

        # Fayl ölçüsünü yoxla
        file.stream.seek(0, os.SEEK_END)
        size = file.stream.tell()
        file.stream.seek(0)
        if size > MAX_SIZE:
            flash("Fayl ölçüsü 3 MB-dən böyükdür.")
            return redirect(url_for("gallery.upload"))

        # Unikal fayl adı yarat
        ext = file.filename.rsplit(".", 1)[1].lower()
        filename = f"{secrets.token_hex(8)}.{ext}"
        path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
        file.save(path)

        # DB-yə yaz
        db = get_db()
        created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        db.execute(
            "INSERT INTO gallery_images (title, filename, uploader, created_at) VALUES (?, ?, ?, ?)",
            (title, filename, uploader, created_at),
        )
        db.commit()
        flash("Şəkil uğurla yükləndi.")
        return redirect(url_for("gallery.grid"))

    # GET
    return render_template("gallery/upload.html")
