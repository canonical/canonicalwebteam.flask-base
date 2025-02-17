"""
This module provides a middleware that adjusts the WSGI environ based on
``X-Forwarded-`` headers that proxies in front of an application may
set.

When an application is running behind a proxy server, WSGI may see the
request as coming from that server rather than the real client. Proxies
set various headers to track where the request actually came from.

This is based on werkzeug's ProxyFix middleware:
https://github.com/pallets/werkzeug/blob/main/src/werkzeug/middleware/proxy_fix.py

With additional support for `X-Original-Forwarded-For` header.
"""

from __future__ import annotations

import typing as t

from werkzeug.http import parse_list_header


class ProxyFix:
    """Adjust the WSGI environ based on ``X-Forwarded-`` that proxies in
        front of the application may set.

        -   ``X-Forwarded-For`` sets ``REMOTE_ADDR``.
        -   ``X-Original-Forwarded-For`` sets ``REMOTE_ADDR``(and takes precedence over ``X-Forwarded-For`` if configured). # noqa
        -   ``X-Forwarded-Proto`` sets ``wsgi.url_scheme``.
        -   ``X-Forwarded-Host`` sets ``HTTP_HOST``, ``SERVER_NAME``
     and ``SERVER_PORT``.
        -   ``X-Forwarded-Port`` sets ``HTTP_HOST`` and ``SERVER_PORT``.
        -   ``X-Forwarded-Prefix`` sets ``SCRIPT_NAME``.

        You must tell the middleware how many proxies set each header so it
        knows what values to trust. It is a security issue to trust values
        that came from the client rather than a proxy.

        The original values of the headers are stored in the WSGI
        environ as ``werkzeug.proxy_fix.orig``, a dict.

        :param app: The WSGI application to wrap.
        :param x_for: Number of values to trust for ``X-Forwarded-For``.
        :param x_original_for: Number of values to trust for
    ``X-Original-Forwarded-For``.
        :param x_proto: Number of values to trust for ``X-Forwarded-Proto``.
        :param x_host: Number of values to trust for ``X-Forwarded-Host``.
        :param x_port: Number of values to trust for ``X-Forwarded-Port``.
        :param x_prefix: Number of values to trust for ``X-Forwarded-Prefix``.

        ```
        from werkzeug.middleware.proxy_fix import ProxyFix
        # App is behind one proxy that sets the -For and -Host headers.
        app = ProxyFix(app, x_for=1, x_host=1)
        ```
    """

    def __init__(
        self,
        app,
        x_for: int = 1,
        x_original_for: int = 0,
        x_proto: int = 1,
        x_host: int = 0,
        x_port: int = 0,
        x_prefix: int = 0,
    ) -> None:
        self.app = app
        self.x_for = x_for
        self.x_original_for = x_original_for
        self.x_proto = x_proto
        self.x_host = x_host
        self.x_port = x_port
        self.x_prefix = x_prefix

    def _get_real_value(self, trusted: int, value: str | None) -> str | None:
        """Get the real value from a list header based on the configured
        number of trusted proxies.

        :param trusted: Number of values to trust in the header.
        :param value: Comma separated list header value to parse.
        :return: The real value, or ``None`` if there are fewer values
            than the number of trusted proxies.
        """
        if not (trusted and value):
            return None
        values = parse_list_header(value)
        if len(values) >= trusted:
            return values[-trusted]
        return None

    def __call__(self, environ, start_response) -> t.Iterable[bytes]:
        """Modify the WSGI environ based on the various forwarding headers
        before calling the wrapped application. Store the original
        environ values in ``werkzeug.proxy_fix.orig``.
        """
        environ_get = environ.get
        orig_remote_addr = environ_get("REMOTE_ADDR")
        orig_wsgi_url_scheme = environ_get("wsgi.url_scheme")
        orig_http_host = environ_get("HTTP_HOST")
        environ.update(
            {
                "werkzeug.proxy_fix.orig": {
                    "REMOTE_ADDR": orig_remote_addr,
                    "wsgi.url_scheme": orig_wsgi_url_scheme,
                    "HTTP_HOST": orig_http_host,
                    "SERVER_NAME": environ_get("SERVER_NAME"),
                    "SERVER_PORT": environ_get("SERVER_PORT"),
                    "SCRIPT_NAME": environ_get("SCRIPT_NAME"),
                }
            }
        )

        # Process X-Forwarded-For
        x_for = self._get_real_value(
            self.x_for, environ_get("HTTP_X_FORWARDED_FOR")
        )
        if x_for:
            environ["REMOTE_ADDR"] = x_for

        # Process X-Original-Forwarded-For.
        # If present, this header takes precedence over X-Forwarded-For.
        x_original_for = self._get_real_value(
            self.x_original_for, environ_get("HTTP_X_ORIGINAL_FORWARDED_FOR")
        )
        if x_original_for:
            environ["REMOTE_ADDR"] = x_original_for

        x_proto = self._get_real_value(
            self.x_proto, environ_get("HTTP_X_FORWARDED_PROTO")
        )
        if x_proto:
            environ["wsgi.url_scheme"] = x_proto

        x_host = self._get_real_value(
            self.x_host, environ_get("HTTP_X_FORWARDED_HOST")
        )
        if x_host:
            environ["HTTP_HOST"] = environ["SERVER_NAME"] = x_host
            # If the host contains a port
            # (and isn't an IPv6 literal without a port),
            # split it out.
            if ":" in x_host and not x_host.endswith("]"):
                environ["SERVER_NAME"], environ["SERVER_PORT"] = x_host.rsplit(
                    ":", 1
                )

        x_port = self._get_real_value(
            self.x_port, environ_get("HTTP_X_FORWARDED_PORT")
        )
        if x_port:
            host = environ.get("HTTP_HOST")
            if host:
                # If the host contains a port
                # (and isn't an IPv6 literal without a port),
                # remove the existing port before appending the new one.
                if ":" in host and not host.endswith("]"):
                    host = host.rsplit(":", 1)[0]
                environ["HTTP_HOST"] = f"{host}:{x_port}"
            environ["SERVER_PORT"] = x_port

        x_prefix = self._get_real_value(
            self.x_prefix, environ_get("HTTP_X_FORWARDED_PREFIX")
        )
        if x_prefix:
            environ["SCRIPT_NAME"] = x_prefix

        return self.app(environ, start_response)
