import re

from flask import redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from app.blueprints.auth import bp
from app.db import create_user, get_portfolio, get_user_by_email, save_portfolio

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _anon_token():
    """The per-browser token used before logging in (same one the builder
    uses) — read-only here, never creates one, so visiting /login or /signup
    doesn't start tracking someone who was never in the builder."""
    return session.get("builder_token")


def _claim_anonymous_portfolio(user_id):
    """If this browser built a portfolio before creating an account, copy
    it over to the new account — so signing up doesn't lose their work."""
    anon_token = _anon_token()
    if not anon_token:
        return
    identity = f"user:{user_id}"
    if get_portfolio(identity) is not None:
        return  # they already have one on this account; don't overwrite it
    anon_data = get_portfolio(anon_token)
    if anon_data is not None:
        save_portfolio(identity, "ai-tech", anon_data)


@bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        error = None
        if not EMAIL_RE.match(email):
            error = "Enter a valid email address."
        elif len(password) < 8:
            error = "Password must be at least 8 characters."
        elif password != confirm:
            error = "Passwords don't match."
        elif get_user_by_email(email) is not None:
            error = "An account with that email already exists."

        if error:
            return render_template("auth/signup.html", error=error, email=email)

        anon_token = _anon_token()
        user_id = create_user(email, generate_password_hash(password))
        session.clear()
        session["user_id"] = user_id
        if anon_token:
            session["builder_token"] = anon_token
            _claim_anonymous_portfolio(user_id)
        return redirect(url_for("main.ai_tech_build"))

    return render_template("auth/signup.html", error=None, email="")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = get_user_by_email(email)

        if user is None or not check_password_hash(user["password_hash"], password):
            return render_template("auth/login.html", error="Incorrect email or password.", email=email)

        anon_token = _anon_token()
        session.clear()
        session["user_id"] = user["id"]
        if anon_token:
            session["builder_token"] = anon_token
            _claim_anonymous_portfolio(user["id"])
        return redirect(url_for("main.ai_tech_build"))

    return render_template("auth/login.html", error=None, email="")


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.home"))