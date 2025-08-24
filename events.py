# -*- coding: utf-8 -*-
"""
events.py — Tədbirlər modulu (Tam işlək, admin session ilə)
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, Response, session
from database import get_db
import datetime, csv, io, sqlite3

bp = Blueprint("events", __name__, url_prefix="/events")
ADMIN_PASS = "admin123"

# -----------------------------
# Tədbirləri siyahıla / filtr
# -----------------------------
@bp.route("/")
def list_events():
    db = get_db()

    category = request.args.get("category", "").strip()
    min_capacity = request.args.get("min_capacity", "").strip()

    query = "SELECT * FROM events WHERE 1=1"
    params = []

    if category:
        query += " AND category = ?"
        params.append(category)

    if min_capacity:
        try:
            min_capacity = int(min_capacity)
            query += " AND capacity >= ?"
            params.append(min_capacity)
        except ValueError:
            pass

    query += " ORDER BY date ASC"
    rows = db.execute(query, params).fetchall()

    final_events = []
    for event in rows:
        count = db.execute(
            "SELECT COUNT(*) FROM event_registrations WHERE event_id = ?",
            (event["id"],)
        ).fetchone()[0]
        remaining = max(0, event["capacity"] - count)

        event_dict = dict(event)
        event_dict["remaining"] = remaining
        final_events.append(event_dict)

    return render_template("events/list.html", events=final_events)

# -----------------------------
# Yeni tədbir yarat
# -----------------------------
@bp.route("/create", methods=["GET","POST"])
def create_event():
    if not session.get('is_admin'):
        flash("Admin modu aktiv deyil.", "danger")
        return redirect(url_for("events.list_events"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        date = request.form.get("date", "").strip()
        location = request.form.get("location", "").strip()
        map_link = request.form.get("map_link", "").strip()
        description = request.form.get("description", "").strip()
        capacity = request.form.get("capacity", "").strip()
        category = request.form.get("category", "").strip()

        required_fields = [title, date, location, map_link, description, category]
        if any(not field for field in required_fields):
            error = "Bütün sahələr doldurulmalıdır."
            return render_template("events/create.html", error=error)

        try:
            capacity = int(capacity) if capacity else 100
        except ValueError:
            capacity = 100

        db = get_db()
        db.execute(
            """
            INSERT INTO events (title, date, location, map_link, description, capacity, category)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (title, date, location, map_link, description, capacity, category)
        )
        db.commit()

        flash("Tədbir uğurla yaradıldı!", "success")
        return redirect(url_for("events.list_events"))

    return render_template("events/create.html", error=None)

# -----------------------------
# Tədbir detallar və qeydiyyat
# -----------------------------
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

# -----------------------------
# Qeydiyyatları CSV-ə export
# -----------------------------
@bp.route("/<int:event_id>/export.csv")
def export_csv(event_id: int):
    db = get_db()
    event = db.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
    if not event:
        return render_template("404.html"), 404

    regs = db.execute("""
        SELECT name, email, created_at
        FROM event_registrations
        WHERE event_id = ?
        ORDER BY id ASC
    """, (event_id,)).fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["name", "email", "created_at"])
    for reg in regs:
        writer.writerow([reg["name"], reg["email"], reg["created_at"]])

    csv_filename = f"event_{event_id}_regs.csv"
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={csv_filename}"}
    )

# -----------------------------
# Tədbir silmək (admin session ilə)
# -----------------------------
@bp.route("/delete", methods=["POST"])
def delete_event():
    if not session.get('is_admin'):
        flash("Admin modu aktiv deyil.", "danger")
        return redirect(url_for("events.list_events"))

    event_id = request.form.get("event_id")
    if not event_id or not event_id.isdigit():
        flash("Yanlış tədbir ID.", "danger")
        return redirect(url_for("events.list_events"))

    db = get_db()
    db.execute("DELETE FROM event_registrations WHERE event_id = ?", (int(event_id),))
    db.execute("DELETE FROM events WHERE id = ?", (int(event_id),))
    db.commit()

    flash("Tədbir və bütün qeydiyyatlar uğurla silindi.", "success")
    return redirect(url_for("events.list_events"))

# -----------------------------
# Admin parol ilə session aktivləşdirmə
# -----------------------------
@bp.route("/admin_access", methods=["POST"])
def admin_access():
    password = request.form.get("password", "").strip()
    if password == ADMIN_PASS:
        session['is_admin'] = True
        flash("Admin modu aktiv edildi.", "success")
    else:
        session['is_admin'] = False
        flash("Səhv parol.", "danger")
    return redirect(url_for("events.list_events"))