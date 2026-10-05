import json
import sqlite3
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any, Dict, Iterator, Optional


def _decode(raw: Optional[str]) -> Dict[str, Any]:
    """Decode a JSON payload into a dict, falling back to an empty dict.

    Guards against missing values and corrupted payloads written by older
    versions or by external tooling.
    """
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except (TypeError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


class BaseStorage(ABC):
    """Storage contract for FSM state and step data.

    Implementations are synchronous and must be safe to call from the bot's
    event loop; keep every call short-lived and non-blocking.
    """

    @abstractmethod
    def get_state(self, user_id: int) -> Optional[str]:
        """Return the active state (e.g. ``"survey:0"``) or ``None``."""

    @abstractmethod
    def set_state(self, user_id: int, state: str) -> None:
        """Persist the active state for a user."""

    @abstractmethod
    def get_data(self, user_id: int) -> Dict[str, Any]:
        """Return the collected step data for a user."""

    @abstractmethod
    def update_data(self, user_id: int, **kwargs) -> None:
        """Merge ``kwargs`` into the user's step data."""

    @abstractmethod
    def clear(self, user_id: int) -> None:
        """Drop all state and data for a user."""


class MemoryStorage(BaseStorage):
    """Volatile storage kept in a plain dictionary (default backend)."""

    def __init__(self):
        # Format: {user_id: {"state": "flow_name:step_name", "data": {...}}}
        self._data: Dict[int, Dict[str, Any]] = {}

    def get_state(self, user_id: int) -> Optional[str]:
        return self._data.get(user_id, {}).get("state")

    def set_state(self, user_id: int, state: str) -> None:
        self._bucket(user_id)["state"] = state

    def get_data(self, user_id: int) -> Dict[str, Any]:
        return self._data.get(user_id, {}).get("data", {})

    def update_data(self, user_id: int, **kwargs) -> None:
        self._bucket(user_id)["data"].update(kwargs)

    def clear(self, user_id: int) -> None:
        self._data.pop(user_id, None)

    def _bucket(self, user_id: int) -> Dict[str, Any]:
        """Return the user's slot, creating it on first write."""
        return self._data.setdefault(user_id, {"state": None, "data": {}})


class SQLiteStorage(BaseStorage):
    """Durable storage backed by a local SQLite file (stdlib only).

    A connection is opened per operation, which keeps the storage safe to use
    from the bot's single-threaded event loop without sharing connections.
    """

    def __init__(self, db_path: str = "bot_storage.db"):
        self.db_path = db_path
        with self._connect() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS fsm_storage ("
                "user_id INTEGER PRIMARY KEY, state TEXT, data TEXT)"
            )

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        """Yield a connection that commits on success and always closes."""
        conn = sqlite3.connect(self.db_path)
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def get_state(self, user_id: int) -> Optional[str]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT state FROM fsm_storage WHERE user_id = ?", (user_id,)
            ).fetchone()
        return row[0] if row else None

    def set_state(self, user_id: int, state: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO fsm_storage (user_id, state) VALUES (?, ?) "
                "ON CONFLICT(user_id) DO UPDATE SET state = excluded.state",
                (user_id, state),
            )

    def get_data(self, user_id: int) -> Dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT data FROM fsm_storage WHERE user_id = ?", (user_id,)
            ).fetchone()
        return _decode(row[0] if row else None)

    def update_data(self, user_id: int, **kwargs) -> None:
        data = self.get_data(user_id)
        data.update(kwargs)
        payload = json.dumps(data)
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO fsm_storage (user_id, data) VALUES (?, ?) "
                "ON CONFLICT(user_id) DO UPDATE SET data = excluded.data",
                (user_id, payload),
            )

    def clear(self, user_id: int) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM fsm_storage WHERE user_id = ?", (user_id,))


class RedisStorage(BaseStorage):
    """Storage backed by a Redis server, shared across bot instances.

    Keys are ``{prefix}:{user_id}:state`` and ``{prefix}:{user_id}:data``.
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        prefix: str = "t8ot:fsm",
        ttl: Optional[int] = None,
    ):
        try:
            import redis
        except ImportError as exc:
            raise ImportError(
                "RedisStorage requires the 'redis' package. "
                "Install it with: pip install redis"
            ) from exc

        self.prefix = prefix
        self.ttl = ttl
        # redis-py's connection pool is thread-safe, so no extra locking.
        self._redis: Any = redis.Redis.from_url(redis_url, decode_responses=True)

    def _key(self, user_id: int, kind: str) -> str:
        return f"{self.prefix}:{user_id}:{kind}"

    def get_state(self, user_id: int) -> Optional[str]:
        return self._redis.get(self._key(user_id, "state"))

    def set_state(self, user_id: int, state: str) -> None:
        self._redis.set(self._key(user_id, "state"), state, ex=self.ttl)

    def get_data(self, user_id: int) -> Dict[str, Any]:
        return _decode(self._redis.get(self._key(user_id, "data")))

    def update_data(self, user_id: int, **kwargs) -> None:
        data = self.get_data(user_id)
        data.update(kwargs)
        self._redis.set(
            self._key(user_id, "data"), json.dumps(data), ex=self.ttl
        )

    def clear(self, user_id: int) -> None:
        self._redis.delete(
            self._key(user_id, "state"), self._key(user_id, "data")
        )