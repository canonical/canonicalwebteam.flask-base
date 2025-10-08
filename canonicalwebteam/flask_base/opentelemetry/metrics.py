import functools
import logging
import statsd
from contextlib import contextmanager
from time import time
from typing import Dict

from flask import Flask, g, request


logger = logging.getLogger(__name__)


class Metric:
    """Abstraction over prometheus and statsd metrics."""

    def __init__(self, name: str):
        self.name = name
        self._client = statsd.StatsClient("localhost", 9125)

    def _format_tags(self, labels: Dict[str, str]) -> str:
        """Convert labels into StatsD-style tag string if supported."""
        if labels:
            tag_str = ",".join(
                f"{key}:{value}" for key, value in labels.items()
            )
            return f"|#{tag_str}"
        return ""


def _safe_call(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            logger.exception(f"Failed to call metric {func.__name__}")

    return wrapper


class Counter(Metric):
    @_safe_call
    def inc(self, amount: int = 1, **labels: str):
        tag_str = self._format_tags(labels)
        # Build raw message manually if needed
        self._client._send(f"{self.name}:{amount}|c{tag_str}")


class Histogram(Metric):
    @_safe_call
    def observe(self, amount: float, **labels: str):
        """Amount in milliseconds"""
        tag_str = self._format_tags(labels)
        self._client._send(f"{self.name}:{amount}|ms{tag_str}")

    @contextmanager
    def time(self, **labels: str):
        start = time()
        try:
            yield
        finally:
            duration_ms = (time() - start) * 1000
            self.observe(duration_ms, **labels)


class RequestsMetrics:
    requests = Counter(name="wsgi_requests")
    latency = Histogram(name="wsgi_latency")
    errors = Counter(name="wsgi_errors")


def register_metrics(app: Flask):
    """
    Register per route metrics for the Flask application.
    This will track the number of requests, their latency, and errors.
    """

    @app.before_request
    def start_timer():
        g.start_time = time()

    @app.after_request
    def record_metrics(response):
        duration_ms = (time() - g.get("start_time", time())) * 1000

        labels = {
            "view": request.endpoint or "unknown",
            "method": request.method,
            "status": str(response.status_code),
        }

        RequestsMetrics.requests.inc(1, **labels)
        RequestsMetrics.latency.observe(duration_ms, **labels)

        return response

    @app.teardown_request
    def handle_teardown(exception):
        if exception:
            # log 5xx errors
            status_code = getattr(exception, "code", 500)

            labels = {
                "view": request.endpoint or "unknown",
                "method": request.method,
                "status": str(status_code),
            }

            if status_code >= 500:
                RequestsMetrics.errors.inc(1, **labels)
