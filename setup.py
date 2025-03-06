#! /usr/bin/env python3

from setuptools import find_packages, setup

setup(
    name="canonicalwebteam.flask-base",
    version="2.3.0",
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
        "talisker[gunicorn,gevent,flask,prometheus,raven] >= 0.21.4",
        "Werkzeug >= 2.3.7",
        # Use latest version of Flask once Talisker supports werkzeug >=3
        "flask==2.3.3",
        "flask-compress==1.17",
    ],
    dependency_links=[],
    include_package_data=True,
    project_urls={},
)
