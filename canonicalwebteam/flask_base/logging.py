import logging
import datetime
import json
import time
from typing import List
from functools import lru_cache

from flask import Flask, has_request_context
from rich.logging import RichHandler
from pythonjsonlogger.json import JsonFormatter
from gunicorn.glogging import Logger as GunicornLogger

from canonicalwebteam.flask_base.env import get_flask_env
from canonicalwebteam.flask_base.observability import get_trace_id


DEFAULT_DEV_FORMAT = "[%(name)s] %(message)s"


def _date_format_with_ms(dt: datetime.datetime):
    return dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


class RequestFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        trace_id = get_trace_id()
        if trace_id:
            record.trace_id = trace_id
        return True


class ProdRequestFilter(RequestFilter):
    def __init__(self, datefmt: str | None = None):
        self.datefmt = datefmt or logging.Formatter.default_time_format
        self.msecfmt = str(logging.Formatter.default_msec_format)

    def filter(self, record: logging.LogRecord) -> bool:
        super().filter(record)
        record.timestamp = self._format_timestamp(record)
        record.level = record.levelname
        return True

    def _format_timestamp(self, record: logging.LogRecord):
        date_hour = time.strftime(
            self.datefmt, time.localtime(record.created)
        )
        return self.msecfmt % (date_hour, record.msecs)


class ExtraRichFormatter(logging.Formatter):
    """
    This formatter takes care of printing the dictionary passed as 'extra' to
    the logging calls.
    """

    # Obtained from Python's documentation and python-json-logger
    # https://docs.python.org/3/library/logging.html#logrecord-attributes
    # https://github.com/nhairs/python-json-logger/blob/main/src/pythonjsonlogger/core.py
    RESERVED_ATTRS: List[str] = [
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "message",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
        "taskName",
    ]

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
            if (
                key not in ExtraRichFormatter.RESERVED_ATTRS
                and not key.startswith("_")
            ):
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
            fmt=DEFAULT_DEV_FORMAT,
        )
    )
    rich_handler.addFilter(RequestFilter())
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
        # for custom ones like "timestamp" check the RequestFilter class
        fmt="%(levelname)s:%(message)s",
    )
    log_handler.setFormatter(formatter)
    log_handler.addFilter(ProdRequestFilter())
    return log_handler


@lru_cache(maxsize=1)
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
