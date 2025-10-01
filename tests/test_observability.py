import time
import unittest

from unittest.mock import patch, MagicMock
from flask import g, request

import opentelemetry as otel
import opentelemetry.context as otel_context
import opentelemetry.instrumentation.requests as otel_requests
import opentelemetry.instrumentation.flask as otel_flask
import opentelemetry.trace as otel_trace

import canonicalwebteam.flask_base.observability as observability

from tests.test_app.webapp.app import create_test_app


class TestMetrics(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_test_app()

    def test_register_metrics(self) -> None:
        # "None" gets the application scoped functions
        # the blueprint functions are the ones that are named
        before_request_functions = [
            function.__name__
            for function in self.app.before_request_funcs.get(None, [])
        ]
        after_request_functions = [
            function.__name__
            for function in self.app.after_request_funcs.get(None, [])
        ]
        teardown_request_functions = [
            function.__name__
            for function in self.app.teardown_request_funcs.get(None, [])
        ]
        self.assertIn("start_timer", before_request_functions)
        self.assertIn("record_metrics", after_request_functions)
        self.assertIn("handle_teardown", teardown_request_functions)

    def test_start_timer(self) -> None:
        with self.app.test_client() as client:
            client.get("/page")
            time.sleep(0.1)
            self.assertGreater(time.time(), g.start_time)

    @patch("canonicalwebteam.flask_base.metrics.RequestsMetrics.requests")
    @patch("canonicalwebteam.flask_base.metrics.RequestsMetrics.latency")
    def test_record_metrics(self, mock_latency, mock_requests) -> None:
        with self.app.test_client() as client:
            response = client.get("/page")
            mock_requests.inc.assert_called_once()
            mock_latency.observe.assert_called_once()
            expected_labels = {
                "view": request.endpoint or "unknown",
                "method": request.method,
                "status": str(response.status_code),
            }
            self.assertEqual(
                mock_requests.inc.call_args.args,
                (1,),
            )
            self.assertEqual(
                mock_requests.inc.call_args.kwargs,
                expected_labels,
            )
            self.assertGreater(
                mock_latency.observe.call_args.args[0],
                0,
            )
            self.assertEqual(
                mock_latency.observe.call_args.kwargs,
                expected_labels,
            )

    @patch("canonicalwebteam.flask_base.metrics.RequestsMetrics.errors")
    def test_handle_teardown(self, mock_errors) -> None:
        with self.app.test_client() as client:
            client.get("/exception")
            mock_errors.inc.assert_called_once()
            expected_labels = {
                "view": request.endpoint or "unknown",
                "method": request.method,
                "status": "500",
            }
            self.assertEqual(
                mock_errors.inc.call_args.args,
                (1,),
            )
            self.assertEqual(
                mock_errors.inc.call_args.kwargs,
                expected_labels,
            )


class TestTraces(unittest.TestCase):
    def setUp(self) -> None:
        self.propagate_patch = patch.object(
            otel,
            "propagate",
            _mock_propagate(),
        )
        self.propagate_patch.start()
        self.detach_patch = patch.object(
            otel_context,
            "detach",
            _mock_detach(),
        )
        self.detach_patch.start()
        self.attach_patch = patch.object(
            otel_context,
            "attach",
            lambda: _mock_token(),
        )
        self.attach_patch.start()
        self.req_inst_patch = patch.object(
            otel_requests,
            "RequestsInstrumentor",
            _mock_req_inst(),
        )
        self.req_inst_patch.start()
        self.flask_inst_patch = patch.object(
            otel_flask,
            "FlaskInstrumentor",
            _mock_flask_inst(),
        )
        self.flask_inst_patch.start()
        self.cur_span_patch = patch.object(
            otel_trace,
            "get_current_span",
            lambda: _mock_span(),
        )
        self.cur_span_patch.start()
        self.tracing_patch = patch.object(
            observability,
            "TRACING_ENABLED",
            True,
        )
        self.tracing_patch.start()
    
        # Once everything is patched, start the app
        self.app = create_test_app()

    def tearDown(self) -> None:
        self.tracing_patch.stop()
        self.propagate_patch.stop()
        self.attach_patch.stop()
        self.detach_patch.stop()
        self.req_inst_patch.stop()
        self.flask_inst_patch.stop()
        self.cur_span_patch.stop()

    def test_get_trace_id(self) -> None:
        expected_trace_id = "eef33c8eba4cfbacb6788f8f8189d51a"
        with patch("opentelemetry.trace.get_current_span") as mock_get_span:
            mock_span_context = MagicMock()
            mock_span_context.trace_id = int(expected_trace_id, 16)
            mock_span = MagicMock()
            mock_span.get_span_context.return_value = mock_span_context
            mock_get_span.return_value = mock_span

            trace_id = observability.get_trace_id()
            self.assertEqual(trace_id, expected_trace_id)

    def test_register_traces(self) -> None:
        pass

    def test_request_hook(self) -> None:
        pass

    def test_extract_trace_context(self) -> None:
        pass

    def test_add_trace_id_header(self) -> None:
        pass

    def test_detach_trace_context(self) -> None:
        pass


# Functions to generate mocks for opentelemetry

def _mock_propagate() -> MagicMock:
    return MagicMock()
    
def _mock_detach() -> MagicMock:
    return MagicMock()

def _mock_token() -> MagicMock:
    return MagicMock()

def _mock_req_inst() -> MagicMock:
    return MagicMock()

def _mock_flask_inst() -> MagicMock:
    return MagicMock()

def _mock_span() -> MagicMock:
    return MagicMock()


class TestNoTracing(unittest.TestCase):
    @patch("opentelemetry.instrumentation.flask.FlaskInstrumentor")
    @patch("opentelemetry.instrumentation.requests.RequestsInstrumentor")
    def test_tracing_not_enabled(
        self,
        mock_requests_instrument,
        mock_flask_instrument,
    ) -> None:
        app = create_test_app()
        # "None" gets the application scoped functions
        # the blueprint functions are the ones that are named
        before_request_functions = [
            function.__name__
            for function in app.before_request_funcs.get(None, [])
        ]
        after_request_functions = [
            function.__name__
            for function in app.after_request_funcs.get(None, [])
        ]
        teardown_request_functions = [
            function.__name__
            for function in app.teardown_request_funcs.get(None, [])
        ]

        self.assertNotIn("extract_trace_context", before_request_functions)
        self.assertNotIn("add_trace_id_header", after_request_functions)
        self.assertNotIn("detach_trace_context", teardown_request_functions)

        mock_requests_instrument.assert_not_called()
        mock_flask_instrument.assert_not_called()
