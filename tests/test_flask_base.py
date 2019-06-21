# Standard library
import os
import unittest
from contextlib import contextmanager

# Packages
import flask
import talisker.testing
from werkzeug.contrib.fixers import ProxyFix
from werkzeug.debug import DebuggedApplication

# Local modules
from canonicalwebteam.flask_base.app import FlaskBase


@contextmanager
def cwd(path):
    """
    Context manager for temporarily changing directory
    """

    oldpwd = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(oldpwd)


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
        with cwd("tests/test-app"):
            os.environ["FLASK_DEBUG"] = "True"
            app = FlaskBase(__name__, "canonicalwebteam.flask-base")
            app.root_path = os.getcwd()

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

    def test_favicon_redirect(self):
        """
        If `favicon_url` is provided, check requests to `/favicon.ico`
        receive a redirect
        """

        external_url = "https://example.com/icos/favcon"
        local_url = "/static/some-image.ico"

        external_app = FlaskBase(
            __name__, "canonicalwebteam.flask-base", favicon_url=external_url
        )
        local_app = FlaskBase(
            __name__, "canonicalwebteam.flask-base", favicon_url=local_url
        )

        with external_app.test_client() as client:
            response = client.get("/favicon.ico")
            self.assertEqual(302, response.status_code)
            self.assertEqual(response.headers.get("Location"), external_url)

        with local_app.test_client() as client:
            response = client.get("/favicon.ico")
            self.assertEqual(302, response.status_code)
            self.assertEqual(
                response.headers.get("Location"),
                "http://localhost" + local_url,
            )

    def test_robots_redirect(self):
        """
        If `robots_url` is provided, check requests to `/robots.txt`
        receive a redirect
        """

        external_url = "https://example.com/files/robots"
        local_url = "/static/robo.txt"

        external_app = FlaskBase(
            __name__, "canonicalwebteam.flask-base", favicon_url=external_url
        )
        local_app = FlaskBase(
            __name__, "canonicalwebteam.flask-base", favicon_url=local_url
        )

        with external_app.test_client() as client:
            response = client.get("/favicon.ico")
            self.assertEqual(302, response.status_code)
            self.assertEqual(response.headers.get("Location"), external_url)

        with local_app.test_client() as client:
            response = client.get("/favicon.ico")
            self.assertEqual(302, response.status_code)
            self.assertEqual(
                response.headers.get("Location"),
                "http://localhost" + local_url,
            )

    def test_humans_redirect(self):
        """
        If `humans_url` is provided, check requests to `/humans.txt`
        receive a redirect
        """

        external_url = "https://example.com/files/humans"
        local_url = "/static/people.txt"

        external_app = FlaskBase(
            __name__, "canonicalwebteam.flask-base", favicon_url=external_url
        )
        local_app = FlaskBase(
            __name__, "canonicalwebteam.flask-base", favicon_url=local_url
        )

        with external_app.test_client() as client:
            response = client.get("/favicon.ico")
            self.assertEqual(302, response.status_code)
            self.assertEqual(response.headers.get("Location"), external_url)

        with local_app.test_client() as client:
            response = client.get("/favicon.ico")
            self.assertEqual(302, response.status_code)
            self.assertEqual(
                response.headers.get("Location"),
                "http://localhost" + local_url,
            )

    def test_error_pages(self):
        """
        If "404.html" and "500.html" are provided as templates,
        check we get the response from those templates when we get an error
        """

        with cwd("tests/test-app"):
            app = FlaskBase(
                __name__,
                "canonicalwebteam.flask-base",
                template_404="404.html",
                template_500="500.html",
            )
            app.root_path = os.getcwd()

            @app.route("/error")
            def error_route():
                flask.abort(500)

            with app.test_client() as client:
                response = client.get("non-existent-page")
                self.assertEqual(404, response.status_code)
                self.assertEqual(response.data, b"error 404")

                response = client.get("error")
                self.assertEqual(500, response.status_code)
                self.assertEqual(response.data, b"error 500")


if __name__ == "__main__":
    unittest.main()
