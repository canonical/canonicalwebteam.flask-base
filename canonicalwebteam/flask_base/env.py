from os import environ


def get_flask_env(key: str, default=None) -> str | None:
    """Return the value of KEY or FLASK_KEY, otherwise, return
    a default.
    """
    return environ.get(key, environ.get(f"FLASK_{key}", default))
