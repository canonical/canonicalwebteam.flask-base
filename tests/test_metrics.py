import time
import unittest
from unittest.mock import patch

from flask import g, request

from tests.test_app.webapp.app import create_test_app
from tests.test_helpers import get_request_functions_names


class TestMetrics(unittest.TestCase):
    def setUp(self) -> None:
        self.app = create_test_app()

    def test_register_metrics(self) -> None:
        before_request_functions = get_request_functions_names(
            self.app.before_request_funcs
        )
        after_request_functions = get_request_functions_names(
            self.app.after_request_funcs
        )
        teardown_request_functions = get_request_functions_names(
            self.app.teardown_request_funcs
        )
        self.assertIn("start_timer", before_request_functions)
        self.assertIn("record_metrics", after_request_functions)
        self.assertIn("handle_teardown", teardown_request_functions)

    def test_start_timer(self) -> None:
        with self.app.test_client() as client:
            client.get("/page")
            time.sleep(0.1)
            self.assertGreater(time.time(), g.start_time)

    @patch(
        (
            "canonicalwebteam.flask_base.opentelemetry."
            "metrics.RequestsMetrics.requests"
        )
    )
    @patch(
        (
            "canonicalwebteam.flask_base.opentelemetry."
            "metrics.RequestsMetrics.latency"
        )
    )
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

    @patch(
        (
            "canonicalwebteam.flask_base.opentelemetry."
            "metrics.RequestsMetrics.errors"
        )
    )
    def test_handle_teardown(self, mock_errors) -> None:
        with self.app.test_client() as client:
            # avoid printing the exception in the log
            self.app.logger.setLevel("CRITICAL")

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
