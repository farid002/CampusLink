# -*- coding: utf-8 -*-
"""
polls.py — Sorğular modulu (SKELETON + TƏLİMAT)

Bu faylda funksiyalar qəsdən “boş” saxlanılıb ki, tələbələr özləri
implement etsinlər. Hər funksiya üçün docstring-də addım-addım nə etmək
lazım olduğu göstərilib.

Tövsiyə olunan şablonlar:
- templates/polls/list.html
- templates/polls/new.html
- templates/polls/detail.html
- templates/polls/toggle_info.html  (opsional, admin düyməsi/izah üçün)
"""

from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import get_db
import json, datetime, secrets

bp = Blueprint("polls", __name__, url_prefix="/polls")
ADMIN_PASS = "admin123"  # demo parol (yalnız dərs məqsədi üçün)


import secrets
from flask import session

@bp.before_app_request
def ensure_session():
    """
    Hər istifadəçi üçün sadə sessiya identifikatoru saxlamaq (demo).
    """
    # Sessiyanı qalıcı et (cookie brauzer bağlansa da qalsın)
    session.permanent = True

    # Əgər voter_id hələ yoxdursa → yarad
    if "voter_id" not in session:
        session["voter_id"] = secrets.token_hex(8)  # məsələn: 'a3f9c1e2...'
    return None


@bp.route("/")
def list_polls():
    """
    Bütün sorğuların siyahısı.

    Bu funksiya **tələbə tərəfindən implement olunmalıdır**:

      1) DB sorğusu:
         - `SELECT * FROM polls ORDER BY id DESC`
         - (İstəyə görə) `is_closed` sütununa görə qruplaşdırıb başlıqda “(bağlı)” kimi göstərmək.

      2) Şablon:
         - `polls/list.html` render et.
         - Şablona `polls` siyahısını ötür.
         - Hər sətirdə: sual, yaradılma tarixi, açıq/bağlı status badge, “Bax” linki.

      3) UX ipucları:
         - Yuxarıda “Yeni sorğu” (admin) linki.
         - Bağlı sorğular üçün `badge bg-secondary`, açıq üçün `badge bg-success`.

    Qeyd: Skeleton olaraq hazırda yalnız şablonu qaytarır.
    """
    db = get_db()
    polls = db.execute(
        "SELECT id, question, is_closed FROM polls ORDER BY id DESC"
    ).fetchall()

    return render_template("polls/list.html", polls=polls)


import datetime, json
from flask import request, render_template, redirect, url_for, flash, session

@bp.route("/new", methods=["GET","POST"], endpoint="new")
def new():
    """
    Yeni sorğu yaratmaq (admin demo).
    """
    if request.method == "POST":
        # 1) Form dəyərləri
        password = request.form.get("password", "").strip()
        question = request.form.get("question", "").strip()
        options_raw = request.form.get("options", "").strip()

        # 2) Admin parolunu yoxla
        if password != ADMIN_PASS:
            error = "Admin parolu səhvdir."
            return render_template("polls/new.html", error=error)

        # 3) Suallar və seçimlər
        if not question:
            error = "Sual boş ola bilməz."
            return render_template("polls/new.html", error=error)

        opts = [o.strip() for o in options_raw.splitlines() if o.strip()]
        if len(opts) < 2:
            error = "Ən azı 2 seçim yazılmalıdır."
            return render_template("polls/new.html", error=error)

        # 4) DB-yə əlavə et
        created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        db = get_db()
        db.execute(
            "INSERT INTO polls (question, options_json, is_closed, created_at) VALUES (?, ?, 0, ?)",
            (question, json.dumps(opts), created_at),
        )
        db.commit()

        flash("Yeni sorğu uğurla yaradıldı.")
        return redirect(url_for("polls.list_polls"))

    # GET metodu: formu göstər
    return render_template("polls/new.html", error=None)



@bp.route("/<int:poll_id>/toggle", methods=["POST"], endpoint="toggle")
def toggle(poll_id: int):
    """
    Sorğunu aç/bağla (admin demo).
    """
    db = get_db()

    # 1) Admin yoxlaması
    pwd = request.form.get("password", "").strip()
    if pwd != ADMIN_PASS:
        flash("Admin şifrəsi səhvdir.")
        return redirect(url_for("polls.detail", poll_id=poll_id))

    # 2) DB UPDATE — statusu çevirmək
    db.execute(
        "UPDATE polls SET is_closed = CASE is_closed WHEN 1 THEN 0 ELSE 1 END WHERE id=?",
        (poll_id,),
    )
    db.commit()

    flash("Sorğunun statusu dəyişdirildi.")
    # 3) Redirect geri detallara
    return redirect(url_for("polls.detail", poll_id=poll_id))



# polls.py (başda: import json, secrets OLUB; indi datetime da əlavə edirik)
import datetime

@bp.route("/<int:poll_id>", methods=["GET", "POST"], endpoint="detail")
def detail(poll_id: int):
    """
    Sorğu detalları: səsvermə (POST) və nəticələr (GET).
    """
    db = get_db()
    poll = db.execute("SELECT * FROM polls WHERE id=?", (poll_id,)).fetchone()
    if not poll:
        return render_template("404.html"), 404

    # Seçimləri yüklə
    options = json.loads(poll["options_json"])

    # --- POST: SƏSVERMƏ ---
    if request.method == "POST":
        # Bağlı sorğuda səs qəbul etmə
        if poll["is_closed"]:
            flash("Bu sorğu bağlıdır. Səs qəbul edilmir.")
            return redirect(url_for("polls.detail", poll_id=poll_id))

        # Eyni istifadəçinin təkrar səsi (demo sessiya əsaslı)
        if session.get(f"voted_{poll_id}"):
            flash("Artıq səs vermisiniz.")
            return redirect(url_for("polls.detail", poll_id=poll_id))

        # Göndərilən option_index-i oxu və doğrula
        try:
            idx = int(request.form.get("option_index", "-1"))
        except ValueError:
            idx = -1

        if 0 <= idx < len(options):
            created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            db.execute(
                "INSERT INTO poll_votes (poll_id, option_index, created_at) VALUES (?, ?, ?)",
                (poll_id, idx, created_at),
            )
            db.commit()
            session[f"voted_{poll_id}"] = True
            flash("Səsiniz qeydə alındı.")
            return redirect(url_for("polls.detail", poll_id=poll_id))
        else:
            flash("Seçim düzgün deyil.")
            return redirect(url_for("polls.detail", poll_id=poll_id))

    # --- GET: NƏTİCƏLƏR ---
    rows = db.execute(
        "SELECT option_index, COUNT(*) AS cnt FROM poll_votes WHERE poll_id=? GROUP BY option_index",
        (poll_id,),
    ).fetchall()

    # Sayımlar
    counts_map = {r["option_index"]: r["cnt"] for r in rows}
    counts = [counts_map.get(i, 0) for i in range(len(options))]
    total = sum(counts)

    # Faizlər
    percentages = []
    for i, opt in enumerate(options):
        c = counts[i]
        pct = (c / total * 100.0) if total > 0 else 0.0
        # Şablonda rahat istifadə üçün tuple şəklində:
        percentages.append((opt, c, round(pct, 1)))  # (ad, say, faiz%)

    return render_template(
        "polls/detail.html",
        poll=poll,
        options=options,
        percentages=percentages,
        total=total,
    )
