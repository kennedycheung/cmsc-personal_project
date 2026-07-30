from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

_is_sqlite = settings.database_url.startswith("sqlite")

# check_same_thread is only meaningful for SQLite; swapping DATABASE_URL to a
# Postgres DSN drops this kwarg automatically and needs no other code changes.
connect_args = {"check_same_thread": False} if _is_sqlite else {}

engine = create_engine(settings.database_url, connect_args=connect_args)

if _is_sqlite:
    # Python's sqlite3 DBAPI driver manages its own implicit transaction
    # boundaries (auto-BEGIN/auto-COMMIT heuristics based on statement type)
    # independently of SQLAlchemy's explicit BEGIN/SAVEPOINT control, unless
    # this is disabled -- without it, SAVEPOINT-based nested transactions
    # (used by the test suite's per-test rollback isolation, see
    # tests/backend/conftest.py) silently lose data on rollback, because the
    # driver has already auto-committed the outer transaction underneath
    # SQLAlchemy without telling it. This is SQLAlchemy's own documented
    # workaround for pysqlite (see "Serializable isolation / Savepoints /
    # Transactional DDL" in the SQLAlchemy SQLite dialect docs).
    @event.listens_for(engine, "connect")
    def _sqlite_disable_pysqlite_implicit_transactions(dbapi_connection, connection_record):
        dbapi_connection.isolation_level = None

    @event.listens_for(engine, "begin")
    def _sqlite_emit_explicit_begin(conn):
        conn.exec_driver_sql("BEGIN")


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
