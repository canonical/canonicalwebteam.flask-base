#! /usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name="canonicalwebteam.flask-base",
    version="2.0.0",
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
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    packages=find_packages(),
    install_requires=[
        "canonicalwebteam.yaml-responses[flask] (>=1,<2)",
        "flask==3.1.0",
        "jinja2 >= 3.1.2, < 3.2.0",
        "gevent==24.11.1",
        "greenlet==3.1.1",
        "talisker[gunicorn,gevent,flask,prometheus,raven]",
        "Werkzeug >=3.1.3, <3.2.0",
        "markupsafe >=3, <4",
        "itsdangerous >= 0.24, < 2.2.0",
    ],
    dependency_links=[],
    include_package_data=True,
    project_urls={},
)
