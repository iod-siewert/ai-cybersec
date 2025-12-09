# db/scans_db.py
import sqlite3
from pathlib import Path
from typing import Optional, List, Tuple

DB_PATH = Path("db/scans.sqlite")

def init_db() -> None:
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS plugins (
            slug TEXT PRIMARY KEY,
            name TEXT,
            repo_url TEXT,
            vcs TEXT,
            last_scan_result TEXT,
            last_scan_findings INTEGER,
            last_scan_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def upsert_plugin(slug: str, name: str, repo_url: str, vcs: str) -> None:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO plugins (slug, name, repo_url, vcs, last_scan_result, last_scan_findings, last_scan_at)
        VALUES (?, ?, ?, ?, NULL, NULL, NULL)
        ON CONFLICT(slug) DO UPDATE SET
          name=excluded.name,
          repo_url=excluded.repo_url,
          vcs=excluded.vcs
    """, (slug, name, repo_url, vcs))
    conn.commit()
    conn.close()

def update_scan(slug: str, result: str, findings: int, scanned_at: str) -> None:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        UPDATE plugins
        SET last_scan_result=?, last_scan_findings=?, last_scan_at=?
        WHERE slug=?
    """, (result, findings, scanned_at, slug))
    conn.commit()
    conn.close()

def get_next_plugins(limit: int, resume_from: Optional[str] = None) -> List[Tuple[str, str, str, str]]:
    """
    Zwraca listę (slug, name, repo_url, vcs) do skanowania.
    Priorytet: brak last_scan_at albo NULL.
    resume_from – opcjonalny slug, od którego kontynuujemy.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if resume_from:
        c.execute("""
            SELECT slug, name, repo_url, vcs
            FROM plugins
            WHERE (last_scan_at IS NULL) AND slug >= ?
            ORDER BY slug
            LIMIT ?
        """, (resume_from, limit))
    else:
        c.execute("""
            SELECT slug, name, repo_url, vcs
            FROM plugins
            WHERE last_scan_at IS NULL
            ORDER BY slug
            LIMIT ?
        """, (limit,))
    rows = c.fetchall()
    conn.close()
    return rows
# db/scans_db.py
import sqlite3
from pathlib import Path
from typing import Optional, List, Tuple

DB_PATH = Path("db/scans.sqlite")

def init_db() -> None:
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS plugins (
            slug TEXT PRIMARY KEY,
            name TEXT,
            repo_url TEXT,
            vcs TEXT,
            last_scan_result TEXT,
            last_scan_findings INTEGER,
            last_scan_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def upsert_plugin(slug: str, name: str, repo_url: str, vcs: str) -> None:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO plugins (slug, name, repo_url, vcs, last_scan_result, last_scan_findings, last_scan_at)
        VALUES (?, ?, ?, ?, NULL, NULL, NULL)
        ON CONFLICT(slug) DO UPDATE SET
          name=excluded.name,
          repo_url=excluded.repo_url,
          vcs=excluded.vcs
    """, (slug, name, repo_url, vcs))
    conn.commit()
    conn.close()

def update_scan(slug: str, result: str, findings: int, scanned_at: str) -> None:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        UPDATE plugins
        SET last_scan_result=?, last_scan_findings=?, last_scan_at=?
        WHERE slug=?
    """, (result, findings, scanned_at, slug))
    conn.commit()
    conn.close()

def get_next_plugins(limit: int, resume_from: Optional[str] = None) -> List[Tuple[str, str, str, str]]:
    """
    Zwraca listę (slug, name, repo_url, vcs) do skanowania.
    Priorytet: brak last_scan_at albo NULL.
    resume_from – opcjonalny slug, od którego kontynuujemy.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if resume_from:
        c.execute("""
            SELECT slug, name, repo_url, vcs
            FROM plugins
            WHERE (last_scan_at IS NULL) AND slug >= ?
            ORDER BY slug
            LIMIT ?
        """, (resume_from, limit))
    else:
        c.execute("""
            SELECT slug, name, repo_url, vcs
            FROM plugins
            WHERE last_scan_at IS NULL
            ORDER BY slug
            LIMIT ?
        """, (limit,))
    rows = c.fetchall()
    conn.close()
    return rows
