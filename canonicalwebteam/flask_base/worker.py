"""
A custom gunicorn gevent worker for Flask applications.

This worker is designed to handle SIGINT and SIGTERM gracefully, by
closing all client connections and logging the stacktrace before
exiting.

## Usage
Run gunicorn in the usual way, but specify the worker class as LogWorker.

talisker.gunicorn.gevent webapp.app:app -k flask_base.worker.LogWorker

"""

import secrets
import sys
import traceback
from typing import NoReturn

from gunicorn import util
from gunicorn.workers.ggevent import GeventWorker


class LogWorker(GeventWorker):
    def __init__(self, *args: tuple, **kwargs: dict) -> None:
        super().__init__(*args, **kwargs)
        self.instance_id = secrets.token_hex(6)
        self.clients = []

    def _log(self, msg: str) -> None:
        print(f"[CUSTOM WORKER][{self.instance_id}]: {msg}")

    def close_clients_gracefully(self) -> None:
        """Send a 200 response to all registered clients"""
        self._log(f"closing {len(self.clients)} clients gracefully")
        msg = "OK"
        size = len(msg)
        response_data = (
            f"HTTP/1.1 200 {msg}\r\nContent-Length: {size}\r\n\r\n{msg}"
        )
        response_data = response_data.encode("utf-8")
        try:
            for conn in self.clients:
                conn.sendall(response_data)
                conn.close()
        except Exception as e:  # noqa: BLE001
            self._log(str(e))

    def notify_error(self, sig: int) -> None:
        """Print recent traceback logs."""
        self._log(f"notifying errors with signal {sig}")
        self._log(traceback.format_exc())

    def accept(self, listener) -> None:
        """Accept a new client connection."""
        client, addr = listener.accept()
        # Register client connections to this worker
        self.clients.append(client)
        client.setblocking(1)
        util.close_on_exec(client)
        self.handle(listener, client, addr)

    def handle_exit(self, sig, frame) -> None:
        """Handle SIGTERM gracefully"""
        self._log(f"handling signal {sig}")
        self.notify_error(sig)
        self.close_clients_gracefully()
        sys.exit(0)

    def handle_quit(self, sig, frame) -> NoReturn:
        """Handle SIGQUIT gracefully"""
        self._log(f"handling signal {sig}")
        self.notify_error(sig)
        self.close_clients_gracefully()
        sys.exit(0)
