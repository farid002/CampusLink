from flask import Blueprint, render_template, request, redirect, url_for, Response, flash
from database import get_db
import datetime, csv, io

bp = Blueprint("feedback", __name__)
ADMIN_PASS = "admin123"  # demo parol


@bp.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        category = request.form.get("category", "general").strip() or "general"
        message = request.form.get("message", "").strip()

        if not name or not email or not message:
            return render_template("feedback/contact.html", error="Ad, e-poçt və mesaj mütləqdir.")

        db = get_db()
        created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        db.execute(
            "INSERT INTO feedback (name,email,category,message,status,created_at) VALUES (?,?,?,?,?,?)",
            (name,email,category,message,"pending",created_at)
        )
        db.commit()
        flash("Mesajınız uğurla göndərildi!", "success")
        return redirect(url_for("feedback.contact"))

    return render_template("feedback/contact.html")


@bp.route("/admin/feedback")
def admin_feedback():
    password = request.args.get("password","")
    if password != ADMIN_PASS:
        return render_template("feedback/admin_list.html", items=[], error="Görüntü üçün ?password=admin123 əlavə edin.")

    db = get_db()
    where = ["1=1"]
    params = []

    q = request.args.get("q","").strip()
    status = request.args.get("status","").strip()
    category = request.args.get("category","").strip()

    if q:
        where.append("(name LIKE ? OR email LIKE ? OR message LIKE ?)")
        params.extend([f"%{q}%", f"%{q}%", f"%{q}%"])
    if status:
        where.append("status = ?")
        params.append(status)
    if category:
        where.append("category LIKE ?")
        params.append(f"%{category}%")

    query = "SELECT * FROM feedback WHERE " + " AND ".join(where) + " ORDER BY id DESC"
    items = db.execute(query, params).fetchall()
    return render_template("feedback/admin_list.html", items=items, error=None)


@bp.route("/admin/feedback/<int:fb_id>/status", methods=["POST"])
def set_status(fb_id: int):
    password = request.form.get("password","")
    if password != ADMIN_PASS:
        return "İcazə yoxdur.", 403

    status = request.form.get("status","").strip()
    if status not in ["pending","open","handled"]:
        return "Yanlış status dəyəri.", 400

    db = get_db()
    db.execute("UPDATE feedback SET status=? WHERE id=?", (status, fb_id))
    db.commit()
    flash("Status uğurla dəyişdirildi!", "success")
    return redirect(url_for("feedback.admin_feedback", password=ADMIN_PASS))


@bp.route("/admin/feedback/export.csv")
def export_csv():
    password = request.args.get("password","")
    if password != ADMIN_PASS:
        return "İcazə yoxdur.", 403

    db = get_db()
    where = ["1=1"]
    params = []

    q = request.args.get("q","").strip()
    status = request.args.get("status","").strip()
    category = request.args.get("category","").strip()

    if q:
        where.append("(name LIKE ? OR email LIKE ? OR message LIKE ?)")
        params.extend([f"%{q}%", f"%{q}%", f"%{q}%"])
    if status:
        where.append("status = ?")
        params.append(status)
    if category:
        where.append("category LIKE ?")
        params.append(f"%{category}%")

    query = "SELECT name,email,category,message,status,created_at FROM feedback WHERE " + " AND ".join(where) + " ORDER BY id DESC"
    rows = db.execute(query, params).fetchall()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["name","email","category","message","status","created_at"])
    for r in rows:
        writer.writerow([r["name"], r["email"], r["category"], r["message"], r["status"], r["created_at"]])

    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=feedback_export.csv"})
