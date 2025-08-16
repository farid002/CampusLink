
# -*- coding: utf-8 -*-
"""
app.py — Genişləndirilmiş Flask tətbiqinin giriş nöqtəsi.

Bu fayl:
 - Flask tətbiqini yaradır və konfiqurasiya edir
 - Yükləmə qovluğunu təyin edir (qalereya üçün)
 - Məlumat bazasını ilkinləşdirir (cədvəllər + demo məlumat)
 - Bütün modulları (blueprint) qeydiyyatdan keçirir
 - Ana səhifəni təqdim edir
"""

import os
from flask import Flask, render_template
from database import init_db
from blog import bp as blog_bp
from events import bp as events_bp
from forum import bp as forum_bp
from gallery import bp as gallery_bp
from polls import bp as polls_bp
from feedback import bp as feedback_bp

def create_app():
    """Flask tətbiq obyektini yaradır və bütün blueprint-ləri qeydiyyatdan keçirir."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "dev-secret-change-me"
    app.config["UPLOAD_FOLDER"] = os.path.join(app.root_path, "static", "uploads")
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Məlumat bazasını qur
    init_db()

    # Modulları qoş
    app.register_blueprint(blog_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(forum_bp)
    app.register_blueprint(gallery_bp)
    app.register_blueprint(polls_bp)
    app.register_blueprint(feedback_bp)

    @app.route("/")
    def index():
        """
        Ana səhifə:
        - Layihənin qısa təqdimatı
        - Naviqasiya üçün başlanğıc
        """
        return render_template("index.html")

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
