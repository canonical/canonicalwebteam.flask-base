# Canonical Webteam Flask-Base
Flask extension that applies common configurations to all of webteam's flask apps.

## Usage
```python
from canonicalwebteam.flask_base.app import FlaskBase

app = FlaskBase(__name__, "app.name")
```

FlaskBase uses [yaml-responses](https://github.com/canonical-web-and-design/canonicalwebteam.yaml-responses)
to allow easy configuration of redirects and return of deleted responses.
In case you need to customize the behaviour of any of these actions you can initialize your app with custom callbacks.

```python
from canonicalwebteam.flask_base.app import FlaskBase

app = FlaskBase(
    __name__,
    "app.name"
    prepare_deleted=your_deleted_callback,
    prepare_redirects=your_redirect_callback,
)
```

## Tests
To run the tests execute `poetry run python -m unittest discover tests`.
