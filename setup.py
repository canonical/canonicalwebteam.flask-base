#! /usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name="canonicalwebteam.flask-base",
    version="1.0.0",
    description=(
        "Flask extension that applies common configurations"
        "to all of webteam's flask apps."
    ),
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Canonical webteam",
    author_email="webteam@canonical.com",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    packages=find_packages(),
    install_requires=[
        "canonicalwebteam.yaml-responses[flask] (>=1,<2)",
        "flask (>=1,<2)",
        "gevent==21.12.0",
        "greenlet==1.1.2",
        "talisker[gunicorn,gevent,flask,prometheus,raven]==0.19.0",
        "Werkzeug (>=1.0.0, <1.2)",
    ],
    dependency_links=[],
    include_package_data=True,
    project_urls={},
)
