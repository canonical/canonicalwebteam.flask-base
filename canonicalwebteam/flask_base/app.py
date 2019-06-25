# Standard library
import os

# Packages
import flask
import talisker.flask
from werkzeug.contrib.fixers import ProxyFix
from werkzeug.debug import DebuggedApplication

# Local modules
from canonicalwebteam.flask_base.context import (
    base_context,
    clear_trailing_slash,
)
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

        self.before_request(clear_trailing_slash)

        self.before_request(
            prepare_redirects(
                path=os.path.join(self.root_path, "..", "redirects.yaml")
            )
        )
        self.before_request(
            prepare_redirects(
                path=os.path.join(
                    self.root_path, "..", "permanent-redirects.yaml"
                ),
                permanent=True,
            )
        )
        self.before_request(
            prepare_deleted(
                path=os.path.join(self.root_path, "..", "deleted.yaml")
            )
        )

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

        robots_path = os.path.join(self.root_path, "..", "robots.txt")
        humans_path = os.path.join(self.root_path, "..", "humans.txt")

        if os.path.isfile(robots_path):

            @self.route("/robots.txt")
            def robots():
                return flask.send_file(robots_path)

        if os.path.isfile(humans_path):

            @self.route("/humans.txt")
            def humans():
                return flask.send_file(humans_path)
