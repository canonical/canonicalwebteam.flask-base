from flask import request
import time
import logging
from urllib.parse import urlparse
import os


class RequestInfo:
    def __init__(self, response):
        self.response_length = response.headers.get('content-length', None)
        self.response_type = response.headers.get('content-type', None)

        self.request_ip = request.remote_addr
        self.request_method = request.method
        self.request_path = request.path
        self.request_protocol = request.environ.get('SERVER_PROTOCOL')
        self.request_referrer = request.referrer
        self.request_user_agent = request.headers.get('User-Agent')

        self.proto = request.environ.get('SERVER_PROTOCOL')
        self.status_code = response.status_code
        self.view_function = request.endpoint


class CustomLoggingFilter(logging.Filter):
    def __init__(self):
        self.record_msg = []
        self.logfmt = None

    def filter(self, record):
        # Get http request url from http request logs
        if record.name == "urllib3.connectionpool":
            if record.levelno == logging.DEBUG:
                message = record.getMessage()
                self.record_msg.append(message)
        return True


DEFAULT_COLOURS = {
        'logfmt': '2;3;36',     # dim italic teal
        'name': '0;33',         # orange
        'msg': '1;16',          # bold white/black, depending on terminal palette
        'time': '2;34',         # dim dark blue
        'DEBUG': '0;32',        # green
        'INFO': '0;32',         # green
        'WARNING': '0;33',      # orange
        'ERROR': '0;31',        # red
        'CRITICAL': '0;31',     # red
    }

COLOUR_SCHEMES = {}
COLOUR_SCHEMES['default'] = DEFAULT_COLOURS

# simple strips italics/bold
COLOUR_SCHEMES['simple'] = DEFAULT_COLOURS.copy()
COLOUR_SCHEMES['simple']['logfmt'] = '0;36'
COLOUR_SCHEMES['simple']['msg'] = '0;37'
COLOUR_SCHEMES['simple']['time'] = '0;34'


class CustomFormatter(logging.Formatter):
    CLEAR = '\x1b[0m'

    def __init__(self, style='default'):
        style = COLOUR_SCHEMES[style]
        self.colours = {k: '\x1b[' + v + 'm' for k, v in style.items()}
        format = (
            '{time}%(asctime)s.%(msecs)03dZ{clear} '
            '%(coloured_levelname)s '
            '{name}%(name)s{clear} '
            '"{msg}%(message)s{clear}"'
            '{logfmt}%(logfmt)s{clear}'
        ).format(clear=self.CLEAR, **self.colours)
        super().__init__(fmt=format)

    def format(self, record):
        default_logfmt = f' service={service} pid={os.getpid()}'
        logfmt = record.__dict__.get('logfmt', {})

        # Add extra attributes to logfmt if present
        if logfmt:
            record.logfmt = logfmt + default_logfmt
        else:
            record.logfmt = default_logfmt

        colour = self.colours[record.levelname]
        record.coloured_levelname = '{colour}{levelname}{clear}'.format(
            colour=colour,
            levelname=record.levelname,
            clear=self.CLEAR,
        )
        return super(CustomFormatter, self).format(record)

# FlaskBase methods
# Global attributes

custom_filter = None
start_time = None
service = None


def set_service(serv):
    global service
    service = serv


def set_start_time():
    global start_time
    start_time = time.time()


def set_custom_filter(filter):
    global custom_filter
    custom_filter = filter


def get_duration():
    return f"{(time.time() - start_time) * 1000.0:.3f}"


def format_logger(logger_name):
    logger = logging.getLogger(logger_name)
    logger.addFilter(custom_filter)
    logger.propagate = True

    return logger


def parse_url(url, proto='http'):
    # urlparse won't parse properly without a protocol
    if '://' not in url:
        url = proto + '://' + url
    return urlparse(url)


def parse_request(request):
    parsed = parse_url(request.url)
    request_type = None
    if parsed.scheme:
        request_type = parsed.scheme + " request"

    return request_type


def enable_requests_logging(response, logger):
    if response is None:
        logger.exception('http request failure')
        return

    format_logger('requests.packages.urllib3')
    request_type = parse_request(request)

    base_host = "base_host"
    base_url = "base_url"
    if request_type:
        meta = get_request_logfmt(response, {'base_url': base_url, 'base_host': base_host})
        logger.info(f'{request_type}', extra={'logfmt': meta})


def set_request_info(response, logger):
    meta = get_request_logfmt(response, None)
    logger.info(f'GET {request.path}', extra={'logfmt': meta})
    enable_requests_logging(response, logger)

    return response


def get_request_logfmt(response, info):    
    rq = RequestInfo(response)
    meta = ''

    # Default attributes
    meta += f' method={rq.request_method}'
    meta += f' status={rq.status_code}'
    meta += f' duration_ms={get_duration()}'

    # http request
    if info:
        meta += f' url={info["base_url"]}'
        meta += f' host={info["base_host"]}'
        meta += f' response_type={rq.response_type}'

    # GET request
    else:
        meta += f' path={rq.request_path}'
        meta += f' view={rq.view_function}'
        meta += f' ip={rq.request_ip}'
        meta += f' proto={rq.proto}'
        meta += f' length={rq.response_length}'
        meta += f' referrer={rq.request_referrer}'
        meta += f' ua={rq.request_user_agent}'

    return meta
