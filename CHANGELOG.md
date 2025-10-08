# 3.1.1 (2025-10-08)

Add missing init file to fix the bug of missing opentelemetry module.

# 3.1.0 (2025-09-24)

- Add prettified logs to Development mode.
- Add JSON structured logs to Production mode.
- The logging "extra" argument can be used to print JSON data out into the logs.
- Custom parameter "handler" of type logging.Handler can be passed to FlaskBase to personalize log output.
- Traces added to logs if tracing is enabled (through paas-charm).
- Custom parameter "untraced_routes" to mark routes for which tracing should not be enabled.

## Upgrade notes

For the production mode to output JSON structured logs you don't need to do anything, as it comes out of the box.
Be aware that you can now pass parameters to the logging method with the "extra" argument and anything you pass
will appear in the structured JSON log.

For the development prettified logs there is one step to be done.
Update your gunicorn entrypoint to add `--logger-class canonicalwebteam.flask_base.log_utils.GunicornDevLogger`
if you are in DEBUG mode.

One can pass a custom logging.Handler to FlaskBase in order to personalize the output of the logs.
All the work of setting the handler in all the appropriate places is done by FlaskBase.

# 3.0.0 (2025-08-01)

- Update to use the latest version of Flask, Werkzeug, gunicorn and gevent.
- Completely remove talisker as a dependency.
- Add per route metrics that report the number of requests, response time, and error rate. (These metrics will be picked up automatically by a statsd-server if you are using the 12f app charm)

## Upgrade notes

This version will require a few updates to remove talisker usage in your application. Namely:

- In your `entrypoint` script, replace `talisker.gunicorn.gevent` with `gunicorn`.
- Replace any instance of `talisker.requests` with `requests`.
- Remove `TALISKER_REVISION_ID` from `Dockerfile`.
- Remove any usage of talisker loggers.
- Remove any usage of `app.extensions["sentry"]` as Sentry support was provided by talisker and is no longer available. You can use the `sentry-sdk` package directly to integrate Sentry into your Flask application.

# 2.4.0 (2025-03-21)

Fix Werkzeug version limit to work with current Flask `2.3.3`.

# 2.3.0 (2025-02-28)

Add response content compression using Gzip

# 2.2.2 (2025-02-17)

Fix forwarded IP header to use `X-Original-Forwarded-For` in priority over `X-Forwarded-For`.

# 2.2.1 (2025-02-12)

Revert `2.1.0` changes to compression of JS and CSS assets

# 2.2.0 (2025-01-32)

- Add support for Python 3.12
- Update dependencies: talisker, Werkzeug
- Remove unused direct dependencies that are used by talisker: gevent, jinja2, markupsafe, itsdangerous gevent, jinja2, markupsafe, itsdangerous

## Upgrade notes

This version will require changes in the `Dockerfile` to use a virtual environment as this is mandatory for Python 3.12.

Here is an example of how to upgrade to `2.2.0`: [canonical/ubuntu.com@82f04d9](https://github.com/canonical/ubuntu.com/pull/14699/commits/82f04d909c81f4495669b1dbc28b7051e77ca2f2)

# 2.1.0 (2025-01-23)

Add compression of JS and CSS assets

# 2.0.0 (2024-07-04)

Pin to Flask 2.3.3
Update dependencies: jinja2, Werkzeug, markupsafe, itsdangerous

# 1.0.6 (2022-08-04)

Disable MIME-sniffing with `x-content-type-options: NOSNIFF` ([rationale here](https://github.com/canonical/web-design-systems-squad/issues/77#issuecomment-1205100399))

# 1.0.5 (2022-05-05)

Pin to Flask 1.1.2 to avoid dependency conflicts

# 1.0.4 (2022-04-26)

Added support for security.txt files

# 1.0.3 (2022-03-29)

Fix dependencies for Flask 1.1.x: jinja2

# 1.0.2 (2022-03-21)

Pass through error messages from flask.abort to 404.html and 500.html templates

# 1.0.1 (2022-02-21)

Fix dependencies for Flask 1.1.x: markupsafe and itsdangerous.

# 1.0.0 (2021-10-27)

Upgrade dependencies: Werkzeug and gevent.

# 0.9.3 (2021-10-27)

Include PID on Talisker logs

# 0.9.2 (2021-10-27)

Check static files against provided `?v=` hashes

# 0.9.0 (2021-04-15)

Add header: `Permissions-Policy: interest-cohort=()` that disables FLoC for privacy reasons.

# 0.8.0 (2021-03-19)

Change default caching headers to `cache-control: max-age=60, stale-while-revalidate=86400, stale-if-error=300`.
Make them individually overrideable.

# 0.7.2 (2021-01-07)

### Added

Added the security header "X-Frame-Options" with the value "SAMEORIGIN"

# 0.7.1 (2020-11-23)

### Added

Changed `SEND_FILE_MAX_AGE_DEFAULT` back to the default value
Set `Cache-Control: max-age 31536000` for requests with the v in the query string

# 0.7.0 (2020-11-18)

### Added

Set `SEND_FILE_MAX_AGE_DEFAULT` to a year (31536000)

# 0.6.4 (2020-09-22)

### Added

Pin gevent to version 20.6.2
Pin greenlet to version 0.4.16

# 0.6.3 (2020-05-27)

### Added

Pin gevent to version 20.6.1

# 0.6.2 (2020-06-11)

### Fix

`versioned_static` shouldn't break the app if files are missing

# 0.6.1 (2020-05-20)

### Features

Serve favicon from static if it exists, otherwise fallback to favicon url.

# 0.6.0 (2020-04-14)

### Added

Update to talisker 0.18.0

# 0.5.1 (2020-04-14)

### Added

Pin gevent to version 1.4.0

# 0.4.0 (2020-02-10)

### Added

Set cache headers for all responses, overridable in the view.

# 0.2.0 (2019-06-10)

### Features

Added a context processor to FlaskBase instances containing common helpers needed acrosss
diferent apps.

# 0.1.0 (2019-06-05)

### Features

Added FlaskBase class to wrap common functionality of canonical webteamm's flask applications
