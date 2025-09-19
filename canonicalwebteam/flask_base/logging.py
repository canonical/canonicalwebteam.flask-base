import logging
import datetime
import json
from typing import List
from functools import lru_cache

from flask import Flask
from rich.logging import RichHandler
from pythonjsonlogger.json import JsonFormatter
from gunicorn.glogging import Logger as GunicornLogger


DEFAULT_DEV_FORMAT = "[%(name)s] [%(threadName)s] %(message)s"

def _date_format_with_ms(dt: datetime.datetime):
    return dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


class ExtraRichFormatter(logging.Formatter):
    """
    This formatter takes care of printing the dictionary passed as 'extra' to
    the logging calls.
    """
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

    def _get_extra_dict(self, record: logging.LogRecord) -> dict | None:
        extra_dict = {}
        for key, value in record.__dict__.items():
            if (
                key not in ExtraRichFormatter.RESERVED_ATTRS
                and not key.startswith("_")
            ):
                extra_dict[key] = value

        return None if len(extra_dict) == 0 else extra_dict


class GUnicornDevLogger(GunicornLogger):
    """
    This logger use is optional and serves to display Gunicorn logs in the
    same style as the default development application logs.
    The way to use it is specified in the README.

    MUST NOT BE USED in production.
    """

    def __init__(self, cfg):
        super().__init__(cfg)
    
    def setup(self, _):
        self.error_log.addHandler(get_default_dev_handler())
        access_handler = RichHandler(
            omit_repeated_times=False,
            log_time_format=_date_format_with_ms,
        )
        access_handler.setFormatter(logging.Formatter(
            fmt=DEFAULT_DEV_FORMAT,
        ))
        self.access_log.addHandler(access_handler)


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
    return rich_handler

@lru_cache(maxsize=1)
def get_default_prod_handler() -> logging.Handler:
    """
    Handler to be used in production. Provides structured JSON logging.
    """
    log_handler = logging.StreamHandler()
    formatter = JsonFormatter()
    log_handler.setFormatter(formatter)
    return log_handler


def setup_root_logger(app: Flask, handler: logging.Handler | None = None):
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    if handler is not None:
        root_logger.addHandler(handler)
        return

    if app.debug:
        root_logger.addHandler(get_default_dev_handler())
        root_logger.setLevel(logging.DEBUG)
    else:
        root_logger.addHandler(get_default_prod_handler())
