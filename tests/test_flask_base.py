import os
import unittest

import talisker.testing
from werkzeug.contrib.fixers import ProxyFix
from werkzeug.debug import DebuggedApplication

from canonicalwebteam.flask_base.app import FlaskBase
from canonicalwebteam.yaml_responses.flask_helpers import (
    prepare_deleted,
    prepare_redirects,
)


class TestFlaskBase(unittest.TestCase):
    def setUp(self):
        talisker.testing.configure_testing()

    def create_app(self, debug="False"):
        os.environ["FLASK_DEBUG"] = debug
        app = FlaskBase(__name__, "canonicalwebteam.flask-base")
        return app

    def test_flask_base_inits(self):
        app = self.create_app()
        self.assertEqual(app.service, "canonicalwebteam.flask-base")

    def test_debug_wsgi_app(self):
        app = self.create_app(debug="True")
        self.assertIsInstance(app.wsgi_app, DebuggedApplication)

    def test_wsgi_app(self):
        app = self.create_app()
        self.assertIsInstance(app.wsgi_app, ProxyFix)

    def test_adds_redirects(self):
        def _deleted_callback(context):
            return "Deleted", 410

        p_deleted = prepare_deleted(
            path="./tests/deleted.yaml", view_callback=_deleted_callback
        )
        p_redirects = prepare_redirects(path="./tests/redirects.yaml")

        app = FlaskBase(
            __name__, "canonicalwebteam.flask-base", p_deleted, p_redirects
        )

        with app.test_client() as client:
            response = client.get("redirect")
            self.assertEqual(302, response.status_code)
            self.assertEqual(
                response.headers.get("Location"), "https://httpbin.org/"
            )

            response = client.get("deleted")
            self.assertEqual(410, response.status_code)
            self.assertEqual(response.data, b"Deleted")

    def test_logs_service_name(self):
        with talisker.testing.TestContext() as ctx:
            app = self.create_app()
            app.logger.info("Test")
            ctx.assert_log(
                msg="Test", extra={"service": "canonicalwebteam.flask-base"}
            )

    def test_global_context(self):
        app = self.create_app()
        context_processors = app.template_context_processors[None]

        # Flask adds it's own context_processor so we should have 2
        self.assertEqual(len(context_processors), 2)

        # We retrieve our base context from the second position
        base_context = context_processors[1]()

        self.assertIn("now", base_context.keys())
        self.assertIn("versioned_static", base_context.keys())


if __name__ == "__main__":
    unittest.main()
