
# -*- coding: utf-8 -*-
"""
polls.py — Sorğular modulu (GENİŞLƏNDİRİLMİŞ).

Yeni imkanlar:
 - Yeni sorğu yaratmaq (admin demo)
 - Sorğunu bağlamaq/açmaq
 - Sessiya köməyi ilə təkrar səslərin qarşısını almağa cəhd
"""

from flask import Blueprint, render_template, request, redirect, url_for, session
from database import get_db
import json, datetime, secrets

bp = Blueprint("polls", __name__, url_prefix="/polls")
ADMIN_PASS = "admin123"

@bp.before_app_request
def ensure_session():
    """Hər kəs üçün sadə sessiya id-si (cookie) yaradır; real auth deyil, demo məqsədi ilə."""
    if "voter_id" not in session:
        session["voter_id"] = secrets.token_hex(8)

@bp.route("/")
def list_polls():
    """Sorğuları siyahıla (bağlı olanlar ayrıca göstərilə bilər)."""
    db = get_db()
    polls = db.execute("SELECT * FROM polls ORDER BY id DESC").fetchall()
    return render_template("polls/list.html", polls=polls)

@bp.route("/new", methods=["GET","POST"])
def new():
    """Yeni sorğu yarat (admin demo)."""
    if request.method == "POST":
        if (request.form.get("password") or "") != ADMIN_PASS:
            return render_template("polls/new.html", error="Admin parolu səhvdir.")
        question = (request.form.get("question") or "").strip()
        options_raw = (request.form.get("options") or "").strip()
        opts = [o.strip() for o in options_raw.splitlines() if o.strip()]
        if not question or len(opts) < 2:
            return render_template("polls/new.html", error="Sual və ən az 2 seçim lazımdır.")
        db = get_db()
        db.execute("INSERT INTO polls (question, options_json, created_at) VALUES (?, ?, ?)",
                   (question, json.dumps(opts), datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
        db.commit()
        return redirect(url_for("polls.list_polls"))
    return render_template("polls/new.html", error=None)

@bp.route("/<int:poll_id>/toggle")
def toggle(poll_id: int):
    """Sorğunu aç/bağla (admin demo)."""
    if request.args.get("password") != ADMIN_PASS:
        return "İcazə yoxdur.", 403
    db = get_db()
    db.execute("UPDATE polls SET is_closed = 1 - is_closed WHERE id=?", (poll_id,))
    db.commit()
    return redirect(url_for("polls.detail", poll_id=poll_id))

@bp.route("/<int:poll_id>", methods=["GET","POST"])
def detail(poll_id: int):
    """
    Sorğu detalları: səs vermə və nəticələr.
    Təkrar səsin qarşısı üçün çox sadə yanaşma:
      - Sessiyada `voted_<poll_id>` açarı saxlanılır.
    """
    db = get_db()
    poll = db.execute("SELECT * FROM polls WHERE id=?", (poll_id,)).fetchone()
    if not poll:
        return render_template("404.html"), 404
    options = json.loads(poll["options_json"])

    if request.method == "POST":
        if poll["is_closed"]:
            return redirect(url_for("polls.detail", poll_id=poll_id))
        if session.get(f"voted_{poll_id}"):
            return redirect(url_for("polls.detail", poll_id=poll_id))
        try:
            idx = int(request.form.get("option_index", "-1"))
        except ValueError:
            idx = -1
        if 0 <= idx < len(options):
            db.execute("INSERT INTO poll_votes (poll_id, option_index, created_at) VALUES (?, ?, ?)",
                       (poll_id, idx, datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
            db.commit()
            session[f"voted_{poll_id}"] = True
        return redirect(url_for("polls.detail", poll_id=poll_id))

    # Nəticələri hazırla
    votes = db.execute("SELECT option_index, COUNT(*) AS cnt FROM poll_votes WHERE poll_id=? GROUP BY option_index", (poll_id,)).fetchall()
    counts = {r["option_index"]: r["cnt"] for r in votes}
    total = sum(counts.values()) if counts else 0
    percentages = [(opt, (counts.get(i,0), (counts.get(i,0)/total*100) if total else 0.0)) for i,opt in enumerate(options)]
    return render_template("polls/detail.html", poll=poll, options=options, percentages=percentages, total=total)
