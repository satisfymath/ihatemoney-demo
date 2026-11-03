"""Gunicorn's access log, kept alive.

The application runs its migrations at start, and Alembic's `fileConfig` (ihatemoney/migrations/env.py) disables
every logger it does not name, `gunicorn.access` among them: with `--access-logfile -` nothing is printed. This
logger class re-enables the access logger before each line, so the container's log has one line per request, the
shape an operated service has (`"GET /path HTTP/1.1" 200`). Configuration only: the application is unchanged.

    gunicorn ... --pythonpath /src/conf --logger-class gunicorn_access.AccessLogger --access-logfile -
"""

from __future__ import annotations

from typing import Any

from gunicorn.glogging import Logger


class AccessLogger(Logger):
    def access(self, resp: Any, req: Any, environ: dict[str, Any], request_time: Any) -> None:
        self.access_log.disabled = False
        super().access(resp, req, environ, request_time)
