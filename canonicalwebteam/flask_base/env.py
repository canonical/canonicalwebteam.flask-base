from os import environ


def get_flask_env(key: str, default=None) -> str | None:
    """Return the value of KEY or FLASK_KEY, otherwise, return
    a default.
    """
    return environ.get(key, environ.get(f"FLASK_{key}", default))


def load_plain_env_variables() -> None:
    """Load environment variables prefixed with 'FLASK_' from the environment,
    and update the environment with the plain variables.
    """
    flask_env_vars = {}
    for k, v in environ.items():
        # Filter for variables that exist and start with 'FLASK_'
        if k.startswith("FLASK_") and v:
            # Remove the 'FLASK_' prefix and update the environment
            flask_env_vars[k[6:]] = v

    # Update the environment with the plain variables
    environ.update(flask_env_vars)
