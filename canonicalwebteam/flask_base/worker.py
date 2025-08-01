"""
A custom gunicorn gevent worker for Flask applications.

This worker is designed to handle SIGINT and SIGTERM gracefully, by
closing all client connections and logging the stacktrace before
exiting.

## Usage
Run gunicorn in the usual way, but specify the worker class as LogWorker.

gunicorn webapp.app:app \
    -k canonicalwebteam.flask_base.worker.LogWorker

"""

from __future__ import annotations

import logging
import os
import secrets
import traceback
from typing import TYPE_CHECKING

from gunicorn.workers.ggevent import GeventWorker

if TYPE_CHECKING:
    from socket import socket
    from types import FrameType


logger = logging.getLogger("gunicorn.error")


class LogWorker(GeventWorker):
    def __init__(self, *args: tuple, **kwargs: dict) -> None:
        super().__init__(*args, **kwargs)
        self.instance_id = secrets.token_hex(6)
        self.clients: list[socket] = []

    def _log(self, msg: str) -> None:
        msg = f"[LOG WORKER][{self.instance_id}]: {msg}"
        self.log.info(msg)

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
            self._log("Unable to close client: " + str(e))

    def notify_error(self, sig: int) -> None:
        """Print recent traceback logs."""
        self._log(f"notifying errors with signal {sig}")
        self._log("Stacktrace: " + traceback.format_exc())

    def handle(self, listener: socket, client: socket, addr: tuple) -> None:
        """Handle a new client connection."""
        # Register client connections to this worker
        self.clients.append(listener)
        super().handle(listener, client, addr)

    def handle_termination_gracefully(
        self,
        sig: int,
        frame: FrameType | None,
    ) -> None:
        """Handle termination signal gracefully"""
        self._log(f"handling signal {sig}")
        self.notify_error(sig)
        self.close_clients_gracefully()
        self._log(f"closing worker {self.instance_id}")
        os._exit(0)  # exit immediately, avoiding later exception catches

    def handle_exit(self, sig: int, frame: FrameType | None) -> None:
        """Handle SIGTERM gracefully"""
        self.handle_termination_gracefully(sig, frame)

    def handle_quit(self, sig: int, frame: FrameType | None) -> None:
        """Handle SIGQUIT gracefully"""
        self.handle_termination_gracefully(sig, frame)

    def handle_interrupt(self, sig: int, frame: FrameType | None) -> None:
        """Handle SIGINT gracefully"""
        self.handle_termination_gracefully(sig, frame)
