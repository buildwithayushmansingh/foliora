import json
import os
from datetime import date

from flask import (
    abort,
    current_app,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)

from app.data import FEATURED_PORTFOLIO, HOW_IT_WORKS, PROBLEMS, UPCOMING_DESIGNS
from app.blueprints.main import bp


TEMPLATE_REGISTRY = {
    "ai-tech": "ayushman.json",
}

HOME_FIELDS = ["name", "title", "tagline", "location", "status"]

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )
    )
)

PORTFOLIO_TEMPLATES_DIR = os.path.join(BASE_DIR, "portfolio_templates")
DEMO_DATA_DIR = os.path.join(BASE_DIR, "demo_data")


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

    if (
        portfolio.get("github", {}).get("activity_enabled")
        and portfolio.get("github", {}).get("username")
    ):
        sections.append(("github", "GitHub Activity"))

    if (
        any((portfolio.get("social_links") or {}).values())
        or portfolio.get("contact", {}).get("email")
        or portfolio.get("email")
    ):
        sections.append(("contact", "Contact"))

    return sections


def _load_demo_portfolio():
    with open(
        os.path.join(DEMO_DATA_DIR, "ayushman.json"),
        encoding="utf-8",
    ) as f:
        return json.load(f)


def _with_safe_defaults(portfolio):
    """
    Guarantees the optional nested keys the template reads with dot-chains
    always exist, so a partially-filled portfolio never crashes the page.
    """
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
    """
    Completely empty portfolio for a new user.
    This prevents demo/Ayushman data from being copied into a new portfolio.
    """
    return {
        "name": "",
        "username": "",
        "title": "",
        "tagline": "",
        "about": "",
        "location": "",
        "email": "",
        "status": "",
        "profile_image": "",
        "stats": [],
        "focus": [],
        "social_links": {},
        "skills": [],
        "projects": [],
        "certificates": [],
        "achievements": [],
        "github": {
            "username": "",
            "profile_url": "",
            "activity_enabled": False,
        },
        "contact": {
            "email": "",
            "message_enabled": False,
        },
        "resume_url": "",
    }


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


def _builder_base():
    """
    Decide what the builder should start with:

    1. Saved user portfolio -> continue editing it
    2. Blank mode -> completely empty portfolio
    3. Otherwise -> demo portfolio
    """
    if "ai_tech_portfolio" in session:
        return session["ai_tech_portfolio"]

    if session.get("ai_tech_blank"):
        return _blank_portfolio()

    return _load_demo_portfolio()


@bp.route("/portfolio-templates/<template_key>/<path:filename>")
def template_asset(template_key, filename):
    if template_key not in TEMPLATE_REGISTRY:
        abort(404)

    return send_from_directory(
        os.path.join(PORTFOLIO_TEMPLATES_DIR, template_key),
        filename,
    )


@bp.route("/templates/ai-tech/build", methods=["GET", "POST"])
def ai_tech_build():

    # "Build yours with this template" starts a completely fresh portfolio.
    if request.method == "GET" and request.args.get("fresh") == "1":
        session.pop("ai_tech_portfolio", None)
        session["ai_tech_blank"] = True

    base = _with_safe_defaults(_builder_base())

    if request.method == "POST":

        entered = {
            field: request.form.get(field, "").strip()
            for field in HOME_FIELDS
        }

        if not entered["name"] or not entered["title"]:
            return render_template(
                "build_ai_tech.html",
                values=entered,
                has_custom_data="ai_tech_portfolio" in session,
                error="Name and title are required.",
                showing_demo=False,
            )

        # Start from the correct base instead of the demo directly.
        merged = dict(base)
        merged.update(entered)

        # These will later be calculated from the user's actual
        # skills/projects/certificates.
        merged["focus"] = []

        total_skills = sum(
            len(group.get("items", []))
            for group in merged.get("skills", [])
        )

        merged["stats"] = [
            stat
            for stat in [
                {
                    "value": str(total_skills),
                    "counter": True,
                    "plus": False,
                    "label": "Skills",
                    "link": "skills",
                }
                if total_skills
                else None,

                {
                    "value": str(len(merged.get("projects", []))),
                    "counter": True,
                    "plus": False,
                    "label": "Projects built",
                    "link": "projects",
                }
                if merged.get("projects")
                else None,

                {
                    "value": str(len(merged.get("certificates", []))),
                    "counter": True,
                    "plus": False,
                    "label": "Certifications",
                    "link": "certificates",
                }
                if merged.get("certificates")
                else None,
            ]
            if stat
        ]

        session["ai_tech_portfolio"] = merged

        # Once the user has saved their portfolio,
        # it is no longer a blank-mode session.
        session.pop("ai_tech_blank", None)

        return redirect(url_for("main.ai_tech_demo"))

    values = {
        field: base.get(field, "")
        for field in HOME_FIELDS
    }

    return render_template(
        "build_ai_tech.html",
        values=values,
        has_custom_data="ai_tech_portfolio" in session,
        showing_demo=(
            "ai_tech_portfolio" not in session
            and not session.get("ai_tech_blank")
        ),
    )


@bp.route("/templates/ai-tech/reset")
def ai_tech_reset():
    session.pop("ai_tech_portfolio", None)
    session.pop("ai_tech_blank", None)

    return redirect(url_for("main.ai_tech_build"))


@bp.route("/templates/ai-tech/demo")
def ai_tech_demo():
    portfolio = session.get("ai_tech_portfolio")

    # If there is no custom/blank-built portfolio,
    # this route can still show the original demo.
    if portfolio is None:
        portfolio = _load_demo_portfolio()

    return render_portfolio("ai-tech", portfolio)


@bp.route("/")
def home():
    featured = dict(FEATURED_PORTFOLIO)

    featured["url"] = current_app.config["PORTFOLIO_URL"]
    featured["title"] = current_app.config["PORTFOLIO_TITLE"]

    shot = os.path.join(
        current_app.static_folder,
        "img",
        "portfolio-preview.png",
    )

    featured["image"] = (
        url_for(
            "static",
            filename="img/portfolio-preview.png",
        )
        if os.path.exists(shot)
        else None
    )

    return render_template(
        "index.html",
        featured=featured,
        steps=HOW_IT_WORKS,
        problems=PROBLEMS,
        upcoming=UPCOMING_DESIGNS,
    )
