import time

from flask import Flask, g, request
from opentelemetry.context import attach, detach
from opentelemetry.trace import get_current_span
from opentelemetry import propagate

from canonicalwebteam.flask_base.metrics import RequestsMetrics


def register_metrics(app: Flask):
    """
    Register per route metrics for the Flask application.
    This will track the number of requests, their latency, and errors.
    """

    @app.before_request
    def start_timer():
        g.start_time = time.time()

    @app.after_request
    def record_metrics(response):
        duration_ms = (time.time() - g.get("start_time", time.time())) * 1000

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


# Traces will only work if properly set up
# They are set up out of the box in the paas-charm
# Example of configuration file:
# https://github.com/canonical/paas-charm/blob/main/src/paas_charm/templates/gunicorn.conf.py.j2#L17
# Then Gunicorn can be run and passed the configuration file path with "-c"

def get_trace_id():
    span = get_current_span()
    ctx = span.get_span_context()
    if ctx and ctx.trace_id != 0:
        return format(ctx.trace_id, "032x")
    return None


def register_trace(app: Flask):
    # OpenTelemetry tracing
    @app.after_request
    def add_trace_id_header(response):
        trace_id = get_trace_id()
        if trace_id:
            response.headers["X-Request-ID"] = trace_id
        return response

    @app.before_request
    def extract_trace_context():
        """Extract trace context from traceparent header if present"""
        traceparent = request.headers.get("traceparent")
        if traceparent:
            carrier = {"traceparent": traceparent}
            context = propagate.extract(carrier)
            g._otel_token = attach(context)

    @app.teardown_request
    def detach_trace_context(exception=None):
        """Detach the trace context at the end of the request"""
        token = getattr(g, "_otel_token", None)
        if token is not None:
            detach(token)
