from functools import wraps

from flask import abort, redirect, render_template, session, url_for

from app.blueprints.admin import bp
from app.db import admin_counts, admin_delete_user, admin_list_users, get_user_by_id


def admin_required(view):
    """Not logged in -> straight to login. Logged in but not the admin ->
    404, same as a route that doesn't exist, rather than revealing that an
    admin panel is even here."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        user_id = session.get("user_id")
        if user_id is None:
            return redirect(url_for("auth.login"))
        user = get_user_by_id(user_id)
        if user is None or not user["is_admin"]:
            abort(404)
        return view(*args, **kwargs)
    return wrapped


@bp.route("/")
@admin_required
def dashboard():
    return render_template("admin/dashboard.html", counts=admin_counts(), users=admin_list_users())


@bp.route("/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def delete_user(user_id):
    if user_id != session.get("user_id"):
        admin_delete_user(user_id)
    return redirect(url_for("admin.dashboard"))