from flask import current_app, render_template

from app.data import FEATURED_PORTFOLIO, HOW_IT_WORKS, PROBLEMS, UPCOMING_DESIGNS
from app.blueprints.main import bp


@bp.route("/")
def home():
    featured = dict(FEATURED_PORTFOLIO)
    featured["url"] = current_app.config["PORTFOLIO_URL"]
    featured["title"] = current_app.config["PORTFOLIO_TITLE"]

    return render_template(
        "index.html",
        featured=featured,
        steps=HOW_IT_WORKS,
        problems=PROBLEMS,
        upcoming=UPCOMING_DESIGNS,
    )