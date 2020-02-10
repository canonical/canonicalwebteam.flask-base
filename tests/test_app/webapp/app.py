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

    @app.route("/cache")
    def cache():
        response = flask.make_response()
        response.cache_control.public = True
        response.cache_control.max_age = 1000

        return response, 200

    @app.route("/_status/test")
    @app.route("/_status/check")
    def status():
        return "_status", 200

    @app.route("/error")
    def error_route():
        flask.abort(500)

    return app
