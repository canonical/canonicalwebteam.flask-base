import flask
import talisker.flask

from werkzeug.contrib.fixers import ProxyFix
from werkzeug.debug import DebuggedApplication

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
        prepare_deleted=prepare_deleted(),
        prepare_redirects=prepare_redirects(),
        *args,
        **kwargs
    ):
        super().__init__(name, *args, **kwargs)

        self.service = service

        self.config.from_object(
            "canonicalwebteam.flask_base.config.BaseConfig"
        )

        self.url_map.strict_slashes = False
        self.url_map.converters["regex"] = RegexConverter

        self.wsgi_app = (
            ProxyFix(self.wsgi_app)
            if not self.debug
            else DebuggedApplication(self.wsgi_app)
        )

        self.before_request(prepare_redirects)
        self.before_request(prepare_deleted)

        talisker.flask.register(self)
        talisker.logs.set_global_extra({"service": self.service})
