"""
SQLite Database Manager with WAL mode.
Handles all database operations for looma backend.

Tables:
  - users              (core, joint ownership)
  - game_profiles      (Jason owns)
  - fleets             (Jason owns)
  - fleet_members      (Jason owns)
  - mission_completions(Jason owns)
  - enterprises        (szbenyx owns)
  - enterprise_users   (szbenyx owns)
  - candidates         (szbenyx owns)
  - invite_codes       (joint)
  - usage_logs         (joint)
"""
from __future__ import annotations
import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime


def _dt_now():
    """Helper for consistent datetime strings."""
    return datetime.now()


SCHEMA_SQL = """
-- ============================================
-- Core: users (joint ownership - dual review)
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id              TEXT PRIMARY KEY,          -- looma uuid4
    email           TEXT UNIQUE,               -- Web registration (nullable for miniprogram-only)
    password_hash   TEXT,                      -- bcrypt hash (nullable for miniprogram-only)
    wechat_openid   TEXT UNIQUE,               -- WeChat miniprogram login
    name            TEXT DEFAULT '',
    tier            TEXT DEFAULT 'free',       -- free | supporter | pro
    role            TEXT DEFAULT 'user',       -- user | admin
    is_early_adopter INTEGER DEFAULT 0,
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_wechat_openid ON users(wechat_openid);

-- ============================================
-- Game: game_profiles (Jason owns)
-- ============================================
CREATE TABLE IF NOT EXISTS game_profiles (
    id                  TEXT PRIMARY KEY,
    user_id             TEXT NOT NULL,
    personality_type    TEXT,                  -- MBTI or custom type
    personality_detail  TEXT,                  -- JSON blob with full analysis
    xp                  INTEGER DEFAULT 0,
    level               INTEGER DEFAULT 1,
    updated_at          TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(user_id)
);

CREATE INDEX IF NOT EXISTS idx_game_profiles_user ON game_profiles(user_id);

-- ============================================
-- Game: fleets (Jason owns)
-- ============================================
CREATE TABLE IF NOT EXISTS fleets (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    captain_id      TEXT NOT NULL,
    description     TEXT DEFAULT '',
    created_at      TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (captain_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS fleet_members (
    id          TEXT PRIMARY KEY,
    fleet_id    TEXT NOT NULL,
    user_id     TEXT NOT NULL,
    joined_at   TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (fleet_id) REFERENCES fleets(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(fleet_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_fleet_members_user ON fleet_members(user_id);

-- ============================================
-- Game: mission_completions (Jason owns)
-- ============================================
CREATE TABLE IF NOT EXISTS mission_completions (
    id          TEXT PRIMARY KEY,
    user_id     TEXT NOT NULL,
    mission_id  TEXT NOT NULL,
    xp_reward   INTEGER DEFAULT 0,
    completed_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(user_id, mission_id)
);

CREATE INDEX IF NOT EXISTS idx_missions_user ON mission_completions(user_id);

-- ============================================
-- Enterprise: enterprises (szbenyx owns)
-- ============================================
CREATE TABLE IF NOT EXISTS enterprises (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    domain          TEXT,                      -- e.g. "genz.ltd"
    plan            TEXT DEFAULT 'free',       -- free | pro | enterprise
    created_at      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS enterprise_users (
    id              TEXT PRIMARY KEY,
    enterprise_id   TEXT NOT NULL,
    user_id         TEXT NOT NULL,
    role            TEXT DEFAULT 'member',     -- member | admin
    created_at      TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (enterprise_id) REFERENCES enterprises(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(enterprise_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_enterprise_users_enterprise ON enterprise_users(enterprise_id);
CREATE INDEX IF NOT EXISTS idx_enterprise_users_user ON enterprise_users(user_id);

-- ============================================
-- Enterprise: candidates (szbenyx owns)
-- ============================================
CREATE TABLE IF NOT EXISTS candidates (
    id              TEXT PRIMARY KEY,
    enterprise_id   TEXT NOT NULL,
    user_id         TEXT,                      -- linked looma user (nullable)
    name            TEXT NOT NULL,
    email           TEXT,
    phone           TEXT,
    status          TEXT DEFAULT 'new',        -- new | contacted | interviewed | hired | rejected
    profile_data    TEXT,                      -- JSON blob (personality, skills, etc.)
    created_at      TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (enterprise_id) REFERENCES enterprises(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_candidates_enterprise ON candidates(enterprise_id);

-- ============================================
-- Growth: invite_codes (joint ownership)
-- ============================================
CREATE TABLE IF NOT EXISTS invite_codes (
    id              TEXT PRIMARY KEY,
    code            TEXT UNIQUE NOT NULL,
    created_by      TEXT,                      -- user_id of creator
    used_by         TEXT,                      -- user_id of user who used it
    tier_grant      TEXT DEFAULT 'free',       -- tier granted when code is used
    expires_at      TEXT,
    used_at         TEXT,
    created_at      TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (created_by) REFERENCES users(id),
    FOREIGN KEY (used_by) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_invite_codes_code ON invite_codes(code);

-- ============================================
-- Usage: usage_logs (joint)
-- ============================================
CREATE TABLE IF NOT EXISTS usage_logs (
    id              TEXT PRIMARY KEY,
    user_id         TEXT NOT NULL,
    endpoint        TEXT NOT NULL,
    tokens_used     INTEGER DEFAULT 0,
    created_at      TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_usage_logs_user_date ON usage_logs(user_id, created_at);

-- ============================================
-- Quota: quota_records (joint)
-- ============================================
CREATE TABLE IF NOT EXISTS quota_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL REFERENCES users(id),
    resource TEXT NOT NULL,
    date TEXT NOT NULL,
    used INTEGER DEFAULT 0,
    daily_limit INTEGER NOT NULL,
    UNIQUE(user_id, resource, date)
);

CREATE INDEX IF NOT EXISTS idx_quota_records_user ON quota_records(user_id, resource, date);

-- ============================================
-- Quota: boost_packs (joint)
-- ============================================
CREATE TABLE IF NOT EXISTS boost_packs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL REFERENCES users(id),
    pack_name TEXT NOT NULL DEFAULT '标准加量包',
    credits INTEGER NOT NULL,
    credits_used INTEGER DEFAULT 0,
    price_yuan INTEGER DEFAULT 29,
    purchased_at TEXT DEFAULT (datetime('now')),
    expires_at TEXT NOT NULL,
    status TEXT DEFAULT 'active'
);

CREATE INDEX IF NOT EXISTS idx_boost_packs_user ON boost_packs(user_id, status);
CREATE INDEX IF NOT EXISTS idx_boost_packs_expires ON boost_packs(expires_at);

-- ============================================
-- Quota: boost_consumptions (joint)
-- ============================================
CREATE TABLE IF NOT EXISTS boost_consumptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL REFERENCES users(id),
    boost_pack_id INTEGER NOT NULL REFERENCES boost_packs(id),
    resource TEXT NOT NULL,
    credits_consumed INTEGER DEFAULT 1,
    consumed_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_boost_consumptions_user ON boost_consumptions(user_id);

-- ============================================
-- Poetry: poems (Jason)
-- ============================================
CREATE TABLE IF NOT EXISTS poems (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    author TEXT NOT NULL DEFAULT '',
    dynasty TEXT NOT NULL DEFAULT '',
    theme TEXT NOT NULL DEFAULT '',
    content TEXT NOT NULL,
    tags TEXT DEFAULT '',              -- comma-separated tags for filtering
    source TEXT DEFAULT 'imported',    -- imported | manual
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(title, author)
);

CREATE INDEX IF NOT EXISTS idx_poems_dynasty ON poems(dynasty);
CREATE INDEX IF NOT EXISTS idx_poems_author ON poems(author);
CREATE INDEX IF NOT EXISTS idx_poems_theme ON poems(theme);
CREATE INDEX IF NOT EXISTS idx_poems_title ON poems(title);

-- ============================================
-- Knowledge: documents (szbenyx)
-- ============================================
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    file_path TEXT NOT NULL UNIQUE,
    doc_type TEXT NOT NULL,
    file_size INTEGER DEFAULT 0,
    metadata TEXT DEFAULT '{}',
    status TEXT DEFAULT 'pending',
    chunk_count INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    processed_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);

-- ============================================
-- Knowledge: chunks (szbenyx)
-- ============================================
CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    char_count INTEGER DEFAULT 0,
    metadata TEXT DEFAULT '{}',
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_chunks_document ON chunks(document_id);

-- ============================================
-- Knowledge: query_logs (joint — data flywheel)
-- ============================================
CREATE TABLE IF NOT EXISTS query_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_text TEXT NOT NULL,
    provider TEXT NOT NULL,
    response_time_ms REAL DEFAULT 0,
    chunk_count INTEGER DEFAULT 0,
    rating INTEGER DEFAULT NULL,
    intent_label TEXT DEFAULT NULL,
    user_id TEXT DEFAULT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_query_logs_time ON query_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_query_logs_user ON query_logs(user_id);

-- ============================================
-- Narrative: sessions (Jason — Phase 0 feedback)
-- ============================================
CREATE TABLE IF NOT EXISTS narrative_sessions (
    id              TEXT PRIMARY KEY,
    user_id         TEXT DEFAULT NULL,          -- nullable (guests can play)
    domain          TEXT NOT NULL,              -- which domain was chosen
    status          TEXT DEFAULT 'active',       -- active | completed | abandoned
    duration_seconds REAL DEFAULT 0,
    started_at      TEXT DEFAULT (datetime('now')),
    ended_at        TEXT DEFAULT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_narrative_sessions_user ON narrative_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_narrative_sessions_domain ON narrative_sessions(domain);

-- ============================================
-- Narrative: events (Jason — Phase 0 event log)
-- ============================================
CREATE TABLE IF NOT EXISTS narrative_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT NOT NULL,
    event_type      TEXT NOT NULL,              -- domain_enter | choice_made | convergence_reached | share_attempt | replay
    domain          TEXT DEFAULT NULL,
    choice          TEXT DEFAULT NULL,
    navigator_line  TEXT DEFAULT NULL,
    metadata_json   TEXT DEFAULT '{}',
    created_at      TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (session_id) REFERENCES narrative_sessions(id)
);

CREATE INDEX IF NOT EXISTS idx_narrative_events_session ON narrative_events(session_id);
CREATE INDEX IF NOT EXISTS idx_narrative_events_type ON narrative_events(event_type);

-- ============================================
-- Narrative: feedback (Jason — Phase 0 convergence feedback)
-- ============================================
CREATE TABLE IF NOT EXISTS narrative_feedback (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id      TEXT NOT NULL,
    resonated       INTEGER NOT NULL DEFAULT 0, -- 0/1: did Navigator touch you?
    navigator_quote TEXT DEFAULT NULL,           -- recalled Navigator line
    would_replay    INTEGER DEFAULT NULL,        -- 0/1/2 (no/maybe/yes)
    shared          INTEGER NOT NULL DEFAULT 0, -- 0/1
    share_channel   TEXT DEFAULT NULL,           -- wechat | moments | link | other
    open_feedback   TEXT DEFAULT NULL,           -- free-text qualitative
    created_at      TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (session_id) REFERENCES narrative_sessions(id),
    UNIQUE(session_id)
);

CREATE INDEX IF NOT EXISTS idx_narrative_feedback_session ON narrative_feedback(session_id);

-- ============================================
-- Domain Engine: value imprints (Jason — GDD §3.2)
-- ============================================
CREATE TABLE IF NOT EXISTS value_imprints (
    user_id         TEXT NOT NULL,
    survival        INTEGER NOT NULL DEFAULT 0,
    freedom         INTEGER NOT NULL DEFAULT 0,
    belonging       INTEGER NOT NULL DEFAULT 0,
    updated_at      TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (user_id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- ============================================
-- Navigator Memory: memory entries (Jason — GDD §3.4)
-- ============================================
CREATE TABLE IF NOT EXISTS navigator_memories (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         TEXT NOT NULL,
    memory_level    TEXT NOT NULL,              -- surface | deep | fragment | taboo
    content         TEXT NOT NULL,
    context         TEXT DEFAULT NULL,
    domain          TEXT DEFAULT NULL,
    choice          TEXT DEFAULT NULL,
    importance      REAL DEFAULT 1.0,
    referenced_count INTEGER DEFAULT 0,
    session_id      TEXT DEFAULT NULL,
    created_at      TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_navigator_memories_user ON navigator_memories(user_id);
CREATE INDEX IF NOT EXISTS idx_navigator_memories_level ON navigator_memories(memory_level);

-- ============================================
-- Domain Engine: emergent strategy log (Jason — GDD §7.3)
-- ============================================
CREATE TABLE IF NOT EXISTS emergent_strategy_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         TEXT NOT NULL,
    strategy_type   TEXT NOT NULL,              -- poetry_refuge | trust_farming | unknown_speedrun | mbti_rejector | cross_domain_hacker
    triggered_at    TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_emergent_strategy_user ON emergent_strategy_log(user_id);

-- ============================================
-- Domain Engine: domain visit log (Jason)
-- ============================================
CREATE TABLE IF NOT EXISTS domain_visits (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         TEXT NOT NULL,
    session_id      TEXT NOT NULL,
    domain          TEXT NOT NULL,
    previous_domain TEXT DEFAULT NULL,
    interaction_level TEXT DEFAULT NULL,        -- intended | acceptable | forbidden
    echo_triggered  INTEGER NOT NULL DEFAULT 0, -- 0/1
    entered_at      TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (session_id) REFERENCES narrative_sessions(id)
);

CREATE INDEX IF NOT EXISTS idx_domain_visits_user ON domain_visits(user_id);
CREATE INDEX IF NOT EXISTS idx_domain_visits_session ON domain_visits(session_id);

-- ============================================
-- Narrative: Act 1 state persistence
-- ============================================
CREATE TABLE IF NOT EXISTS act1_sessions (
    session_id      TEXT PRIMARY KEY,
    state_json      TEXT NOT NULL,
    updated_at      TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (session_id) REFERENCES narrative_sessions(id)
);
"""


