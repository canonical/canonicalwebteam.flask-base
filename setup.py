from setuptools import setup, find_packages
from os import path
from io import open

here = path.abspath(path.dirname(__file__))
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="canonicalwebteam.flask-base",
    version="0.6.0",
    description="",
    long_description=long_description,
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
        "talisker[gunicorn,flask,prometheus,raven] (>=0.16,<0.17)",
        "gunicorn[gevent]",
        "Werkzeug (>=0.15,<0.16)",
    ],
    dependency_links=[],
    include_package_data=True,
    project_urls={},
)
