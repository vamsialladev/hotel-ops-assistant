"""Daily question cap shared by every visitor, so the public demo can't drain the API credit.

The count lives in a small JSON file on the server (git-ignored), so refreshing the page or opening
a new browser session does not reset it. It resets at midnight UTC. On Streamlit Community Cloud
the file is lost when the app restarts, which resets the count early (documented in SECURITY.md).
"""

import json
import os
import tempfile
import threading
from datetime import UTC, datetime
from pathlib import Path

_LOCK = threading.Lock()


def today_utc() -> str:
    return datetime.now(UTC).date().isoformat()


class DailyCounter:
    def __init__(self, path: Path, limit: int, today=today_utc):
        self.path, self.limit, self.today = Path(path), limit, today

    def _read(self) -> dict:
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if data.get("date") == self.today() and isinstance(data.get("count"), int):
                return data
        except (OSError, ValueError):
            pass
        return {"date": self.today(), "count": 0}

    def _write(self, data: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=self.path.parent, prefix=".daily-")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f)
        os.replace(tmp, self.path)  # atomic: a crash never leaves a half-written file

    def used(self) -> int:
        with _LOCK:
            return self._read()["count"]

    def try_consume(self) -> bool:
        """Count one question if today's cap allows it. Returns False once the cap is reached."""
        with _LOCK:
            data = self._read()
            if data["count"] >= self.limit:
                return False
            data["count"] += 1
            self._write(data)
            return True
