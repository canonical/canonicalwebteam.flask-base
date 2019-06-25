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

    @app.route("/error")
    def error_route():
        flask.abort(500)

    return app
