import logging
import datetime
import json
from functools import lru_cache

from flask import Flask
from rich.logging import RichHandler
from rich.text import Text
from pythonjsonlogger.json import JsonFormatter
from pythonjsonlogger.core import RESERVED_ATTRS
from gunicorn.glogging import Logger as GunicornLogger

from canonicalwebteam.flask_base.env import get_flask_env
from canonicalwebteam.flask_base.opentelemetry.tracing import get_trace_id


def _date_format_with_ms(dt: datetime.datetime) -> Text:
    return Text(dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3])


class RequestTraceIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        trace_id = get_trace_id()
        if trace_id:
            record.trace_id = trace_id
        return True


class ExtraRichFormatter(logging.Formatter):
    """
    This formatter takes care of printing the dictionary passed as 'extra' to
    the logging calls.
    """

    def __init__(self, fmt=None, datefmt=None):
        super().__init__(fmt, datefmt)

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        extra_data = self._get_extra_dict(record)
        if extra_data:
            json_str = json.dumps(extra_data, indent=2, ensure_ascii=False)
            return f"{message}\n{json_str}"
        return message

    def _get_extra_dict(self, record: logging.LogRecord) -> dict:
        extra_dict = {}
        for key, value in record.__dict__.items():
            if key not in RESERVED_ATTRS and not key.startswith("_"):
                extra_dict[key] = value

        return extra_dict


class GunicornDevLogger(GunicornLogger):
    """
    This logger use is optional and serves to display Gunicorn logs in the
    same style as the default development application logs.
    The way to use it is specified in the README.

    MUST NOT BE USED in production.
    """

    def __init__(self, cfg):
        super().__init__(cfg)

    def setup(self, cfg):
        super().setup(cfg)
        self._substitute_stream_by_rich(self.error_log)
        self._substitute_stream_by_rich(self.access_log)

    def _substitute_stream_by_rich(self, logger):
        for handler in list(logger.handlers):
            if isinstance(handler, logging.StreamHandler):
                logger.removeHandler(handler)
                logger.addHandler(get_default_dev_handler())


# Handlers (just one of each)


@lru_cache(maxsize=1)
def get_default_dev_handler() -> logging.Handler:
    """
    Handler to be used in development mode to get nice colored logs
    """
    rich_handler = RichHandler(
        omit_repeated_times=False,
        rich_tracebacks=True,
        tracebacks_show_locals=True,
        log_time_format=_date_format_with_ms,
    )
    rich_handler.setFormatter(
        ExtraRichFormatter(
            fmt="[%(name)s] %(message)s",
        )
    )
    rich_handler.addFilter(RequestTraceIdFilter())
    return rich_handler


@lru_cache(maxsize=1)
def get_default_prod_handler() -> logging.Handler:
    """
    Handler to be used in production. Provides structured JSON logging.
    """
    log_handler = logging.StreamHandler()
    formatter = JsonFormatter(
        # the order of the format string doesn't matter
        # it just needs to include the fields that you want in the output
        # this is just for the default LogRecord attributes
        # for custom ones like "trace_id" check the RequestTraceIdFilter class
        fmt="%(levelname)s:%(message)s",
        rename_fields={"levelname": "level"},
        timestamp=True,
    )
    log_handler.setFormatter(formatter)
    log_handler.addFilter(RequestTraceIdFilter())
    return log_handler


def is_debug_environment():
    debug_value = get_flask_env("DEBUG")
    return debug_value is not None and debug_value.lower() == "true"


def setup_root_logger(app: Flask, handler: logging.Handler | None = None):
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_handler = None

    if handler is not None:
        root_handler = handler
    elif is_debug_environment():
        root_handler = get_default_dev_handler()
        root_logger.setLevel(logging.DEBUG)
    else:
        root_handler = get_default_prod_handler()

    root_logger.addHandler(root_handler)
