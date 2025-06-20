from os import environ


def get_flask_env(key: str, default=None, error=False) -> str | None:
    """Return the value of KEY or FLASK_KEY, otherwise, return
    a default.
    If neither is found and error is True, raise a KeyError.

    :param key: The environment variable key to look for.
    :param default: The default value to return if the key is not found.
    :param error: If True, raise a KeyError if the key is not found.
    """
    value = environ.get(key, environ.get(f"FLASK_{key}", default))
    if not value and error:
        message = f"Environment variable '{key}' not found."
        raise KeyError(message)
    return value


def load_plain_env_variables() -> None:
    """Load environment variables prefixed with 'FLASK_' from the environment,
    strip the prefix and update the environment with the plain variables.
    """
    flask_env_vars = {}
    for k, v in environ.items():
        # Filter for variables that exist and start with 'FLASK_'
        if k.startswith("FLASK_") and v:
            # Remove the 'FLASK_' prefix and update the environment
            flask_env_vars[k[6:]] = v

    # Update the environment with the plain variables
    environ.update(flask_env_vars)
