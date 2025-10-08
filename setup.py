#! /usr/bin/env python3

from setuptools import find_packages, setup

setup(
    name="canonicalwebteam.flask-base",
    version="3.1.1",
    description=(
        "Flask extension that applies common configurations"
        "to all of webteam's flask apps."
    ),
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Canonical webteam",
    author_email="webteam@canonical.com",
    url="https://github.com/canonical-web-and-design/canonicalwebteam.flask-base",
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Topic :: Internet :: WWW/HTTP :: WSGI",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Middleware",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
    packages=find_packages(),
    install_requires=[
        "canonicalwebteam.yaml-responses[flask] (>=1,<2)",
        "Werkzeug",
        "flask",
        "gunicorn",
        "gevent",
        "statsd",
        "flask-compress==1.17",
        "rich",
        "python-json-logger",
        # Observability
        "opentelemetry-api",
        "opentelemetry-exporter-otlp",
        "opentelemetry-exporter-otlp-proto-http",
        "opentelemetry-instrumentation",
        "opentelemetry-instrumentation-wsgi",
        "opentelemetry-instrumentation-flask",
        "opentelemetry-instrumentation-requests",
        "opentelemetry-sdk",
    ],
    dependency_links=[],
    include_package_data=True,
    project_urls={},
)
