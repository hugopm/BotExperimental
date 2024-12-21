import sqlite3
import json
from pathlib import Path

class BotData:
    """Manages SQLite operations for bot scores."""

    def __init__(self, db_path="bot_scores.db"):
        """Initialize SQLite database and create table if needed."""
        self.db_path = db_path
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS scores (
                    id TEXT PRIMARY KEY,
                    liste TEXT
                )
            """)

    def get_one(self, id):
        """Retrieve a single score list by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT liste FROM scores WHERE id = ?", (id,))
            result = cursor.fetchone()
            if result is None:
                raise KeyError(f"No data found for ID: {id}")
            return json.loads(result[0])

    def set_one(self, id, score_list):
        """Store a score list for given ID, replacing any existing score."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO scores (id, liste) VALUES (?, ?)",
                (id, json.dumps(score_list))
            )

    def delete(self, id):
        """Delete an entry by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM scores WHERE id = ?", (id,))

    def scan(self):
        """Retrieve all scores from the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT id, liste FROM scores")
            return [
                (int(id), json.loads(liste))
                for id, liste in cursor.fetchall()
            ]

    def delete_all(self):
        """Delete all entries from the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM scores")
