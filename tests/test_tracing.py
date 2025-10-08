import unittest

from unittest.mock import patch, MagicMock
from flask import g, Response

import canonicalwebteam.flask_base.opentelemetry.tracing as tracing

from tests.test_app.webapp.app import create_test_app
from tests.test_helpers import get_request_functions_names


class TestTraces(unittest.TestCase):
    trace_id = "eef33c8eba4cfbacb6788f8f8189d51a"

    def setUp(self) -> None:
        self.mock_token = MagicMock()
        self.mock_span = MagicMock()
        self.propagate_patch = patch.object(
            tracing,
            "propagate",
        )
        self.mock_propagate = self.propagate_patch.start()
        self.detach_patch = patch.object(
            tracing,
            "detach",
        )
        self.mock_detach = self.detach_patch.start()
        self.attach_patch = patch.object(
            tracing,
            "attach",
        )
        self.mock_attach = self.attach_patch.start()
        self.req_inst_patch = patch.object(
            tracing,
            "RequestsInstrumentor",
        )
        self.mock_request_instrumentor = self.req_inst_patch.start()
        self.flask_inst_patch = patch.object(
            tracing,
            "FlaskInstrumentor",
        )
        self.mock_flask_instrumentor = self.flask_inst_patch.start()
        self.cur_span_patch = patch.object(
            tracing,
            "get_current_span",
        )
        self.mock_get_current_span = self.cur_span_patch.start()
        self.tracing_patch = patch.object(
            tracing,
            "TRACING_ENABLED",
            True,
        )
        self.mock_tracing = self.tracing_patch.start()

        # Once everything is patched, start the app
        self.app = create_test_app()

    def tearDown(self) -> None:
        for patcher in (
            self.flask_inst_patch,
            self.req_inst_patch,
            self.propagate_patch,
            self.attach_patch,
            self.detach_patch,
            self.cur_span_patch,
            self.tracing_patch,
        ):
            patcher.stop()

        for mock in (
            self.mock_token,
            self.mock_span,
            self.mock_propagate,
            self.mock_attach,
            self.mock_detach,
            self.mock_flask_instrumentor,
            self.mock_request_instrumentor,
            self.mock_get_current_span,
        ):
            mock.reset_mock()

    def _mock_get_trace_id(self, id: str) -> None:
        mock_span_context = MagicMock()
        mock_span_context.trace_id = int(id, 16)

        self.mock_span.get_span_context.return_value = mock_span_context
        self.mock_get_current_span.return_value = self.mock_span

    def test_get_trace_id(self) -> None:
        self._mock_get_trace_id(TestTraces.trace_id)

        trace_id = tracing.get_trace_id()
        self.assertEqual(trace_id, TestTraces.trace_id)

    def test_register_traces(self) -> None:
        self.mock_flask_instrumentor.assert_called_once()
        self.mock_request_instrumentor.assert_called_once()

        before_request_functions = get_request_functions_names(
            self.app.before_request_funcs
        )
        after_request_functions = get_request_functions_names(
            self.app.after_request_funcs
        )
        teardown_request_functions = get_request_functions_names(
            self.app.teardown_request_funcs
        )

        self.assertIn("extract_trace_context", before_request_functions)
        self.assertIn("add_trace_id_header", after_request_functions)
        self.assertIn("detach_trace_context", teardown_request_functions)

    def test_request_hook(self) -> None:
        mock_flask_instrumentor_instance = (
            self.mock_flask_instrumentor.return_value
        )
        mock_flask_instrumentor_instance.instrument_app.assert_called_with(
            self.app,
            excluded_urls="/_status",
            request_hook=tracing.request_hook,
        )
        mock_requests_instrumentor_instance = (
            self.mock_request_instrumentor.return_value
        )
        mock_requests_instrumentor_instance.instrument.assert_called_with()

        self.mock_span.is_recording.return_value = True
        environ = {
            "REQUEST_METHOD": "GET",
            "PATH_INFO": "/test",
        }

        tracing.request_hook(self.mock_span, environ)
        self.mock_span.update_name.assert_called_once_with("GET /test")

    def test_extract_trace_context(self) -> None:
        with self.app.test_request_context(
            "/", headers={"traceparent": "long_hex_string"}
        ):
            context_mock = MagicMock()
            self.mock_propagate.extract.return_value = context_mock
            self.mock_attach.return_value = self.mock_token

            tracing.extract_trace_context()

            self.mock_propagate.extract.assert_called_once_with(
                {"traceparent": "long_hex_string"}
            )
            self.mock_attach.assert_called_once_with(context_mock)
            self.assertIs(g._otel_token, self.mock_token)

    def test_add_trace_id_header(self) -> None:
        response = Response(status=200, headers={})
        self._mock_get_trace_id(TestTraces.trace_id)

        tracing.add_trace_id_header(response)

        self.assertEqual(
            response.headers.get("X-Request-ID"), TestTraces.trace_id
        )

    def test_detach_trace_context(self) -> None:
        with self.app.app_context():
            g._otel_token = self.mock_token

            tracing.detach_trace_context()

            self.mock_detach.assert_called_once_with(self.mock_token)


class TestNoTracing(unittest.TestCase):
    @patch("opentelemetry.instrumentation.flask.FlaskInstrumentor")
    @patch("opentelemetry.instrumentation.requests.RequestsInstrumentor")
    def test_tracing_not_enabled(
        self,
        mock_requests_instrument,
        mock_flask_instrument,
    ) -> None:
        app = create_test_app()
        before_request_functions = get_request_functions_names(
            app.before_request_funcs
        )
        after_request_functions = get_request_functions_names(
            app.after_request_funcs
        )
        teardown_request_functions = get_request_functions_names(
            app.teardown_request_funcs
        )

        self.assertNotIn("extract_trace_context", before_request_functions)
        self.assertNotIn("add_trace_id_header", after_request_functions)
        self.assertNotIn("detach_trace_context", teardown_request_functions)

        mock_requests_instrument.assert_not_called()
        mock_flask_instrument.assert_not_called()
