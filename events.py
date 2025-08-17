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
from flask import g
from database import get_db
import datetime, csv, io,sqlite3

bp = Blueprint("events", __name__, url_prefix="/events")
ADMIN_PASS = "admin123"  # demo üçün sadə parol (yalnız dərs məqsədli)
@bp.route("/")
def list_events():
    db = get_db()

    rows = db.execute("SELECT * FROM events ORDER BY date ASC").fetchall()

    final_events = []
    for event in rows:
        count = db.execute(
            "SELECT COUNT(*) FROM event_registrations WHERE event_id = ?",
            (event["id"],)
        ).fetchone()[0]
        remaining = max(0, event["capacity"] - count)

        # Row → dict
        event_dict = dict(event)
        event_dict["remaining"] = remaining

        final_events.append(event_dict)

    return render_template("events/list.html", events=final_events)
@bp.route("/create", methods=["GET","POST"])
def create_event():
    ADMIN_PASS = "admin123"  # demo üçün sadə parol

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        date = request.form.get("date", "").strip()
        location = request.form.get("location", "").strip()
        description = request.form.get("description", "").strip()
        capacity = request.form.get("capacity", "").strip()
        password = request.form.get("password", "").strip()

        # Admin parol yoxlanışı
        if password != ADMIN_PASS:
            error = "Admin parolu səhvdir."
            return render_template("events/create.html", error=error)

        # Vacib sahələrin yoxlanışı
        if not title or not date or not location or not description:
            error = "Bütün sahələr doldurulmalıdır."
            return render_template("events/create.html", error=error)

        # Capacity int-ə çevrilir, boşdursa 100 götürülür
        try:
            capacity = int(capacity) if capacity else 100
        except ValueError:
            capacity = 100

        # DB-yə əlavə
        db = get_db()
        db.execute(
            "INSERT INTO events (title, date, location, description, capacity) VALUES (?, ?, ?, ?, ?)",
            (title, date, location, description, capacity)
        )
        db.commit()

        flash("Tədbir uğurla yaradıldı!", "success")
        return redirect(url_for("events.list_events"))

    # GET request: form göstərilir
    return render_template("events/create.html", error=None)
@bp.route("/<int:event_id>", methods=["GET", "POST"])
def detail(event_id: int):
    db = get_db()
    event = db.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
    if not event:
        return render_template("404.html"), 404

    reg_count = db.execute(
        "SELECT COUNT(*) FROM event_registrations WHERE event_id = ?", (event_id,)
    ).fetchone()[0]
    remaining = max(0, event["capacity"] - reg_count)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        if not name or not email:
            flash("Ad və e-poçt mütləqdir.")
            return redirect(url_for("events.detail", event_id=event_id))
        if remaining <= 0:
            flash("Kapasite dolub.")
            return redirect(url_for("events.detail", event_id=event_id))
        try:
            db.execute(
                "INSERT INTO event_registrations (event_id, name, email, created_at) VALUES (?, ?, ?, ?)",
                (event_id, name, email, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
            )
            db.commit()
            flash("Qeydiyyat uğurla tamamlandı.")
            return redirect(url_for("events.detail", event_id=event_id))
        except sqlite3.IntegrityError:
            flash("Bu e-poçt ilə artıq qeydiyyatdan keçmisiniz.")
            return redirect(url_for("events.detail", event_id=event_id))

    regs = db.execute(
        "SELECT * FROM event_registrations WHERE event_id = ? ORDER BY id DESC", (event_id,)
    ).fetchall()

    return render_template("events/detail.html", event=event, regs=regs, remaining=remaining)
@bp.route("/<int:event_id>/export.csv")
def export_csv(event_id: int):
    db = get_db()

    # 1️⃣ Tədbiri yoxlayın
    event = db.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
    if not event:
        return render_template("404.html"), 404

    # 2️⃣ Qeydiyyatları götürün
    regs = db.execute("""
        SELECT name, email, created_at
        FROM event_registrations
        WHERE event_id = ?
        ORDER BY id ASC
    """, (event_id,)).fetchall()

    # 3️⃣ CSV hazırlayın
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["name", "email", "created_at"])  # başlıq

    for reg in regs:
        writer.writerow([reg["name"], reg["email"], reg["created_at"]])

    # 4️⃣ Cavabı qaytarın
    csv_filename = f"event_{event_id}_regs.csv"
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={csv_filename}"}
    )

@bp.route("/my-registrations")
def my_regs():
    db = get_db()
    email = request.args.get("email", "").strip()
    items = []

    if email:
        items = db.execute("""
            SELECT e.title, e.date, e.location, r.created_at
            FROM event_registrations r
            JOIN events e ON e.id = r.event_id
            WHERE r.email = ?
            ORDER BY r.created_at DESC
        """, (email,)).fetchall()

    return render_template(
        "events/my_registrations.html",
        email=email,
        items=items
    )
from flask import request, render_template, redirect, url_for, current_app

ADMIN_PASS = "admin123"  # Dərs məqsədli demo parol

@bp.route("/delete", methods=["POST"])
def delete_event():
    """
    Tədbiri admin parolu ilə silmək üçün.
    Form POST edir: event_id və password.
    """
    event_id = request.form.get("event_id")
    password = request.form.get("password", "").strip()

    if password != ADMIN_PASS:
        flash("Admin parolu səhvdir.", "danger")
        return redirect(url_for("events.list_events"))

    if not event_id or not event_id.isdigit():
        flash("Yanlış tədbir ID.", "danger")
        return redirect(url_for("events.list_events"))

    db = get_db()
    # 1️⃣ Əvvəl qeydiyyatları sil
    db.execute("DELETE FROM event_registrations WHERE event_id = ?", (int(event_id),))
    # 2️⃣ Sonra tədbiri sil
    db.execute("DELETE FROM events WHERE id = ?", (int(event_id),))
    db.commit()

    flash("Tədbir və bütün qeydiyyatlar uğurla silindi.", "success")
    return redirect(url_for("events.list_events"))