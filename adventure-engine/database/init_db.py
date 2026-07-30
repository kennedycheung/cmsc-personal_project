import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR.parent / 'adventure.db'
SCHEMA_PATH = BASE_DIR / 'schema.sql'


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as connection:
        with SCHEMA_PATH.open('r', encoding='utf-8') as schema_file:
            connection.executescript(schema_file.read())
    print(f'Initialized SQLite database at {DB_PATH}')


if __name__ == '__main__':
    init_db()
