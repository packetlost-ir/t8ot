"""Self-check for the FSM storage backends. Run: python tests/test_storage.py"""

import sqlite3
import tempfile
import threading

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


def check_sqlite_persistence() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = f"{tmp}/check.db"
        storage = SQLiteStorage(path)
        exercise(storage)
        storage.set_state(7, "survey:1")
        storage.update_data(7, note="kept")
        storage.close()
        storage.close()  # close() must be idempotent

        # A fresh instance sees everything the closed one persisted.
        reopened = SQLiteStorage(path)
        assert reopened.get_state(7) == "survey:1"
        assert reopened.get_data(7) == {"note": "kept"}
        reopened.close()
        print("[ok] sqlite persists across close/reopen")


def check_sqlite_corrupt_payload() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = f"{tmp}/check.db"
        storage = SQLiteStorage(path)
        storage.set_state(7, "survey:1")
        storage.close()

        # Corrupted payloads degrade to an empty dict instead of raising.
        with sqlite3.connect(path) as conn:
            conn.execute("UPDATE fsm_storage SET data = '{bad' WHERE user_id = 7")

        reopened = SQLiteStorage(path)
        assert reopened.get_data(7) == {}
        reopened.close()
        print("[ok] sqlite tolerates corrupted JSON")


def check_sqlite_concurrency() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        path = f"{tmp}/check.db"
        storage = SQLiteStorage(path)
        errors = []

        def worker(uid: int) -> None:
            try:
                for i in range(50):
                    storage.set_state(uid, f"flow:{i}")
                    storage.update_data(uid, count=i)
                assert storage.get_state(uid) == "flow:49", uid
                assert storage.get_data(uid) == {"count": 49}, uid
            except Exception as exc:  # noqa: BLE001 - surfaced via errors list
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(uid,)) for uid in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert not errors, errors
        # The shared connection + lock must have kept every user isolated.
        for uid in range(8):
            assert storage.get_state(uid) == "flow:49"
            assert storage.get_data(uid) == {"count": 49}
        storage.close()
        print("[ok] sqlite survives concurrent threaded writes")


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
    check_sqlite_persistence()
    check_sqlite_corrupt_payload()
    check_sqlite_concurrency()
    check_redis_import_error()
    print("storage self-check OK")


if __name__ == "__main__":
    main()
