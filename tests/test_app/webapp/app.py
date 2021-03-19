# Packages
import flask

# Local modules
from canonicalwebteam.flask_base.app import FlaskBase


def create_test_app():
    app = FlaskBase(
        __name__,
        "test_app",
        template_folder="../templates",
        template_404="404.html",
        template_500="500.html",
    )

    @app.route("/")
    @app.route("/page")
    def page():
        return "page"

    @app.route("/auth")
    def auth():
        flask.session["test"] = True
        return "auth", 200

    @app.route("/hard-redirect")
    def hard_redirect():
        flask.session["test"] = True
        return "Moved Permanently", 301

    @app.route("/soft-redirect")
    def soft_redirect():
        flask.session["test"] = True
        return "Found", 302

    @app.route("/cache/max-age")
    def cache_max_age():
        response = flask.make_response()
        response.cache_control.max_age = 4321

        return response, 200

    @app.route("/cache/none")
    def cache_empty():
        response = flask.make_response()
        response.cache_control.max_age = None
        response.cache_control._set_cache_value(
            "stale-while-revalidate", None, int
        )
        response.cache_control._set_cache_value("stale-if-error", None, int)

        return response, 200

    @app.route("/cache/stale")
    def cache_stale():
        response = flask.make_response()
        response.cache_control._set_cache_value(
            "stale-while-revalidate", 4321, int
        )

        return response, 200

    @app.route("/cache/all")
    def cache_all():
        response = flask.make_response()
        response.cache_control.max_age = 4321
        response.cache_control.public = True
        response.cache_control._set_cache_value(
            "stale-while-revalidate", 4321, int
        )
        response.cache_control._set_cache_value("stale-if-error", 4321, int)

        return response, 200

    @app.route("/error")
    def error_route():
        flask.abort(500)

    return app
