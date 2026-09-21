import sqlite3
from pathlib import Path
from contextlib import contextmanager

class Database:
    def __init__(self, path: str):
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.init()

    @contextmanager
    def conn(self):
        c = sqlite3.connect(self.path)
        c.row_factory = sqlite3.Row
        try:
            yield c
            c.commit()
        finally:
            c.close()

    def init(self):
        with self.conn() as c:
            c.executescript('''
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT NOT NULL,
                balance INTEGER NOT NULL DEFAULT 450,
                referrals INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                reply TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            ''')

    def upsert_user(self, telegram_id, username, first_name):
        with self.conn() as c:
            c.execute('''
            INSERT INTO users(telegram_id, username, first_name)
            VALUES(?,?,?)
            ON CONFLICT(telegram_id) DO UPDATE SET
              username=excluded.username,
              first_name=excluded.first_name
            ''', (telegram_id, username, first_name))

    def get_user(self, telegram_id):
        with self.conn() as c:
            row = c.execute("SELECT * FROM users WHERE telegram_id=?", (telegram_id,)).fetchone()
            return dict(row) if row else None

    def add_ticket(self, telegram_id, text):
        with self.conn() as c:
            cur = c.execute("INSERT INTO tickets(telegram_id,text) VALUES(?,?)", (telegram_id, text))
            return cur.lastrowid

    def get_tickets(self, telegram_id):
        with self.conn() as c:
            rows = c.execute(
                "SELECT id,text,status,reply FROM tickets WHERE telegram_id=? ORDER BY id DESC",
                (telegram_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    def add_balance(self, telegram_id, amount):
        with self.conn() as c:
            c.execute("UPDATE users SET balance=balance+? WHERE telegram_id=?", (amount, telegram_id))
            row = c.execute("SELECT balance FROM users WHERE telegram_id=?", (telegram_id,)).fetchone()
            return row["balance"]
