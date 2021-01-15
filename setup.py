from setuptools import setup, find_packages

setup(
    name="canonicalwebteam.flask-base",
    version="0.7.3",
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
        "gevent==20.6.2",
        "greenlet==0.4.16",
        "talisker[gunicorn,gevent,flask,prometheus,raven] (>=0.18)",
        "Werkzeug (>=0.15,<0.16)",
    ],
    dependency_links=[],
    include_package_data=True,
    project_urls={},
)
