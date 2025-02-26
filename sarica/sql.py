import os
import sqlite3
from .essence import Essence, ClassProgress, UserClass


SCHEMA_VERSION = "1"


class Database:
    def __init__(self):
        os.makedirs("guilds", exist_ok=True)

        guild_id = os.getenv("GUILD_ID")
        self.db_path = f"guilds/{guild_id}.db"

        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
        except sqlite3.OperationalError as e:
            print(f"Error opening database: {e}", flush=True)
            raise SystemExit

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """
        )
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS classes (
                member_id INTEGER,
                class_id INTEGER,
                points INTEGER,
                PRIMARY KEY (member_id, class_id)
            )
            """
        )

        self.conn.commit()
        self.update_schema()

    def update_schema(self):
        schema_version = self.get("schema_version")

        if schema_version == SCHEMA_VERSION:
            return

        if schema_version is None:
            self.set("schema_version", SCHEMA_VERSION)
            return

        print(f"Unknown schema version: {schema_version}", flush=True)
        raise SystemExit

    def get(self, key):
        self.cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
        value = self.cursor.fetchone()
        if value is None:
            return None
        return value[0]

    def set(self, key, value):
        self.cursor.execute(
            "INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (key, value)
        )
        self.conn.commit()

    def get_essence(self, member_id):
        essence = Essence()

        query = self.cursor.fetchone()
        if query is not None:
            essence.exp = query[0]
            essence.level = query[1]

        self.cursor.execute(
            "SELECT class_id, points FROM classes WHERE member_id = ?", (member_id,)
        )
        query = self.cursor.fetchall()
        for class_id, points in query:
            essence.add_points(UserClass(class_id), points)

        return essence

    def set_essence(self, member_id, essence: Essence):
        for progress in essence.classes:
            if not progress.changed:
                continue

            self.cursor.execute(
                "INSERT OR REPLACE INTO classes (member_id, class_id, points) VALUES (?, ?, ?)",
                (member_id, progress.user_class.value, progress.points),
            )

        self.conn.commit()
