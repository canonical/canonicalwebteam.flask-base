import os


class BaseConfig(object):
    SECRET_KEY = os.getenv("SECRET_KEY", "base_secret")
