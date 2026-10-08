import json
import os
import re
import secrets
import shutil
import uuid
from datetime import date

from flask import abort, current_app, redirect, render_template, request, send_from_directory, session, url_for

from app.db import delete_portfolio, get_portfolio, save_portfolio

from app.data import FEATURED_PORTFOLIO, HOW_IT_WORKS, PROBLEMS, UPCOMING_DESIGNS
from app.blueprints.main import bp

TEMPLATE_REGISTRY = {
    "ai-tech": "ayushman.json",
}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PORTFOLIO_TEMPLATES_DIR = os.path.join(BASE_DIR, "portfolio_templates")
DEMO_DATA_DIR = os.path.join(BASE_DIR, "demo_data")

# --- Phase 3/4: a persistent identity for "whose portfolio is this" -------
# Logged in (Phase 4): the account owns it — identity is "user:<id>", so it
# follows them to any browser. Not logged in: a per-browser token (Phase 3),
# good for exactly one browser, until they sign up and it gets claimed
# (see app.blueprints.auth._claim_anonymous_portfolio).
TOKEN_KEY = "builder_token"


def _identity_key():
    if session.get("user_id"):
        return f"user:{session['user_id']}"
    session.permanent = True
    if TOKEN_KEY not in session:
        session[TOKEN_KEY] = uuid.uuid4().hex
    return session[TOKEN_KEY]


