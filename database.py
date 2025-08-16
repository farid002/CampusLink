
# -*- coding: utf-8 -*-
"""
database.py — SQLite bağlantısı, sxem yeniləmələri və demo məlumatların daxil edilməsi.

Bu fayl həmçinin *kiçik yardımçı funksiyalar* təqdim edir:
 - `paginate_query` — səhifələmə üçün limit/offset tənzimləyir
 - `dict_from_row` — sqlite3.Row -> dict çevrilməsi
"""

import os, sqlite3, datetime, json
from flask import g

DB_PATH = os.path.join(os.path.dirname(__file__), "campusconnect.db")

def get_db():
    """Flask `g` daxilində tək SQLite bağlantısı saxlayır və qaytarır."""
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

def dict_from_row(row):
    """sqlite3.Row obyektini adi lüğətə çevirir (şablonlarda rahat istifadə üçün)."""
    return {k: row[k] for k in row.keys()} if row else None

def paginate_query(base_sql: str, page: int, per_page: int):
    """
    Səhifələmə üçün LIMIT/OFFSET hesablayır və SQL-i genişləndirir.

    Parametrlər:
      - base_sql: 'SELECT ... FROM ... WHERE ... ORDER BY ...' tipli əsas sorğu
      - page: 1-dən başlayan səhifə nömrəsi
      - per_page: hər səhifədə neçə sətir

    Qayıdır: (sql_with_limit, limit, offset)
    """
    page = max(1, int(page or 1))
    per_page = max(1, min(100, int(per_page or 10)))
    offset = (page - 1) * per_page
    sql = f"{base_sql} LIMIT ? OFFSET ?"
    return sql, per_page, offset

def init_db(force: bool = False):
    """
    DB faylını yaradır və cədvəlləri qurur. Əgər `force=True` olarsa, DB silinib sıfırdan qurulur.
    İlk işə salınmada demo məlumatlar daxil edilir.
    """
    if os.path.exists(DB_PATH) and not force:
        return
    if force and os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.executescript(
        """
        PRAGMA foreign_keys = ON;

        -- Blog
        CREATE TABLE IF NOT EXISTS blog_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            tags TEXT,
            created_at TEXT NOT NULL,
            is_published INTEGER NOT NULL DEFAULT 1,
            slug TEXT UNIQUE
        );

        -- Events
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            location TEXT NOT NULL,
            description TEXT NOT NULL,
            capacity INTEGER NOT NULL DEFAULT 100
        );

        CREATE TABLE IF NOT EXISTS event_registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(event_id, email), -- eyni email-in eyni tədbirə iki dəfə yazılmasının qarşısını alır
            FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
        );

        -- Forum
        CREATE TABLE IF NOT EXISTS forum_topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            is_pinned INTEGER NOT NULL DEFAULT 0,
            likes INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS forum_replies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id INTEGER NOT NULL,
            author TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (topic_id) REFERENCES forum_topics(id) ON DELETE CASCADE
        );

        -- Gallery
        CREATE TABLE IF NOT EXISTS gallery_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            filename TEXT NOT NULL,
            uploader TEXT NOT NULL,
            created_at TEXT NOT NULL
        );

        -- Polls
        CREATE TABLE IF NOT EXISTS polls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            options_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            is_closed INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS poll_votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            poll_id INTEGER NOT NULL,
            option_index INTEGER NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (poll_id) REFERENCES polls(id) ON DELETE CASCADE
        );

        -- Feedback
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            category TEXT NOT NULL,
            message TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL
        );
        """
    )

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    # Seed Blog
    c.executemany(
        "INSERT INTO blog_posts (title, content, tags, created_at, is_published, slug) VALUES (?, ?, ?, ?, ?, ?)",
        [
            ("CampusLink-ə xoş gəldiniz", "Workshop-da birlikdə qurduğumuz icma platforması!", "intro,xəbər", now, 1, "xos-geldiniz"),
            ("3 saata necə qurduq", "Flask + SQLite + Jinja2 + komanda işi.", "flask,workshop", now, 1, "3-saata-nece"),
            ("Daxili işlər", "Bu yazı dərc olunmayıb (draft).", "draft", now, 0, "daxili-isler"),
        ],
    )

    # Seed Events
    c.executemany(
        "INSERT INTO events (title, date, location, description, capacity) VALUES (?, ?, ?, ?, ?)",
        [
            ("Python Study Jam", "2025-09-10 18:00", "A12 otağı", "Birlikdə Python məsələləri həll edirik.", 30),
            ("Data Viz Gecəsi", "2025-09-15 19:00", "Lab 3", "Dataseti gətir, birlikdə qrafiklər quraq.", 20),
        ],
    )

    # Seed Forum
    c.executemany(
        "INSERT INTO forum_topics (title, author, content, created_at, is_pinned, likes) VALUES (?, ?, ?, ?, ?, ?)",
        [
            ("Ən yaxşı Python fəndləri?", "Aysu", "Sevdiyiniz Python fəndlərini paylaşın!", now, 1, 5),
            ("Uygun büdcəli noutbuk?", "Murad", "Tələbə büdcəsi üçün seçim axtarıram.", now, 0, 2),
        ],
    )
    c.executemany(
        "INSERT INTO forum_replies (topic_id, author, content, created_at) VALUES (?, ?, ?, ?)",
        [
            (1, "Kamran", "List comprehension və f-strings çox işə yarayır ;)", now),
            (2, "Nərmin", "Ryzen 7 + 16GB RAM modellərinə baxın.", now),
        ],
    )

    # Seed Gallery
    c.executemany(
        "INSERT INTO gallery_images (title, filename, uploader, created_at) VALUES (?, ?, ?, ?)",
        [
            ("Workshop Komandası", "placeholder.jpg", "Admin", now),
            ("Kampus Günbatımı", "placeholder.jpg", "Admin", now),
        ],
    )

    # Seed Polls (open & closed)
    poll1 = json.dumps(["Tünd", "Açıq", "Auto"])
    poll2 = json.dumps(["Bəli", "Xeyr"])
    c.execute("INSERT INTO polls (question, options_json, created_at, is_closed) VALUES (?, ?, ?, ?)", ("CampusLink mövzusu?", poll1, now, 0))
    c.execute("INSERT INTO polls (question, options_json, created_at, is_closed) VALUES (?, ?, ?, ?)", ("Mentor sistemi istəyirsiniz?", poll2, now, 1))
    c.executemany("INSERT INTO poll_votes (poll_id, option_index, created_at) VALUES (?, ?, ?)", [(1,0,now),(1,0,now),(1,1,now),(1,2,now),(2,1,now)])

    # Seed Feedback
    c.executemany(
        "INSERT INTO feedback (name, email, category, message, status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        [
            ("Leyla", "leyla@example.com", "general", "Platforma çox xoşuma gəldi!", "pending", now),
            ("Turan", "turan@example.com", "bug", "Sorğu nəticə səhifəsi mobil görünüşdə pozulur.", "open", now),
        ],
    )

    conn.commit()
    conn.close()
