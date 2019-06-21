# Standard library
import os

# Packages
import flask
import talisker.flask
from werkzeug.contrib.fixers import ProxyFix
from werkzeug.debug import DebuggedApplication

# Local modules
from canonicalwebteam.flask_base.context import base_context
from canonicalwebteam.flask_base.converters import RegexConverter
from canonicalwebteam.yaml_responses.flask_helpers import (
    prepare_deleted,
    prepare_redirects,
)


class FlaskBase(flask.Flask):
    def __init__(
        self,
        name,
        service,
        favicon_url=None,
        template_404=None,
        template_500=None,
        robots_url=None,
        humans_url=None,
        *args,
        **kwargs
    ):
        super().__init__(name, *args, **kwargs)

        self.service = service

        self.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "base_secret")

        self.url_map.strict_slashes = False
        self.url_map.converters["regex"] = RegexConverter

        self.wsgi_app = ProxyFix(self.wsgi_app)

        if self.debug:
            self.wsgi_app = DebuggedApplication(self.wsgi_app)

        self.before_request(prepare_redirects())
        self.before_request(prepare_deleted())

        self.context_processor(base_context)

        talisker.flask.register(self)
        talisker.logs.set_global_extra({"service": self.service})

        # Default error handlers
        if template_404:

            @self.errorhandler(404)
            def not_found_error(error):
                return flask.render_template(template_404), 404

        if template_500:

            @self.errorhandler(500)
            def internal_error(error):
                return flask.render_template(template_500), 500

        # Default routes
        if favicon_url:

            @self.route("/favicon.ico")
            def favicon():
                return flask.redirect(favicon_url)

        if robots_url:

            @self.route("/robots.txt")
            def robots():
                return flask.redirect(robots_url)

        if humans_url:

            @self.route("/humans.txt")
            def humans():
                return flask.redirect(humans_url)
