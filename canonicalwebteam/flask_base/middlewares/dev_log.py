"""
This module provides a middleware that adjusts the WSGI environ to
include a prettified logger for development environments.
"""

import io
import typing as t

from rich.console import Console
from rich.traceback import Traceback
from rich.text import Text


class RichWSGIErrorsWrapper(io.RawIOBase):

    def __init__(self):
        # There is no public __init__ method for RawIOBase so
        # we don't need to call super() in the __init__ method.
        self.__console = Console()

    def write(self, data):
        """
        This method should be called mainly to print stack traces.
        Used by Werkzeug here:
        https://github.com/pallets/werkzeug/blob/main/src/werkzeug/debug/__init__.py#L381
        """
        rich_render = None
        try:
            traceback = Traceback(show_locals=True)
            rich_render = traceback
        except ValueError:
            # Someone tried to write outside of a except block
            rich_render = Text(data)

        self.__console.print(rich_render)


rich_wsgi_errors_wrapper = RichWSGIErrorsWrapper()


class DevLogWSGI:
    """
    Adjust the WSGI environ to modify the default "wsgi.errors" key
    that contains a File Object that writes to the stderr stream output
    and substitute it by another object that outputs text in a prettier way.
    """

    def __init__(self, app) -> None:
        self.app = app

    def __call__(self, environ, start_response) -> t.Iterable[bytes]:
        """
        Modify the WSGI environ to update the "wsgi.errors" output stream
        for a Rich equivalent that prettifies the text.
        """
        environ_get = environ.get
        error_stream = environ_get("wsgi.errors")

        environ["wsgi.errors"] = rich_wsgi_errors_wrapper

        return self.app(environ, start_response)
