"""Self-check for the FSM storage backends. Run: python tests/test_storage.py"""

import sqlite3
import tempfile

from t8ot import BaseStorage, MemoryStorage, RedisStorage, SQLiteStorage


def exercise(storage: BaseStorage) -> None:
    assert storage.get_state(1) is None
    assert storage.get_data(1) == {}

    storage.set_state(1, "survey:0")
    assert storage.get_state(1) == "survey:0"

    storage.update_data(1, name="ada", age=36)
    storage.update_data(1, age=37)
    assert storage.get_data(1) == {"name": "ada", "age": 37}

    # Writes must not leak between users, and clear() is idempotent.
    assert storage.get_state(2) is None
    assert storage.get_data(2) == {}

    storage.clear(1)
    storage.clear(1)
    assert storage.get_state(1) is None
    assert storage.get_data(1) == {}


def check_sqlite() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = f"{tmp}/check.db"
        exercise(SQLiteStorage(path))

        # Reopening the same file must see the rows written earlier.
        reopened = SQLiteStorage(path)
        reopened.set_state(7, "survey:1")
        assert reopened.get_state(7) == "survey:1"

        # Corrupted payloads degrade to an empty dict instead of raising.
        with sqlite3.connect(path) as conn:
            conn.execute("UPDATE fsm_storage SET data = '{bad' WHERE user_id = 7")
        assert reopened.get_data(7) == {}


def check_redis_import_error() -> None:
    try:
        import redis  # noqa: F401
    except ImportError:
        try:
            RedisStorage()
        except ImportError as exc:
            assert "pip install redis" in str(exc), exc
            return
        raise AssertionError("RedisStorage must raise without the redis package")


def main() -> None:
    exercise(MemoryStorage())
    check_sqlite()
    check_redis_import_error()
    print("storage self-check OK")


if __name__ == "__main__":
    main()