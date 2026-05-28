import sqlite3
from typing import List, Dict, Any

DB_PATH = "loan.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY,
        name TEXT,
        income INTEGER,
        loan_amount INTEGER,
        credit_score INTEGER,
        email TEXT,
        status TEXT,
        notes TEXT,
        history TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        app_id INTEGER NOT NULL,
        filename TEXT,
        content BLOB,
        verified INTEGER DEFAULT 0,
        FOREIGN KEY (app_id) REFERENCES applications (id) ON DELETE CASCADE
    )
    """)

    # --- Simple Schema Migration ---
    # Add 'email' column to applications if it doesn't exist
    cur.execute("PRAGMA table_info(applications)")
    columns = [row['name'] for row in cur.fetchall()]
    if 'email' not in columns:
        print("DB Migration: Adding 'email' column to 'applications' table.")
        cur.execute("ALTER TABLE applications ADD COLUMN email TEXT")
    if 'history' not in columns:
        print("DB Migration: Adding 'history' column to 'applications' table.")
        cur.execute("ALTER TABLE applications ADD COLUMN history TEXT")

    # You can add more migration checks here in the future
    # -----------------------------

    conn.commit()
    conn.close()

def save_application(name: str, income: int, loan_amount: int, email: str) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO applications (name, income, loan_amount, email, status) VALUES (?, ?, ?, ?, ?)",
        (name, income, loan_amount, email, "SUBMITTED")
    )
    app_id = cur.lastrowid
    conn.commit()
    conn.close()
    return app_id

def save_document(app_id: int, filename: str, content: bytes):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO documents (app_id, filename, content) VALUES (?, ?, ?)",
        (app_id, filename, content)
    )
    conn.commit()
    conn.close()

def list_applications() -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM applications ORDER BY id DESC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def get_documents(app_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    # We only need to know if they exist, but fetching filename is good for logging
    cur.execute("SELECT id, filename FROM documents WHERE app_id=?", (app_id,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def get_application(app_id: int) -> Dict[str, Any]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM applications WHERE id=?", (app_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None

def update_application_status(app_id: int, status: str, notes: str = ""):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE applications SET status=?, notes=? WHERE id=?", (status, notes, app_id))
    conn.commit()
    conn.close()

def update_application_credit_score(app_id: int, credit_score: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE applications SET credit_score=? WHERE id=?", (credit_score, app_id))
    conn.commit()
    conn.close()

def update_application_history(app_id: int, history: str):
    """Updates the history log for a given application."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE applications SET history=? WHERE id=?", (history, app_id))
    conn.commit()
    conn.close()

def delete_application(app_id: int):
    """Deletes an application and its related documents from the database."""
    conn = get_connection()
    cur = conn.cursor()
    # Also delete associated documents to keep the database clean
    cur.execute("DELETE FROM documents WHERE app_id = ?", (app_id,))
    cur.execute("DELETE FROM applications WHERE id = ?", (app_id,))
    conn.commit()
    conn.close()

def clear_application_history(app_id: int):
    """Clears the history log for a given application."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE applications SET history=? WHERE id=?", ("", app_id))
    conn.commit()
    conn.close()
