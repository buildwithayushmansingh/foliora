"""Phase 3/4: permanent storage for portfolios and user accounts.

Uses Python's built-in sqlite3 (no new dependency to install). One row per
portfolio, keyed by an identity string — a random per-browser token before
login, or "user:<id>" once someone has an account (see
app.blueprints.main.routes._identity_key).

The whole portfolio is kept as one JSON blob per row. That's a deliberate
simplification — splitting skills/projects/certificates into their own
relational tables is worth doing once there's an admin view to justify it.
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
    """Creates the database file and tables if they don't exist yet, and
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
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        _ensure_publish_columns(db)
        _ensure_admin_column(db)
        db.commit()
        close_db()
    app.teardown_appcontext(close_db)


def _ensure_publish_columns(db):
    """Phase 5: adds the publish-related columns to an existing database
    without losing any data already in it — SQLite has no 'ADD COLUMN IF
    NOT EXISTS', so this checks first. Safe to run every startup."""
    existing = {row["name"] for row in db.execute("PRAGMA table_info(portfolios)")}
    if "slug" not in existing:
        db.execute("ALTER TABLE portfolios ADD COLUMN slug TEXT")
    if "is_published" not in existing:
        db.execute("ALTER TABLE portfolios ADD COLUMN is_published INTEGER NOT NULL DEFAULT 0")
    if "published_data" not in existing:
        db.execute("ALTER TABLE portfolios ADD COLUMN published_data TEXT")
    if "published_at" not in existing:
        db.execute("ALTER TABLE portfolios ADD COLUMN published_at TEXT")
    # SQLite ignores NULLs in a unique index, so unpublished/no-slug rows
    # never collide with each other — only real slugs have to be unique.
    db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_portfolios_slug ON portfolios(slug)")

def _ensure_admin_column(db):
    """Phase 8: marks one account as the admin. See routes.py's
    _sync_admin_flag — whoever logs in with config.ADMIN_EMAIL gets this
    flag set automatically, no manual DB edit required."""
    existing = {row["name"] for row in db.execute("PRAGMA table_info(users)")}
    if "is_admin" not in existing:
        db.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0")
def get_portfolio(token):
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


# --- Phase 5: publish, with a stable public URL ----------------------------

def get_portfolio_row(token):
    """The full row — needed for slug/publish status, not just the data."""
    row = get_db().execute("SELECT * FROM portfolios WHERE token = ?", (token,)).fetchone()
    return dict(row) if row else None


def is_slug_taken(slug, exclude_token=None):
    db = get_db()
    if exclude_token:
        row = db.execute(
            "SELECT token FROM portfolios WHERE slug = ? AND token != ?", (slug, exclude_token)
        ).fetchone()
    else:
        row = db.execute("SELECT token FROM portfolios WHERE slug = ?", (slug,)).fetchone()
    return row is not None


def publish_portfolio(token, slug, template_key, data):
    """Publishing takes a snapshot: the public page at /u/<slug> is served
    from published_data, not the live draft, so edits only show up once
    published again. The slug, once set, stays reserved for this portfolio
    even across an unpublish, so nobody else can grab it in the meantime."""
    now = datetime.now(timezone.utc).isoformat()
    db = get_db()
    db.execute("""
        UPDATE portfolios
        SET slug = ?, is_published = 1, published_data = ?, published_at = ?
        WHERE token = ?
    """, (slug, json.dumps(data), now, token))
    db.commit()


def unpublish_portfolio(token):
    db = get_db()
    db.execute("UPDATE portfolios SET is_published = 0 WHERE token = ?", (token,))
    db.commit()


def get_published_by_slug(slug):
    """Returns (template_key, data) for a live public page, or None if
    nothing is published at that URL (never published, or unpublished)."""
    row = get_db().execute(
        "SELECT template_key, published_data FROM portfolios WHERE slug = ? AND is_published = 1",
        (slug,),
    ).fetchone()
    if row is None:
        return None
    return row["template_key"], json.loads(row["published_data"])


# --- Phase 4: accounts ------------------------------------------------------

def create_user(email, password_hash):
    now = datetime.now(timezone.utc).isoformat()
    db = get_db()
    cur = db.execute(
        "INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)",
        (email, password_hash, now),
    )
    db.commit()
    return cur.lastrowid


def get_user_by_email(email):
    row = get_db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    return dict(row) if row else None


def get_user_by_id(user_id):
    row = get_db().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


def set_user_admin(user_id, is_admin):
    db = get_db()
    db.execute("UPDATE users SET is_admin = ? WHERE id = ?", (1 if is_admin else 0, user_id))
    db.commit()


# --- Phase 8: admin panel ---------------------------------------------------

def admin_counts():
    db = get_db()
    users = db.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"]
    portfolios = db.execute(
        "SELECT COUNT(*) AS n FROM portfolios WHERE token LIKE 'user:%'"
    ).fetchone()["n"]
    published = db.execute(
        "SELECT COUNT(*) AS n FROM portfolios WHERE token LIKE 'user:%' AND is_published = 1"
    ).fetchone()["n"]
    anonymous_drafts = db.execute(
        "SELECT COUNT(*) AS n FROM portfolios WHERE token NOT LIKE 'user:%'"
    ).fetchone()["n"]
    return {
        "users": users,
        "portfolios": portfolios,
        "published": published,
        "anonymous_drafts": anonymous_drafts,
    }


def admin_list_users():
    """Every account, with their portfolio's status if they have one —
    newest signups first."""
    rows = get_db().execute("""
        SELECT u.id, u.email, u.created_at, u.is_admin,
               p.is_published, p.slug, p.updated_at AS portfolio_updated_at
        FROM users u
        LEFT JOIN portfolios p ON p.token = 'user:' || u.id
        ORDER BY u.created_at DESC
    """).fetchall()
    return [dict(r) for r in rows]


def admin_delete_user(user_id):
    """Removes the account and whatever portfolio it owns. A user's
    anonymous (never-signed-up) drafts aren't touched by this."""
    db = get_db()
    db.execute("DELETE FROM portfolios WHERE token = ?", (f"user:{user_id}",))
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()