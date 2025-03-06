# Standard library
import os
import unittest
import warnings
from contextlib import contextmanager

# Packages
import talisker.testing
from werkzeug.debug import DebuggedApplication

# Local modules
from canonicalwebteam.flask_base.app import FlaskBase
from canonicalwebteam.flask_base.middlewares.proxy_fix import ProxyFix
from tests.test_app.webapp.app import create_test_app


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

    def create_app(self, debug=False):
        if debug:
            os.environ["FLASK_DEBUG"] = "true"
        else:
            os.environ.pop("FLASK_DEBUG", None)
        app = FlaskBase(__name__, "canonicalwebteam.flask-base")
        return app

    def test_flask_base_inits(self):
        app = self.create_app()
        self.assertEqual(app.service, "canonicalwebteam.flask-base")

    def test_debug_wsgi_app(self):
        app = self.create_app(debug=True)
        self.assertIsInstance(app.wsgi_app.app, DebuggedApplication)

    def test_wsgi_app(self):
        app = self.create_app()
        self.assertIsInstance(app.wsgi_app, ProxyFix)

    def test_security_headers(self):
        with create_test_app().test_client() as client:
            response = client.get("page")
            self.assertEqual(
                response.headers.get("X-Frame-Options"),
                "SAMEORIGIN",
            )

    def test_default_cache_headers(self):
        with create_test_app().test_client() as client:
            cached_response = client.get("page")
            cache = cached_response.headers.get("Cache-Control")
            self.assertNotIn("public", cache)
            self.assertIn("max-age=60", cache)
            self.assertIn("stale-while-revalidate=86400", cache)
            self.assertIn("stale-if-error=300", cache)

    def test_redirects_have_no_cache_headers(self):
        with create_test_app().test_client() as client:
            soft_redirect = client.get("soft-redirect")
            hard_redirect = client.get("hard-redirect")
            self.assertTrue("Cache-Control" not in soft_redirect.headers)
            self.assertTrue("Cache-Control" not in hard_redirect.headers)

    def test_vary_cookie_when_session(self):
        with create_test_app().test_client() as client:
            cached_response_with_session = client.get("auth")
            self.assertEqual(
                cached_response_with_session.headers.get("Vary"),
                "Accept-Encoding, Cookie",
            )

    def test_cache_override(self):
        """
        Check each part of the cache-control instruction can be overridden
        individually, or nullified
        """

        with create_test_app().test_client() as client:
            # all 3 values are overriden, and "public" is added
            all_response = client.get("cache/all")
            all_cache = all_response.headers.get("Cache-Control")
            self.assertIn("public", all_cache)
            self.assertIn("max-age=4321", all_cache)
            self.assertIn("stale-while-revalidate=4321", all_cache)
            self.assertIn("stale-if-error=4321", all_cache)

            # all values are set to zero
            zero_response = client.get("cache/zero")
            zero_cache = zero_response.headers.get("Cache-Control")
            self.assertIn("max-age=0", zero_cache)
            self.assertIn("stale-while-revalidate=0", zero_cache)
            self.assertIn("stale-if-error=0", zero_cache)

            # only max-age is overridden, so the "stale" instructions remain
            max_age_response = client.get("cache/max-age")
            max_age_cache = max_age_response.headers.get("Cache-Control")
            self.assertNotIn("public", max_age_cache)
            self.assertIn("max-age=4321", max_age_cache)
            self.assertIn("stale-while-revalidate=86400", max_age_cache)
            self.assertIn("stale-if-error=300", max_age_cache)

            # only "stale-while-revalidate" is overridden
            stale_response = client.get("cache/stale")
            stale_cache = stale_response.headers.get("Cache-Control")
            self.assertNotIn("public", stale_cache)
            self.assertIn("max-age=60", stale_cache)
            self.assertIn("stale-while-revalidate=4321", stale_cache)
            self.assertIn("stale-if-error=300", stale_cache)

    def test_status_endpoints(self):
        with create_test_app().test_client() as client:
            response = client.get("_status/check")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data.decode(), "OK")
            self.assertEqual(response.headers.get("Cache-Control"), "no-store")

    def test_redirects_deleted(self):
        """
        Check test_app/{redirects,permanent-redirects,deleted}.yaml
        are processed correctly
        """

        with create_test_app().test_client() as client:
            redirect_response = client.get("redirect")
            self.assertEqual(302, redirect_response.status_code)
            self.assertEqual(
                redirect_response.headers.get("Location"),
                "https://httpbin.org/",
            )

            permanent_response = client.get("permanent-redirect")
            self.assertEqual(301, permanent_response.status_code)
            self.assertEqual(
                permanent_response.headers.get("Location"),
                "https://example.com/",
            )

            deleted_response = client.get("deleted")
            self.assertEqual(410, deleted_response.status_code)
            self.assertEqual(deleted_response.data, b"Deleted")

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
                local_url,
            )

    def test_favicon_serve(self):
        """
        If `favicon_url` is provided, check requests to `/favicon.ico`
        receive a redirect
        """

        local_app = create_test_app()

        with local_app.test_client() as client:
            response = client.get("/favicon.ico")
            self.assertEqual(200, response.status_code)

    def test_text_files(self):
        """
        If `robots.txt`, `humans.txt`, `security.txt` are provided at the root
        of the project, check requests to `/robots.txt` load the content
        """

        with create_test_app().test_client() as client:
            warnings.simplefilter("ignore", ResourceWarning)
            robots_response = client.get("robots.txt")
            humans_response = client.get("humans.txt")
            security_response = client.get("/.well-known/security.txt")
            self.assertEqual(200, robots_response.status_code)
            self.assertEqual(200, humans_response.status_code)
            self.assertEqual(200, security_response.status_code)
            self.assertEqual(robots_response.data, b"robots!")
            self.assertEqual(humans_response.data, b"humans!")
            self.assertEqual(
                security_response.data, b"security is very important!"
            )

    def test_error_pages(self):
        """
        If "404.html" and "500.html" are provided as templates,
        check we get the response from those templates when we get an error
        """

        with create_test_app().test_client() as client:
            response = client.get("non-existent-page")
            self.assertEqual(404, response.status_code)
            self.assertEqual(response.data, b"error 404")

            response = client.get("error")
            self.assertEqual(500, response.status_code)
            self.assertEqual(response.data, b"error 500")

    def test_clear_trailing_slash(self):
        with create_test_app().test_client() as client:
            response = client.get("/")
            self.assertEqual(200, response.status_code)

            response = client.get("/page")
            self.assertEqual(200, response.status_code)

            response = client.get("/page/")
            self.assertEqual(302, response.status_code)
            self.assertEqual(
                "http://localhost/page", response.headers.get("Location")
            )

    def test_static_files(self):
        flask_app = create_test_app()
        flask_app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 31536000  # 1 year

        with flask_app.test_client() as client:
            # Check basic serving of static files works
            # status is 200, contents matches and cache is as expected
            plain_response = client.get("static/test.json")
            plain_cache = plain_response.headers.get("Cache-Control")

            self.assertEqual(plain_response.status_code, 200)
            self.assertEqual(plain_response.json["fish"], "chips")
            self.assertIn("public", plain_cache)

            max_age = flask_app.config["SEND_FILE_MAX_AGE_DEFAULT"]
            if max_age:
                self.assertIn(f"max-age={max_age}", plain_cache)
            else:
                self.assertIn("max-age=60", plain_cache)

            # Check hashed content is served with a year-long cache
            hash_response = client.get("static/test.json?v=527d233")
            hash_cache = hash_response.headers.get("Cache-Control")
            self.assertEqual(hash_response.status_code, 200)
            self.assertEqual(hash_response.json["fish"], "chips")
            self.assertIn("public", hash_cache)
            self.assertIn("max-age=31536000", hash_cache)

            # Check when hash doesn't match, we get a 404
            not_found_response = client.get("static/test.json?v=527d234")
            self.assertEqual(not_found_response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
