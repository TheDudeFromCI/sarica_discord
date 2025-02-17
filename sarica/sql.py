import os
import sqlite3


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
            print(f"Error opening database: {e}")
            raise SystemExit

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT
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

        print(f"Unknown schema version: {schema_version}")
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
