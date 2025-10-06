import logging
import unittest

from unittest.mock import MagicMock, patch
from pythonjsonlogger.json import JsonFormatter

from canonicalwebteam.flask_base.log_utils import (
    ExtraRichFormatter,
    RequestTraceIdFilter,
    GunicornDevLogger,
    get_default_dev_handler,
    get_default_prod_handler,
    is_debug_environment,
    setup_root_logger,
    _date_format_with_ms,
)
from tests.test_app.webapp.app import create_test_app


class TestLogging(unittest.TestCase):
    def setUp(self) -> None:
        # necessary to clear lru_cache to avoid test pollution
        get_default_dev_handler.cache_clear()
        get_default_prod_handler.cache_clear()

    @patch("canonicalwebteam.flask_base.log_utils.get_trace_id")
    def test_request_filter(self, mock_get_trace_id) -> None:
        trace_id = "0000000000000000"
        mock_get_trace_id.return_value = trace_id
        filter = RequestTraceIdFilter()
        record = logging.makeLogRecord({})
        self.assertTrue(filter.filter(record))
        self.assertEqual(trace_id, record.__dict__.get("trace_id"))

    def test_extra_rich_formatter(self) -> None:
        logger = logging.Logger("test")
        rich_formatter = ExtraRichFormatter()
        record = logger.makeRecord(
            "test",
            logging.DEBUG,
            "",
            0,
            "message",
            (),
            None,
            "",
            {"test": 42},
            None,
        )
        self.assertEqual(
            rich_formatter.format(record), 'message\n{\n  "test": 42\n}'
        )

    @patch("canonicalwebteam.flask_base.log_utils.get_default_dev_handler")
    def test_gunicorn_dev_logger_setup(self, mock_handler) -> None:
        class Config:
            loglevel = "debug"
            errorlog = "-"

            def __getattr__(self, _):
                return None

        config = Config()
        dev_handler = MagicMock()
        mock_handler.return_value = dev_handler
        logger = GunicornDevLogger(config)
        self.assertListEqual(logger.error_log.handlers, [dev_handler])
        self.assertListEqual(logger.access_log.handlers, [dev_handler])

    @patch("canonicalwebteam.flask_base.log_utils.RichHandler")
    def test_default_dev_handler(self, mock_rich_handler) -> None:
        rich_handler_instance = MagicMock()
        mock_rich_handler.return_value = rich_handler_instance
        result = get_default_dev_handler()
        # this next call should use the lru_cache, so the methods
        # will have been called just once
        result = get_default_dev_handler()

        self.assertIs(result, rich_handler_instance)
        mock_rich_handler.assert_called_once_with(
            omit_repeated_times=False,
            rich_tracebacks=True,
            tracebacks_show_locals=True,
            log_time_format=_date_format_with_ms,
        )
        rich_handler_instance.setFormatter.assert_called_once()
        self.assertIsInstance(
            rich_handler_instance.setFormatter.call_args.args[0],
            ExtraRichFormatter,
        )
        rich_handler_instance.addFilter.assert_called_once()
        self.assertIsInstance(
            rich_handler_instance.addFilter.call_args.args[0],
            RequestTraceIdFilter,
        )

    def test_default_prod_handler(self) -> None:
        result = get_default_prod_handler()
        # this next call should use the lru_cache, so the returned result
        # should be the same
        self.assertIs(result, get_default_prod_handler())

        self.assertIsInstance(result.formatter, JsonFormatter)
        self.assertIsInstance(result.filters[0], RequestTraceIdFilter)

    @patch("canonicalwebteam.flask_base.log_utils.get_flask_env")
    def test_is_debug_environment(self, mock_get_flask_env) -> None:
        mock_get_flask_env.side_effect = ["TruE", "?", None]
        self.assertTrue(is_debug_environment())
        self.assertFalse(is_debug_environment())
        self.assertFalse(is_debug_environment())

    def test_setup_root_logger_custom_handler(self) -> None:
        app = create_test_app()
        handler = logging.Handler()
        setup_root_logger(app, handler)
        self.assertIs(logging.getLogger().handlers[0], handler)

    @patch("canonicalwebteam.flask_base.log_utils.is_debug_environment")
    def test_setup_root_logger_debug(self, mock_is_debug) -> None:
        mock_is_debug.return_value = True
        app = create_test_app()
        setup_root_logger(app)
        self.assertIs(
            logging.getLogger().handlers[0],
            get_default_dev_handler(),
        )
        self.assertEqual(logging.getLogger().level, logging.DEBUG)

    @patch("canonicalwebteam.flask_base.log_utils.is_debug_environment")
    def test_setup_root_logger_prod(self, mock_is_debug) -> None:
        mock_is_debug.return_value = False
        app = create_test_app()
        setup_root_logger(app)
        self.assertIs(
            logging.getLogger().handlers[0],
            get_default_prod_handler(),
        )
