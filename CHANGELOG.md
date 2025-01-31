# 2.2.0 (2024-01-32)

Add support for Python 3.12
Update dependencies: talisker, Werkzeug
Remove unused direct dependencies that are used by talisker: gevent, jinja2, markupsafe, itsdangerous gevent, jinja2, markupsafe, itsdangerous

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
