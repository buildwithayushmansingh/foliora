"""Phase 3: permanent storage for portfolios.

Uses Python's built-in sqlite3 (no new dependency to install). One row per
portfolio, keyed by a random token stored in the visitor's session cookie —
there's no login yet (that's Phase 4), so this is what "theirs" means for
now: whoever holds that browser's cookie.

The whole portfolio is kept as one JSON blob per row. That's a deliberate
simplification for this phase — splitting skills/projects/certificates into
their own relational tables is worth doing once real accounts and an admin
view exist to justify it (Phase 4/5), not before.
"""
import json
import os
import sqlite3
from datetime import datetime, timezone

from flask import current_app, g


def get_db():
    """One connection per request, reused if called again in the same
    request, closed automatically at the end of the request."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE_PATH"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app):
    """Creates the database file and table if they don't exist yet, and
    registers the connection to close cleanly after every request."""
    os.makedirs(os.path.dirname(app.config["DATABASE_PATH"]), exist_ok=True)
    with app.app_context():
        db = get_db()
        db.execute("""
            CREATE TABLE IF NOT EXISTS portfolios (
                token TEXT PRIMARY KEY,
                template_key TEXT NOT NULL,
                data TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        db.commit()
        close_db()
    app.teardown_appcontext(close_db)


def get_portfolio(token):
    """Returns the saved portfolio dict for this token, or None if this
    visitor has never saved one (they'll fall back to the demo)."""
    row = get_db().execute(
        "SELECT data FROM portfolios WHERE token = ?", (token,)
    ).fetchone()
    return json.loads(row["data"]) if row else None


def save_portfolio(token, template_key, data):
    now = datetime.now(timezone.utc).isoformat()
    db = get_db()
    db.execute("""
        INSERT INTO portfolios (token, template_key, data, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(token) DO UPDATE SET
            template_key = excluded.template_key,
            data = excluded.data,
            updated_at = excluded.updated_at
    """, (token, template_key, json.dumps(data), now, now))
    db.commit()


def delete_portfolio(token):
    db = get_db()
    db.execute("DELETE FROM portfolios WHERE token = ?", (token,))
    db.commit()