import sqlite3
import pytest
from app.adapters.sqlite.inspector import inspect_sqlite_database


def test_inspector_rejects_symlink(tmp_path):
    target = tmp_path / "real.db"
    with sqlite3.connect(target) as connection:
        connection.execute("CREATE TABLE example (id INTEGER PRIMARY KEY)")

    symlink = tmp_path / "linked.db"

    try:
        symlink.symlink_to(target)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"Cannot create symlink in this environment: {exc}")

    with pytest.raises(sqlite3.OperationalError, match="regular file"):
        inspect_sqlite_database(
            path=symlink,
            database_id="test-database",
        )