# --- image uploads (profile photo, certificate images) -----------------------
UPLOAD_DIRNAME = "uploads"
ALLOWED_IMAGE_EXT = {"png", "jpg", "jpeg", "webp"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB per image


def _upload_dir():
    """Every visitor's uploads live in their own folder, named after their
    identity — so photos never collide, and survive across visits the same
    way their portfolio data now does. ':' isn't safe in folder names on
    every filesystem, so "user:5" becomes "user_5" on disk only."""
    token = _identity_key()
    folder_name = token.replace(":", "_")
    path = os.path.join(current_app.static_folder, UPLOAD_DIRNAME, folder_name)
    os.makedirs(path, exist_ok=True)
    return path, folder_name


def _save_uploaded_image(file_storage, prefix):
    """Saves an uploaded image if it's actually present and valid; returns
    the path (relative to /static) to store on the portfolio, or None."""
    if not file_storage or not file_storage.filename:
        return None
    filename = file_storage.filename
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_IMAGE_EXT:
        return None
    file_storage.stream.seek(0, os.SEEK_END)
    size = file_storage.stream.tell()
    file_storage.stream.seek(0)
    if size == 0 or size > MAX_IMAGE_BYTES:
        return None
    upload_path, upload_id = _upload_dir()
    fname = f"{prefix}-{secrets.token_hex(4)}.{ext}"
    file_storage.save(os.path.join(upload_path, fname))
    return f"{UPLOAD_DIRNAME}/{upload_id}/{fname}"


# --- repeatable form-row parsing (skills, projects, certificates) ------------


def _row_indices(form, field_prefix):
    """Finds every row index present for a repeatable field, e.g. fields
    named 'skill_category_3' -> 3. Order is preserved; gaps are fine, since
    rows are only ever appended or removed client-side, never renumbered."""
    pattern = re.compile(rf"^{re.escape(field_prefix)}_(\d+)$")
    found = {int(m.group(1)) for key in form for m in [pattern.match(key)] if m}
    return sorted(found)


def _parse_skills(form):
    groups = []
    for i in _row_indices(form, "skill_category"):
        category = form.get(f"skill_category_{i}", "").strip()
        items = [s.strip() for s in form.get(f"skill_items_{i}", "").split(",") if s.strip()]
        if category and items:
            groups.append({"category": category, "code": f"{len(groups) + 1:02d} // GROUP", "items": items})
    return groups


def _parse_projects(form):
    projects = []
    for i in _row_indices(form, "project_name"):
        name = form.get(f"project_name_{i}", "").strip()
        if not name:
            continue
        technologies = [t.strip() for t in form.get(f"project_tech_{i}", "").split(",") if t.strip()]
        projects.append({
            "name": name,
            "icon": form.get(f"project_icon_{i}", "").strip(),
            "description": form.get(f"project_desc_{i}", "").strip(),
            "technologies": technologies,
            "github_url": form.get(f"project_github_{i}", "").strip(),
            "live_url": form.get(f"project_live_{i}", "").strip(),
        })
    return projects


def _parse_certificates(form, files):
    certs = []
    for i in _row_indices(form, "cert_name"):
        name = form.get(f"cert_name_{i}", "").strip()
        if not name:
            continue
        uploaded = _save_uploaded_image(files.get(f"cert_image_{i}"), f"cert-{i}")
        image = uploaded or form.get(f"cert_existing_{i}", "").strip()
        if not image:
            continue  # a certificate with no image at all isn't shown
        tags = [t.strip() for t in form.get(f"cert_tags_{i}", "").split(",") if t.strip()]
        certs.append({
            "name": name,
            "issuer": form.get(f"cert_issuer_{i}", "").strip(),
            "detail": form.get(f"cert_detail_{i}", "").strip(),
            "tags": tags,
            "image": image,
            "url": "",
        })
    return certs


def _initials(name):
    parts = [p for p in name.split() if p]
    letters = "".join(p[0] for p in parts[:2])
    return letters.upper() or "?"


def _background_tags(portfolio):
    flat = []
    for group in portfolio.get("skills", []):
        for item in group.get("items", []):
            if item not in flat:
                flat.append(item)
    return flat or ["HTML", "CSS", "JS", "PYTHON", "GIT", "SQL"]


def _available_sections(portfolio):
    sections = []
    if portfolio.get("about"):
        sections.append(("about", "About"))
    if portfolio.get("skills"):
        sections.append(("skills", "Skills"))
    if portfolio.get("projects"):
        sections.append(("projects", "Projects"))
    if portfolio.get("certificates"):
        sections.append(("certificates", "Certificates"))
    if portfolio.get("name"):
        sections.append(("id-card", "Developer ID"))
    if portfolio.get("github", {}).get("activity_enabled") and portfolio.get("github", {}).get("username"):
        sections.append(("github", "GitHub Activity"))
    if any((portfolio.get("social_links") or {}).values()) or portfolio.get("contact", {}).get("email") or portfolio.get("email"):
        sections.append(("contact", "Contact"))
    return sections


def _load_demo_portfolio():
    with open(os.path.join(DEMO_DATA_DIR, "ayushman.json"), encoding="utf-8") as f:
        return json.load(f)


def _with_safe_defaults(portfolio):
    """Guarantees the optional nested keys the template reads with dot-chains
    (portfolio.social_links.github, portfolio.contact.email, ...) always
    exist, so a partially-filled portfolio never crashes the page."""
    safe = dict(portfolio)
    safe.setdefault("social_links", {})
    safe.setdefault("contact", {})
    safe.setdefault("github", {})
    safe.setdefault("stats", [])
    safe.setdefault("focus", [])
    safe.setdefault("skills", [])
    safe.setdefault("projects", [])
    safe.setdefault("certificates", [])
    safe.setdefault("achievements", [])
    return safe


def _blank_portfolio():
    """An empty portfolio, so someone building their own starts with none of
    the demo person's details."""
    return {
        "name": "", "username": "", "title": "", "tagline": "", "about": "",
        "location": "", "email": "", "status": "", "profile_image": "",
        "stats": [], "focus": [], "social_links": {}, "skills": [],
        "projects": [], "certificates": [], "achievements": [],
        "github": {"username": "", "profile_url": "", "activity_enabled": False},
        "contact": {"email": "", "message_enabled": False},
        "resume_url": "",
    }


def _builder_base(token):
    """What the builder form starts from: the person's saved data (from the
    database) if they have any, else a blank form if they chose 'start
    blank', else the demo."""
    saved = get_portfolio(token)
    if saved is not None:
        return saved
    if session.get("ai_tech_blank"):
        return _blank_portfolio()
    return _load_demo_portfolio()


def render_portfolio(template_key, portfolio):
    if template_key not in TEMPLATE_REGISTRY:
        abort(404)
    portfolio = _with_safe_defaults(portfolio)
    return render_template(
        f"{template_key}/template.html",
        portfolio=portfolio,
        bg_tags=_background_tags(portfolio),
        available_sections=_available_sections(portfolio),
        initials=_initials(portfolio.get("name", "?")),
        current_year=date.today().year,
    )


@bp.route("/portfolio-templates/<template_key>/<path:filename>")
def template_asset(template_key, filename):
    if template_key not in TEMPLATE_REGISTRY:
        abort(404)
    return send_from_directory(os.path.join(PORTFOLIO_TEMPLATES_DIR, template_key), filename)


@bp.route("/templates/ai-tech/build", methods=["GET", "POST"])
def ai_tech_build():
    """The full AI & Tech builder: home, about, skills, projects,
    certificates (with image upload), social links and contact — all in one
    form. Saved to the database (Phase 3), keyed by this visitor's session
    token; there's still no login, so a cleared cookie means a fresh start."""
    token = _identity_key()
    if request.method == "GET" and request.args.get("fresh") == "1":
        delete_portfolio(token)
        session["ai_tech_blank"] = True
    base = _with_safe_defaults(_builder_base(token))

    if request.method == "POST":
        form = request.form
        files = request.files

        merged = dict(base)
        merged["name"] = form.get("name", "").strip()
        merged["title"] = form.get("title", "").strip()
        merged["tagline"] = form.get("tagline", "").strip()
        merged["location"] = form.get("location", "").strip()
        merged["status"] = form.get("status", "").strip()
        merged["about"] = form.get("about", "").strip()

        profile_image = _save_uploaded_image(files.get("profile_image"), "profile")
        if profile_image:
            merged["profile_image"] = profile_image
        elif form.get("remove_profile_image") == "1":
            merged["profile_image"] = ""

        contact_email = form.get("email", "").strip()
        merged["email"] = contact_email
        merged["contact"] = {"email": contact_email, "message_enabled": bool(contact_email)}

        merged["social_links"] = {
            "github": form.get("social_github", "").strip(),
            "linkedin": form.get("social_linkedin", "").strip(),
            "twitter": form.get("social_twitter", "").strip(),
            "instagram": form.get("social_instagram", "").strip(),
            "website": form.get("social_website", "").strip(),
        }

        github_username = form.get("github_username", "").strip()
        merged["github"] = {
            "username": github_username,
            "profile_url": merged["social_links"]["github"] or (
                f"https://github.com/{github_username}" if github_username else ""
            ),
            "activity_enabled": bool(github_username),
        }

        merged["skills"] = _parse_skills(form)
        merged["projects"] = _parse_projects(form)
        merged["certificates"] = _parse_certificates(form, files)

        # "focus" (About panel) and the old hero stats are personal to the
        # original demo (GNIOT, 2nd year...) with no form field of their own
        # yet, so they'd otherwise keep showing on every portfolio. Clear
        # focus, and recompute stats from what was actually submitted.
        merged["focus"] = []
        total_skills = sum(len(g["items"]) for g in merged["skills"])
        merged["stats"] = [
            s for s in [
                {"value": str(total_skills), "counter": True, "plus": False, "label": "Skills", "link": "skills"} if total_skills else None,
                {"value": str(len(merged["projects"])), "counter": True, "plus": False, "label": "Projects built", "link": "projects"} if merged["projects"] else None,
                {"value": str(len(merged["certificates"])), "counter": True, "plus": False, "label": "Certifications", "link": "certificates"} if merged["certificates"] else None,
            ] if s
        ]

        if not merged["name"] or not merged["title"]:
            return render_template(
                "build_ai_tech.html",
                portfolio=merged,
                has_custom_data=get_portfolio(token) is not None,
                showing_demo=False,
                error="Name and title are required.",
            )

        save_portfolio(token, "ai-tech", merged)
        session.pop("ai_tech_blank", None)
        return redirect(url_for("main.ai_tech_demo"))

    return render_template(
        "build_ai_tech.html",
        portfolio=base,
        has_custom_data=get_portfolio(token) is not None,
        showing_demo=(get_portfolio(token) is None and not session.get("ai_tech_blank")),
    )


@bp.route("/templates/ai-tech/reset")
def ai_tech_reset():
    token = _identity_key()
    delete_portfolio(token)
    shutil.rmtree(os.path.join(current_app.static_folder, UPLOAD_DIRNAME, token.replace(":", "_")), ignore_errors=True)
    session.pop("ai_tech_blank", None)
    return redirect(url_for("main.ai_tech_build"))


@bp.route("/templates/ai-tech/demo")
def ai_tech_demo():
    token = _identity_key()
    portfolio = get_portfolio(token) or _load_demo_portfolio()
    return render_portfolio("ai-tech", portfolio)


@bp.route("/")
def home():
    featured = dict(FEATURED_PORTFOLIO)
    featured["url"] = current_app.config["PORTFOLIO_URL"]
    featured["title"] = current_app.config["PORTFOLIO_TITLE"]
    shot = os.path.join(current_app.static_folder, "img", "portfolio-preview.png")
    featured["image"] = url_for("static", filename="img/portfolio-preview.png") if os.path.exists(shot) else None
    return render_template(
        "index.html",
        featured=featured,
        steps=HOW_IT_WORKS,
        problems=PROBLEMS,
        upcoming=UPCOMING_DESIGNS,
    )