# ============================================
# Beta seed data
# ============================================
BETA_USERS = [
    {"name": "测试用户-免费版",   "email": "beta_free@looma.test",       "tier": "free",       "is_early_adopter": 1},
    {"name": "测试用户-支持者",   "email": "beta_supporter@looma.test",  "tier": "supporter",  "is_early_adopter": 1},
    {"name": "测试用户-专业版",   "email": "beta_pro@looma.test",        "tier": "pro",        "is_early_adopter": 1},
    {"name": "测试用户-管理员",   "email": "beta_admin@looma.test",      "tier": "pro",        "is_early_adopter": 1, "role": "admin"},
]


class DatabaseManager:
    """Thread-safe SQLite manager with WAL mode.

    For in-memory databases (testing), uses URI format with cache=shared
    so that all connections share the same in-memory DB.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._is_memory = db_path == ":memory:"
        if not self._is_memory:
            os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)

    def _connect(self):
        """Create a new SQLite connection."""
        if self._is_memory:
            # Use URI format to share in-memory DB across connections
            conn = sqlite3.connect(
                "file:memdb1?mode=memory&cache=shared",
                uri=True,
            )
        else:
            conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        if not self._is_memory:
            conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    @contextmanager
    def get_conn(self):
        """Get a SQLite connection with WAL mode enabled."""
        conn = self._connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_schema(self):
        """Initialize all tables. Safe to call on every startup."""
        with self.get_conn() as conn:
            conn.executescript(SCHEMA_SQL)

    # ============================================
    # User operations (joint)
    # ============================================
    def create_user(self, email=None, password_hash=None, wechat_openid=None, name=""):
        """Create a new user. email and wechat_openid are both nullable."""
        user_id = str(uuid.uuid4())
        with self.get_conn() as conn:
            conn.execute(
                """INSERT INTO users (id, email, password_hash, wechat_openid, name)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, email, password_hash, wechat_openid, name)
            )
        return user_id

    def get_user_by_email(self, email: str):
        with self.get_conn() as conn:
            row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        return dict(row) if row else None

    def get_user_by_openid(self, openid: str):
        with self.get_conn() as conn:
            row = conn.execute("SELECT * FROM users WHERE wechat_openid = ?", (openid,)).fetchone()
        return dict(row) if row else None

    def get_user_by_id(self, user_id: str):
        with self.get_conn() as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None

    def bind_wechat_to_user(self, user_id: str, wechat_openid: str):
        """Bind a WeChat openid to an existing user (cross-platform account linking)."""
        with self.get_conn() as conn:
            conn.execute(
                "UPDATE users SET wechat_openid = ?, updated_at = datetime('now') WHERE id = ?",
                (wechat_openid, user_id)
            )

    def update_user_tier(self, user_id: str, tier: str):
        with self.get_conn() as conn:
            conn.execute(
                "UPDATE users SET tier = ?, updated_at = datetime('now') WHERE id = ?",
                (tier, user_id)
            )

    # ============================================
    # Usage tracking (joint)
    # ============================================
    def log_usage(self, user_id: str, endpoint: str, tokens_used: int = 0):
        with self.get_conn() as conn:
            conn.execute(
                """INSERT INTO usage_logs (id, user_id, endpoint, tokens_used)
                   VALUES (?, ?, ?, ?)""",
                (str(uuid.uuid4()), user_id, endpoint, tokens_used)
            )

    def get_daily_usage_count(self, user_id: str) -> int:
        with self.get_conn() as conn:
            row = conn.execute(
                """SELECT COUNT(*) as cnt FROM usage_logs
                   WHERE user_id = ? AND date(created_at) = date('now')""",
                (user_id,)
            ).fetchone()
        return row["cnt"] if row else 0

    # ============================================
    # Game profile operations (Jason)
    # ============================================
    def upsert_game_profile(self, user_id: str, personality_type: str, personality_detail: str = ""):
        with self.get_conn() as conn:
            conn.execute(
                """INSERT INTO game_profiles (id, user_id, personality_type, personality_detail)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(user_id) DO UPDATE SET
                     personality_type = excluded.personality_type,
                     personality_detail = excluded.personality_detail,
                     updated_at = datetime('now')""",
                (str(uuid.uuid4()), user_id, personality_type, personality_detail)
            )

    def get_game_profile(self, user_id: str):
        with self.get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM game_profiles WHERE user_id = ?", (user_id,)
            ).fetchone()
        return dict(row) if row else None

    def add_xp(self, user_id: str, xp_amount: int):
        with self.get_conn() as conn:
            conn.execute(
                """UPDATE game_profiles SET xp = xp + ?, updated_at = datetime('now')
                   WHERE user_id = ?""",
                (xp_amount, user_id)
            )

    def update_level(self, user_id: str, level: int):
        """Update the user's game level."""
        with self.get_conn() as conn:
            conn.execute(
                """UPDATE game_profiles SET level = ?, updated_at = datetime('now')
                   WHERE user_id = ?""",
                (level, user_id)
            )

    # ============================================
    # Fleet operations (Jason)
    # ============================================
    def create_fleet(self, captain_id: str, name: str, description: str = ""):
        """Create a new fleet. Captain is auto-added as first member."""
        fleet_id = str(uuid.uuid4())
        member_id = str(uuid.uuid4())
        with self.get_conn() as conn:
            conn.execute(
                """INSERT INTO fleets (id, name, captain_id, description)
                   VALUES (?, ?, ?, ?)""",
                (fleet_id, name, captain_id, description)
            )
            conn.execute(
                """INSERT INTO fleet_members (id, fleet_id, user_id)
                   VALUES (?, ?, ?)""",
                (member_id, fleet_id, captain_id)
            )
        return fleet_id

    def get_fleet_by_id(self, fleet_id: str):
        """Get fleet details by ID."""
        with self.get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM fleets WHERE id = ?", (fleet_id,)
            ).fetchone()
        return dict(row) if row else None

    def get_user_fleet(self, user_id: str):
        """Get the fleet the user belongs to (one fleet per user in MVP)."""
        with self.get_conn() as conn:
            row = conn.execute(
                """SELECT f.* FROM fleets f
                   JOIN fleet_members fm ON f.id = fm.fleet_id
                   WHERE fm.user_id = ?""",
                (user_id,)
            ).fetchone()
        return dict(row) if row else None

    def get_fleet_members(self, fleet_id: str):
        """Get all members of a fleet."""
        with self.get_conn() as conn:
            rows = conn.execute(
                """SELECT fm.id, fm.fleet_id, fm.user_id, fm.joined_at,
                          u.name, u.email
                   FROM fleet_members fm
                   JOIN users u ON fm.user_id = u.id
                   WHERE fm.fleet_id = ?""",
                (fleet_id,)
            ).fetchall()
        return [dict(r) for r in rows]

    def join_fleet(self, fleet_id: str, user_id: str):
        """Add a user to a fleet. Raises if fleet doesn't exist or user already in one."""
        member_id = str(uuid.uuid4())
        with self.get_conn() as conn:
            # Verify fleet exists
            fleet = conn.execute(
                "SELECT id FROM fleets WHERE id = ?", (fleet_id,)
            ).fetchone()
            if not fleet:
                raise ValueError(f"Fleet {fleet_id} does not exist")

            # Check user not already in a fleet (MVP: one fleet per user)
            existing = conn.execute(
                """SELECT fm.fleet_id FROM fleet_members fm
                   WHERE fm.user_id = ?""",
                (user_id,)
            ).fetchone()
            if existing:
                raise ValueError(
                    f"User {user_id} already in fleet {existing['fleet_id']}"
                )

            conn.execute(
                """INSERT INTO fleet_members (id, fleet_id, user_id)
                   VALUES (?, ?, ?)""",
                (member_id, fleet_id, user_id)
            )

    def leave_fleet(self, user_id: str):
        """Remove a user from their fleet. Captain cannot leave (must dissolve)."""
        with self.get_conn() as conn:
            # Find user's current fleet
            membership = conn.execute(
                """SELECT fm.fleet_id, fm.user_id FROM fleet_members fm
                   WHERE fm.user_id = ?""",
                (user_id,)
            ).fetchone()
            if not membership:
                return  # User not in any fleet, nothing to do

            fleet_id = membership["fleet_id"]

            # Check if user is captain — captain cannot leave, must dissolve
            fleet = conn.execute(
                "SELECT captain_id FROM fleets WHERE id = ?", (fleet_id,)
            ).fetchone()
            if fleet and fleet["captain_id"] == user_id:
                raise ValueError("Captain cannot leave fleet; dissolve the fleet instead")

            conn.execute(
                "DELETE FROM fleet_members WHERE user_id = ? AND fleet_id = ?",
                (user_id, fleet_id)
            )

    def dissolve_fleet(self, fleet_id: str, captain_id: str):
        """Dissolve a fleet. Only the captain can dissolve. Removes all members."""
        with self.get_conn() as conn:
            fleet = conn.execute(
                "SELECT * FROM fleets WHERE id = ?", (fleet_id,)
            ).fetchone()
            if not fleet:
                raise ValueError(f"Fleet {fleet_id} does not exist")
            if fleet["captain_id"] != captain_id:
                raise ValueError("Only the captain can dissolve the fleet")

            conn.execute(
                "DELETE FROM fleet_members WHERE fleet_id = ?", (fleet_id,)
            )
            conn.execute(
                "DELETE FROM fleets WHERE id = ?", (fleet_id,)
            )

    def get_fleet_member_count(self, fleet_id: str) -> int:
        """Get number of members in a fleet."""
        with self.get_conn() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM fleet_members WHERE fleet_id = ?",
                (fleet_id,)
            ).fetchone()
        return row["cnt"] if row else 0

    # ============================================
    # Mission operations (Jason)
    # ============================================
    def complete_mission(self, user_id: str, mission_id: str, xp_reward: int = 0):
        """Record a mission completion. Returns (completion_id, was_new).
        If user already completed this mission, returns (None, False) — no double reward."""
        completion_id = str(uuid.uuid4())
        with self.get_conn() as conn:
            try:
                conn.execute(
                    """INSERT INTO mission_completions (id, user_id, mission_id, xp_reward)
                       VALUES (?, ?, ?, ?)""",
                    (completion_id, user_id, mission_id, xp_reward)
                )
            except sqlite3.IntegrityError:
                # UNIQUE(user_id, mission_id) — already completed
                return None, False

            # Award XP to game profile
            if xp_reward > 0:
                conn.execute(
                    """UPDATE game_profiles SET xp = xp + ?, updated_at = datetime('now')
                       WHERE user_id = ?""",
                    (xp_reward, user_id)
                )

        return completion_id, True

    def get_user_missions(self, user_id: str):
        """Get all missions completed by a user."""
        with self.get_conn() as conn:
            rows = conn.execute(
                """SELECT mc.id, mc.mission_id, mc.xp_reward, mc.completed_at
                   FROM mission_completions mc
                   WHERE mc.user_id = ?
                   ORDER BY mc.completed_at DESC""",
                (user_id,)
            ).fetchall()
        return [dict(r) for r in rows]

    def is_mission_completed(self, user_id: str, mission_id: str) -> bool:
        """Check if a user has already completed a specific mission."""
        with self.get_conn() as conn:
            row = conn.execute(
                """SELECT id FROM mission_completions
                   WHERE user_id = ? AND mission_id = ?""",
                (user_id, mission_id)
            ).fetchone()
        return row is not None

    # ============================================
    # Quota operations (joint)
    # ============================================
    def get_quota(self, user_id: str, resource: str, date: str):
        """Get quota record for a specific user + resource + date."""
        with self.get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM quota_records WHERE user_id=? AND resource=? AND date=?",
                (user_id, resource, date),
            ).fetchone()
        return dict(row) if row else None

    def consume_quota(self, user_id: str, resource: str, date: str, limit: int) -> bool:
        """Consume 1 quota unit. Returns True=success, False=exceeded."""
        with self.get_conn() as conn:
            existing = conn.execute(
                "SELECT used FROM quota_records WHERE user_id=? AND resource=? AND date=?",
                (user_id, resource, date),
            ).fetchone()
            if existing:
                used = existing[0]
                if used >= limit:
                    return False
                conn.execute(
                    "UPDATE quota_records SET used=used+1 WHERE user_id=? AND resource=? AND date=?",
                    (user_id, resource, date),
                )
            else:
                conn.execute(
                    "INSERT INTO quota_records (user_id, resource, date, used, daily_limit) VALUES (?, ?, ?, 1, ?)",
                    (user_id, resource, date, limit),
                )
        return True

    # ============================================
    # Boost pack operations (joint)
    # ============================================
    def create_boost_pack(self, user_id: str, pack_name: str, credits: int,
                          price_yuan: int = 29, days_valid: int = 30) -> int:
        """Create a boost pack for a user."""
        from datetime import timedelta
        now = _dt_now()
        expires = (now + timedelta(days=days_valid)).isoformat()
        with self.get_conn() as conn:
            cursor = conn.execute(
                """INSERT INTO boost_packs (user_id, pack_name, credits, credits_used, price_yuan, purchased_at, expires_at, status)
                   VALUES (?, ?, ?, 0, ?, ?, ?, 'active')""",
                (user_id, pack_name, credits, price_yuan, now.isoformat(), expires),
            )
        return cursor.lastrowid or 0

    def get_boost_credit_remaining(self, user_id: str) -> int:
        """Get total remaining boost credits for a user."""
        with self.get_conn() as conn:
            row = conn.execute(
                """SELECT COALESCE(SUM(credits - credits_used), 0) AS remaining
                   FROM boost_packs
                   WHERE user_id=? AND status='active'
                     AND expires_at > datetime('now')""",
                (user_id,),
            ).fetchone()
        return row[0] if row else 0

    def consume_boost_credit(self, user_id: str, resource: str) -> bool:
        """Consume 1 boost credit from the earliest-expiring active pack."""
        with self.get_conn() as conn:
            pack = conn.execute(
                """SELECT * FROM boost_packs
                   WHERE user_id=? AND status='active'
                     AND expires_at > datetime('now')
                     AND credits_used < credits
                   ORDER BY expires_at ASC LIMIT 1""",
                (user_id,),
            ).fetchone()

            if not pack:
                return False

            pack_dict = dict(pack)
            pack_id = pack_dict["id"]

            conn.execute(
                "UPDATE boost_packs SET credits_used=credits_used+1 WHERE id=?",
                (pack_id,),
            )
            conn.execute(
                "INSERT INTO boost_consumptions (user_id, boost_pack_id, resource, credits_consumed) VALUES (?, ?, ?, 1)",
                (user_id, pack_id, resource),
            )
            if pack_dict["credits_used"] + 1 >= pack_dict["credits"]:
                conn.execute("UPDATE boost_packs SET status='exhausted' WHERE id=?", (pack_id,))
        return True

    # ============================================
    # Poetry operations (Jason)
    # ============================================
    def insert_poem(self, title: str, author: str = "", dynasty: str = "",
                    theme: str = "", content: str = "", tags: str = "",
                    source: str = "imported") -> int:
        """Insert a single poem. Returns the row id."""
        with self.get_conn() as conn:
            cursor = conn.execute(
                """INSERT OR IGNORE INTO poems (title, author, dynasty, theme, content, tags, source)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (title, author, dynasty, theme, content, tags, source)
            )
        return cursor.lastrowid or 0

    def bulk_insert_poems(self, poems: list[dict]) -> int:
        """Bulk insert poems from a list of dicts.
        Each dict must have: title, content. Optional: author, dynasty, theme, tags.
        Returns count of inserted rows."""
        inserted = 0
        with self.get_conn() as conn:
            for p in poems:
                try:
                    conn.execute(
                        """INSERT OR IGNORE INTO poems (title, author, dynasty, theme, content, tags, source)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (p.get("title", ""), p.get("author", ""), p.get("dynasty", ""),
                         p.get("theme", ""), p.get("content", ""), p.get("tags", ""),
                         p.get("source", "imported"))
                    )
                    inserted += 1
                except sqlite3.IntegrityError:
                    pass  # duplicate title, skip
        return inserted

    def get_poem_by_id(self, poem_id: int):
        """Get a single poem by id."""
        with self.get_conn() as conn:
            row = conn.execute("SELECT * FROM poems WHERE id = ?", (poem_id,)).fetchone()
        return dict(row) if row else None

    def get_poems(self, dynasty: str | None = None, author: str | None = None,
                  theme: str | None = None, keyword: str | None = None,
                  page: int = 1, per_page: int = 20) -> dict:
        """Browse/filter poems with pagination.
        Returns {items: [...], total: N, page: P, per_page: PP}."""
        clauses = []
        params = []
        if dynasty:
            clauses.append("dynasty = ?")
            params.append(dynasty)
        if author:
            clauses.append("author = ?")
            params.append(author)
        if theme:
            clauses.append("theme = ?")
            params.append(theme)
        if keyword:
            clauses.append("(title LIKE ? OR content LIKE ? OR author LIKE ?)")
            params.extend([f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"])

        where = " AND ".join(clauses) if clauses else ""
        where_sql = f"WHERE {where}" if where else ""

        # Count
        with self.get_conn() as conn:
            count_row = conn.execute(
                f"SELECT COUNT(*) as cnt FROM poems {where_sql}", params
            ).fetchone()
            total = count_row["cnt"] if count_row else 0

            # Paginate
            offset = (page - 1) * per_page
            rows = conn.execute(
                f"""SELECT id, title, author, dynasty, theme,
                           SUBSTR(content, 1, 80) as content_preview, tags
                    FROM poems {where_sql}
                    ORDER BY id ASC
                    LIMIT ? OFFSET ?""",
                params + [per_page, offset]
            ).fetchall()

        return {
            "items": [dict(r) for r in rows],
            "total": total,
            "page": page,
            "per_page": per_page,
        }

    def get_random_poems(self, count: int = 3):
        """Get random poems for discovery mode."""
        with self.get_conn() as conn:
            rows = conn.execute(
                """SELECT id, title, author, dynasty, theme,
                          SUBSTR(content, 1, 120) as content_preview
                   FROM poems
                   ORDER BY RANDOM()
                   LIMIT ?""",
                (count,)
            ).fetchall()
        return [dict(r) for r in rows]

    def count_poems(self) -> int:
        """Total poem count."""
        with self.get_conn() as conn:
            row = conn.execute("SELECT COUNT(*) as cnt FROM poems").fetchone()
        return row["cnt"] if row else 0

    def get_poetry_stats(self) -> dict:
        """Get poetry collection stats: total, dynasty distribution, theme distribution."""
        with self.get_conn() as conn:
            total = conn.execute("SELECT COUNT(*) as cnt FROM poems").fetchone()["cnt"]
            dynasties = conn.execute(
                "SELECT dynasty, COUNT(*) as cnt FROM poems GROUP BY dynasty ORDER BY cnt DESC LIMIT 20"
            ).fetchall()
            themes = conn.execute(
                "SELECT theme, COUNT(*) as cnt FROM poems GROUP BY theme ORDER BY cnt DESC LIMIT 20"
            ).fetchall()
        return {
            "total": total,
            "dynasties": [{"name": r["dynasty"], "count": r["cnt"]} for r in dynasties],
            "themes": [{"name": r["theme"], "count": r["cnt"]} for r in themes],
        }

    # ============================================
    # Document operations (szbenyx)
    # ============================================
    def register_document(self, title: str, file_path: str, doc_type: str,
                          file_size: int = 0, metadata: dict | None = None) -> int:
        """Register a new document for processing."""
        with self.get_conn() as conn:
            cursor = conn.execute(
                """INSERT INTO documents (title, file_path, doc_type, file_size, metadata, status, created_at)
                   VALUES (?, ?, ?, ?, ?, 'pending', ?)""",
                (title, file_path, doc_type, file_size, json.dumps(metadata or {}),
                 _dt_now().isoformat())
            )
        return cursor.lastrowid or 0

    def update_document_status(self, doc_id: int, status: str, chunk_count: int = 0):
        with self.get_conn() as conn:
            conn.execute(
                "UPDATE documents SET status=?, chunk_count=?, processed_at=? WHERE id=?",
                (status, chunk_count, _dt_now().isoformat(), doc_id)
            )

    def get_documents(self, status: str | None = None):
        with self.get_conn() as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM documents WHERE status=? ORDER BY created_at DESC", (status,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM documents ORDER BY created_at DESC"
                ).fetchall()
        return [dict(r) for r in rows]

    # ============================================
    # Query log operations (joint — data flywheel)
    # ============================================
    def log_query(self, query_text: str, provider: str, response_time_ms: float,
                  chunk_count: int = 0, user_id: str | None = None,
                  intent_label: str | None = None):
        """Log a query for the data flywheel."""
        with self.get_conn() as conn:
            conn.execute(
                """INSERT INTO query_logs (query_text, provider, response_time_ms, chunk_count, user_id, intent_label, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (query_text, provider, response_time_ms, chunk_count, user_id, intent_label,
                 _dt_now().isoformat())
            )

    # ============================================
    # Seed: beta users
    # ============================================
    def seed_beta_users(self) -> list[str]:
        """Seed a set of beta test users with pre-assigned tiers.
        Only inserts users that don't already exist (by email / wechat_openid).
        Returns list of created user IDs.

        Creates:
          - beta_free@looma.test       (tier=free,   early_adopter)
          - beta_supporter@looma.test  (tier=supporter, early_adopter)
          - beta_pro@looma.test        (tier=pro,     early_adopter)
          - beta_admin@looma.test      (tier=pro,     early_adopter, role=admin)
        """
        import bcrypt

        created = []
        with self.get_conn() as conn:
            for u in BETA_USERS:
                # Check if already exists (by email)
                existing = conn.execute(
                    "SELECT id FROM users WHERE email = ?", (u["email"],)
                ).fetchone()
                if existing:
                    continue

                user_id = str(uuid.uuid4())
                # Dev-only: use a simple password for test accounts
                password_hash = bcrypt.hashpw(
                    "looma123".encode("utf-8"), bcrypt.gensalt()
                ).decode("utf-8")

                conn.execute(
                    """INSERT INTO users (id, email, password_hash, name, tier, role, is_early_adopter)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        user_id,
                        u["email"],
                        password_hash,
                        u["name"],
                        u["tier"],
                        u.get("role", "user"),
                        u.get("is_early_adopter", 0),
                    ),
                )
                created.append(user_id)
        return created

    def rate_query(self, query_id: int, rating: int):
        """Rate a query (1-5)."""
        with self.get_conn() as conn:
            conn.execute(
                "UPDATE query_logs SET rating=? WHERE id=?",
                (rating, query_id),
            )

    def get_last_query_id(self, user_id: str) -> int | None:
        """Get the ID of the user's most recent query."""
        with self.get_conn() as conn:
            row = conn.execute(
                "SELECT id FROM query_logs WHERE user_id=? ORDER BY created_at DESC LIMIT 1",
                (user_id,),
            ).fetchone()
        return row[0] if row else None

    # ============================================
    # Narrative operations (Jason — Phase 0 feedback)
    # ============================================
    def create_narrative_session(self, user_id: str | None, domain: str) -> str:
        """Create a new narrative session. Returns session_id."""
        session_id = str(uuid.uuid4())
        with self.get_conn() as conn:
            conn.execute(
                """INSERT INTO narrative_sessions (id, user_id, domain)
                   VALUES (?, ?, ?)""",
                (session_id, user_id, domain),
            )
        return session_id

    def update_narrative_session(self, session_id: str, status: str,
                                 duration_seconds: float = 0):
        """Mark a session as completed or abandoned."""
        with self.get_conn() as conn:
            conn.execute(
                """UPDATE narrative_sessions
                   SET status=?, duration_seconds=?, ended_at=datetime('now')
                   WHERE id=?""",
                (status, duration_seconds, session_id),
            )

    def log_narrative_event(self, session_id: str, event_type: str,
                            domain: str | None = None,
                            choice: str | None = None,
                            navigator_line: str | None = None,
                            metadata: dict | None = None):
        """Log a narrative event during a session."""
        with self.get_conn() as conn:
            conn.execute(
                """INSERT INTO narrative_events
                   (session_id, event_type, domain, choice, navigator_line, metadata_json)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (session_id, event_type, domain, choice, navigator_line,
                 json.dumps(metadata or {})),
            )

    def submit_narrative_feedback(self, session_id: str, resonated: bool,
                                  navigator_quote: str | None = None,
                                  would_replay: int | None = None,
                                  shared: bool = False,
                                  share_channel: str | None = None,
                                  open_feedback: str | None = None):
        """Submit convergence-point qualitative feedback."""
        with self.get_conn() as conn:
            conn.execute(
                """INSERT INTO narrative_feedback
                   (session_id, resonated, navigator_quote, would_replay,
                    shared, share_channel, open_feedback)
                   VALUES (?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(session_id) DO UPDATE SET
                     resonated = excluded.resonated,
                     navigator_quote = excluded.navigator_quote,
                     would_replay = excluded.would_replay,
                     shared = excluded.shared,
                     share_channel = excluded.share_channel,
                     open_feedback = excluded.open_feedback""",
                (session_id, 1 if resonated else 0, navigator_quote, would_replay,
                 1 if shared else 0, share_channel, open_feedback),
            )

    # ============================================================
    # Act 1 state persistence
    # ============================================================

    def save_act1_state(self, session_id: str, state_json: str):
        """Persist Act 1 session state as JSON."""
        with self.get_conn() as conn:
            conn.execute(
                """INSERT INTO act1_sessions (session_id, state_json, updated_at)
                   VALUES (?, ?, datetime('now'))
                   ON CONFLICT(session_id) DO UPDATE SET
                     state_json = excluded.state_json,
                     updated_at = datetime('now')""",
                (session_id, state_json),
            )

    def get_act1_state(self, session_id: str) -> str | None:
        """Retrieve Act 1 session state JSON, or None."""
        with self.get_conn() as conn:
            row = conn.execute(
                "SELECT state_json FROM act1_sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            return row["state_json"] if row else None

    def get_narrative_stats(self) -> dict:
        """Get aggregated Phase 0 metrics for admin dashboard.

        Returns completion_rate, resonance_rate, share_rate,
        replay_intent_rate, and top navigator quotes.
        """
        with self.get_conn() as conn:
            # Total sessions
            total = conn.execute(
                "SELECT COUNT(*) as cnt FROM narrative_sessions"
            ).fetchone()["cnt"]

            # Completed sessions
            completed = conn.execute(
                "SELECT COUNT(*) as cnt FROM narrative_sessions WHERE status='completed'"
            ).fetchone()["cnt"]

            # Feedback stats
            fb_total = conn.execute(
                "SELECT COUNT(*) as cnt FROM narrative_feedback"
            ).fetchone()["cnt"]

            resonated = conn.execute(
                "SELECT COUNT(*) as cnt FROM narrative_feedback WHERE resonated=1"
            ).fetchone()["cnt"]

            shared_cnt = conn.execute(
                "SELECT COUNT(*) as cnt FROM narrative_feedback WHERE shared=1"
            ).fetchone()["cnt"]

            would_replay_yes = conn.execute(
                "SELECT COUNT(*) as cnt FROM narrative_feedback WHERE would_replay=2"
            ).fetchone()["cnt"]

            # Top Navigator quotes (non-empty, deduped, sample)
            quotes = conn.execute(
                """SELECT navigator_quote, COUNT(*) as cnt
                   FROM narrative_feedback
                   WHERE navigator_quote IS NOT NULL AND navigator_quote != ''
                   GROUP BY navigator_quote
                   ORDER BY cnt DESC LIMIT 10"""
            ).fetchall()

            # Per-domain breakdown
            domain_rows = conn.execute(
                """SELECT domain, COUNT(*) as cnt
                   FROM narrative_sessions
                   GROUP BY domain ORDER BY cnt DESC"""
            ).fetchall()

            # Open feedback samples (latest 20)
            open_fb_rows = conn.execute(
                """SELECT nf.open_feedback, ns.domain, nf.created_at
                   FROM narrative_feedback nf
                   JOIN narrative_sessions ns ON nf.session_id = ns.id
                   WHERE nf.open_feedback IS NOT NULL AND nf.open_feedback != ''
                   ORDER BY nf.created_at DESC LIMIT 20"""
            ).fetchall()

        return {
            "total_sessions": total,
            "completed_sessions": completed,
            "completion_rate": round(completed / total * 100, 1) if total > 0 else 0,
            "feedback_count": fb_total,
            "resonance_rate": round(resonated / fb_total * 100, 1) if fb_total > 0 else 0,
            "share_rate": round(shared_cnt / fb_total * 100, 1) if fb_total > 0 else 0,
            "replay_intent_rate": round(would_replay_yes / fb_total * 100, 1) if fb_total > 0 else 0,
            "top_quotes": [{"quote": r["navigator_quote"], "count": r["cnt"]} for r in quotes],
            "domains": [{"domain": r["domain"], "count": r["cnt"]} for r in domain_rows],
            "open_feedback": [{"domain": r["domain"], "text": r["open_feedback"], "at": r["created_at"]} for r in open_fb_rows],
        }

    # ================================================================
    # Value Imprint methods (GDD §3.2)
    # ================================================================

    def get_value_imprints(self, user_id: str) -> dict | None:
        """Get accumulated value imprints for a user."""
        with self.get_conn() as conn:
            row = conn.execute(
                "SELECT survival, freedom, belonging FROM value_imprints WHERE user_id=?",
                (user_id,)
            ).fetchone()
        if row is None:
            return None
        return {"survival": row["survival"], "freedom": row["freedom"], "belonging": row["belonging"]}

    def save_value_imprints(self, user_id: str, imprints: dict):
        """Save/update value imprints for a user."""
        with self.get_conn() as conn:
            conn.execute(
                """INSERT INTO value_imprints (user_id, survival, freedom, belonging, updated_at)
                   VALUES (?, ?, ?, ?, datetime('now'))
                   ON CONFLICT(user_id) DO UPDATE SET
                     survival = excluded.survival,
                     freedom = excluded.freedom,
                     belonging = excluded.belonging,
                     updated_at = excluded.updated_at""",
                (user_id, imprints.get("survival", 0),
                 imprints.get("freedom", 0), imprints.get("belonging", 0)),
            )

    # ================================================================
    # Navigator Memory methods (GDD §3.4)
    # ================================================================

    def record_navigator_memory(self, user_id: str, memory_level: str,
                                content: str, context: str | None = None,
                                domain: str | None = None,
                                importance: float = 1.0,
                                session_id: str | None = None):
        """Persist a Navigator memory entry."""
        with self.get_conn() as conn:
            conn.execute(
                """INSERT INTO navigator_memories
                   (user_id, memory_level, content, context, domain, importance, session_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (user_id, memory_level, content, context, domain, importance, session_id),
            )

    def get_navigator_memories(self, user_id: str, memory_level: str | None = None,
                                limit: int = 20) -> list[dict]:
        """Retrieve Navigator memories for a user."""
        if memory_level:
            sql = """SELECT * FROM navigator_memories
                     WHERE user_id=? AND memory_level=?
                     ORDER BY importance DESC, referenced_count ASC
                     LIMIT ?"""
            params = (user_id, memory_level, limit)
        else:
            sql = """SELECT * FROM navigator_memories
                     WHERE user_id=?
                     ORDER BY created_at DESC LIMIT ?"""
            params = (user_id, limit)
        with self.get_conn() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]

    def mark_memory_referenced(self, memory_id: int):
        """Increment reference count for a memory."""
        with self.get_conn() as conn:
            conn.execute(
                "UPDATE navigator_memories SET referenced_count = referenced_count + 1 WHERE id=?",
                (memory_id,),
            )

    # ================================================================
    # Emergent Strategy Log (GDD §7.3)
    # ================================================================

    def log_emergent_strategy(self, user_id: str, strategy_type: str):
        """Log an emergent strategy detection."""
        with self.get_conn() as conn:
            conn.execute(
                "INSERT INTO emergent_strategy_log (user_id, strategy_type) VALUES (?, ?)",
                (user_id, strategy_type),
            )

    def get_emergent_strategies(self, user_id: str) -> list[str]:
        """Get all strategies detected for a user."""
        with self.get_conn() as conn:
            rows = conn.execute(
                "SELECT DISTINCT strategy_type FROM emergent_strategy_log WHERE user_id=?",
                (user_id,),
            ).fetchall()
        return [r["strategy_type"] for r in rows]

    # ================================================================
    # Domain Visit Log
    # ================================================================

    def log_domain_visit(self, user_id: str, session_id: str, domain: str,
                         previous_domain: str | None = None,
                         interaction_level: str | None = None,
                         echo_triggered: bool = False):
        """Log a domain visit event."""
        with self.get_conn() as conn:
            conn.execute(
                """INSERT INTO domain_visits
                   (user_id, session_id, domain, previous_domain, interaction_level, echo_triggered)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (user_id, session_id, domain, previous_domain, interaction_level,
                 1 if echo_triggered else 0),
            )

    def get_user_domain_history(self, user_id: str, limit: int = 20) -> list[dict]:
        """Get recent domain visit history for a user."""
        with self.get_conn() as conn:
            rows = conn.execute(
                """SELECT domain, interaction_level, echo_triggered, entered_at
                   FROM domain_visits WHERE user_id=?
                   ORDER BY entered_at DESC LIMIT ?""",
                (user_id, limit),
            ).fetchall()
        return [dict(r) for r in rows]
