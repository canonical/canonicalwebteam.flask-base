# Canonical Webteam Flask-Base

Flask extension that applies common configurations to all of webteam's flask apps.

## Usage

```python3
from canonicalwebteam.flask_base.app import FlaskBase

app = FlaskBase(__name__, "app.name")
```

Or:

```python3
from canonicalwebteam.flask_base.app import FlaskBase

app = FlaskBase(
    __name__,
    "app.name",
    template_404="404.html",
    template_500="500.html",
    favicon_url="/static/favicon.ico",
)
```

## Local development

For local development, it's best to test this module with one of our website projects like [ubuntu.com](https://github.com/canonical-web-and-design/ubuntu.com/). For more information, follow [this guide (internal only)](https://discourse.canonical.com/t/how-to-run-our-python-modules-for-local-development/308).

## Features

### Logging

Logging is divided in 2 types depending on the environment:
- Prod: uses a simple structured logging, that outputs JSON so that logs are searchable in tools like Grafana.
- Dev: uses the Rich package to output logs to the terminal with colors to make them easier to look at.

The logging configuration is set in the root logger, so every logger that you generate like this
```python
import logging
logger = logging.getLogger(__name__)
```
will use by default the handler set for the root logger and will be output properly. This includes logs in
3rd party packages too.

You can log custom JSON using the "extra" argument. Example:
```python
logger.error("This is a test log with extra arguments", extra={
    "test": "I can add any JSON item",
    "test2": "In this extra dictionary",
    "number": 42,
})
```

The Gunicorn loggers are set up in a way that they don't use the root logger. If you want to get the same type 
of logs than the rest you need to execute your application passing the 'logger-class' attribute:
```bash
gunicorn webapp.app:app --logger-class canonicalwebteam.flask_base.log_utils.GunicornDevLogger ...
```

#### Configuring logging

The logging defaults set are good for probably most of the cases and teams, but in case of specific needs 
you can pass to FlaskBase a 'handler' object so that each project can configure logging to their liking. 
The 'handler' has to be of type logging.Handler. Example:
```python
app = FlaskBase(..., handler=myHandler)
```

### Tracing

If tracing is enabled in the project then you can get the trace ID of a request using
```python
from canonicalwebteam.flask_base.opentelemetry.tracing import get_trace_id
trace_id = get_trace_id()
```

The trace ID will also be added by default to all the logs your application prints when it is
available.

Tracing is enabled when setting up the [`tracing`](charmhub.io/integrations/tracing) relation for an application
that uses [paas-charm](https://github.com/canonical/paas-charm/blob/main/src/paas_charm/templates/gunicorn.conf.py.j2).

#### Configuring tracing

There is a parameter that has been added to FlaskBase constructor in order to exclude certain routes from
being traced.
```python
app = FlaskBase(..., untraced_routes=["/demo"])
```

By default, just the "/_status" route is ignored.

### Per route metrics

If a statsd-client is configured (which is enabled by default with 12f apps), FlaskBase will automatically add per route metrics. Including error counts, request counts, and response times.


### ProxyFix

FlaskBase includes [ProxyFix](https://werkzeug.palletsprojects.com/en/3.0.x/middleware/proxy_fix/) to avoid SSL stripping on redirects.

### Redirects and deleted paths

FlaskBase uses [yaml-responses](https://github.com/canonical-web-and-design/canonicalwebteam.yaml-responses) to allow easy configuration of redirects and return of deleted responses, by creating `redirects.yaml`, `permanent-redirects.yaml` and `deleted.yaml` in the site root directory.

### Error templates

`FlaskBase` can optionally use templates to generate the `404` and `500` error responses:

```python3
app = FlaskBase(
    __name__,
    "app.name",
    template_404="404.html",
    template_500="500.html",
)
```

This will lead to e.g. `http://localhost/non-existent-path` returning a `404` status with the contents of `templates/404.html`.

### Redirect /favicon.ico

`FlaskBase` can optionally provide redirects for the commonly queried paths `/favicon.ico`, `/robots.txt` and `/humans.txt` to sensible locations:

```python3
from canonicalwebteam.flask_base.app import FlaskBase

app = FlaskBase(
    __name__,
    "app.name",
    template_404="404.html",
    template_500="500.html",
    favicon_url="/static/favicon.ico",
    robots_url="/static/robots.txt",
    humans_url="/static/humans.txt"
)
```

This will lead to e.g. `http://localhost/favicon.ico` returning a `302` redirect to `http://localhost/static/favicon.ico`.

### Clear trailing slashes

Automatically clears all trailing slashes from all routes.

### Jinja2 helpers

You get two jinja2 helpers to use in your templates from flask-base:

- `now` is a function that outputs the current date in the passed [format](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes) - `{{ now('%Y') }}` -> `YYYY`
- `versioned_static` is a function that fingerprints the passed asset - `{{ versioned_static('asset.js') }}` -> `static/asset?v=asset-hash`

### HTTP headers

You get the following headers automatically set:

- `X-Content-Type-Options: NOSNIFF`
- `Permissions-Policy: interest-cohort=()`
- `X-Frame-Options: SAMEORIGIN`, which can be excluded with `exclude_xframe_options_header` decorator
- `Cache-Control` if `response.cache_control.*` not set and according to static asset versioning (see `versioned_static` above)

### `security.txt`, `robots.txt` and `humans.txt`

If you create a `security.txt`, `robots.txt` or `humans.txt` in the root of your project, these will be served at `/.well-known/security.txt`, `/robots.txt` and `/humans.txt` respectively.

### `/_status/check` endpoint

Automatically adds the `/_status/check` endpoint which is used by content-caches for backend health checking or e.g. by k8s for checking the status of pods.

### Custom gunicorn gevent worker

Included is a custom gunicorn gevent worker designed to handle SIGINT and SIGTERM gracefully, by closing all client connections and logging the stacktrace before exiting.

#### Usage
Run gunicorn in the usual way, but specify the worker class as LogWorker.

```bash
gunicorn webapp.app:app \
    -k canonicalwebteam.flask_base.worker.LogWorker
```

### Planned features

- Add support for open telemetry tracing. Using opentelemetry-instrumentation-flask and opentelemetry-exporter-otlp.

## Tests

To run the tests execute `SECRET_KEY=fake python3 -m unittest discover tests`.

