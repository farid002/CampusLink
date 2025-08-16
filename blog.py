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
from database import get_db, paginate_query
import datetime, re

bp = Blueprint("blog", __name__, url_prefix="/blog")

ADMIN_PASS = "admin123"  # demo

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
    Blog yazılarının siyahısını göstərən səhifə.

    Bu funksiya **student tərəfindən implement olunmalıdır**. Məqsəd:
      1. **Axtarış (q parametri):**
         - URL query parametri `q` varsa, `title` və `content` sahələrində LIKE ilə axtarış aparın.
         - Məsələn: `/blog/?q=python` yalnız başlığında və ya mətnində "python" olan yazıları göstərsin.

      2. **Teq filtr (tag parametri):**
         - URL query parametri `tag` varsa, `tags` sahəsində uyğun olan yazıları süzün.
         - Məsələn: `/blog/?tag=flask` yalnız `flask` teqi olan yazıları göstərsin.

      3. **Dərc statusu filtr (published parametri):**
         - `published=1` → yalnız dərc olunmuş yazılar
         - `published=0` → yalnız draft yazılar
         - Boş qoyulsa → hamısı göstərilsin.

      4. **Səhifələmə (page parametri):**
         - Hər səhifədə **5 yazı** göstərilməlidir.
         - `page` query parametri əsasında OFFSET hesablanmalıdır.
         - Default olaraq `page=1` (ilk səhifə).

      5. **SQL sorğusu:**
         - Dinamik WHERE şərtləri qurun (1=1 ilə başlayın).
         - Parametrləri `?` ilə bağlayın (SQL injection təhlükəsizliyi üçün).
         - Sıralama: `ORDER BY created_at DESC` (ən yeni yazılar üstdə).

      6. **Template render:**
         - `blog/list.html` şablonuna göndərin:
           - `posts`: tapılmış yazılar
           - `q`, `tag`, `published`, `page`: query parametrləri (geri göstərmək üçün)

    Qeyd: Hal-hazırda funksiya yalnız boş şablonu qaytarır.
    """

    return render_template("blog/list.html")

@bp.route("/<slug>")
def show_post(slug: str):
    """
    Verilmiş **unikal ad** (slug) əsasında blog yazısını göstərən səhifə.

    Bu funksiya **tələbə tərəfindən implement olunmalıdır**:
      1. **DB sorğusu:**
         - `slug` URL parametrini götürün.
         - `blog_posts` cədvəlində `slug` uyğun olan yazını axtarın.
         - Nümunə: `/blog/python-intro` → `slug="python-intro"` olan yazı tapılmalıdır.

      2. **Tapılmadıqda:**
         - Əgər yazı mövcud deyilsə, `404.html` şablonu render olunmalı və status kodu `404` qaytarılmalıdır.

      3. **Tapıldıqda:**
         - `blog/detail.html` şablonunu (HTML Səhifəsini) render edin.
         - Şablona `post` obyektini ötürün (`title`, `content`, `tags`, `created_at` və s.).

      4. **Əlavə:**
         - İmkan olsa, eyni teq-ə malik “oxşar yazılar” da göstərilə bilər.
         - “Bütün yazılara qayıt” linki əlavə edin.

    Qeyd: hazırda funksiya yalnız boş şablon qaytarır.
    """
    return render_template("blog/detail.html")

@bp.route("/<int:post_id>")
def show_post_by_id(post_id: int):
    """
    Verilmiş **ID** əsasında blog yazısını göstərən səhifə.

    Bu funksiya **tələbə tərəfindən implement olunmalıdır**:
      1. **DB sorğusu:**
         - `post_id` URL parametrini götürün.
         - `blog_posts` cədvəlində `id = post_id` olan yazını axtarın.
         - Nümunə: `/blog/5` → `id=5` olan yazı tapılmalıdır.

      2. **Tapılmadıqda:**
         - Əgər yazı mövcud deyilsə, `404.html` şablonu render olunmalı və status kodu `404` qaytarılmalıdır.

      3. **Tapıldıqda:**
         - `blog/detail.html` şablonunu render edin.
         - Şablona `post` obyektini ötürün (`title`, `content`, `tags`, `created_at` və s.).

      4. **Əlavə:**
         - Əvvəlki və növbəti postlara keçid (Previous/Next) əlavə edə bilərsiniz.
         - Əgər `is_published` sahəsi mövcuddursa, dərc olunmamış yazılara xüsusi xəbərdarlıq göstərin.

    Qeyd: hazırda funksiya yalnız boş şablon qaytarır.
    """
    return render_template("blog/detail.html")

@bp.route("/new", methods=["GET", "POST"])
def new_post():
    """
    Yeni blog yazısı yaratmaq üçün səhifə (GET formu göstərir, POST məlumatı qəbul edir).

    Bu funksiya **tələbə tərəfindən implement olunmalıdır**. Görüləcək işlər:

    1) GET sorğusu (formun göstərilməsi):
       - `blog/new.html` şablonunu render edin.
       - Form sahələri: `title` (məcburi), `content` (məcburi), `tags` (istəyə bağlı),
         `is_published` (checkbox: işarələnərsə 1, yoxdursa 0).
       - UI ipucu: `tags` sahəsində vergüllə ayrılmış teqlər yazıla bilər (məs., "flask,python").

    2) POST sorğusu (formun emalı və DB-yə yazma):
       - `request.form` vasitəsilə dəyərləri oxuyun:
         - `title` → `.strip()` edin; boşdursa, səhv mesajı verib form səhifəsinə geri yönləndirin.
         - `content` → `.strip()` edin; boşdursa, eyni qaydada geri göndərin.
         - `tags` → boş ola bilər (None və ya boş sətir kimi saxlanması normaldır).
         - `is_published` → checkbox işarələnibsə 1, işarələnməyibsə 0 alın.
       - **Validasiya**:
         - `title` və `content` *boş ola bilməz* — bu halda istifadəçiyə xəbərdarlıq göstərin
           (məsələn, `flash()` mesajı) və `url_for("blog.new_post")` ilə yenidən form səhifəsinə yönləndirin.
       - **slug**:
         - `title` əsasında URL-də istifadə üçün sadə `slug` yaradın:
           - Kiçik hərflər, boşluqları `-` ilə əvəzləmək, latın olmayan simvolları təmizləmək.
         - (İrəli səviyyə) Əgər bu `slug` artıq mövcuddursa, sonuna rəqəm əlavə edib unikal edin
           (məs., `python-intro-2`). Bu hissə *opsional tapşırıq* kimi verilə bilər.
       - **DB-yə yazma**:
         - `blog_posts` cədvəlinə sətir əlavə edin:
           - sahələr: `title`, `content`, `tags`, `created_at`, `is_published`, `slug`
           - `created_at` üçün `datetime.now().strftime("%Y-%m-%d %H:%M")` istifadə edə bilərsiniz.
         - SQL injection-dan qorunmaq üçün parametr bağlama (`?`) istifadə edin.
         - `commit()` etməyi unutmayın.

    3) Uğurlu əlavə etdikdən sonra:
       - İstifadəçini **blog siyahısı**na yönləndirin (məs., `redirect(url_for("blog.list_posts"))`).

    4) Şablon və UX ipucları:
       - `blog/new.html` daxilində:
         - Əgər geri qayıdış oldu (validation xətası), istifadəçinin əvvəl yazdığı dəyərləri input-lara geri qoyun.
         - `flash` mesajlarını `base.html` içində göstərmək üçün bootstrap `alert` istifadə edin.
         - `is_published` üçün checkbox (default: işarəli) məntiqlidir.

    5) Təhlükəsizlik/Keyfiyyət:
       - **Server-tərəfli** validasiya mütləqdir (təkcə HTML `required` yetərli deyil).
       - `SECRET_KEY` olmalıdır ki, `flash()` işləsin.
       - Müvəqqəti olaraq admin yoxlaması (parol və s.) əlavə etmək istəsəniz, bu ayrıca tapşırıq ola bilər.

    Qeyd: Hal-hazırda funksiya **yalnız boş form şablonunu qaytarır**; bütün emal məntiqi tələbə tərəfindən yazılmalıdır.
    """

    return render_template("blog/new.html")

@bp.route("/<int:post_id>/edit", methods=["GET", "POST"])
def edit(post_id: int):
    """
    Mövcud blog yazısını redaktə edən səhifə (GET formu göstərir, POST dəyişiklikləri DB-yə yazır).

    Bu funksiya **tələbə tərəfindən implement olunmalıdır**. Görüləcək işlər:

    1) **Admin icazəsi (sadə demo):**
       - URL query-dən `password` götürün: `request.args.get("password", "")`.
       - Parol yanlış olduqda form göstərməyin; `blog/edit.html`-i `error` mesajı ilə render edin.
       - *Qeyd:* Bu yalnız dərs üçün sadə yoxlamadır. Real layihədə proper auth istifadə olunmalıdır.

    2) **Mövcud postu DB-dən gətirmək (GET və POST üçün ortaq):**
       - `post_id` əsasında `blog_posts` cədvəlindən yazını seçin.
       - Tapılmasa → `404.html` render edin və 404 status kodu qaytarın.

    3) **GET sorğusu (formun ilkin doldurulması):**
       - `blog/edit.html` şablonuna `post` obyektini ötürün ki, input-ların `value`-ları mövcud dəyərlərlə dolsun:
         - `title`, `content`, `tags`, `is_published` (checkbox).
       - `error=None` verin (xəta yoxdursa).

    4) **POST sorğusu (forma emalı və DB-yə yazma):**
       - `request.form` ilə dəyərləri oxuyun, `.strip()` tətbiq edin:
         - `title` (məcburi), `content` (məcburi), `tags` (istəyə bağlı),
           `is_published` (checkbox → işarələnibsə `1`, yoxdursa `0`).
       - **Validasiya:**
         - `title` və `content` boş ola bilməz.
         - Xəta olduqda eyni `blog/edit.html` şablonunu *`post` üçün istifadəçinin FORM-dan gələn* dəyərlərlə render edin
           ki, yazılanlar itməsin; `error` mesajı göstərin.
       - **Yeniləmə sorğusu:**
         - Parametr bağlama ilə `UPDATE blog_posts SET title=?, content=?, tags=?, is_published=? WHERE id=?`.
         - `db.commit()` etməyi unutmayın.
       - Uğurlu olduqda:
         - Məsələn, `redirect(url_for("blog.detail", post_id=post_id))` ilə detala yönləndirin.

    5) **Şablon və UX ipucları (`blog/edit.html`):**
       - Input value-larını `post`-dan doldurun; POST xətasında `request.form` dəyərlərini geri yazın.
       - `is_published` üçün checkbox-u serverdən gələn dəyərlə `checked` edin.
       - Yuxarıda `flash` və ya `error` mesajlarını Bootstrap `alert` ilə göstərin.
       - “Geri” linki əlavə edin (məs., siyahıya və ya detala).

    6) **Təhlükəsizlik/Keyfiyyət:**
       - SQL injection-dan qorunmaq üçün həmişə `?` placeholder istifadə edin.
       - Sadə `password` query-demo sırf dərs üçündür; real auth sistemi əlavə etmək *stretch goal* ola bilər.
       - `SECRET_KEY` olmalıdır ki, `flash()` işləsin (əgər istifadə edəcəksinizsə).

    7) **Stretch goals (istəyə görə):**
       - `title` dəyişəndə `slug`-u da sinxron yeniləmək (əgər sxemdə var).
       - Redaktə tarixini (`updated_at`) saxlamaq.
       - Sadə “preview” rejimi: POST etmədən əvvəl şablonda görüntüləmə.

    Qeyd: Hal-hazırda funksiya **yalnız boş form şablonunu** qaytarır; bütün emal məntiqi tələbə tərəfindən yazılmalıdır.
    """
    return render_template("blog/edit.html")

@bp.route("/<int:post_id>/delete")
def delete(post_id: int):
    """
    Mövcud blog yazısını silmək üçün route.

    Bu funksiya **tələbə tərəfindən implement olunmalıdır**. Görüləcək işlər:

    1) **Admin icazəsi (sadə demo):**
       - URL query parametrlərindən `password` götürün: `request.args.get("password", "")`.
       - Əgər parol düzgün deyilsə (`!= ADMIN_PASS`):
         - HTTP 403 status qaytarın.
         - İstifadəçiyə “icazə yoxdur” tipli mesaj göstərin.
       - *Qeyd:* Bu sadəcə dərs məqsədi üçündür. Real sistemlərdə silmə əməliyyatı **POST/DELETE method** və
         **authentication** tələb edir. Bu mövzunu dərsdə təhlükəsizlik baxımından müzakirə edin.

    2) **Mövcud yazını DB-dən silmək:**
       - `post_id` əsasında `blog_posts` cədvəlindən müvafiq yazını silin.
       - Parametr bağlama (`?`) istifadə edin ki, SQL injection riski olmasın.
       - Silmə əməliyyatından sonra `db.commit()` edin.

    3) **Nəticə (redirect və ya mesaj):**
       - Ən sadə halda → `redirect(url_for("blog.list_posts"))` edərək istifadəçini blog siyahısına qaytarın.
       - Alternativ → xüsusi “yazı silindi” səhifəsi göstərin.

    4) **Stretch goals (opsional tapşırıqlar):**
       - Silmə əməliyyatı öncəsi “Əminsiniz?” təsdiq səhifəsi əlavə etmək.
       - “Soft delete” — yazını tam silmək yerinə `is_deleted=1` kimi flag əlavə etmək.
       - Audit log aparmaq (kim nə vaxt sildi).

    Qeyd: Hal-hazırda funksiya yalnız boş şablon qaytarır; tələbə öz məntiqini əlavə etməlidir.
    """
